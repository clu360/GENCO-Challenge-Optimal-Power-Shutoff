from __future__ import annotations
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import torch
from .adapter import AdapterResult,to_heterodata
from ..objectives import compute_j_trade,compute_l_shed,compute_r_norm
def _namespace(value):
    if isinstance(value, dict):
        return SimpleNamespace(**{k: _namespace(v) for k, v in value.items()})
    return value

def _args(task: str):
    return _namespace({'task': {'task_name': task}, 'data': {'baseMVA': 100.0, 'mask_value': 0.0}, 'model': {'attention_head': 8, 'edge_dim': 10, 'hidden_size': 48, 'input_bus_dim': 15, 'input_gen_dim': 6, 'output_bus_dim': 2, 'output_gen_dim': 1, 'num_layers': 12, 'dropout': 0.0}})

def _prepare(result: AdapterResult, task: str, stats: dict, device: torch.device):
    from gridfm_graphkit.datasets.normalizers import HeteroDataMVANormalizer
    from gridfm_graphkit.datasets.task_transforms import OptimalPowerFlowTransforms, PowerFlowTransforms
    data = to_heterodata(result)
    normalizer = HeteroDataMVANormalizer(_args(task))
    normalizer.fit_from_dict(stats)
    normalizer.transform(data)
    normalized_before_mask = deepcopy(data)
    transform = OptimalPowerFlowTransforms(_args(task)) if task == 'OptimalPowerFlow' else PowerFlowTransforms(_args(task))
    data = transform(data)
    return (data.to(device), normalized_before_mask, normalizer)

def _known_input_checks(result: AdapterResult, normalized, masked, task: str, stats: dict) -> dict:
    base = float(stats['baseMVA'])
    pd_cmd = torch.tensor(result.bus['Pd'].to_numpy(), dtype=torch.float32) / base
    qd_cmd = torch.tensor(result.bus['Qd'].to_numpy(), dtype=torch.float32) / base
    checks = {'pd_before_mask': torch.allclose(normalized['bus'].x[:, 0], pd_cmd, atol=1e-06), 'qd_before_mask': torch.allclose(normalized['bus'].x[:, 1], qd_cmd, atol=1e-06), 'pd_after_mask': torch.allclose(masked['bus'].x[:, 0].cpu(), pd_cmd, atol=1e-06), 'qd_after_mask': torch.allclose(masked['bus'].x[:, 1].cpu(), qd_cmd, atol=1e-06)}
    if task == 'PowerFlow':
        online_mask = result.gen['in_service'].to_numpy() == 1
        active = result.gen.loc[online_mask].reset_index(drop=True)
        pg_cmd = torch.tensor(active['p_mw'].to_numpy(), dtype=torch.float32) / base
        ref_bus = result.bus.loc[result.bus['REF'] == 1, 'bus'].astype(int).tolist()
        nonref = ~active['bus'].isin(ref_bus).to_numpy()
        checks['nonref_pg_before_mask'] = torch.allclose(normalized['gen'].x[online_mask, 0][nonref], pg_cmd[nonref], atol=1e-06)
        checks['nonref_pg_after_mask'] = torch.allclose(masked['gen'].x[nonref, 0].cpu(), pg_cmd[nonref], atol=1e-06)
    return {key: bool(value) for key, value in checks.items()}

def _case_metrics(identity, result: AdapterResult, output, data, normalizer, lambda_r: float) -> tuple[dict, dict]:
    bus_out = output['bus'].detach().cpu().clone()
    gen_out = output['gen'].detach().cpu().clone()
    edge_index = data.edge_index_dict['bus', 'connects', 'bus']
    edge_attr = data.edge_attr_dict['bus', 'connects', 'bus']
    from gridfm_graphkit.models.utils import ComputeBranchFlow
    p, q = ComputeBranchFlow()(output['bus'], edge_index, edge_attr)
    p_flow = p.detach().cpu().numpy() * float(normalizer.baseMVA)
    q_flow = q.detach().cpu().numpy() * float(normalizer.baseMVA)
    flow = np.sqrt(p_flow ** 2 + q_flow ** 2)
    normalizer.inverse_output({'bus': bus_out, 'gen': gen_out}, None)
    active_ids = result.branch.loc[result.branch['br_status'] == 1, 'canonical_branch_id'].astype(int).tolist()
    count = len(active_ids)
    rating = result.branch.loc[result.branch['br_status'] == 1, 'rate_a'].to_numpy(float)
    loading = np.maximum(flow[:count], flow[count:]) / rating
    loading_by_id = dict(zip(active_ids, loading, strict=True))
    p_env = identity.branches.set_index('canonical_branch_id')['p_env'].astype(float).to_dict()
    baseline = identity.branches.set_index('canonical_branch_id')['baseline_loading'].astype(float).to_dict()
    offline = result.branch.loc[result.branch['br_status'] == 0, 'canonical_branch_id'].astype(int).tolist()
    r_norm = compute_r_norm(identity.l_trans, offline, p_env, loading_by_id, 32.975425699285616)
    pd = identity.loads.set_index('canonical_load_id')['pd_requested_mw'].astype(float).to_dict()
    l_shed = compute_l_shed(pd, result.alpha_effective)
    vmin = result.bus['min_vm_pu'].to_numpy(float)
    vmax = result.bus['max_vm_pu'].to_numpy(float)
    vm = bus_out[:, 0].numpy()
    voltage_pac = float(np.mean(np.maximum(0.0, vm - vmax) ** 2 + np.maximum(0.0, vmin - vm) ** 2))
    thermal_pac = float(np.mean(np.maximum(0.0, loading - 1.0) ** 2))
    active_gen = result.gen.loc[result.gen['in_service'] == 1].reset_index(drop=True)
    pg = gen_out[:, 0].numpy()
    span = np.maximum(active_gen['max_p_mw'].to_numpy(float) - active_gen['min_p_mw'].to_numpy(float), 1e-09)
    pmin = active_gen['min_p_mw'].to_numpy(float)
    pmax = active_gen['max_p_mw'].to_numpy(float)
    gen_p_pac = float(np.mean((np.maximum(0.0, pg - pmax) / span) ** 2 + (np.maximum(0.0, pmin - pg) / span) ** 2))
    metrics = {'r_norm': r_norm, 'l_shed': l_shed, 'j_trade_lambda_0p5': compute_j_trade(lambda_r, r_norm, l_shed), 'max_loading': float(np.max(loading)), 'overloaded_lines': int(np.sum(loading > 1.0)), 'vm_min': float(bus_out[:, 0].min()), 'vm_max': float(bus_out[:, 0].max()), 'pac_thermal': thermal_pac, 'pac_voltage': voltage_pac, 'pac_generator_p': gen_p_pac, 'pac_operational': thermal_pac + voltage_pac + gen_p_pac, 'pac_ac': None, 'pac_ac_note': 'GENCO checkpoint has no GridSFM feasibility head; exact AC reference required', 'finite_output': bool(torch.isfinite(bus_out).all() and torch.isfinite(gen_out).all())}
    decoded = {'bus': {'Vm_pu': bus_out[:, 0].tolist(), 'Va_rad': bus_out[:, 1].tolist(), 'Pg_mw': bus_out[:, 2].tolist(), 'Qg_mvar': bus_out[:, 3].tolist()}, 'generator_pg_mw': gen_out[:, 0].tolist(), 'branch': {'canonical_branch_id': active_ids, 'loading': loading.tolist(), 'forward_s_mva': flow[:count].tolist(), 'reverse_s_mva': flow[count:].tolist(), 'p_from_mw': p_flow[:count].tolist(), 'q_from_mvar': q_flow[:count].tolist(), 'p_to_mw': p_flow[count:].tolist(), 'q_to_mvar': q_flow[count:].tolist()}}
    return (metrics, decoded)
