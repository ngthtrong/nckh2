# Flood Rescue Paper Draft

This folder contains the preliminary LNCS-style LaTeX manuscript.

## Files

- `main.tex`: main paper draft.
- `llncs.cls`: Springer LNCS document class copied from the provided template.
- `splncs04.bst`: LNCS BibTeX style copied from the provided template.

## Compile

From this folder:

```powershell
& 'C:\Users\jhiny\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe' -interaction=nonstopmode -halt-on-error main.tex
& 'C:\Users\jhiny\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe' -interaction=nonstopmode -halt-on-error main.tex
```

The generated PDF is `main.pdf`.

## Python Environment

The project virtual environment is located at `../.venv`.

From the repository root:

```powershell
.\.venv\Scripts\python.exe demo\review3\scripts\import_sample_data.py
.\.venv\Scripts\python.exe demo\review3\scripts\run_louvain.py
```

The current preliminary Louvain run on `demo/review3/data/sample_reports.csv` produced:

- Nodes: 240
- Edges: 1425
- Communities: 16
- Modularity: 0.9205

## Sections To Update After Experiments

- Final Edge AI accuracy/F1, model size, and mobile inference latency.
- Final Louvain/DBSCAN/ST-DBSCAN clustering metrics.
- Network simulation results for full payload vs compact metadata.
- Final author emails, ORCID IDs, acknowledgments, and target conference formatting rules.
