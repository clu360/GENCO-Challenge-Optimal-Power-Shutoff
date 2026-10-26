"""Public GENCO example provenance must be independently checkable."""
import hashlib
import json
from pathlib import Path

import pytest

from genco_ops.public_genco_demo import verify_public_data

ROOT = Path(__file__).resolve().parents[1]


def test_public_fixture_matches_pinned_upstream_git_blobs():
    manifest = verify_public_data(ROOT)
    assert manifest['source_commit'] == '95b90eecc7f5c2c86a9dd776f0c3f40434def22f'
    assert len(manifest['files']) == 10
    for relative, item in manifest['files'].items():
        data = (ROOT / relative).read_bytes()
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == item['upstream_git_blob_sha1']


def test_changed_public_fixture_is_rejected_before_processing(tmp_path):
    path = tmp_path / 'experiments/ieee14_public/data_manifest.json'
    path.parent.mkdir(parents=True)
    fixture = path.parent / 'data/changed.parquet'
    fixture.parent.mkdir()
    fixture.write_bytes(b'changed')
    path.write_text(json.dumps(dict(schema='PUBLIC_GRAPHKIT_CASE14_FIXTURE_V1',
        public_git_tree_blob_parity=True, files={fixture.relative_to(tmp_path).as_posix(): dict(sha256='0'*64)})))
    with pytest.raises(ValueError, match='checksum differs'):
        verify_public_data(tmp_path)


def test_unlisted_public_fixture_files_are_not_processed(tmp_path):
    path = tmp_path / 'experiments/ieee14_public/data_manifest.json'
    raw = path.parent / 'data'
    raw.mkdir(parents=True)
    (raw / 'extra.parquet').write_bytes(b'not part of the pinned input')
    path.write_text(json.dumps(dict(schema='PUBLIC_GRAPHKIT_CASE14_FIXTURE_V1',
        public_git_tree_blob_parity=True, files={})))
    with pytest.raises(ValueError, match='inventory differs'):
        verify_public_data(tmp_path)
