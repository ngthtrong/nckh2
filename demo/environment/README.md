# Reproducible environment

The Python boundary is CPython `>=3.12,<3.13`.  `requirements.lock` at the
repository root pins every distribution in the audited environment; direct
runtime dependencies are also pinned in `pyproject.toml`. It is the sole
canonical dependency lock; no second lock format is maintained.

Create a clean environment from the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
```

The native candidate runner additionally requires Git and Bubblewrap
(`bwrap`).  Bubblewrap mounts the repository read-only and exposes only the
new candidate run's output directories as writable.  Paper compilation
requires XeLaTeX and BibTeX; the audited host used TeX Live 2023.

Capture the exact Python, OS, CPU, RAM, NumPy/BLAS, thread-pool, package, Git,
Bubblewrap, XeLaTeX, and BibTeX state without replacing a previous record:

```bash
.venv/bin/python -m demo.environment.capture --output environment.json
```

Every candidate run invokes the same capture function and embeds the result
in its immutable provenance files and final manifest.
