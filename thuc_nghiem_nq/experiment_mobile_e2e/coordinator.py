"""Compatibility entry point; implementation moved to products/fe/experiment_mobile."""
from pathlib import Path
import runpy
import sys

if __name__ == '__main__':
    target = Path(__file__).resolve().parents[2] / 'products/fe/experiment_mobile'
    sys.path.insert(0, str(target))
    runpy.run_path(str(target/'coordinator.py'), run_name='__main__')
