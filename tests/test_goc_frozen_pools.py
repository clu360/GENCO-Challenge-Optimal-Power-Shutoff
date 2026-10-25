import csv
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT=Path(__file__).resolve().parents[1]


def test_original_ordered_goc_pools_match_manifest_and_recorded_searches():
    directory=ROOT/'experiments/goc_500/configs/historical/frozen_pools'
    manifest=json.loads((directory/'MANIFEST.json').read_text())
    actual=pd.read_parquet(ROOT/'experiments/goc_500/results/ft3_ft4/topology_objectives_all.parquet')
    assert len(manifest['records'])==30 and manifest['settings']==15
    assert manifest['fresh_topology_discovery'] is False
    total=0
    for record in manifest['records']:
        path=directory/record['setting_code']/record['pool_name']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
        assert path.stat().st_size==record['bytes']
        with path.open(newline='') as handle:
            rows=list(csv.DictReader(handle))
        assert len(rows)==record['row_count']
        setting=record['setting_code']
        scenario='J-S'+setting[1]
        weight=float(setting.split('_l')[1].replace('p','.'))
        subset=actual.loc[actual.scenario_id.eq(scenario)&actual.lambda_r.eq(weight)]
        for expected in rows:
            rank=int(expected['rank'])
            method='Guided-GridSFM' if record['pool_name']=='guided.csv' else 'TH-GridSFM-top'+expected['th_k']
            selected=subset.loc[subset.method.eq(method)&subset.topology_rank.eq(rank)]
            assert len(selected)==1
            row=selected.iloc[0]
            topology='' if pd.isna(row.topology_id) else str(row.topology_id)
            assert topology==expected['shutoff_branch_ids']
            assert int(row.num_shutoffs)==int(expected['num_shutoffs'])
            total+=1
    assert total==1530 and len(actual)==1530
