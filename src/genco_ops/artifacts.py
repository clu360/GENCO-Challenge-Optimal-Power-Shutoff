"""Checksum-bound local artifact acquisition; no credentials or implicit downloads."""

import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import zipfile
import os
import sys


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
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


def acquire(root,bundle):
    root=Path(root).resolve()
    plan=json.loads((root/'artifacts/model_bundle.json').read_text())
    digest=sha(bundle)
    matches=[item for item in [plan,*plan.get('supplemental_bundles',[])] if item['sha256']==digest]
    if len(matches)!=1:raise ValueError('model bundle checksum mismatch or ambiguous manifest')
    plan=matches[0]
    with zipfile.ZipFile(bundle) as archive:
        if set(archive.namelist())!=set(plan['files']):raise ValueError('model bundle inventory differs')
        for name,item in plan['files'].items():
            data=archive.read(name)
            if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('model member mismatch')
            path=checked_path(root,name);path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and sha(path)!=item['sha256']:raise ValueError('refuse to replace a different artifact')
            path.write_bytes(data)
    return dict(status='PASS_ACQUIRED',files=len(plan['files']),bundle_sha256=digest,
        bundle_role=plan.get('role','primary'))
