"""Build or verify the local phase-one ZIP from its explicit file inventory.

Build: python3 scripts/package_phase1.py
Verify and reproduce in a temporary extracted copy:
    python3 scripts/package_phase1.py --verify dist/phase-1-nacc.zip --reproduce

No Git, GitHub or course-system mutation is performed by this script.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

import nbformat

PREFIX = "phase-1-nacc"
PACKAGE_MANIFEST = "_PACKAGE_MANIFEST.json"
INVENTORY = "config/phase1_delivery_files.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory_files(root: Path) -> list[dict]:
    inventory = json.loads((root / INVENTORY).read_text(encoding="utf-8"))
    entries = inventory["files"]
    names = [item["path"] for item in entries]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate paths in delivery inventory")
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("Unsafe inventory path: " + name)
        source = root / name
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError("Inventory item is missing or not a regular local file: " + name)
    return entries


def check_root(root: Path) -> dict:
    root = root.resolve()
    entries = inventory_files(root)
    names = {item["path"] for item in entries}
    sys.path.insert(0, str(root))
    from src.phase1_dataset import load_dataset
    from src.phase1_quality import fingerprint
    from scripts.build_phase1_pdf import verify_report

    participants, manifest = load_dataset(root)
    descriptive = json.loads((root / "reports/phase1/descriptive_statistics.json").read_text(encoding="utf-8"))
    figures = json.loads((root / "reports/phase1/figures_metadata.json").read_text(encoding="utf-8"))
    checksums = {**descriptive["output_sha256"], **figures["output_sha256"],
                 **descriptive["provenance"]["code_sha256"],
                 **figures["provenance"]["protected_sha256"], **figures["provenance"]["code_sha256"]}
    for path, digest in checksums.items():
        if fingerprint(root / path) != digest:
            raise ValueError("A scientific artifact or dependency changed: " + path)
    p = descriptive["provenance"]
    if fingerprint(root / p["dataset"]) != p["dataset_sha256"] or fingerprint(root / p["dataset_manifest"]) != p["dataset_manifest_sha256"]:
        raise ValueError("Descriptive source does not match the participant table")
    expected = {"all_shared": len(participants), **{key: value["included"] for key, value in manifest["samples"].items()}}
    if descriptive["populations"] != expected or figures["n_main_pair"] != expected["main_pair"]:
        raise ValueError("Population counts disagree between outputs")
    n = nbformat.read(root / "notebooks/phase1.ipynb", as_version=4)
    nbformat.validate(n)
    code = [c for c in n.cells if c.cell_type == "code"]
    if [c.execution_count for c in code] != list(range(1, len(code)+1)) or not all(c.outputs for c in code):
        raise ValueError("Notebook is not completely executed in order")
    if any(o.output_type == "error" or (o.output_type == "stream" and o.name == "stderr") for c in code for o in c.outputs):
        raise ValueError("Notebook has an error or stderr output needing review")
    embedded = [hashlib.sha256(base64.b64decode(o.data["image/png"])).hexdigest()
                for c in code for o in c.outputs if "data" in o and "image/png" in o.data]
    images = [fingerprint(root / path) for path in figures["files"] if path.endswith(".png")]
    if len(embedded) != 4 or sorted(embedded) != sorted(images):
        raise ValueError("Embedded images differ from the four saved PNGs")
    pdf_checks = verify_report(root)
    notebook_text = "\n".join(c.source for c in n.cells if c.cell_type == "markdown")
    anchors = re.findall(r'<a id="([^"]+)"></a>', notebook_text)
    if len(anchors) != len(set(anchors)):
        raise ValueError("Duplicate explicit notebook anchors")
    documents = [(root / name, (root / name).read_text(encoding="utf-8")) for name in names if name.endswith(".md")]
    documents += [(root / "notebooks/phase1.ipynb", c.source) for c in n.cells if c.cell_type == "markdown"]
    documents += [(root / "notebooks/phase1.ipynb", o.data["text/markdown"]) for c in code for o in c.outputs if "data" in o and "text/markdown" in o.data]
    links = 0
    for source, text in documents:
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            target = target.strip("<>")
            if target.startswith(("https:", "http:", "mailto:")):
                continue
            part, _, anchor = target.partition("#")
            resolved = (source.parent / unquote(part)).resolve() if part else source
            if not resolved.is_relative_to(root) or not resolved.is_file() or resolved.relative_to(root).as_posix() not in names:
                raise ValueError(f"Local reference is outside the package: {source.relative_to(root)} -> {target}")
            if resolved.suffix == ".ipynb" and anchor and anchor not in anchors:
                raise ValueError("Missing notebook anchor: " + anchor)
            links += 1
    return {"inventory_files": len(entries), "notebook_cells": len(n.cells), "executed_code_cells": len(code),
            "errors": 0, "stderr_outputs": 0, "embedded_images": len(embedded),
            "participants": len(participants), "participant_columns": manifest["columns"],
            "populations": expected, "local_links_verified": links,
            "scientific_hashes_verified": len(checksums), **pdf_checks}


def build(root: Path, destination: Path) -> dict:
    checks = check_root(root)
    inventory = inventory_files(root)
    entries = [entry for entry in inventory if entry.get("archive", True)]
    external = [entry for entry in inventory if not entry.get("archive", True)]
    payload = {"schema_version": 1, "phase": 1, "archive_root": PREFIX,
               "status": "local_package_not_uploaded", "checks": checks,
               "external_inputs": [{"path": entry["path"], "bytes": (root / entry["path"]).stat().st_size,
                                    "sha256": sha256(root / entry["path"])} for entry in external],
               "files": [{**entry, "bytes": (root / entry["path"]).stat().st_size,
                          "sha256": sha256(root / entry["path"])} for entry in entries]}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".zip", prefix=".phase1-", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            # Fixed archive timestamps and permissions keep repeated packaging
            # independent of local mtimes and private source-file permissions.
            def add(name: str, data: bytes) -> None:
                info = zipfile.ZipInfo(PREFIX + "/" + name, date_time=(2026, 10, 31, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
            for entry in sorted(entries, key=lambda item: item["path"]):
                data = (root / entry["path"]).read_bytes()
                expected = next(f["sha256"] for f in payload["files"] if f["path"] == entry["path"])
                if hashlib.sha256(data).hexdigest() != expected:
                    raise ValueError("File changed during packaging: " + entry["path"])
                add(entry["path"], data)
            add(PACKAGE_MANIFEST, (json.dumps(payload, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return checks


def verify(archive_path: Path, reproduce: bool = False, data_root: Path | None = None) -> dict:
    with tempfile.TemporaryDirectory(prefix="statistics-phase1-package-") as temp:
        temporary = Path(temp)
        with zipfile.ZipFile(archive_path) as archive:
            if archive.testzip() is not None:
                raise ValueError("Archive CRC verification failed")
            members = archive.namelist()
            if len(members) != len(set(members)):
                raise ValueError("Duplicate archive member")
            payload = json.loads(archive.read(PREFIX + "/" + PACKAGE_MANIFEST))
            expected = {PREFIX + "/" + f["path"] for f in payload["files"]} | {PREFIX + "/" + PACKAGE_MANIFEST}
            if set(members) != expected:
                raise ValueError("Archive file set differs from its manifest")
            for info in archive.infolist():
                name = PurePosixPath(info.filename)
                if name.is_absolute() or ".." in name.parts or name.parts[0] != PREFIX or (info.external_attr >> 16) & 0o170000 != 0o100000:
                    raise ValueError("Unsafe or non-regular archive member")
            for entry in payload["files"]:
                data = archive.read(PREFIX + "/" + entry["path"])
                if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise ValueError("Archived bytes differ from manifest: " + entry["path"])
            archive.extractall(temporary)
        root = temporary / PREFIX
        # Raw TA inputs are intentionally absent from the submission archive.
        # Restore verified local copies only inside the temporary validation tree.
        for entry in payload.get("external_inputs", []):
            name = PurePosixPath(entry["path"])
            if name.is_absolute() or ".." in name.parts or not name.parts:
                raise ValueError("Unsafe external-input path")
            if data_root is None:
                raise ValueError("Archive verification requires --data-root with the original TA inputs")
            source = data_root / entry["path"]
            if (not source.is_file() or source.is_symlink() or
                    not source.resolve().is_relative_to(data_root.resolve()) or
                    source.stat().st_size != entry["bytes"] or sha256(source) != entry["sha256"]):
                raise ValueError("Original TA input missing or changed: " + entry["path"])
            target = root / entry["path"]
            if target.exists():
                raise ValueError("External input must not be stored in the archive: " + entry["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        command = [sys.executable, str(root / "scripts/package_phase1.py"), "--check-root", str(root)]
        checked = subprocess.run(command, cwd=root, env=environment, text=True, capture_output=True, check=True)
        checks = json.loads(checked.stdout)
        if checked.stderr:
            raise ValueError("Extracted-package validation emitted stderr: " + checked.stderr)
        result = {"archive": archive_path.name, "sha256": sha256(archive_path),
                  "bytes": archive_path.stat().st_size, "archive_members": len(members),
                  "archive_crc_ok": True, "all_file_hashes_match": True, "extracted_checks": checks,
                  "raw_inputs_in_archive": False, "external_inputs_verified": len(payload.get("external_inputs", [])),
                  "reproduced": False}
        if reproduce:
            before = nbformat.read(root / "notebooks/phase1.ipynb", as_version=4)
            run = subprocess.run([sys.executable, str(root / "scripts/run_phase1_notebook.py")],
                                 cwd=root, env=environment, text=True, capture_output=True, check=True)
            if run.stderr:
                raise ValueError("Notebook reproduction emitted stderr: " + run.stderr)
            execution = json.loads(run.stdout)
            if execution["stderr_outputs"]:
                raise ValueError("Reproduced notebook has stderr outputs")
            after = nbformat.read(root / "notebooks/phase1.ipynb", as_version=4)
            a = [c for c in before.cells if c.cell_type == "code"]
            b = [c for c in after.cells if c.cell_type == "code"]
            if len(a) != len(b) or any((x.source, x.execution_count, x.outputs) != (y.source, y.execution_count, y.outputs) for x, y in zip(a, b)):
                raise ValueError("Reproduction changed a code cell or analytical output")
            for entry in payload["files"]:
                if entry["path"] != "notebooks/phase1.ipynb" and sha256(root / entry["path"]) != entry["sha256"]:
                    raise ValueError("Reproduction changed an archived scientific artifact: " + entry["path"])
            tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                                   cwd=root, env=environment, text=True, capture_output=True, check=True)
            match = re.search(r"Ran (\d+) tests", tests.stdout + tests.stderr)
            result.update(reproduced=True, notebook_execution=execution,
                          analytical_outputs_equal=True, tests_passed=int(match.group(1)) if match else None)
            subprocess.run(command, cwd=root, env=environment, text=True, capture_output=True, check=True)
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path, metavar="ZIP")
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--data-root", type=Path, help="Project tree containing the original data/ CSVs; defaults to --root")
    parser.add_argument("--check-root", type=Path, help="Validate a complete local tree without creating an archive")
    args = parser.parse_args()
    if args.check_root:
        result = check_root(args.check_root)
    elif args.verify:
        result = verify(args.verify.resolve(), reproduce=args.reproduce, data_root=(args.data_root or args.root).resolve())
    else:
        root = args.root.resolve()
        output = args.output.resolve() if args.output else root / "dist/phase-1-nacc.zip"
        if output.resolve().is_relative_to(root) and output.relative_to(root).as_posix() in {f["path"] for f in inventory_files(root)}:
            parser.error("Archive destination would overwrite an inventory file")
        build(root, output)
        result = verify(output, reproduce=args.reproduce, data_root=(args.data_root or root).resolve())
        output.with_suffix(".zip.sha256").write_text(result["sha256"] + "  " + output.name + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
