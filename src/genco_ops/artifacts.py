"""Checksum-bound artifact acquisition; downloads occur only on explicit request."""

import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import zipfile
import os
import sys
import shutil
import subprocess
import tempfile
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    return digest.hexdigest()


def _stream_sha(stream):
    digest=hashlib.sha256()
    for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    return digest.hexdigest()


def configure_native_cache(root):
    """Use the official cache API under this checkout, never a hidden user cache."""
    cache=checked_path(root,'outputs/runtime_cache')
    cache.mkdir(parents=True,exist_ok=True)
    os.environ['XDG_CACHE_HOME']=str(cache)
    module=sys.modules.get('gridsfm.cycle_basis')
    if module is not None:
        module.DEFAULT_CYCLE_CACHE=module.CycleBasisCache(cache_dir=cache/'gridsfm/cycle_basis')
    return cache


def checked_path(root,relative):
    posix,windows=PurePosixPath(relative),PureWindowsPath(relative)
    if posix.is_absolute() or windows.drive or '..' in posix.parts or '..' in windows.parts:
        raise ValueError('artifact path must be relative to this release')
    root=Path(root).resolve();path=(root/relative).resolve()
    if not path.is_relative_to(root):raise ValueError('artifact escaped release')
    return path


def verify(root):
    root=Path(root).resolve()
    inventory=json.loads((root/'artifacts/inventory.json').read_text())
    for name,item in inventory['files'].items():
        if sha(checked_path(root,name))!=item['sha256']:
            raise ValueError('release artifact mismatch: '+name)
    return dict(status='PASS_PACKAGED_FILES',files=len(inventory['files']),
        phase_i_complete=inventory['phase_i_complete'],phase_ii=inventory['phase_ii'])


def bundle_plans(root):
    """Return the immutable model and, when present, authorized-input archives."""
    root=Path(root).resolve()
    plans=[]
    for filename in ('model_bundle.json','input_bundle.json'):
        path=root/'artifacts'/filename
        if path.exists():
            primary=json.loads(path.read_text())
            plans.extend([primary,*primary.get('supplemental_bundles',[])])
    return plans


def acquire(root,bundle):
    """Validate every archive member before writing any artifact into the checkout."""
    root=Path(root).resolve()
    digest=sha(bundle)
    matches=[item for item in bundle_plans(root) if item['sha256']==digest]
    if len(matches)!=1:raise ValueError('artifact bundle checksum mismatch or ambiguous manifest')
    plan=matches[0]
    if 'bytes' in plan and Path(bundle).stat().st_size!=plan['bytes']:
        raise ValueError('artifact bundle size mismatch')
    with zipfile.ZipFile(bundle) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or set(names)!=set(plan['files']):
            raise ValueError('artifact bundle inventory differs or repeats a member')
        for name,item in plan['files'].items():
            path=checked_path(root,name)
            with archive.open(name) as stream:
                member_digest=_stream_sha(stream)
            if member_digest!=item['sha256']:raise ValueError('artifact member mismatch')
            if path.exists() and sha(path)!=item['sha256']:raise ValueError('refuse to replace a different artifact')
        for name,item in plan['files'].items():
            path=checked_path(root,name)
            if path.exists():continue
            path.parent.mkdir(parents=True,exist_ok=True)
            temporary=None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.acquire-',delete=False) as target:
                    temporary=Path(target.name)
                    with archive.open(name) as source:shutil.copyfileobj(source,target)
                if sha(temporary)!=item['sha256']:raise ValueError('artifact changed during extraction')
                temporary.replace(path)
            finally:
                if temporary is not None:temporary.unlink(missing_ok=True)
    return dict(status='PASS_ACQUIRED',files=len(plan['files']),bundle_sha256=digest,
        bundle_role=plan.get('role','primary'))


def bundle_status(root):
    """Inspect checksum readiness without importing models, downloading, or solving."""
    records=[]
    for plan in bundle_plans(root):
        missing=[];mismatched=[]
        for name,item in plan['files'].items():
            path=checked_path(root,name)
            if not path.exists():missing.append(name)
            elif sha(path)!=item['sha256']:mismatched.append(name)
        records.append(dict(role=plan.get('role','primary'),filename=plan.get('filename'),
            files=len(plan['files']),missing=missing,mismatched=mismatched,
            status='READY' if not missing and not mismatched else 'UNAVAILABLE_OR_MISMATCHED',
            access=plan.get('access','LOCAL_ONLY')))
    return records


def _github_token():
    """Use existing authorization; never put credentials in commands or messages."""
    for key in ('GH_TOKEN','GITHUB_TOKEN'):
        if os.environ.get(key):return os.environ[key]
    environment={**os.environ,'GCM_INTERACTIVE':'Never','GIT_TERMINAL_PROMPT':'0'}
    try:
        completed=subprocess.run(['git','-c','credential.interactive=false','credential','fill'],
            input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,
            env=environment,timeout=30,check=False)
    except (OSError,subprocess.TimeoutExpired):return None
    if completed.returncode:return None
    fields=dict(line.split('=',1) for line in completed.stdout.splitlines() if '=' in line)
    return fields.get('password')


class _GitHubRedirects(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        parsed=urlparse(newurl)
        if parsed.scheme!='https' or parsed.hostname not in {
            'api.github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}:
            raise ValueError('unexpected GitHub artifact redirect')
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if parsed.hostname!='api.github.com':redirected.remove_header('Authorization')
        return redirected


def _github_request(url,token,*,binary=False):
    if urlparse(url).scheme!='https' or urlparse(url).hostname!='api.github.com':
        raise ValueError('authenticated requests must target the GitHub API')
    headers={'Accept':'application/octet-stream' if binary else 'application/vnd.github+json',
        'X-GitHub-Api-Version':'2022-11-28','User-Agent':'genco-ops-artifact-acquisition'}
    if token:headers['Authorization']='Bearer '+token
    try:return build_opener(_GitHubRedirects()).open(Request(url,headers=headers),timeout=120)
    except HTTPError as exc:
        if exc.code in (401,403,404):
            raise RuntimeError('GitHub artifact is unavailable to this account; authorize repository access '
                'with GH_TOKEN/GITHUB_TOKEN or an existing Git credential, or acquire a local bundle') from None
        raise RuntimeError('GitHub artifact request failed (HTTP '+str(exc.code)+')') from None


def fetch_release(root,*,roles=None,download_dir=None):
    """Explicitly fetch pinned model archives using existing GitHub authorization.

    Exact local archives under ``dist/`` or ``download_dir`` are reused. All
    archive and member hashes are checked before extraction. Raw private inputs
    without a download URL remain local and are never uploaded by this function.
    """
    root=Path(root).resolve()
    plans=bundle_plans(root)
    if roles is None:plans=[p for p in plans if p.get('download_url')]
    else:
        wanted=set(roles);plans=[p for p in plans if p.get('role','primary') in wanted]
        if wanted!={p.get('role','primary') for p in plans}:raise ValueError('unknown bundle role')
        if any(not p.get('download_url') for p in plans):
            raise ValueError('this bundle has no authorized hosted distribution; acquire its local ZIP')
    destination=Path(download_dir).resolve() if download_dir else checked_path(root,'outputs/downloads')
    destination.mkdir(parents=True,exist_ok=True)
    results=[];token=None;release_cache={}
    for plan in plans:
        # URLs have owner/repository/releases/download/tag/filename (six parts).
        parsed=urlparse(plan['download_url']);parts=parsed.path.strip('/').split('/')
        if parsed.scheme!='https' or parsed.hostname!='github.com' or len(parts)!=6 or parts[2:4]!=['releases','download']:
            raise ValueError('expected a pinned GitHub release asset URL')
        repository='/'.join(parts[:2]);tag=parts[4];name=parts[5]
        if plan.get('filename',name)!=name:raise ValueError('release asset name differs from manifest')
        target=destination/name
        cached=next((p for p in [target,root/'dist'/name] if p.exists() and
            p.stat().st_size==plan.get('bytes',p.stat().st_size) and sha(p)==plan['sha256']),None)
        if cached is not None:
            result=acquire(root,cached);result['source']='VERIFIED_LOCAL_ARCHIVE';results.append(result);continue
        if token is None:token=_github_token()
        key=(repository,tag)
        if key not in release_cache:
            with _github_request(f'https://api.github.com/repos/{repository}/releases/tags/{tag}',token) as response:
                release_cache[key]=json.load(response)
        assets=[item for item in release_cache[key]['assets'] if item['name']==name]
        if len(assets)!=1:raise ValueError('pinned release asset is missing or ambiguous')
        asset=assets[0]
        if asset['size']!=plan['bytes']:raise ValueError('GitHub asset size differs from manifest')
        if asset.get('digest') and asset['digest']!='sha256:'+plan['sha256']:
            raise ValueError('GitHub asset checksum differs from manifest')
        if target.exists():raise ValueError('refuse to replace a different downloaded archive')
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(dir=destination,prefix='.download-',delete=False) as target_stream:
                temporary=Path(target_stream.name)
                with _github_request(f'https://api.github.com/repos/{repository}/releases/assets/{asset["id"]}',token,binary=True) as source:
                    shutil.copyfileobj(source,target_stream)
            if temporary.stat().st_size!=plan['bytes'] or sha(temporary)!=plan['sha256']:
                raise ValueError('downloaded archive size/checksum mismatch')
            temporary.replace(target)
        finally:
            if temporary is not None:temporary.unlink(missing_ok=True)
        result=acquire(root,target);result['source']='AUTHENTICATED_GITHUB_RELEASE'
        results.append(result)
    return dict(status='PASS_RELEASE_ACQUIRED',bundles=results)
