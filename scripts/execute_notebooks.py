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
    prior=os.environ.get('JUPYTER_PATH')
    os.environ['JUPYTER_PATH']=directory
    try:
        for name in names:
            book=nbformat.read(root/'notebooks'/name,as_version=4)
            NotebookClient(book,timeout=600,kernel_name='genco-release',
                resources={'metadata':{'path':str(root/'notebooks')}}).execute()
            nbformat.write(book,output/name)
            print(json.dumps(dict(notebook=name,status='EXECUTED',
                texas_public_input='UNAVAILABLE_EXPLICIT_SKIP' if name.startswith('03') else 'NOT_APPLICABLE')),flush=True)
    finally:
        if prior is None:os.environ.pop('JUPYTER_PATH',None)
        else:os.environ['JUPYTER_PATH']=prior
