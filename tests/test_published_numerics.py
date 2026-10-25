import ast
import hashlib
import json
from pathlib import Path

import pytest

from genco_ops.published.search import sequential_powell,ALPHA_SEARCH_ID
from genco_ops.published.journal import SurrogateJournal,UncertainSurrogateCall
from genco_ops.published.io import atomic_json
from genco_ops.artifacts import configure_native_cache


ROOT=Path(__file__).resolve().parents[1]


def test_native_cache_uses_only_the_explicit_checkout(tmp_path,monkeypatch):
    import os
    monkeypatch.setenv('XDG_CACHE_HOME','unused-old-cache')
    path=configure_native_cache(tmp_path)
    assert path==tmp_path/'outputs/runtime_cache'
    assert os.environ['XDG_CACHE_HOME']==str(path)
    assert path.exists()


def test_numerical_exports_match_their_scoped_source_manifest():
    directory=ROOT/'src/genco_ops/published'
    manifest=json.loads((directory/'SOURCE_EXPORT.json').read_text())
    for name,item in manifest.items():
        path=directory/(name+'.py')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['exported_sha256']
        tree=ast.parse(path.read_text())
        assert 'sys.path' not in ast.unparse(tree)
        assert 'experiments.test' not in ast.unparse(tree)
        definitions={node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
        for key,expected in item['definitions'].items():
            assert hashlib.sha256(ast.dump(definitions[key],include_attributes=False).encode()).hexdigest()==expected


def test_original_alpha_optimizer_counts_actual_calls_and_reuses_points():
    calls=[]
    def evaluate(x):
        calls.append(x)
        return dict(eligible=True,search_objective=sum((v-.75)**2 for v in x),effective_x=x)
    result=sequential_powell(alpha0=[1.]*5,alpha_bounds=[(0.,1.)]*5,evaluate=evaluate)
    assert result.search_id==ALPHA_SEARCH_ID
    assert len(calls)==len(result.trace)<=20
    assert len(set(calls))==len(calls)
    assert result.blocks[0]['budget']==20
    assert result.best_payload is not None


def test_original_journal_replays_without_spending_and_stops_uncertain_calls(tmp_path):
    journal=SurrogateJournal(tmp_path/'good',{'request':'frozen'})
    calls=[]
    value,replayed=journal.call([1.],lambda:calls.append(1) or {'score':2.})
    assert value=={'score':2.} and replayed is False
    value,replayed=SurrogateJournal(tmp_path/'good',{'request':'frozen'}).call([1.],lambda:pytest.fail('no repeated inference'))
    assert replayed is True and calls==[1]
    bad=SurrogateJournal(tmp_path/'uncertain',{'request':'frozen'})
    with pytest.raises(RuntimeError):bad.call([1.],lambda:(_ for _ in ()).throw(RuntimeError('interrupted')))
    with pytest.raises(UncertainSurrogateCall):
        SurrogateJournal(tmp_path/'uncertain',{'request':'frozen'}).call([1.],lambda:pytest.fail('no blind retry'))
