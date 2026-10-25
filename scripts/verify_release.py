"""Bounded local release checks; no training, Slurm, downloads or AC solves."""
import argparse
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import genco_ops

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--models',action='store_true',help='Run bounded model tests/notebooks using already acquired weights')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
if not Path(genco_ops.__file__).resolve().is_relative_to(root):
    raise RuntimeError('installed package did not resolve to this checkout')
if not args.models and importlib.util.find_spec('torch') is not None:
    raise RuntimeError('use a Torch-free environment to qualify the results-only path')
output=root/'outputs/release_checks'/('models' if args.models else 'results_only')
output.mkdir(parents=True,exist_ok=True)
commands=[['-I','-m','genco_ops.cli','verify'],['-I','-m','pytest','tests','-q'],
    ['-I','scripts/execute_notebooks.py']+(['--models'] if args.models else [])]
rows=[]
for index,arguments in enumerate(commands):
    started=time.perf_counter()
    completed=subprocess.run([sys.executable,*arguments],cwd=root,capture_output=True,text=True,timeout=600)
    stdout=completed.stdout.encode();stderr=completed.stderr.encode()
    (output/(str(index)+'_stdout.txt')).write_bytes(stdout)
    (output/(str(index)+'_stderr.txt')).write_bytes(stderr)
    row=dict(command=['python',*arguments],exit_code=completed.returncode,
        seconds=time.perf_counter()-started,stdout_sha256=hashlib.sha256(stdout).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr).hexdigest())
    rows.append(row);print(json.dumps(row),flush=True)
    if completed.returncode:raise RuntimeError('release check failed; evidence retained in outputs/release_checks')
result=dict(status='PASS_BOUNDED_ADVERTISED_MODES',mode='models' if args.models else 'results_only',
    commands=rows,python=platform.python_version(),platform=platform.system(),
    installed_package_from_this_checkout=True,torch_absent=importlib.util.find_spec('torch') is None,
    packages={name:metadata.version(name) for name in ('numpy','pandas','scipy','pyarrow','matplotlib','nbformat','nbclient','pytest')},
    inventory_sha256=hashlib.sha256((root/'artifacts/inventory.json').read_bytes()).hexdigest(),
    no_cluster_credentials_used=True,full_historical_campaign_recomputed=False,
    independent_numerical_ac_audit_tested=False)
(output/'verification.json').write_text(json.dumps(result,indent=2))
