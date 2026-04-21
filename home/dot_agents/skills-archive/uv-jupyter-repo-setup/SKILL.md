---
name: uv-jupyter-repo-setup
description: Setup and standardize Python repositories for Jupyter notebooks using uv. Use when a user asks to configure uv, install Jupyter Notebook/Lab tooling, migrate notebook repos from requirements/conda to uv, infer dependencies from .ipynb files, pin Python versions, or create repeatable `uv sync` + `uv run jupyter ...` workflows across repos.
---

# UV Jupyter Repo Setup

## Overview

Set up or migrate a repository to `uv` for notebook work with a repeatable workflow.
Prefer a CPU-first default for PyTorch to avoid large CUDA downloads, and expose GPU extras as optional.

## Workflow

1. Inspect current repo state.
2. Infer dependencies from notebooks with the bundled script.
3. Create or update `pyproject.toml`, `.python-version`, and `.gitignore`.
4. Run `uv lock` and `uv sync`.
5. Verify notebook tooling and critical imports.

## Step 1: Inspect Existing Environment Files

Run:

```bash
rg --files -g 'pyproject.toml' -g 'uv.lock' -g 'requirements*.txt' -g 'environment*.yml' -g 'Pipfile' -g 'poetry.lock' -g '.python-version' -g '*.ipynb'
```

If `pyproject.toml` already exists, preserve its existing structure and only add missing dependency/config entries.

## Step 2: Infer Notebook Dependencies

Use the bundled script:

```bash
python3 scripts/detect_notebook_dependencies.py --repo <target-repo>
```

For machine-readable output:

```bash
python3 scripts/detect_notebook_dependencies.py --repo <target-repo> --format json
```

Use the recommended dependency list as input for `pyproject.toml`.

## Step 3: Apply Standard uv + Jupyter Baseline

Set:
- `.python-version` to `3.12` unless the user asks for another version.
- `.gitignore` entries for `.venv/` and `.ipynb_checkpoints/` if missing.

Use a `pyproject.toml` dependency baseline that always includes:
- `ipykernel`
- `ipython`
- `jupyterlab`
- `notebook`

For PyTorch notebook repos, default to CPU wheels:

```toml
[tool.uv.sources]
torch = [{ index = "pytorch-cpu" }]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

Use optional extras for GPU-specific packages (e.g. `bitsandbytes`) instead of default install.

See `references/dependency-notes.md` for package mapping and baseline guidance.

## Step 4: Lock and Sync

Run in target repo:

```bash
uv python install 3.12
uv lock --python 3.12
uv sync --python 3.12 --frozen
```

If the user asks for GPU extras:

```bash
uv sync --python 3.12 --extra gpu
```

## Step 5: Verify

Run:

```bash
uv run python --version
uv run jupyter --version
uv run jupyter notebook --version
```

For project-specific sanity checks, import a small set of high-value packages from the dependency list:

```bash
uv run python -c "import notebook, jupyterlab, ipykernel; print('ok')"
```

## Output Requirements

When reporting completion:
- List created or modified files.
- State selected Python version explicitly.
- State whether torch is CPU-default or GPU-enabled.
- Provide exact launch commands:
  - `uv run jupyter notebook`
  - `uv run jupyter lab`

## Guardrails

- Do not overwrite unrelated existing config.
- Do not remove user-defined dependencies unless asked.
- Prefer minimal additions when repo already has packaging metadata.
- If dependency inference returns unknown third-party modules, report them for review instead of guessing silently.
