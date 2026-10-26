"""Create a local-only, checksum-bound Texas input ZIP from authorized local data.

No network or upload is performed. The exact modified electrical case remains
private; this export is for users who already have permission to access it.
"""

import argparse
import json
from pathlib import Path
import sys
import zipfile

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))

from genco_ops.artifacts import checked_path,sha

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=root)
parser.add_argument('--dataset',choices=['texas2k.authorized_inputs','texas2k.ops_inputs'],default='texas2k.authorized_inputs')
parser.add_argument('--output',type=Path,help='Default: ignored dist/texas2k_authorized_inputs_v1.zip')
args=parser.parse_args()
root=args.root.resolve()
plan=json.loads((root/'artifacts/data_catalog.json').read_text())['datasets'][args.dataset]
default_name='texas2k_authorized_ops_inputs_v1.zip' if args.dataset=='texas2k.ops_inputs' else 'texas2k_authorized_inputs_v1.zip'
target=args.output.resolve() if args.output else root/'dist'/default_name
if target.exists():raise FileExistsError('Choose a new output path; existing bundles are immutable')
for name,item in plan['files'].items():
    path=checked_path(root,name)
    if path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']:
        raise ValueError('Authorized input differs from the fixed experiment contract: '+name)
target.parent.mkdir(parents=True,exist_ok=True)
try:
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(plan['files']):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,checked_path(root,name).read_bytes())
except BaseException:
    target.unlink(missing_ok=True)
    raise
manifest=dict(schema='GENCO_AUTHORIZED_TEXAS_INPUT_BUNDLE_V1',role=plan['role'],filename=target.name,
    access='LOCAL_AUTHORIZED_USERS_ONLY',distribution='PRIVATE_MODIFIED_ELECTRICAL_INPUTS',
    weather_access=plan['weather_access'],bytes=target.stat().st_size,sha256=sha(target),files=plan['files'])
manifest_path=root/'artifacts/input_bundle.json'
if manifest_path.exists() and json.loads(manifest_path.read_text())!=manifest:
    raise FileExistsError('Existing input-bundle manifest differs; preserve it and review the new bundle')
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='PASS_LOCAL_INPUT_BUNDLE',bytes=manifest['bytes'],
    sha256=manifest['sha256'],files=len(manifest['files']),public_distribution=False)))
