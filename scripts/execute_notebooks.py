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
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
output=root/'outputs/executed_notebooks';output.mkdir(parents=True,exist_ok=True)
names=['01_explore_published_results.ipynb']
if args.models:names+=['02_goc500_model_and_ops_demo.ipynb','03_texas2k_model_and_ops_demo.ipynb']
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
            NotebookClient(book,timeout=600,kernel_name='genco-release',
                resources={'metadata':{'path':str(root/'notebooks')}}).execute()
            nbformat.write(book,output/name)
            texas_status='NOT_APPLICABLE'
            texas_ops='NOT_APPLICABLE'
            if name.startswith('03'):
                outcomes=[item.get('data',{}).get('application/json',{})
                    for cell in book.cells if cell.cell_type=='code' for item in cell.get('outputs',[])]
                texas_status=next((value.get('status') for value in outcomes if value.get('status') and value.get('kind')!='original_ops_probe'),'UNREPORTED_SEE_NOTEBOOK')
                texas_ops=next((value.get('status') for value in outcomes if value.get('kind')=='original_ops_probe'),'UNREPORTED_SEE_NOTEBOOK')
            print(json.dumps(dict(notebook=name,status='EXECUTED',
                texas_inference_outcome=texas_status,texas_ops_probe_outcome=texas_ops)),flush=True)
    finally:
        for key,value in prior.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
