
"""Deterministic modified-Texas2k to official GENCO GraphKit adapter."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping
import networkx as nx
import numpy as np
import pandas as pd
from .identity import StageKIdentity
from .service import effective_alpha

@dataclass(frozen=True)
class AdapterResult:
    bus: pd.DataFrame
    gen: pd.DataFrame
    branch: pd.DataFrame
    alpha_effective: dict[int, float]
    source_less_load_ids: tuple[int, ...]
    mapping: dict[str, object]
    sourced_components: tuple[tuple[int, ...], ...]

def _admittance(row) -> tuple[complex, complex, complex, complex, float]:
    z = complex(float(row.BR_R), float(row.BR_X))
    if abs(z) == 0.0:
        raise ValueError(f'zero series impedance on branch {row.canonical_branch_id}')
    y = 1.0 / z
    charging = 0.5j * float(row.BR_B)
    tap = float(row.TAP) if abs(float(row.TAP)) > 1e-12 else 1.0
    phase = np.deg2rad(float(row.SHIFT))
    complex_tap = tap * np.exp(1j * phase)
    yff = (y + charging) / (tap * tap)
    yft = -y / np.conj(complex_tap)
    ytf = -y / complex_tap
    ytt = y + charging
    return (yff, yft, ytf, ytt, tap)

def _components(identity: StageKIdentity, offline: set[int]) -> tuple[tuple[int, ...], ...]:
    graph = nx.Graph()
    graph.add_nodes_from(identity.buses['bus_id'].astype(int))
    active = identity.branches.loc[(identity.branches['status'].astype(int) > 0) & ~identity.branches['canonical_branch_id'].astype(int).isin(offline)]
    graph.add_edges_from(active[['from_bus_id', 'to_bus_id']].itertuples(index=False, name=None))
    source = set(identity.generators.loc[identity.generators['GEN_STATUS'] > 0, 'bus_id'].astype(int))
    return tuple((tuple(sorted(component)) for component in sorted(nx.connected_components(graph), key=lambda c: min(c)) if source.intersection(component)))

def build_tables(identity: StageKIdentity, *, offline_branch_ids: Iterable[int]=(), alpha_requested: Mapping[int, float] | None=None, redispatch_mw: Mapping[int, float] | None=None) -> AdapterResult:
    """Build official GraphKit raw tables without candidate-dependent indexing."""
    offline = {int(x) for x in offline_branch_ids}
    unknown = offline.difference(identity.l_trans)
    if unknown:
        raise ValueError(f'non-switchable branches requested offline: {sorted(unknown)}')
    requested = {int(k): float(v) for k, v in (alpha_requested or {}).items()}
    alpha, source_less = effective_alpha(identity, offline, requested)
    redispatch = {int(k): float(v) for k, v in (redispatch_mw or {}).items()}
    buses = identity.buses.sort_values('canonical_bus_index').copy()
    if not np.array_equal(buses['canonical_bus_index'].to_numpy(), np.arange(len(buses))):
        raise ValueError('canonical bus indices are not contiguous')
    bus_index = buses.set_index('bus_id')['canonical_bus_index'].astype(int).to_dict()
    load = identity.loads.copy()
    load['alpha'] = load['canonical_load_id'].astype(int).map(alpha)
    load['Pd'] = load['pd_requested_mw'] * load['alpha']
    load['Qd'] = load['qd_requested_mvar'] * load['alpha']
    demand = load.groupby('bus_id')[['Pd', 'Qd']].sum()
    gens = identity.generators.sort_values('canonical_generator_id').copy()
    cost = identity.gencost.iloc[gens['canonical_generator_id'].astype(int)].reset_index(drop=True)
    gens['p_command_mw'] = gens['PG'].astype(float) + gens['canonical_generator_id'].astype(int).map(redispatch).fillna(0.0)
    online = gens['GEN_STATUS'].astype(int) > 0
    if ((gens.loc[online, 'p_command_mw'] < gens.loc[online, 'PMIN'] - 1e-09) | (gens.loc[online, 'p_command_mw'] > gens.loc[online, 'PMAX'] + 1e-09)).any():
        raise ValueError('redispatch command violates a generator active-power bound')
    q_agg = gens.loc[online].groupby('bus_id')['QG'].sum()
    qmin = gens.loc[online].groupby('bus_id')['QMIN'].sum()
    qmax = gens.loc[online].groupby('bus_id')['QMAX'].sum()
    bus_table = pd.DataFrame({'bus': buses['canonical_bus_index'].astype(int), 'Pd': buses['bus_id'].map(demand.get('Pd', pd.Series(dtype=float))).fillna(0.0), 'Qd': buses['bus_id'].map(demand.get('Qd', pd.Series(dtype=float))).fillna(0.0), 'Qg': buses['bus_id'].map(q_agg).fillna(0.0), 'Vm': buses['VM'].astype(float), 'Va': buses['VA'].astype(float), 'PQ': (buses['BUS_TYPE'].astype(int) == 1).astype(int), 'PV': (buses['BUS_TYPE'].astype(int) == 2).astype(int), 'REF': (buses['BUS_TYPE'].astype(int) == 3).astype(int), 'min_vm_pu': buses['VMIN'].astype(float), 'max_vm_pu': buses['VMAX'].astype(float), 'min_q_mvar': buses['bus_id'].map(qmin).fillna(0.0), 'max_q_mvar': buses['bus_id'].map(qmax).fillna(0.0), 'GS': buses['GS'].astype(float) / 100.0, 'BS': buses['BS'].astype(float) / 100.0, 'vn_kv': buses['BASE_KV'].astype(float)})
    gen_table = pd.DataFrame({'canonical_generator_id': gens['canonical_generator_id'].astype(int), 'bus': gens['bus_id'].map(bus_index).astype(int), 'p_mw': gens['p_command_mw'].astype(float), 'min_p_mw': gens['PMIN'].astype(float), 'max_p_mw': gens['PMAX'].astype(float), 'cp0_eur': cost['C0'].astype(float), 'cp1_eur_per_mw': cost['C1'].astype(float), 'cp2_eur_per_mw2': cost['C2'].astype(float), 'in_service': gens['GEN_STATUS'].astype(int)})
    branch_rows = []
    for row in identity.branches.sort_values('canonical_branch_id').itertuples(index=False):
        yff, yft, ytf, ytt, tap = _admittance(row)
        branch_rows.append({'canonical_branch_id': int(row.canonical_branch_id), 'from_bus': bus_index[int(row.from_bus_id)], 'to_bus': bus_index[int(row.to_bus_id)], 'pf': 0.0, 'qf': 0.0, 'pt': 0.0, 'qt': 0.0, 'Yff_r': yff.real, 'Yff_i': yff.imag, 'Yft_r': yft.real, 'Yft_i': yft.imag, 'Ytt_r': ytt.real, 'Ytt_i': ytt.imag, 'Ytf_r': ytf.real, 'Ytf_i': ytf.imag, 'tap': tap, 'ang_min': float(row.ANGMIN), 'ang_max': float(row.ANGMAX), 'rate_a': float(row.rate_a_mva), 'br_status': int(int(row.status) > 0 and int(row.canonical_branch_id) not in offline)})
    branch_table = pd.DataFrame(branch_rows)
    active_ids = branch_table.loc[branch_table['br_status'] == 1, 'canonical_branch_id'].astype(int).tolist()
    edge_map = {str(branch_id): {'forward': i, 'reverse': i + len(active_ids)} for i, branch_id in enumerate(active_ids)}
    active_gens = gen_table.loc[gen_table['in_service'] == 1, 'canonical_generator_id'].astype(int).tolist()
    mapping = {'bus_id_to_model_index': {str(k): int(v) for k, v in bus_index.items()}, 'active_generator_id_to_model_index': {str(k): i for i, k in enumerate(active_gens)}, 'active_branch_id_to_directed_edges': edge_map, 'canonical_orientation': {str(r.canonical_branch_id): [int(r.from_bus_id), int(r.to_bus_id)] for r in identity.branches.itertuples(index=False)}}
    return AdapterResult(bus_table, gen_table, branch_table, alpha, source_less, mapping, _components(identity, offline))

def to_heterodata(result: AdapterResult):
    """Delegate tensor construction to the pinned official GraphKit function."""
    from gridfm_graphkit.datasets.hetero_preprocess import build_hetero_data_for_scenario
    return build_hetero_data_for_scenario(0, result.bus, result.gen, result.branch)
