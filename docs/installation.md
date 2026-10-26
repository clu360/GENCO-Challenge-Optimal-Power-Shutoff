# Installation

Use Python 3.12 and a short, writable checkout path. Current model qualification
uses Windows/CPU; a shell recipe alone is not a platform-test claim.

## Results and notebooks

Windows PowerShell:

```powershell
python -m venv .venv-results
& .venv-results/Scripts/Activate.ps1
python -m pip install -e '.[notebooks,test]'
genco-ops results --study goc_500 --output outputs/goc500
genco-ops results --study texas2k --output outputs/texas2k
python scripts/execute_notebooks.py
```

For a shell where virtual environments use `bin/`, activate with
`source .venv-results/bin/activate` and use the same Python commands.
Open the notebooks in VS Code or an existing Jupyter environment with this
interpreter. The execution script runs fresh kernels without a browser.

If activation is disabled by PowerShell policy, invoke
`.venv-results/Scripts/python.exe` directly instead of changing system policy.
Models, solvers and cluster access are unnecessary for saved-results exploration.

## Official CPU model runtime

Keep a separate environment to preserve the numerical package pins:

```powershell
python -m venv .venv-models
& .venv-models/Scripts/Activate.ps1
python -m pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r environments/model_cpu_requirements.txt
python -m pip install -e '.[notebooks,test]'
python scripts/download_models.py
genco-ops models --study goc_500 --verify-hashes
```

GraphKit and GridSFM are installed from the pinned official commits. Do not import
the original research checkout as a substitute. The two model archives total
approximately 951 MB; downloads and extraction are explicit and checksum-verified.

## Optional AC solver and paper builds

Exact A/B uses Julia, PowerModels and Ipopt under `environments/julia/`.
Instantiation and execution are separate steps in [reproduction](reproduction.md).
Existing A/B is economic redispatch/service auditing, separate from the proposed
risk-aware shortlist refinement.

The optional `paper` extra installs PDF-layout tools for the compact submission.
Its figures regenerate from included compact data; see `submission/README.md`.
