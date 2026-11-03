"""Execute the phase-one notebook with this Python interpreter in a fresh kernel.

From the project root: python3 scripts/run_phase1_notebook.py
Install requirements.txt first. No global kernel registration or server is needed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--timeout", type=int, default=180, help="Maximum seconds per code cell")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    root = args.root.resolve()
    notebook_path = root / "notebooks/phase1.ipynb"
    if not (root / "data/udslong_imputed.csv").is_file():
        raise FileNotFoundError("Run with the project root and its supplied data files available")
    notebook = nbformat.read(notebook_path, as_version=4)
    # Some IDEs persist a nonstandard output-only display handle. It is not
    # scientific content and must not prevent a fresh standard-kernel execution.
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            output.pop("jetTransient", None)
    nbformat.validate(notebook)

    # This temporary kernel specification uses the same environment as this
    # command; nothing is installed into the user's global kernels directory.
    with tempfile.TemporaryDirectory(prefix="statistics-phase1-kernel-") as temp:
        base = Path(temp)
        kernel_dir = base / "kernels/statistics-phase1"
        kernel_dir.mkdir(parents=True)
        (kernel_dir / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Statistics phase one", "language": "python",
        }), encoding="utf-8")
        names = ("JUPYTER_PATH", "JUPYTER_RUNTIME_DIR", "IPYTHONDIR")
        previous = {name: os.environ.get(name) for name in names}
        os.environ["JUPYTER_PATH"] = str(base) + (os.pathsep + previous["JUPYTER_PATH"] if previous["JUPYTER_PATH"] else "")
        os.environ["JUPYTER_RUNTIME_DIR"] = str(base / "runtime")
        os.environ["IPYTHONDIR"] = str(base / "ipython")
        try:
            NotebookClient(notebook, timeout=args.timeout, kernel_name="statistics-phase1",
                           resources={"metadata": {"path": str(root)}}).execute()
        finally:
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    notebook.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nbformat.validate(notebook)
    cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    if [c.execution_count for c in cells] != list(range(1, len(cells) + 1)):
        raise ValueError("Code cells were not executed in order")
    if any(out.output_type == "error" for cell in cells for out in cell.outputs):
        raise ValueError("Notebook contains an execution error")
    stderr = [out.text for cell in cells for out in cell.outputs if out.output_type == "stream" and out.name == "stderr"]
    if stderr:
        raise ValueError("Notebook emitted stderr; review it before replacing the saved notebook: " + "\n".join(stderr))
    # Save only a successfully executed, valid notebook; an execution failure
    # leaves the previously saved notebook intact. Generated stage outputs are
    # refreshed by their existing writers and integrity checks.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=notebook_path.parent,
                                     prefix=".phase1-", suffix=".ipynb", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        nbformat.write(notebook, temp_path)
        os.replace(temp_path, notebook_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    # Build the report only after the executed notebook has been saved. Its
    # provenance ignores timing metadata, but covers sources and saved outputs.
    from build_phase1_pdf import build_report
    pdf = build_report(root)
    print(json.dumps({"notebook": "notebooks/phase1.ipynb", "cells": len(notebook.cells),
                      "executed_code_cells": len(cells), "errors": 0,
                      "stderr_outputs": len(stderr), "pdf_report": pdf}, ensure_ascii=False))


if __name__ == "__main__":
    main()
