"""Checksum-bound local artifact acquisition; no credentials or implicit downloads."""

import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import zipfile


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    return digest.hexdigest()


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
    if sha(bundle)!=plan['sha256']:raise ValueError('model bundle checksum mismatch')
    with zipfile.ZipFile(bundle) as archive:
        if set(archive.namelist())!=set(plan['files']):raise ValueError('model bundle inventory differs')
        for name,item in plan['files'].items():
            data=archive.read(name)
            if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('model member mismatch')
            path=checked_path(root,name);path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and sha(path)!=item['sha256']:raise ValueError('refuse to replace a different artifact')
            path.write_bytes(data)
    return dict(status='PASS_ACQUIRED',files=len(plan['files']))
