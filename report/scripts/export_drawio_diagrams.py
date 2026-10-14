#!/usr/bin/env python3
"""Export all .drawio diagrams in report/assets/diagrams/ to vector PDF using Draw.io CLI."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT / "assets/diagrams"

def find_drawio():
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/draw.io/draw.io.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "draw.io/draw.io.exe",
        Path("C:/Program Files/draw.io/draw.io.exe"),
        Path("C:/Program Files (x86)/draw.io/draw.io.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None

def main():
    drawio_exe = find_drawio()
    if not drawio_exe:
        print("ERROR: draw.io.exe not found.")
        sys.exit(1)

    print(f"Using draw.io: {drawio_exe}")
    drawio_files = sorted(DIAGRAMS_DIR.glob("*.drawio"))
    print(f"Found {len(drawio_files)} .drawio files to export.\n")

    success_count = 0
    for f in drawio_files:
        pdf_out = f.with_suffix(".pdf")
        cmd = [drawio_exe, "-x", "-f", "pdf", "--crop", "-o", str(pdf_out), str(f)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"[OK] {f.name} -> {pdf_out.name} ({pdf_out.stat().st_size} bytes)")
            success_count += 1
        except subprocess.CalledProcessError as err:
            print(f"[FAIL] {f.name}: {err.stderr}")

    print(f"\nCompleted: {success_count}/{len(drawio_files)} diagrams exported to vector PDF.")

if __name__ == "__main__":
    main()
