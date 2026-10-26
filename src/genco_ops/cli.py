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
    inference.add_argument('--inputs',type=Path,help='Optional authorized saved-case file or graph-pack directory; catalog checksum still required')
    catalog=commands.add_parser('models',help='List grid-compatible checkpoints and local model/input availability')
    catalog.add_argument('--root',type=Path,default=Path.cwd())
    catalog.add_argument('--study',choices=['texas2k','goc_500'])
    catalog.add_argument('--verify-hashes',action='store_true',help='Verify present model/input bytes rather than file presence alone')
    catalog.add_argument('--json',action='store_true',help='Emit complete machine-readable readiness records')
    workflow=commands.add_parser('run',help='Select a model and grid, inspect a plan, then explicitly run an existing pipeline')
    workflow.add_argument('--root',type=Path,default=Path.cwd())
    workflow.add_argument('--study',choices=['texas2k','goc_500'],required=True)
    workflow.add_argument('--model',required=True)
    workflow.add_argument('--mode',choices=['infer','demo','published'],default='infer')
    workflow.add_argument('--output',type=Path,required=True)
    workflow.add_argument('--inputs',type=Path,help='Authorized saved case/graph pack for infer, or prepared electrical-input directory for published')
    workflow.add_argument('--config',type=Path,help='Bounded GOC demo config only; published numerical contracts remain frozen')
    workflow.add_argument('--device',choices=['cpu','cuda:0'],help='Default CPU for inference/demo/probe; cuda:0 for full Texas search')
    workflow.add_argument('--probe-topology',help='Texas published portability probe only: intact or sorted line IDs separated by semicolons')
    workflow.add_argument('--execute',action='store_true',help='Perform numerical work; omission only inspects the plan')
    public_genco=commands.add_parser('public-genco',help='Run the released GENCO base on public IEEE14; separate from Texas results')
    public_genco.add_argument('--root',type=Path,default=Path.cwd())
    public_genco.add_argument('--output',type=Path,required=True)
    public_genco.add_argument('--scenario',type=int,default=0)
    public_genco.add_argument('--execute',action='store_true',help='Run one real prediction; omission only inspects the plan')
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
    if args.command=='models':
        from .catalog import models,format_models
        rows=models(args.root,args.study,verify_hashes=args.verify_hashes)
        print(json.dumps(rows,indent=2) if args.json else format_models(rows))
    elif args.command=='public-genco':
        from .workflow import run_public_genco
        print(json.dumps(run_public_genco(args.root,args.output,scenario=args.scenario,execute=args.execute),indent=2))
    elif args.command=='run':
        from .workflow import run_workflow
        topology=None if args.probe_topology is None else ([] if args.probe_topology=='intact'
            else list(map(int,args.probe_topology.split(';'))))
        print(json.dumps(run_workflow(args.root,args.study,args.model,args.output,mode=args.mode,
            execute=args.execute,inputs=args.inputs,config=args.config,device=args.device,probe_topology=topology),indent=2))
    elif args.command=='results':
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
        print(json.dumps(predict_saved_case(args.root,args.model,args.output,inputs=args.inputs)))


if __name__=='__main__':main()
