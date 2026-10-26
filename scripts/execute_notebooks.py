"""Execute explicitly selected notebooks with this Python, using a temporary kernel."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

import nbformat
from nbclient import NotebookClient

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--models',action='store_true',help='Also execute bounded model demos; explicit acquired artifacts required')
parser.add_argument('--notebook',action='append',choices=[
    '01_explore_published_results.ipynb', '02_goc500_model_and_ops_demo.ipynb',
    '03_texas2k_model_and_ops_demo.ipynb','04_public_genco_ieee14.ipynb'],help='Execute only this notebook (repeatable)')
parser.add_argument('--in-place',action='store_true',help='Also save measured outputs into the source notebooks for readers')
parser.add_argument('--require-model-execution',action='store_true',
    help='Fail if any requested saved-case inference or bounded probe is unavailable')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
output=root/'outputs/executed_notebooks';output.mkdir(parents=True,exist_ok=True)
names=['01_explore_published_results.ipynb']
if args.models:names+=['02_goc500_model_and_ops_demo.ipynb','03_texas2k_model_and_ops_demo.ipynb','04_public_genco_ieee14.ipynb']
if args.notebook:names=args.notebook
with tempfile.TemporaryDirectory(prefix='genco-notebook-kernel-') as directory:
    kernel=Path(directory)/'kernels/genco-release';kernel.mkdir(parents=True)
    (kernel/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
        display_name='Isolated release verification',language='python')))
    settings=dict(JUPYTER_PATH=directory,IPYTHONDIR=str(Path(directory)/'ipython'),
        JUPYTER_CONFIG_DIR=str(Path(directory)/'config'),
        JUPYTER_RUNTIME_DIR=str(Path(directory)/'runtime'))
    prior={key:os.environ.get(key) for key in settings}
    os.environ.update(settings)
    try:
        for name in names:
            book=nbformat.read(root/'notebooks'/name,as_version=4)
            NotebookClient(book,timeout=1800,kernel_name='genco-release',
                resources={'metadata':{'path':str(root/'notebooks')}}).execute()
            # Do not retain the temporary kernel identity as a reader requirement.
            book.metadata['kernelspec']=dict(display_name='Python 3',language='python',name='python3')
            nbformat.write(book,output/name)
            if args.in_place:nbformat.write(book,root/'notebooks'/name)
            outcomes=[item.get('data',{}).get('application/json',{})
                for cell in book.cells if cell.cell_type=='code' for item in cell.get('outputs',[])]
            numerical=[value for value in outcomes if isinstance(value,dict)
                and value.get('kind') in ('saved_case_inference','original_ops_probe','bounded_sample_ops','public_genco_inference')]
            unavailable=[value for value in numerical if not value.get('status','').startswith('PASS_')]
            result=dict(notebook=name,status='EXECUTED_WITH_UNAVAILABLE_NUMERICAL_MODES' if unavailable else 'EXECUTED',
                source_outputs_updated=args.in_place,
                inference_outcomes=[dict(model_id=value.get('model_id'),status=value.get('status'))
                    for value in numerical if value.get('kind') in ('saved_case_inference','public_genco_inference')],
                ops_outcomes=[dict(model_id=value.get('model_id'),status=value.get('status'),
                    calls=value.get('actual_surrogate_calls',value.get('actual_model_calls')))
                    for value in numerical if value.get('kind') not in ('saved_case_inference','public_genco_inference')],
                unavailable_numerical_modes=len(unavailable),new_ac_solves=0)
            print(json.dumps(result),flush=True)
            (output/(Path(name).stem+'.execution.json')).write_text(json.dumps(result,indent=2)+'\n')
            if args.require_model_execution and unavailable:
                raise RuntimeError('Requested numerical modes were unavailable; this is not passed model execution. Acquire the exact documented assets.')
    finally:
        for key,value in prior.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
