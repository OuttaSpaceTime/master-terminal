# Dependency Notes

Use this mapping when notebook imports need translation into package names:

- `sklearn` -> `scikit-learn`
- `matplotlib_inline` -> `matplotlib-inline`
- `mauve` -> `mauve-text`
- `faiss` -> `faiss-cpu`
- `IPython` -> `ipython`

Always include notebook runtime baseline dependencies:

- `ipykernel`
- `ipython`
- `jupyterlab`
- `notebook`

For torch-heavy repos on Linux, prefer CPU by default in `pyproject.toml`:

```toml
[tool.uv.sources]
torch = [{ index = "pytorch-cpu" }]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

Put GPU-specific packages behind an optional extra:

```toml
[project.optional-dependencies]
gpu = ["bitsandbytes"]
```
