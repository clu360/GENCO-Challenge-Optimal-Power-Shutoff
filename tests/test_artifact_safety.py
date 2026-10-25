import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from genco_ops.artifacts import acquire,checked_path


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
