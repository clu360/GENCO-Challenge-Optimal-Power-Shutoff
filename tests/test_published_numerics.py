import ast
import hashlib
import json
from pathlib import Path

import pytest

from genco_ops.published.search import sequential_powell,ALPHA_SEARCH_ID
from genco_ops.published.journal import SurrogateJournal,UncertainSurrogateCall
from genco_ops.published.io import atomic_json
from genco_ops.artifacts import configure_native_cache
from genco_ops.published import runner
from genco_ops.published.identity import load_identity


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


def test_dry_run_never_enters_model_or_execution_preflight(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'plan',lambda *a,**k:({'identity_sha256':'a'*64},object()))
    monkeypatch.setattr(runner,'verify',lambda *a:pytest.fail('no execution preflight in dry run'))
    result=runner.run(ROOT,'model',tmp_path/'inputs',tmp_path/'output',execute=False)
    assert result['numerical_execution'] is False
    assert not (tmp_path/'output').exists()


def test_full_search_cannot_silently_use_cpu(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'load_identity',lambda *a:(object(),{}))
    with pytest.raises(ValueError,match='no CPU substitution'):
        runner.plan(ROOT,'texas2k.genco_opf.G500',tmp_path/'inputs',tmp_path/'output',device='cpu')
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('name',['canonical_bus.parquet','gencost.parquet'])
def test_changed_prepared_or_cost_bytes_never_reach_numerical_loading(tmp_path,name):
    original=b'accepted fixture';path=tmp_path/name;path.write_bytes(original)
    digest=hashlib.sha256(original).hexdigest()
    config=dict(case_sha256='c'*64,risk_base=32.975425699285616,prepared_artifacts_sha256={name:digest})
    contract=dict(schema='PUBLISHED_TEXAS2K_SCENARIO16_INPUTS_V1',case_sha256='c'*64,
        r_base=config['risk_base'],weather_timestamp_utc='2023-06-23T21:00:00Z',scenario=16,
        files={name:digest},gencost_sha256=digest)
    (tmp_path/'input_contract.json').write_text(json.dumps(contract))
    path.write_bytes(b'changed bytes')
    with pytest.raises(ValueError,match='prepared input changed'):load_identity(tmp_path,config)


def test_execution_identity_changes_with_runtime_without_reinterpreting_cached_work():
    request=dict(identity_sha256='old',checkpoint_sha256='model',device='cuda:0')
    a=runner._execution_request(request,{'device':'GPU A','torch':'2.8'})
    b=runner._execution_request(request,{'device':'GPU B','torch':'2.8'})
    assert a['identity_sha256']!=b['identity_sha256']
    assert request['identity_sha256']=='old'


def test_original_optimizer_replays_committed_prefix_with_twenty_total_actual_calls(tmp_path):
    class InterruptedBetweenCalls(BaseException):pass
    calls=[];journal=SurrogateJournal(tmp_path,{'request':'same'})
    def model(x):
        calls.append(x)
        return dict(eligible=True,search_objective=sum((v-.73)**2 for v in x),effective_x=list(x))
    def first(x):
        if journal.cursor==5:raise InterruptedBetweenCalls
        return journal.call(x,lambda:model(x))[0]
    with pytest.raises(InterruptedBetweenCalls):
        sequential_powell(alpha0=[1.]*5,alpha_bounds=[(0.,1.)]*5,evaluate=first)
    assert len(calls)==5
    restarted=SurrogateJournal(tmp_path,{'request':'same'})
    result=sequential_powell(alpha0=[1.]*5,alpha_bounds=[(0.,1.)]*5,
        evaluate=lambda x:restarted.call(x,lambda:model(x))[0])
    assert len(result.trace)==len(calls)==20
    assert len(json.loads((tmp_path/'ledger.json').read_text())['calls'])==20
