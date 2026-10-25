from dataclasses import asdict
import json
import numpy as np
from .schemas import CandidateResult
def _plain(value):
    """Convert NumPy values before durable JSON/Parquet serialization."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value

def _candidate_row(result: CandidateResult) -> dict:
    row = _plain(asdict(result))
    row['metadata'] = json.dumps(row['metadata'], sort_keys=True)
    return row
