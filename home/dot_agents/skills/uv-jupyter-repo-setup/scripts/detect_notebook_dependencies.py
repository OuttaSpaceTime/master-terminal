#!/usr/bin/env python3
"""Infer third-party dependencies from Jupyter notebooks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE_DEPENDENCIES = {
    "ipykernel",
    "ipython",
    "jupyterlab",
    "notebook",
}

MODULE_TO_PACKAGE = {
    "IPython": "ipython",
    "datasets": "datasets",
    "datatrove": "datatrove",
    "faiss": "faiss-cpu",
    "fsspec": "fsspec",
    "gensim": "gensim",
    "matplotlib": "matplotlib",
    "matplotlib_inline": "matplotlib-inline",
    "mauve": "mauve-text",
    "mpl_toolkits": "matplotlib",
    "nbformat": "nbformat",
    "numpy": "numpy",
    "pandas": "pandas",
    "requests": "requests",
    "scipy": "scipy",
    "seaborn": "seaborn",
    "sklearn": "scikit-learn",
    "spacy": "spacy",
    "statsmodels": "statsmodels",
    "sympy": "sympy",
    "tiktoken": "tiktoken",
    "torch": "torch",
    "torchinfo": "torchinfo",
    "tqdm": "tqdm",
    "transformers": "transformers",
    "wasabi": "wasabi",
}

OPTIONAL_GPU_PACKAGES = ["bitsandbytes"]

IGNORED_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    ".ipynb_checkpoints",
}

IMPORT_RE = re.compile(r"^\s*import\s+([^#]+)")
FROM_RE = re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+")
PIP_PREFIXES = (
    "!pip install ",
    "%pip install ",
    "python -m pip install ",
    "# !pip install ",
    "# %pip install ",
    "# python -m pip install ",
)


def iter_notebooks(repo: Path):
    for path in repo.rglob("*.ipynb"):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        yield path


def normalize_pip_token(token: str) -> str | None:
    token = token.strip().strip("\"'").rstrip("\\")
    if not token:
        return None
    if token.startswith("-"):
        return None
    if token.startswith("git+"):
        return None
    if token.startswith("http://") or token.startswith("https://"):
        return None
    token = token.split("#", 1)[0].strip()
    token = re.split(r"[<>=!~\[]", token, maxsplit=1)[0].strip()
    token = token.replace("_", "-")
    return token or None


def extract_pip_payload(line: str) -> str | None:
    lower = line.lower().strip()
    for prefix in PIP_PREFIXES:
        if lower.startswith(prefix):
            return line.strip()[len(prefix) :]
    return None


def extract_modules_and_pip_packages(lines):
    modules = []
    pip_packages = []

    for raw_line in lines:
        line = str(raw_line).strip()
        if not line:
            continue

        import_match = IMPORT_RE.match(line)
        if import_match:
            for part in import_match.group(1).split(","):
                part = part.strip()
                if not part:
                    continue
                base = part.split(" as ", 1)[0].strip().split(".", 1)[0]
                if base:
                    modules.append(base)
            continue

        from_match = FROM_RE.match(line)
        if from_match:
            base = from_match.group(1).split(".", 1)[0]
            if base:
                modules.append(base)
            continue

        payload = extract_pip_payload(line)
        if payload:
            payload = payload.split("#", 1)[0]
            for token in payload.split():
                package = normalize_pip_token(token)
                if package:
                    pip_packages.append(package)

    return modules, pip_packages


def to_package(module_name: str, stdlib: set[str]) -> tuple[str | None, bool]:
    if module_name in MODULE_TO_PACKAGE:
        return MODULE_TO_PACKAGE[module_name], False
    if module_name in stdlib:
        return None, False
    return module_name.replace("_", "-"), True


def scan_repo(repo: Path, include_base: bool):
    stdlib = set(sys.stdlib_module_names)
    module_counts: Counter[str] = Counter()
    pip_counts: Counter[str] = Counter()
    unknown_modules: Counter[str] = Counter()
    package_set: set[str] = set()
    notebook_count = 0

    for notebook in iter_notebooks(repo):
        notebook_count += 1
        try:
            payload = json.loads(notebook.read_text(encoding="utf-8"))
        except Exception:
            continue

        cells = payload.get("cells", [])
        for cell in cells:
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source", [])
            if isinstance(source, str):
                source = source.splitlines()
            modules, pip_packages = extract_modules_and_pip_packages(source)
            module_counts.update(modules)
            pip_counts.update(pip_packages)

    for module in module_counts:
        package, is_unknown = to_package(module, stdlib)
        if package:
            package_set.add(package)
        if is_unknown:
            unknown_modules[module] += module_counts[module]

    package_set.update(pip_counts.keys())
    package_set.difference_update(OPTIONAL_GPU_PACKAGES)
    if include_base:
        package_set.update(BASE_DEPENDENCIES)

    return {
        "repo": str(repo.resolve()),
        "notebook_count": notebook_count,
        "recommended_dependencies": sorted(package_set),
        "optional_gpu_dependencies": OPTIONAL_GPU_PACKAGES,
        "module_counts": dict(sorted(module_counts.items())),
        "pip_install_counts": dict(sorted(pip_counts.items())),
        "unknown_third_party_modules": dict(sorted(unknown_modules.items())),
    }


def print_text(result: dict):
    print("# Recommended dependencies")
    for dep in result["recommended_dependencies"]:
        print(dep)

    print("\n# Optional GPU dependencies")
    for dep in result["optional_gpu_dependencies"]:
        print(dep)

    print("\n# Unknown third-party modules (review)")
    unknown = result["unknown_third_party_modules"]
    if unknown:
        for name, count in unknown.items():
            print(f"{name}\t{count}")
    else:
        print("none")

    print("\n# Notebook count")
    print(result["notebook_count"])


def print_toml(result: dict):
    print("dependencies = [")
    for dep in result["recommended_dependencies"]:
        print(f'    "{dep}",')
    print("]")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument(
        "--format",
        choices=("text", "json", "toml"),
        default="text",
    )
    parser.add_argument(
        "--no-base",
        action="store_true",
        help="Do not include core notebook dependencies.",
    )
    args = parser.parse_args()

    result = scan_repo(args.repo, include_base=not args.no_base)

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    elif args.format == "toml":
        print_toml(result)
    else:
        print_text(result)


if __name__ == "__main__":
    main()
