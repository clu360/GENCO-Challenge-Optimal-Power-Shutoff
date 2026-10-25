"""Canonical identity from explicitly supplied, hash-bound prepared study tables."""
from dataclasses import dataclass
from pathlib import Path
import json

import pandas as pd

from ..artifacts import checked_path,sha
from ..demo_physics import BranchIdentity,GOC500Identity,LoadIdentity
from ..demo_physics import source_less_load_ids as stage_j_source_less


@dataclass(frozen=True)
class StageKIdentity:
    buses: pd.DataFrame
    loads: pd.DataFrame
    generators: pd.DataFrame
    branches: pd.DataFrame
    branch_model_mapping: pd.DataFrame
    stage_j_identity: GOC500Identity
    gencost: pd.DataFrame

    @property
    def l_trans(self):
        return tuple(self.branches.loc[self.branches.is_switchable_transmission,'canonical_branch_id'].astype(int))

    @property
    def l_fixed(self):
        return tuple(self.branches.loc[~self.branches.is_switchable_transmission,'canonical_branch_id'].astype(int))


def source_less_load_ids(identity,offline_branch_ids):
    return stage_j_source_less(identity.stage_j_identity,offline_branch_ids)


def load_identity(directory,config):
    directory=Path(directory).resolve()
    contract=json.loads((directory/'input_contract.json').read_text())
    if (contract['schema']!='PUBLISHED_TEXAS2K_SCENARIO16_INPUTS_V1'
            or contract['case_sha256']!=config['case_sha256']
            or contract['r_base']!=config['risk_base']
            or contract['weather_timestamp_utc']!='2023-06-23T21:00:00Z'
            or contract['scenario']!=16):
        raise ValueError('prepared inputs differ from the frozen Scenario16/hazard contract')
    expected=config['prepared_artifacts_sha256']
    if any(contract['files'].get(name)!=value for name,value in expected.items()):
        raise ValueError('prepared inputs do not match the published artifact identities')
    for name,value in contract['files'].items():
        if sha(checked_path(directory,name))!=value:raise ValueError('prepared input changed: '+name)
    if contract['gencost_sha256']!=contract['files'].get('gencost.parquet'):
        raise ValueError('generator costs lack an explicit immutable binding')
    buses=pd.read_parquet(directory/'canonical_bus.parquet')
    loads=pd.read_parquet(directory/'canonical_load.parquet')
    generators=pd.read_parquet(directory/'canonical_generator.parquet')
    branches=pd.read_parquet(directory/'canonical_branch.parquet')
    mapping=pd.read_parquet(directory/'branch_model_mapping.parquet')
    cost=pd.read_parquet(directory/'gencost.parquet')
    if len(cost)!=len(generators):raise ValueError('generator/cost row count mismatch')
    if any(frame[column].duplicated().any() for frame,column in ((buses,'bus_id'),(loads,'canonical_load_id'),
            (generators,'canonical_generator_id'),(branches,'canonical_branch_id'))):
        raise ValueError('canonical physical identities are duplicated')
    records=tuple(BranchIdentity(canonical_branch_id=int(row.canonical_branch_id),
        original_case_branch_id=int(row.powermodels_branch_id),edge_family=str(row.branch_family),
        family_index=int(mapping.loc[idx,'model_family_index']),from_bus_id=int(row.from_bus_id),
        to_bus_id=int(row.to_bus_id),from_bus_index=int(row.from_row_id),to_bus_index=int(row.to_row_id),
        orientation_sign=1,rate_a=float(row.rate_a_mva),is_risk=bool(row.is_switchable_transmission),
        is_candidate=bool(row.is_switchable_transmission)) for idx,row in branches.iterrows())
    index=buses.set_index('bus_id').canonical_bus_index.to_dict()
    load_records=tuple(LoadIdentity(canonical_load_id=int(row.canonical_load_id),load_index=int(row.canonical_load_id),
        bus_id=int(row.bus_id),bus_index=int(index[int(row.bus_id)]),pd_pre=float(row.pd_requested_mw),
        qd_pre=float(row.qd_requested_mvar)) for row in loads.itertuples(index=False))
    sources=tuple(sorted(set(generators.loc[generators.GEN_STATUS>0,'bus_id'].astype(int))))
    j_identity=GOC500Identity(branches=records,loads=load_records,bus_ids=tuple(buses.bus_id.astype(int)),
        generator_bus_ids=sources)
    identity=StageKIdentity(buses,loads,generators,branches,mapping,j_identity,cost)
    proxy=pd.read_parquet(directory/'proxy_components.parquet')
    if proxy.canonical_branch_id.duplicated().any() or set(proxy.canonical_branch_id)!=set(identity.l_trans):
        raise ValueError('risk proxy does not cover the switching universe')
    view=branches.set_index('canonical_branch_id')
    for row in proxy.itertuples(index=False):
        original=view.loc[row.canonical_branch_id]
        if (row.p_env!=original.p_env or row.baseline_loading!=original.baseline_loading
                or row.weight!=float(row.p_env)*float(row.baseline_loading)**2):
            raise ValueError('stored wildfire proxy values changed')
    return identity,contract
