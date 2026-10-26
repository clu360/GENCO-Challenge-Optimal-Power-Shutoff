"""Publication checks guard population and interpretation rather than plot styling."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'submission/data'


def test_compact_evidence_hashes_and_populations():
    manifest = json.loads((DATA / 'provenance.json').read_text(encoding='utf-8'))
    for name, entry in manifest['exports'].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == entry['sha256']
    validation = pd.read_csv(DATA / 'texas_validation.csv')
    assert len(validation) == 9
    assert set(validation.distribution) == {'G', 'R', 'W'}
    assert set(validation.cases) == {100}
    assert set(pd.read_csv(DATA / 'goc_agreement.csv').selected_decisions) == {15}


def test_selected_ac_comparison_preserves_limits():
    selected = pd.read_csv(DATA / 'texas_selected_ac.csv').set_index('model')
    assert len(selected) == 3
    assert (selected.a_r > 1).all()
    assert selected.loc['GENCO G100 -> R400', 'topology_key'] == selected.loc['GENCO G100 -> W400', 'topology_key'] == '117;281'
    assert np.isclose(selected.loc['GENCO G500', 'a_r'], 1.1641443400722764)
    assert np.isclose(selected.loc['GENCO G100 -> R400', 'a_r'], 1.0890420110534258)
    g = pd.read_csv(DATA / 'texas_validation.csv').query("distribution == 'G'")
    assert (g.mean_worst_bus_abs_p_mw > 6000).all()
    assert (g.mean_bus_abs_p_mw < 53).all()


def test_publication_builder_is_standalone():
    builder = (ROOT / 'submission/build_submission.py').read_text(encoding='utf-8')
    assert 'experiments/test/' not in builder
    assert "HERE / 'data'" in builder
