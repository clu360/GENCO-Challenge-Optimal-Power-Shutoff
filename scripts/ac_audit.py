"""Prepare an exact fixed-decision audit, optionally execute it explicitly."""
import argparse
import json
from pathlib import Path
from genco_ops.ac_audit import prepare,execute

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--decision',type=Path,required=True)
parser.add_argument('--case',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--julia',default='julia')
parser.add_argument('--execute',action='store_true')
args=parser.parse_args()
plan=prepare(Path(__file__).resolve().parents[1],args.decision,args.case,args.output,julia=args.julia)
print(json.dumps(execute(plan,args.output) if args.execute else plan,indent=2))
