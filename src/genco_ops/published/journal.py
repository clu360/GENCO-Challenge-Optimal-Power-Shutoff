
"""Durable exact-input objective replay without exceeding a topology's call cap."""
import hashlib
import json
from pathlib import Path
import sqlite3
import zlib
from contextlib import contextmanager
from filelock import FileLock
from ..artifacts import sha
from .io import atomic_json
from .canonical import canonical

class UncertainSurrogateCall(RuntimeError):
    pass

class PackedPayloadStore:
    """One lossless database per trajectory; ledgers retain their normal call cap."""

    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS payloads (scope TEXT NOT NULL, key TEXT NOT NULL, digest TEXT NOT NULL, payload BLOB NOT NULL, PRIMARY KEY(scope, key))')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            connection.execute('PRAGMA journal_mode=DELETE')
            connection.execute('PRAGMA synchronous=FULL')
            with connection:
                yield connection
        finally:
            connection.close()

    def write(self, identity, key, result):
        scope = hashlib.sha256(canonical(identity).encode()).hexdigest()
        payload = (canonical(result) + '\n').encode()
        digest = hashlib.sha256(payload).hexdigest()
        with self.connect() as connection:
            connection.execute('INSERT INTO payloads VALUES (?, ?, ?, ?)', (scope, key, digest, sqlite3.Binary(zlib.compress(payload, 6))))
        return digest

    def read(self, identity, key, expected):
        scope = hashlib.sha256(canonical(identity).encode()).hexdigest()
        with self.connect() as connection:
            row = connection.execute('SELECT digest, payload FROM payloads WHERE scope=? AND key=?', (scope, key)).fetchone()
        if row is None or row[0] != expected:
            raise ValueError('cached surrogate result changed or is missing')
        payload = zlib.decompress(row[1])
        if hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError('cached surrogate result changed')
        return json.loads(payload)

def payload_store_for_request(request, output):
    config = request.get('packed_journal')
    if config is None:
        return None
    if set(config) != {'policy_id', 'database'} or config['policy_id'] != 'SQLITE_ZLIB_V1':
        raise ValueError('explicit supported packed-journal policy required')
    path = Path(config['database'])
    if not path.is_absolute() or path.suffix != '.sqlite':
        raise ValueError('absolute packed-journal database path required')
    path = path.resolve()
    owner = path.with_suffix('.owner.json')
    output = Path(output).resolve()
    if any((candidate.is_relative_to(output) for candidate in (path, owner, path.with_suffix('.owner.lock')))):
        raise ValueError('packed database and sidecars must be outside the trajectory output')
    path.parent.mkdir(parents=True, exist_ok=True)
    identity = dict(policy_id=config['policy_id'], request_sha256=hashlib.sha256(canonical(request).encode()).hexdigest(), output=str(output))
    with FileLock(str(path.with_suffix('.owner.lock')), timeout=0):
        if path.exists() and (not owner.exists()):
            raise ValueError('refuse to adopt an unowned packed database')
        if owner.exists() and json.loads(owner.read_text()) != identity:
            raise ValueError('packed database belongs to another trajectory')
        if not owner.exists():
            atomic_json(owner, identity)
        return PackedPayloadStore(path)

class SurrogateJournal:

    def __init__(self, root, identity, budget=20, *, payload_store=None):
        self.root, self.identity, self.budget = (Path(root).resolve(), identity, budget)
        self.cursor = 0
        self.payload_store = payload_store
        self.root.mkdir(parents=True, exist_ok=True)
        if budget != 20:
            raise ValueError('retain the twenty-call topology cap')

    def call(self, x, evaluate):
        values = list(map(float, x))
        key = hashlib.sha256(json.dumps(values, allow_nan=False).encode()).hexdigest()
        with FileLock(str(self.root / 'journal.lock'), timeout=0):
            path = self.root / 'ledger.json'
            ledger = json.loads(path.read_text()) if path.exists() else dict(identity=self.identity, calls=[])
            if ledger.get('identity') != self.identity:
                raise ValueError('surrogate journal scientific identity changed')
            found = [r for r in ledger['calls'] if r['key'] == key]
            if len(found) > 1:
                raise ValueError('duplicate call records in journal')
            if found:
                record = found[0]
                if record['actual_call_index'] != self.cursor + 1:
                    raise ValueError('optimizer replay sequence diverged; no new inference permitted')
                if record['x'] != values or record['status'] != 'COMPLETE':
                    raise UncertainSurrogateCall('interrupted call has no committed result; no blind reevaluation')
                if self.payload_store is not None:
                    result = self.payload_store.read(self.identity, key, record['sha256'])
                else:
                    payload = self.root / (key + '.json')
                    if sha(payload) != record['sha256']:
                        raise ValueError('cached surrogate result changed')
                    result = json.loads(payload.read_text())
                self.cursor += 1
                return (result, True)
            if any((r['status'] != 'COMPLETE' for r in ledger['calls'])):
                raise UncertainSurrogateCall('unresolved call exists; stop rather than spend unaccounted evaluations')
            if self.cursor != len(ledger['calls']):
                raise ValueError('optimizer replay sequence diverged before committed prefix was consumed')
            if len(ledger['calls']) >= self.budget:
                raise ValueError('actual surrogate call cap exhausted across restarts')
            record = dict(key=key, x=values, status='INTENT', actual_call_index=len(ledger['calls']) + 1)
            ledger['calls'].append(record)
            atomic_json(path, ledger)
            result = evaluate()
            if not isinstance(result, dict):
                raise ValueError('objective payload must be a structured record')
            if self.payload_store is not None:
                digest = self.payload_store.write(self.identity, key, result)
            else:
                payload = self.root / (key + '.json')
                atomic_json(payload, result)
                digest = sha(payload)
            record.update(status='COMPLETE', sha256=digest)
            atomic_json(path, ledger)
            self.cursor += 1
            return (result, False)
