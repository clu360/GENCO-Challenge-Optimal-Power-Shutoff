import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from genco_ops.artifacts import acquire,checked_path


def test_certified_catalog_entries_are_not_also_unavailable():
    root=Path(__file__).resolve().parents[1]
    catalog=json.loads((root/'artifacts/model_catalog.json').read_text())
    assert not set(catalog['models']).intersection(catalog.get('unavailable_models',{}))


@pytest.mark.parametrize('name',['../escape','C:/private','/absolute','folder/../../escape'])
def test_no_escaping_artifact_path(tmp_path,name):
    with pytest.raises(ValueError):checked_path(tmp_path,name)


def test_model_acquisition_requires_exact_bundle_and_member(tmp_path):
    root=tmp_path/'repo';(root/'artifacts').mkdir(parents=True)
    bundle=tmp_path/'bundle.zip'
    with zipfile.ZipFile(bundle,'w') as archive:archive.writestr('artifacts/cache/model.pt',b'weights')
    digest=lambda data:hashlib.sha256(data).hexdigest()
    plan=dict(sha256=digest(bundle.read_bytes()),files={'artifacts/cache/model.pt':dict(sha256=digest(b'weights'))})
    (root/'artifacts/model_bundle.json').write_text(json.dumps(plan))
    assert acquire(root,bundle)['status']=='PASS_ACQUIRED'
    (root/'artifacts/cache/model.pt').write_bytes(b'changed')
    with pytest.raises(ValueError,match='different'):acquire(root,bundle)


def test_new_certified_checkpoint_can_use_a_separate_immutable_supplement(tmp_path):
    root=tmp_path/'repo';(root/'artifacts').mkdir(parents=True)
    def package(name,member,payload):
        archive=tmp_path/name
        with zipfile.ZipFile(archive,'w') as stream:stream.writestr(member,payload)
        return archive,dict(sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            files={member:dict(sha256=hashlib.sha256(payload).hexdigest())})
    base,plan=package('base.zip','artifacts/cache/base.pt',b'accepted base')
    addition,supplement=package('new.zip','artifacts/cache/new.pt',b'newly certified fit')
    supplement['role']='certified_g500_supplement'
    plan['supplemental_bundles']=[supplement]
    (root/'artifacts/model_bundle.json').write_text(json.dumps(plan))
    assert acquire(root,base)['bundle_role']=='primary'
    assert acquire(root,addition)['bundle_role']=='certified_g500_supplement'
    assert (root/'artifacts/cache/base.pt').read_bytes()==b'accepted base'
    assert (root/'artifacts/cache/new.pt').read_bytes()==b'newly certified fit'
    assert acquire(root,addition)['bundle_sha256']==supplement['sha256']
    plan['supplemental_bundles'].append(supplement)
    (root/'artifacts/model_bundle.json').write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='ambiguous'):acquire(root,addition)
