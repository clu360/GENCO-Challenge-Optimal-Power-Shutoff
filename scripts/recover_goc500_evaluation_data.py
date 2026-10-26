"""Inspect or explicitly recover the hash-bound GOC-500 FT6 evaluation data."""

import argparse
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))

from genco_ops.goc500_population import recover

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=root)
parser.add_argument('--output', type=Path, default=root / 'outputs/goc500_evaluation_data')
parser.add_argument('--download', action='store_true', help='Explicitly download two official archives, 2,406,018,938 bytes total')
parser.add_argument('--prepare', action='store_true', help='Decode existing archives and recover the exact 750 saved graph identities; no model execution')
args = parser.parse_args()
print(json.dumps(recover(args.root, args.output, download=args.download, prepare=args.prepare), indent=2))
