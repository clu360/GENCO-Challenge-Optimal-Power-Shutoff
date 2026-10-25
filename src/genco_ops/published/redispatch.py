
"""Scenario-16 generator eligibility and frozen bidirectional-headroom audit."""
from __future__ import annotations
import pandas as pd
from .identity import StageKIdentity

def audit_generators(identity: StageKIdentity) -> pd.DataFrame:
    gens = identity.generators.copy()
    ref_buses = set(identity.buses.loc[identity.buses['BUS_TYPE'].astype(int) == 3, 'bus_id'].astype(int))
    out = pd.DataFrame({'canonical_generator_id': gens['canonical_generator_id'].astype(int), 'bus_id': gens['bus_id'].astype(int), 'online': gens['GEN_STATUS'].astype(int) > 0, 'slack_reference': gens['bus_id'].astype(int).isin(ref_buses), 'pg0_mw': gens['PG'].astype(float), 'pmin_mw': gens['PMIN'].astype(float), 'pmax_mw': gens['PMAX'].astype(float)})
    out['upward_headroom_mw'] = out['pmax_mw'] - out['pg0_mw']
    out['downward_headroom_mw'] = out['pg0_mw'] - out['pmin_mw']
    out['bidirectional_headroom_mw'] = out[['upward_headroom_mw', 'downward_headroom_mw']].min(axis=1)
    out['eligible'] = out['online'] & ~out['slack_reference'] & (out['bidirectional_headroom_mw'] > 0.0)
    return out.sort_values(['eligible', 'bidirectional_headroom_mw', 'canonical_generator_id'], ascending=[False, False, True]).reset_index(drop=True)

def frozen_top10(identity: StageKIdentity) -> tuple[int, ...]:
    rows = audit_generators(identity)
    return tuple(rows.loc[rows['eligible'], 'canonical_generator_id'].head(10).astype(int))

def redispatch_from_r(identity: StageKIdentity, r_by_generator: dict[int, float]) -> dict[int, float]:
    gens = identity.generators.set_index('canonical_generator_id')
    delta = {}
    for gen_id, r in r_by_generator.items():
        if not -1.0 <= float(r) <= 1.0:
            raise ValueError(f'r[{gen_id}] outside [-1, 1]')
        row = gens.loc[int(gen_id)]
        headroom = float(row.PMAX - row.PG) if r >= 0 else float(row.PG - row.PMIN)
        delta[int(gen_id)] = float(r) * headroom
    return delta
