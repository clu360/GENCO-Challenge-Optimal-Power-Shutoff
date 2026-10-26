"""Download and verify pinned model archives using existing GitHub authorization."""

import argparse
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))

from genco_ops.artifacts import bundle_status,fetch_release

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=root)
parser.add_argument('--role',action='append',help='Optional bundle role; repeat to select multiple archives')
parser.add_argument('--status',action='store_true',help='Inspect local readiness without network or model imports')
args=parser.parse_args()
print(json.dumps(bundle_status(args.root) if args.status else fetch_release(args.root,roles=args.role),indent=2))
