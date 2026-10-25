"""Small explicit entry points for published results and bounded model inference."""

import argparse
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    results=commands.add_parser('results',help='Regenerate figures from published numeric tables; no model or solver')
    results.add_argument('--root',type=Path,default=Path.cwd())
    results.add_argument('--study',choices=['texas2k','goc_500'],required=True)
    results.add_argument('--output',type=Path,required=True)
    verify=commands.add_parser('verify',help='Verify the packaged result/artifact inventory')
    verify.add_argument('--root',type=Path,default=Path.cwd())
    acquisition=commands.add_parser('acquire',help='Verify and extract the explicitly supplied model bundle')
    acquisition.add_argument('--root',type=Path,default=Path.cwd())
    acquisition.add_argument('--bundle',type=Path,required=True)
    inference=commands.add_parser('infer',help='Run one real saved-case prediction using an acquired checkpoint')
    inference.add_argument('--root',type=Path,default=Path.cwd())
    inference.add_argument('--model',required=True)
    inference.add_argument('--output',type=Path,required=True)
    demo=commands.add_parser('ops-demo',help='Run fresh bounded GOC500 OPS on the official sample, not the published full search')
    demo.add_argument('--root',type=Path,default=Path.cwd())
    demo.add_argument('--model',required=True)
    demo.add_argument('--output',type=Path,required=True)
    demo.add_argument('--config',type=Path)
    published=commands.add_parser('published-config',help='Load a checksum-pinned full configuration without executing it')
    published.add_argument('--config',type=Path,required=True)
    published.add_argument('--sha256',required=True)
    full=commands.add_parser('phase-i-ops',help='Validate or explicitly execute the original Texas Phase I numerical pipeline')
    full.add_argument('--root',type=Path,default=Path.cwd())
    full.add_argument('--model',required=True)
    full.add_argument('--inputs',type=Path,required=True,help='Authorized hash-bound private electrical inputs')
    full.add_argument('--output',type=Path,required=True)
    full.add_argument('--device',choices=['cpu','cuda:0'],default='cuda:0')
    full.add_argument('--probe-topology',help='Bounded 20-call portability probe only: intact or sorted IDs separated by semicolons')
    full.add_argument('--execute',action='store_true',help='Without this flag only validate a plan; never submit Slurm jobs')
    args=parser.parse_args()
    if args.command=='results':
        from .results import regenerate
        print(json.dumps(regenerate(args.root,args.study,args.output)))
    elif args.command=='verify':
        from .artifacts import verify
        print(json.dumps(verify(args.root)))
    elif args.command=='acquire':
        from .artifacts import acquire
        print(json.dumps(acquire(args.root,args.bundle)))
    elif args.command=='ops-demo':
        from .goc500_demo import run_demo
        print(json.dumps(run_demo(args.root,args.model,args.output,args.config)))
    elif args.command=='published-config':
        from .goc500_demo import load_published_config
        print(json.dumps(load_published_config(args.config,args.sha256)))
    elif args.command=='phase-i-ops':
        from .published.runner import run
        topology=None if args.probe_topology is None else ([] if args.probe_topology=='intact'
            else list(map(int,args.probe_topology.split(';'))))
        print(json.dumps(run(args.root,args.model,args.inputs,args.output,device=args.device,
            execute=args.execute,probe_topology=topology)))
    else:
        from .inference import predict_saved_case
        print(json.dumps(predict_saved_case(args.root,args.model,args.output)))


if __name__=='__main__':main()
