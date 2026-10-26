"""Exercise authenticated acquisition without network calls or real credentials."""

import hashlib
from io import BytesIO
import json
from pathlib import Path
from urllib.request import Request
import zipfile

import pytest

from genco_ops import artifacts


def fixture_bundle(tmp_path):
    root=tmp_path/'repo';(root/'artifacts').mkdir(parents=True)
    content=BytesIO()
    with zipfile.ZipFile(content,'w') as archive:
        archive.writestr('artifacts/cache/model.pt',b'weights')
    payload=content.getvalue()
    plan=dict(role='primary',filename='models.zip',bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        files={'artifacts/cache/model.pt':dict(sha256=hashlib.sha256(b'weights').hexdigest())},
        download_url='https://github.com/owner/repository/releases/download/models-v1/models.zip')
    (root/'artifacts/model_bundle.json').write_text(json.dumps(plan))
    return root,payload,plan


def test_download_uses_api_and_validates_bytes_and_members(tmp_path,monkeypatch):
    root,payload,plan=fixture_bundle(tmp_path)
    monkeypatch.setattr(artifacts,'_github_token',lambda:'secret-not-for-output')
    requests=[]
    def request(url,token,*,binary=False):
        requests.append((url,binary))
        assert token=='secret-not-for-output'
        if binary:return BytesIO(payload)
        return BytesIO(json.dumps(dict(assets=[dict(name='models.zip',id=12,
            size=plan['bytes'],digest='sha256:'+plan['sha256'])])).encode())
    monkeypatch.setattr(artifacts,'_github_request',request)
    result=artifacts.fetch_release(root)
    assert result['status']=='PASS_RELEASE_ACQUIRED'
    assert len(requests)==2
    assert requests[1]==('https://api.github.com/repos/owner/repository/releases/assets/12',True)
    assert (root/'artifacts/cache/model.pt').read_bytes()==b'weights'
    assert 'secret' not in json.dumps(result)
    assert artifacts.bundle_status(root)[0]['status']=='READY'


def test_valid_local_archive_needs_no_credentials_or_network(tmp_path,monkeypatch):
    root,payload,_=fixture_bundle(tmp_path)
    (root/'dist').mkdir();(root/'dist/models.zip').write_bytes(payload)
    monkeypatch.setattr(artifacts,'_github_token',lambda:pytest.fail('must remain offline'))
    result=artifacts.fetch_release(root)
    assert result['bundles'][0]['source']=='VERIFIED_LOCAL_ARCHIVE'


def test_changed_server_asset_is_rejected_before_download(tmp_path,monkeypatch):
    root,_,plan=fixture_bundle(tmp_path)
    monkeypatch.setattr(artifacts,'_github_token',lambda:None)
    monkeypatch.setattr(artifacts,'_github_request',lambda *a,**kw:BytesIO(json.dumps(dict(
        assets=[dict(name='models.zip',id=12,size=plan['bytes'],digest='sha256:wrong')])).encode()))
    with pytest.raises(ValueError,match='checksum'):artifacts.fetch_release(root)
    assert not (root/'artifacts/cache/model.pt').exists()


def test_corrupted_download_is_not_installed_or_left_as_a_valid_archive(tmp_path,monkeypatch):
    root,payload,plan=fixture_bundle(tmp_path)
    monkeypatch.setattr(artifacts,'_github_token',lambda:None)
    def request(url,token,*,binary=False):
        if binary:return BytesIO(payload[:-1]+b'x')
        return BytesIO(json.dumps(dict(assets=[dict(name='models.zip',id=12,
            size=plan['bytes'],digest='sha256:'+plan['sha256'])])).encode())
    monkeypatch.setattr(artifacts,'_github_request',request)
    with pytest.raises(ValueError,match='downloaded archive'):artifacts.fetch_release(root)
    assert not (root/'artifacts/cache/model.pt').exists()
    assert list((root/'outputs/downloads').iterdir())==[]


def test_local_input_bundle_uses_same_safe_acquisition(tmp_path):
    root,payload,plan=fixture_bundle(tmp_path)
    (root/'artifacts/model_bundle.json').unlink()
    plan.pop('download_url');plan['role']='texas2k_authorized_inputs'
    (root/'artifacts/input_bundle.json').write_text(json.dumps(plan))
    bundle=tmp_path/'authorized.zip';bundle.write_bytes(payload)
    assert artifacts.acquire(root,bundle)['bundle_role']=='texas2k_authorized_inputs'
    with pytest.raises(ValueError,match='no authorized hosted'):
        artifacts.fetch_release(root,roles=['texas2k_authorized_inputs'])


def test_wrong_later_member_does_not_partially_extract(tmp_path):
    root,payload,plan=fixture_bundle(tmp_path)
    archive=tmp_path/'wrong.zip'
    with zipfile.ZipFile(archive,'w') as stream:
        stream.writestr('artifacts/cache/model.pt',b'weights')
        stream.writestr('artifacts/cache/other.pt',b'changed')
    plan['sha256']=artifacts.sha(archive);plan['bytes']=archive.stat().st_size
    plan['files']['artifacts/cache/other.pt']=dict(sha256='0'*64)
    (root/'artifacts/model_bundle.json').write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='member mismatch'):artifacts.acquire(root,archive)
    assert not (root/'artifacts/cache/model.pt').exists()


def test_redirect_never_sends_api_token_to_asset_host():
    handler=artifacts._GitHubRedirects()
    request=Request('https://api.github.com/repos/owner/repo/releases/assets/12',
        headers={'Authorization':'Bearer secret'})
    redirected=handler.redirect_request(request,None,302,'Found',{},
        'https://release-assets.githubusercontent.com/path?signature=signed')
    assert not redirected.has_header('Authorization')
    with pytest.raises(ValueError,match='unexpected'):
        handler.redirect_request(request,None,302,'Found',{},'https://untrusted.test/file')


def test_environment_token_does_not_invoke_credential_helper(monkeypatch):
    monkeypatch.setenv('GH_TOKEN','secret')
    monkeypatch.setattr(artifacts.subprocess,'run',lambda *a,**kw:pytest.fail('should not ask credential helper'))
    assert artifacts._github_token()=='secret'
