"""Identity recovery and opt-in acquisition checks on small authentic schemas."""

import base64
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tarfile

import pytest

from genco_ops.goc500_population import (
    _PythonCRC32C, download_archive, graph_from_raw, graph_sha256,
    load_manifest, recover_variant, recovery_plan, verify_archive,
)


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_preserves_all_750_ordered_graph_identities_and_official_sources(tmp_path):
    manifest = load_manifest(ROOT)
    assert manifest['evaluation_graphs'] == sum(item['count'] for item in manifest['datasets'].values()) == 750
    assert sum(item['size_bytes'] for item in manifest['archives']) == 2406018938
    assert all('storage.googleapis.com/gridopt-dataset/' in item['url'] for item in manifest['archives'])
    hashes = [row['sha256'] for data in manifest['datasets'].values() for row in data['ordered_graphs']]
    assert len(set(hashes)) == 750
    plan = recovery_plan(ROOT, tmp_path / 'no-output')
    assert plan['status'] == 'PLAN_ONLY_NOT_DOWNLOADED_OR_RECONSTRUCTED'
    assert plan['numerical_model_execution'] is False
    assert not (tmp_path / 'no-output').exists()


def test_crc32c_matches_standard_castagnoli_vector():
    checksum = _PythonCRC32C()
    checksum.update(b'123')
    checksum.update(b'456789')
    assert checksum.digest().hex() == 'e3069283'


def _archive_spec(payload):
    crc = _PythonCRC32C()
    crc.update(payload)
    return dict(variant='fulltop', url='https://storage.googleapis.com/gridopt-dataset/test.tar.gz',
                generation='123', size_bytes=len(payload),
                crc32c_base64=base64.b64encode(crc.digest()).decode())


class Response(BytesIO):
    def __init__(self, payload, spec, generation=None):
        super().__init__(payload)
        self.headers = {'x-goog-generation': generation or spec['generation'],
                        'Content-Length': str(spec['size_bytes'])}


def test_download_requires_matching_immutable_generation_and_payload_checksum(tmp_path):
    payload = b'small acquisition fixture'
    spec = _archive_spec(payload)
    requests = []

    def open_request(request, **kwargs):
        requests.append(request.full_url)
        return Response(payload, spec)

    path, record = download_archive(spec, tmp_path / 'valid', opener=open_request)
    assert requests == [spec['url'] + '?generation=123']
    assert record['sha256'] == hashlib.sha256(payload).hexdigest()
    assert verify_archive(path, spec) == record
    with pytest.raises(ValueError, match='generation'):
        download_archive(spec, tmp_path / 'changed-generation',
                         opener=lambda *a, **k: Response(payload, spec, '456'))
    assert not list((tmp_path / 'changed-generation').glob('*.tar.gz'))
    with pytest.raises(ValueError, match='CRC32C'):
        download_archive(spec, tmp_path / 'corrupt',
                         opener=lambda *a, **k: Response(b'X' * len(payload), spec))
    assert (tmp_path / 'corrupt/fulltop.tar.gz.part').exists()
    assert not (tmp_path / 'corrupt/fulltop.tar.gz').exists()


def _raw_case(value):
    return dict(grid=dict(context=[[[100.0]]], nodes=dict(
        bus=[[0., 0., .9, 1.1]], generator=[[0., 0., 0., 1.]],
        load=[[value, .1]], shunt=[]), edges=dict(
        ac_line=dict(senders=[0], receivers=[0], features=[[.01, .1]]),
        transformer=dict(senders=[], receivers=[], features=[]),
        generator_link=dict(senders=[0], receivers=[0]),
        load_link=dict(senders=[0], receivers=[0]),
        shunt_link=dict(senders=[], receivers=[]))),
        solution=dict(nodes=dict(bus=[[0., 1.]], generator=[[value, .1]]),
                      edges=dict(ac_line=dict(features=[[value, .1, -value, -.1]]),
                                 transformer=dict(features=[]))), metadata=dict(objective=value * 10))


def _write_tar(path, values):
    prefix = 'gridopt-dataset-tmp/dataset_release_1/pglib_opf_case500_goc/group_0/'
    with tarfile.open(path, 'w:gz') as archive:
        for index, raw in values:
            encoded = json.dumps(raw).encode()
            member = tarfile.TarInfo(prefix + f'example_{index}.json')
            member.size = len(encoded)
            archive.addfile(member, BytesIO(encoded))


def test_preparation_restores_hash_order_and_never_substitutes_missing_graphs(tmp_path):
    torch = pytest.importorskip('torch')
    pytest.importorskip('torch_geometric')
    raw_a, raw_b = _raw_case(.3), _raw_case(.7)
    a, b = graph_from_raw(raw_a), graph_from_raw(raw_b)
    assert a.feasible.dtype == torch.long and a.feasible.item() == 1
    assert a['bus'].y.tolist() == [[0., 1.]]
    assert a['bus', 'load_link', 'load'].edge_index.tolist() == [[0], [0]]
    assert a['bus', 'ac_line', 'bus'].edge_label.shape == (1, 4)
    hashes = [graph_sha256(b), graph_sha256(a)]
    dataset = dict(count=2, ordered_graphs=[dict(order=i, index=i, sha256=digest)
                                         for i, digest in enumerate(hashes)])
    spec = dict(release='dataset_release_1', raw_test_id_min=14250, raw_test_id_max=14251)
    archive = tmp_path / 'raw.tar.gz'
    _write_tar(archive, [(14250, raw_a), (14251, raw_b)])
    recovered, receipt = recover_variant(archive, spec, dataset)
    assert [graph_sha256(graph) for graph in recovered] == hashes
    assert receipt['ordered_graphs'][0]['archive_member'].endswith('example_14251.json')
    changed = deepcopy(raw_b)
    changed['grid']['nodes']['load'][0][0] = .8
    _write_tar(archive, [(14250, raw_a), (14251, changed)])
    with pytest.raises(ValueError, match='fingerprints missing'):
        recover_variant(archive, spec, dataset)
