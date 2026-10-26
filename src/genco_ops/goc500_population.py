"""Recover the exact FT6 population from official OPFData, without model execution.

The original ordered graph fingerprints are the identity authority. Raw archive
file order is deliberately ignored: PyG's historical loader used os.listdir.
"""

import base64
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import re
import tarfile
import urllib.request

from .workflow import validate_output


SCHEMA = 'GOC500_FT6_EVALUATION_POPULATION_V1'


def load_manifest(root):
    path = Path(root) / 'experiments/goc_500/data/evaluation_population.json'
    manifest = json.loads(path.read_text())
    if (manifest.get('schema') != SCHEMA or manifest.get('case_name') != 'pglib_opf_case500_goc'
            or manifest.get('num_groups') != 1 or manifest.get('evaluation_graphs') != 750):
        raise ValueError('a frozen 750-graph GOC-500 FT6 population manifest is required')
    expected_releases = {'fulltop': 'dataset_release_1', 'n1': 'dataset_release_1_nminusone'}
    if len(manifest['archives']) != 2 or {item['variant'] for item in manifest['archives']} != set(expected_releases):
        raise ValueError('exactly the FullTop and N-1 group-zero archives are required')
    for item in manifest['archives']:
        release = expected_releases[item['variant']]
        url = f'https://storage.googleapis.com/gridopt-dataset/{release}/pglib_opf_case500_goc_0.tar.gz'
        if (item['release'] != release or item['url'] != url or not item['generation'].isdigit()
                or type(item['size_bytes']) is not int or item['size_bytes'] <= 0
                or len(base64.b64decode(item['crc32c_base64'], validate=True)) != 4):
            raise ValueError('official archive identity fields changed')
        dataset = manifest['datasets'][item['variant']]
        if (dataset['count'] != 375 or dataset['split'] != 'test'
                or [row['index'] for row in dataset['ordered_graphs']] != list(range(375))):
            raise ValueError('the sealed FT6 population requires 375 original test indices per stratum')
        _ordered_hashes(dataset)
    return manifest


def _ordered_hashes(dataset):
    records = dataset['ordered_graphs']
    hashes = [row['sha256'] for row in records]
    if (len(hashes) != dataset['count'] or len(set(hashes)) != len(hashes)
            or [row['order'] for row in records] != list(range(len(records)))
            or any(re.fullmatch('[0-9A-F]{64}', digest) is None for digest in hashes)):
        raise ValueError('population requires unique SHA256 fingerprints in explicit historical order')
    return hashes


def recovery_plan(root, output):
    manifest = load_manifest(root)
    output = validate_output(root, output)
    return dict(status='PLAN_ONLY_NOT_DOWNLOADED_OR_RECONSTRUCTED',
                evaluation_graphs=manifest['evaluation_graphs'],
                total_archive_bytes=sum(item['size_bytes'] for item in manifest['archives']),
                output=str(output), archives=manifest['archives'],
                source_identity='OFFICIAL_GCS_OBJECT_GENERATION_AND_CRC32C',
                population_identity=manifest['graph_hash_scheme'],
                numerical_model_execution=False, historical_750_graph_replay_performed=False)


class _PythonCRC32C:
    """Portable fallback; google-crc32c provides faster checks for 2.4 GB archives."""
    def __init__(self):
        self.value = 0xffffffff
        self.table = []
        for number in range(256):
            for _ in range(8):
                number = (number >> 1) ^ (0x82f63b78 if number & 1 else 0)
            self.table.append(number)

    def update(self, data):
        value = self.value
        for byte in data:
            value = self.table[(value ^ byte) & 0xff] ^ (value >> 8)
        self.value = value

    def digest(self):
        return (self.value ^ 0xffffffff).to_bytes(4, 'big')


def _checksum():
    try:
        import google_crc32c
        return google_crc32c.Checksum()
    except ImportError:
        return _PythonCRC32C()


def _stream_digests(stream, destination=None):
    checksum, digest, count = _checksum(), hashlib.sha256(), 0
    for block in iter(lambda: stream.read(1048576), b''):
        checksum.update(block)
        digest.update(block)
        count += len(block)
        if destination is not None:
            destination.write(block)
    return dict(size_bytes=count, sha256=digest.hexdigest(),
                crc32c_base64=base64.b64encode(checksum.digest()).decode('ascii'))


def _check_archive(record, spec):
    if record['size_bytes'] != spec['size_bytes'] or record['crc32c_base64'] != spec['crc32c_base64']:
        raise ValueError('official archive size or CRC32C checksum differs')


def verify_archive(path, spec):
    with Path(path).open('rb') as stream:
        record = _stream_digests(stream)
    _check_archive(record, spec)
    return dict(record, generation=spec['generation'], url=spec['url'])


def download_archive(spec, directory, *, opener=urllib.request.urlopen):
    """Explicitly download one immutable GCS generation and verify its CRC32C."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (spec['variant'] + '.tar.gz')
    if path.exists():
        return path, verify_archive(path, spec)
    partial = path.with_suffix(path.suffix + '.part')
    if partial.exists():
        raise ValueError('preserve the incomplete archive; choose a fresh output directory')
    request = urllib.request.Request(spec['url'] + '?generation=' + spec['generation'])
    with opener(request, timeout=60) as response:
        if (response.headers.get('x-goog-generation') != spec['generation']
                or int(response.headers.get('Content-Length', -1)) != spec['size_bytes']):
            raise ValueError('GCS generation or advertised archive size differs')
        with partial.open('xb') as stream:
            record = _stream_digests(response, stream)
    _check_archive(record, spec)
    partial.rename(path)
    return path, dict(record, generation=spec['generation'], url=spec['url'])


def graph_sha256(graph):
    """Exact original FT6 typed-tensor recursive hash, before PE/transforms."""
    import torch

    def update(digest, value):
        if isinstance(value, torch.Tensor):
            tensor = value.detach().cpu().contiguous()
            digest.update(b'tensor')
            digest.update(str(tensor.dtype).encode('ascii'))
            digest.update(str(tuple(tensor.shape)).encode('ascii'))
            digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(value, Mapping):
            digest.update(b'mapping')
            for key in sorted(value, key=lambda item: repr(item)):
                digest.update(repr(key).encode('utf-8'))
                update(digest, value[key])
        elif isinstance(value, (list, tuple)):
            digest.update(type(value).__name__.encode('ascii'))
            for item in value:
                update(digest, item)
        else:
            digest.update(repr(value).encode('utf-8'))

    digest = hashlib.sha256()
    update(digest, graph.to_dict())
    return digest.hexdigest().upper()


def graph_from_raw(obj):
    """PyG 2.8.0.post1 OPFDataset.process schema, plus official feasible label.

    Source is pinned in evaluation_population.json. Every reconstructed tensor
    must match its saved FT6 fingerprint; no labels or operating states are solved.
    """
    import torch
    from torch_geometric.data import HeteroData
    if torch.get_default_dtype() != torch.float32:
        raise ValueError('historical OPFData conversion requires the default float32 dtype')
    grid, solution = obj['grid'], obj['solution']
    data = HeteroData()
    data.x = torch.tensor(grid['context']).view(-1)
    data.objective = torch.tensor(obj['metadata']['objective'])
    for family in ('bus', 'generator', 'load', 'shunt'):
        data[family].x = torch.tensor(grid['nodes'][family])
        if family in ('bus', 'generator'):
            data[family].y = torch.tensor(solution['nodes'][family])
    for family in ('ac_line', 'transformer'):
        edge = grid['edges'][family]
        data['bus', family, 'bus'].edge_index = torch.tensor([edge['senders'], edge['receivers']])
        data['bus', family, 'bus'].edge_attr = torch.tensor(edge['features'])
        data['bus', family, 'bus'].edge_label = torch.tensor(solution['edges'][family]['features'])
    for node in ('generator', 'load', 'shunt'):
        family = node + '_link'
        edge = grid['edges'][family]
        data[node, family, 'bus'].edge_index = torch.tensor([edge['senders'], edge['receivers']])
        data['bus', family, node].edge_index = torch.tensor([edge['receivers'], edge['senders']])
    data.feasible = torch.tensor(1, dtype=torch.long)
    return data


def recover_variant(archive, spec, dataset):
    """Match all required fingerprints, independent of archive/OS enumeration."""
    expected = _ordered_hashes(dataset)
    expected_set, matched, names = set(expected), {}, {}
    prefix = f'gridopt-dataset-tmp/{spec["release"]}/pglib_opf_case500_goc/group_0/'
    raw_count = 0
    with tarfile.open(archive, 'r|gz') as stream:
        for member in stream:
            name = member.name.removeprefix('./')
            if not member.isfile() or not name.startswith(prefix):
                continue
            match = re.fullmatch(r'example_(\d+)\.json', name[len(prefix):])
            if match is None or not spec['raw_test_id_min'] <= int(match[1]) <= spec['raw_test_id_max']:
                continue
            if member.size > 10000000:
                raise ValueError('unexpectedly large GOC-500 JSON record')
            raw_count += 1
            with stream.extractfile(member) as source:
                graph = graph_from_raw(json.load(source))
            digest = graph_sha256(graph)
            if digest in expected_set:
                if digest in matched:
                    raise ValueError('duplicate matching graph; exact population would be ambiguous')
                matched[digest], names[digest] = graph, name
    missing = expected_set.difference(matched)
    if missing:
        raise ValueError(f'{len(missing)} historical graph fingerprints missing; do not substitute other samples')
    if raw_count != spec['raw_test_id_max'] - spec['raw_test_id_min'] + 1:
        raise ValueError('official test range is incomplete or contains duplicate raw members')
    return [matched[digest] for digest in expected], dict(raw_test_graphs_examined=raw_count,
        ordered_graphs=[dict(order=index, sha256=digest, archive_member=names[digest])
                        for index, digest in enumerate(expected)])


def recover(root, output, *, download=False, prepare=False):
    manifest = load_manifest(root)
    output = validate_output(root, output)
    if not download and not prepare:
        return recovery_plan(root, output)
    if prepare:
        try:
            import torch
            import torch_geometric  # noqa: F401 -- fail before scanning multi-GB archives
        except ImportError as exc:
            raise RuntimeError('Preparation requires the documented PyTorch/PyG model environment; '
                               'the plan and archive download do not require models') from exc
    archives, receipts = {}, {}
    for spec in manifest['archives']:
        path = output / 'downloads' / (spec['variant'] + '.tar.gz')
        if download:
            path, receipt = download_archive(spec, path.parent)
        else:
            if not path.exists():
                raise FileNotFoundError('archive missing; --download explicitly transfers the documented 2.4 GB')
            receipt = verify_archive(path, spec)
        archives[spec['variant']], receipts[spec['variant']] = path, receipt
    result = dict(status='OFFICIAL_ARCHIVES_VERIFIED_NOT_PREPARED', archives=receipts,
                  numerical_model_execution=False, historical_750_graph_replay_performed=False)
    prior_path = output / 'recovery_receipt.json'
    if not prepare and prior_path.exists():
        prior = json.loads(prior_path.read_text())
        if prior.get('status') == 'EXACT_ORDERED_750_GRAPH_POPULATION_RECOVERED_NOT_EVALUATED':
            if prior.get('archives') != receipts:
                raise ValueError('previous recovery archive identities differ')
            return prior
    if prepare:
        prepared = output / 'prepared'
        if prepared.exists() and any(prepared.iterdir()):
            raise ValueError('preserve existing prepared evidence; choose a fresh output directory')
        prepared.mkdir(parents=True, exist_ok=True)
        datasets = {}
        for spec in manifest['archives']:
            variant = spec['variant']
            graphs, record = recover_variant(archives[variant], spec, manifest['datasets'][variant])
            destination = prepared / (variant + '.pt')
            torch.save([graph.to_dict() for graph in graphs], destination)
            record.update(count=len(graphs), file=destination.name,
                          file_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            datasets[variant] = record
        result.update(status='EXACT_ORDERED_750_GRAPH_POPULATION_RECOVERED_NOT_EVALUATED',
                      datasets=datasets, torch=torch.__version__)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'recovery_receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
