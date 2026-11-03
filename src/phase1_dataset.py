"""Export the selected participant table and explicit sample denominators.

Run from the project root with ``python3 -m src.phase1_dataset``. The CSVs are
derived analysis intermediates, not edited copies of the supplied input files.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from collections import Counter
from pathlib import Path

from .phase1_quality import INPUT_FILES, audit, fingerprint, load_table


DATA_PATH = "data/processed/phase1_participants.csv"
MANIFEST_PATH = "data/processed/phase1_manifest.json"
FLOW_PATH = "reports/phase1/sample_flow.csv"
DENOMINATOR_PATH = "reports/phase1/denominators.csv"
REPORT_PATH = "reports/phase1/sample_flow.md"
SAMPLE_FLAGS = {
    "main_pair": "MAIN_PAIR_ELIGIBLE",
    "main_common": "MAIN_COMMON_SAMPLE_ELIGIBLE",
    "integer_pair": "INTEGER_SENSITIVITY_PAIR_ELIGIBLE",
    "integer_common": "INTEGER_SENSITIVITY_COMMON_ELIGIBLE",
}
REASON_FIELDS = {
    "main_pair": "MAIN_PAIR_EXCLUSION_REASONS",
    "main_common": "MAIN_COMMON_EXCLUSION_REASONS",
    "integer_pair": "INTEGER_PAIR_EXCLUSION_REASONS",
    "integer_common": "INTEGER_COMMON_EXCLUSION_REASONS",
}
ANALYSIS_COLUMNS = [
    "MOCATOTS_ANALYSIS", "NACCAGE_ANALYSIS", "SEX_ANALYSIS", "EDUC_ANALYSIS",
    "NACCUDSD_ANALYSIS", "LH_ENTORHINAL_AVGTH_ANALYSIS",
    "RH_ENTORHINAL_AVGTH_ANALYSIS", "ENTORHINAL_THICKNESS_MEAN",
]
IQR_FIELDS = {
    "MOCATOTS_ANALYSIS": "MOCA_IQR_FLAG",
    "NACCAGE_ANALYSIS": "AGE_IQR_FLAG",
    "EDUC_ANALYSIS": "EDUC_IQR_FLAG",
    "ENTORHINAL_THICKNESS_MEAN": "ENTORHINAL_IQR_FLAG",
}
RAW_FIELDS = {
    "NACCAGE_RAW": ("UDS", "NACCAGE"),
    "SEX_RAW": ("UDS", "SEX"),
    "EDUC_RAW": ("UDS", "EDUC"),
    "NACCUDSD_RAW_UDS": ("UDS", "NACCUDSD"),
    "NACCUDSD_RAW_MRI": ("MRI", "NACCUDSD"),
    "LH_ENTORHINAL_AVGTH_RAW": ("MRI", "LH_ENTORHINAL_AVGTH"),
    "RH_ENTORHINAL_AVGTH_RAW": ("MRI", "RH_ENTORHINAL_AVGTH"),
}


def _reason(status: str, detail: str | None) -> str:
    return status + (":" + detail if detail else "")


def exclusion_reasons(row: dict) -> dict[str, str]:
    pair = []
    if not row["MRI_MATCHED"]:
        pair.append("MRI:not_matched")
    if row["MOCATOTS_ANALYSIS"] is None:
        pair.append("MOCA:" + _reason(row["MOCA_STATUS"], row["MOCA_DETAIL"]))
    if row["ENTORHINAL_THICKNESS_MEAN"] is None:
        for side in ("LH_ENTORHINAL_AVGTH", "RH_ENTORHINAL_AVGTH"):
            if row[side + "_ANALYSIS"] is None:
                pair.append(side + ":" + row[side + "_STATUS"])
    covariates = [
        col + ":" + _reason(row[col + "_STATUS"], row[col + "_DETAIL"])
        for col in ("NACCAGE", "SEX", "EDUC") if row[col + "_ANALYSIS"] is None
    ]
    sensitivity = ["MOCA:fractional_in_range"] if row["MOCA_FRACTIONAL_IN_RANGE"] else []
    reasons = {
        "main_pair": pair,
        "main_common": pair + covariates,
        "integer_pair": pair + sensitivity,
        "integer_common": pair + sensitivity + covariates,
    }
    for sample, values in reasons.items():
        if bool(row[SAMPLE_FLAGS[sample]]) != (not values):
            raise ValueError(f"Eligibility and reasons disagree for {sample}")
    return {REASON_FIELDS[sample]: ";".join(values) for sample, values in reasons.items()}


def enrich_rows(prepared: list[dict], uds: list[dict], mri: list[dict], report: dict) -> list[dict]:
    """Attach exact raw strings, source lines, and review flags by identifier."""
    u = {row["NACCID"]: (line, row) for line, row in enumerate(uds, 2)}
    m = {row["NACCID"]: (line, row) for line, row in enumerate(mri, 2)}
    if len(u) != len(uds) or len(m) != len(mri):
        raise ValueError("Duplicate identifiers cannot be exported as a one-to-one join")
    if len({r["NACCID"] for r in prepared}) != len(prepared):
        raise ValueError("Duplicate prepared identifiers")
    lookup = {review["column"]: {item["NACCID"] for item in review["issues"]}
              for review in report["outlier_reviews"] if review["column"] in IQR_FIELDS}
    if set(lookup) != set(IQR_FIELDS):
        raise ValueError("Missing selected-variable IQR review")
    rows = []
    for item in prepared:
        key = item["NACCID"]
        if key not in u:
            raise ValueError("Prepared row is absent from the clinical source")
        if key not in m:
            # Unmatched identifiers are explicitly recorded in the join summary.
            continue
        if not item["MRI_MATCHED"]:
            raise ValueError("Prepared matching flag contradicts the source identifiers")
        ul, ur = u[key]
        ml, mr = m[key]
        if float(ur["NACCUDSD"]) != float(mr["NACCUDSD"]):
            raise ValueError("Conflicting source cognitive-status labels")
        if item["MOCATOTS_RAW"] != ur["MOCATOTS"]:
            raise ValueError("The original response string was modified")
        row = dict(item)
        row["UDS_CSV_LINE"] = ul
        row["MRI_CSV_LINE"] = ml
        for output, (source, col) in RAW_FIELDS.items():
            row[output] = (ur if source == "UDS" else mr)[col]
        for value_col, flag_col in IQR_FIELDS.items():
            # An unavailable measurement was not evaluated; that is not False.
            row[flag_col] = (key in lookup[value_col]) if row[value_col] is not None else None
        row.update(exclusion_reasons(row))
        rows.append(row)
    if {r["NACCID"] for r in rows} != set(u) & set(m):
        raise ValueError("Export must contain every shared participant exactly once")
    return rows


def build_flow(rows: list[dict]) -> list[dict]:
    flow, endpoints = [], {}

    def chain(scenario, parent, start, steps):
        current = list(start)
        flow.append({"scenario": scenario, "parent_sample": parent, "step": 0,
                     "criterion": "start", "description": "شروع این شاخه؛ با شاخه‌های دیگر جمع نشود",
                     "n_before": len(current), "n_removed": 0, "n_after": len(current)})
        for i, (name, description, condition) in enumerate(steps, 1):
            kept = [r for r in current if condition(r)]
            flow.append({"scenario": scenario, "parent_sample": parent, "step": i,
                         "criterion": name, "description": description,
                         "n_before": len(current), "n_removed": len(current)-len(kept), "n_after": len(kept)})
            current = kept
        endpoints[scenario] = current

    cov = [(c + "_available", f"نیاز به مقدار قابل استفادهٔ {c}",
            lambda r, col=c: r[col + "_ANALYSIS"] is not None)
           for c in ("NACCAGE", "SEX", "EDUC")]
    chain("main_pair", "all_shared", rows, [
        ("moca_not_special", "کنارگذاشتن کدهای ویژهٔ پاسخ از این خروجی، نه از جدول مرجع",
         lambda r: r["MOCA_STATUS"] != "known_special"),
        ("moca_usable_main", "نیاز به MoCA داخل دامنه طبق سیاست اصلی، شامل اعشار",
         lambda r: r["MOCATOTS_ANALYSIS"] is not None),
        ("both_thicknesses_available", "نیاز به هر دو ضخامت قابل استفاده برای میانگین",
         lambda r: r["ENTORHINAL_THICKNESS_MEAN"] is not None),
    ])
    chain("main_common", "main_pair", endpoints["main_pair"], cov)
    chain("integer_pair", "main_pair", endpoints["main_pair"], [
        ("moca_integer", "فقط در سناریوی حساسیت، کنارگذاشتن اعشار درون دامنه",
         lambda r: not r["MOCA_FRACTIONAL_IN_RANGE"]),
    ])
    chain("integer_common", "integer_pair", endpoints["integer_pair"], cov)
    for sample, endpoint in endpoints.items():
        expected = {r["NACCID"] for r in rows if r[SAMPLE_FLAGS[sample]]}
        if {r["NACCID"] for r in endpoint} != expected:
            raise ValueError(f"Sequential flow and membership differ: {sample}")
    return flow


def denominator_rows(rows: list[dict]) -> list[dict]:
    result = []
    populations = {"all_shared": rows}
    populations.update({sample: [r for r in rows if r[flag]] for sample, flag in SAMPLE_FLAGS.items()})
    for sample, participants in populations.items():
        for column in ANALYSIS_COLUMNS:
            unusable = [r for r in participants if r[column] is None]
            reasons = Counter()
            for row in unusable:
                if column == "MOCATOTS_ANALYSIS":
                    why = _reason(row["MOCA_STATUS"], row["MOCA_DETAIL"])
                elif column == "ENTORHINAL_THICKNESS_MEAN":
                    why = ";".join(side + ":" + row[side + "_STATUS"] for side in
                                   ("LH_ENTORHINAL_AVGTH", "RH_ENTORHINAL_AVGTH")
                                   if row[side + "_ANALYSIS"] is None)
                else:
                    base = column.removesuffix("_ANALYSIS")
                    why = _reason(row[base + "_STATUS"], row.get(base + "_DETAIL"))
                reasons[why] += 1
            n = len(participants)
            result.append({"sample": sample, "variable": column, "n_population": n,
                           "n_usable": n - len(unusable), "n_unusable": len(unusable),
                           "percent_unusable": 100 * len(unusable) / n if n else None,
                           "unusable_reason_counts": json.dumps(dict(reasons), ensure_ascii=False, sort_keys=True)})
    return result


def field_schema(rows: list[dict]) -> list[dict]:
    if not rows:
        raise ValueError("An empty shared cohort needs an explicit project decision")
    fields = []
    for name in rows[0]:
        values = [r[name] for r in rows]
        observed = [v for v in values if v is not None]
        if name in REASON_FIELDS.values() or name.endswith("_RAW") or "_RAW_" in name or name == "NACCID" or name.endswith("_STATUS"):
            typ = "string"
        elif name.endswith("_DETAIL"):
            typ = "string"
        elif name.endswith("_CSV_LINE"):
            typ = "integer"
        elif name in IQR_FIELDS.values() or name in SAMPLE_FLAGS.values() or name in {"MRI_MATCHED", "MOCA_FRACTIONAL_IN_RANGE"}:
            typ = "boolean"
        else:
            typ = "number"
        if name in ANALYSIS_COLUMNS:
            role = "analysis_value"
        elif name in SAMPLE_FLAGS.values():
            role = "sample_membership"
        elif name in REASON_FIELDS.values():
            role = "sample_exclusion_reasons"
        elif name in IQR_FIELDS.values():
            role = "iqr_review_only"
        elif "_RAW" in name:
            role = "exact_selected_source_string"
        elif name.endswith("_CSV_LINE"):
            role = "source_provenance"
        elif name == "NACCID":
            role = "person_identifier"
        else:
            role = "quality_status_or_flag"
        unit = "mm" if name in {"LH_ENTORHINAL_AVGTH_ANALYSIS", "RH_ENTORHINAL_AVGTH_ANALYSIS", "ENTORHINAL_THICKNESS_MEAN"} else None
        if name in {"NACCAGE_ANALYSIS", "EDUC_ANALYSIS"}:
            unit = "years"
        if name == "MOCATOTS_ANALYSIS":
            unit = "score"
        nullable = name.endswith("_DETAIL") or name in ANALYSIS_COLUMNS or name in IQR_FIELDS.values()
        for value in observed:
            if typ == "boolean" and type(value) is not bool:
                raise ValueError(f"Non-boolean value in {name}")
            if typ == "number" and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise ValueError(f"Nonfinite/non-numeric analysis value in {name}")
        if name in {"SEX_ANALYSIS", "NACCUDSD_ANALYSIS"}:
            statistical_type = "categorical_codes_not_continuous_measurements"
        elif name == "MOCATOTS_ANALYSIS":
            statistical_type = "bounded_score_including_flagged_prepared_decimals"
        elif name == "EDUC_ANALYSIS":
            statistical_type = "discrete_years"
        elif name == "NACCAGE_ANALYSIS":
            statistical_type = "age_recorded_in_years"
        elif unit == "mm":
            statistical_type = "continuous_measurement"
        else:
            statistical_type = role
        if name in RAW_FIELDS:
            source = ":".join(RAW_FIELDS[name])
        elif name == "MOCATOTS_RAW":
            source = "UDS:MOCATOTS"
        elif name in ANALYSIS_COLUMNS and name != "ENTORHINAL_THICKNESS_MEAN":
            source = ("MRI:" if name.startswith(("LH_", "RH_")) else "UDS:") + name.removesuffix("_ANALYSIS")
        elif name == "ENTORHINAL_THICKNESS_MEAN":
            source = "Arithmetic mean of the two usable MRI entorhinal AVGTH values for this identifier"
        elif name == "NACCID":
            source = "UDS:NACCID, matched one-to-one to MRI:NACCID"
        elif name.endswith("_CSV_LINE"):
            source = "CSV line in " + (INPUT_FILES["UDS"] if name.startswith("UDS_") else INPUT_FILES["MRI"])
        else:
            source = "Derived classification or sample/review flag; see quality and sample definitions"
        fields.append({"name": name, "type": typ, "nullable": nullable, "role": role,
                       "statistical_type": statistical_type, "unit": unit, "source": source})
    if any(list(row) != [f["name"] for f in fields] for row in rows):
        raise ValueError("Inconsistent participant record fields")
    return fields


def write_csv(path: Path, rows: list[dict], fields: list[dict] | None = None) -> None:
    """Atomic replacement of a derived CSV; None is blank, bool is exactly 0/1."""
    if not rows:
        raise ValueError("Cannot infer CSV columns from an empty table")
    names = [f["name"] for f in fields] if fields else list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent, prefix=".phase1-", suffix=".tmp", delete=False) as handle:
        temp = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=names, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row[k] is None else ("1" if row[k] else "0")
                             if isinstance(row[k], bool) else row[k] for k in names})
    try:
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def read_typed_csv(path: Path, fields: list[dict]) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != [f["name"] for f in fields]:
            raise ValueError("Saved columns differ from the declared schema")
        rows = []
        for source in reader:
            row = {}
            for field in fields:
                name, typ = field["name"], field["type"]
                raw = source[name]
                if raw is None:
                    raise ValueError("A saved record has fewer cells than its header")
                if raw == "" and field["nullable"]:
                    value = None
                elif typ == "string":
                    value = raw
                elif typ == "boolean":
                    if raw not in {"0", "1"}:
                        raise ValueError(f"Invalid saved boolean in {name}")
                    value = raw == "1"
                elif typ == "integer":
                    value = int(raw)
                elif typ == "number":
                    value = float(raw)
                    if not math.isfinite(value):
                        raise ValueError(f"Nonfinite saved analysis value in {name}")
                else:
                    raise ValueError(f"Unsupported saved field type: {typ}")
                row[name] = value
            if None in source:
                raise ValueError("A saved record has more cells than its header")
            rows.append(row)
    return rows


def _ids_digest(rows: list[dict]) -> str:
    import hashlib
    return hashlib.sha256("\n".join(sorted(r["NACCID"] for r in rows)).encode("utf-8")).hexdigest()


def build_dataset(root: Path) -> dict:
    root = root.resolve()
    report, prepared, _ = audit(root)
    _, uds = load_table(root / INPUT_FILES["UDS"])
    _, mri = load_table(root / INPUT_FILES["MRI"])
    if any(fingerprint(root / p) != digest for p, digest in report["input_sha256"].items()):
        raise ValueError("Inputs changed after the audit")
    rows = enrich_rows(prepared, uds, mri, report)
    fields, flow, denominators = field_schema(rows), build_flow(rows), denominator_rows(rows)
    uids, mids = {r["NACCID"] for r in uds}, {r["NACCID"] for r in mri}
    expected_keys = {"main_pair": "main_pair", "main_common": "main_common",
                     "integer_pair": "integer_sensitivity_pair", "integer_common": "integer_sensitivity_common"}
    samples = {}
    for name, flag in SAMPLE_FLAGS.items():
        included = [r for r in rows if r[flag]]
        if len(included) != report["eligibility"][expected_keys[name]]:
            raise ValueError("Audited eligibility differs from export membership")
        reason_counts = Counter(reason for r in rows for reason in r[REASON_FIELDS[name]].split(";") if reason)
        samples[name] = {"flag": flag, "reasons_field": REASON_FIELDS[name], "included": len(included),
                         "not_included": len(rows)-len(included), "sorted_identifier_sha256": _ids_digest(included),
                         "nonexclusive_reason_counts": dict(reason_counts)}
    return {"rows": rows, "fields": fields, "flow": flow, "denominators": denominators,
            "samples": samples, "input_sha256": report["input_sha256"], "config_sha256": report["config_sha256"],
            "join": {"uds_rows": len(uds), "mri_rows": len(mri), "shared_unique_ids": len(rows),
                     "uds_only_ids": sorted(uids-mids), "mri_only_ids": sorted(mids-uids),
                     "join_kind": "inner_one_to_one_by_NACCID", "canonical_group": "NACCUDSD from UDS after numeric agreement with MRI"}}


def export_dataset(root: Path, bundle: dict) -> dict:
    root = root.resolve()
    if any(fingerprint(root / p) != digest for p, digest in bundle["input_sha256"].items()):
        raise ValueError("Inputs changed before export")
    if fingerprint(root / "config/phase1_quality_rules.json") != bundle["config_sha256"]:
        raise ValueError("Quality policy changed before export")
    write_csv(root / DATA_PATH, bundle["rows"], bundle["fields"])
    if read_typed_csv(root / DATA_PATH, bundle["fields"]) != bundle["rows"]:
        raise AssertionError("CSV round trip changed raw strings, numeric values, flags, or missingness")
    write_csv(root / FLOW_PATH, bundle["flow"])
    write_csv(root / DENOMINATOR_PATH, bundle["denominators"])
    report_text = make_report(bundle)
    (root / REPORT_PATH).write_text(report_text, encoding="utf-8")
    if any(fingerprint(root / p) != digest for p, digest in bundle["input_sha256"].items()):
        raise AssertionError("Protected input changed during export")
    manifest = {
        "schema_version": 1, "status": "complete", "decision_date": "2026-10-31",
        "scope": "Derived intermediate table of every shared participant; row inclusion in a particular analysis requires its explicit flag.",
        "dataset": DATA_PATH, "rows": len(bundle["rows"]), "columns": len(bundle["fields"]),
        "encoding": "UTF-8", "csv_null": "Empty cell in nullable fields only; raw strings and empty exclusion reasons remain strings.",
        "csv_boolean": "1=true, 0=false; blank nullable IQR flag means not evaluated, not false.",
        "numeric_precision": "Python round-trip float representation; no analytical rounding or clipping.",
        "input_sha256": bundle["input_sha256"], "config_sha256": bundle["config_sha256"],
        "code_sha256": {p: fingerprint(root / p) for p in ("src/phase1_quality.py", "src/phase1_dataset.py")},
        "output_sha256": {p: fingerprint(root / p) for p in (DATA_PATH, FLOW_PATH, DENOMINATOR_PATH, REPORT_PATH)},
        "join": bundle["join"], "samples": bundle["samples"], "fields": bundle["fields"],
        "no_global_subject_deletion": True, "no_raw_data_changes": True,
        "sensitivity_scope": "Integer-score inclusion scenario and counts only; no statistical effect comparison has been performed.",
    }
    path = root / MANIFEST_PATH
    # Written last: readers verify all output hashes before using the table.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".manifest-", suffix=".tmp", delete=False) as handle:
        temp = Path(handle.name)
        json.dump(manifest, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    os.replace(temp, path)
    return manifest


def load_dataset(root: Path, verify_sources: bool = True) -> tuple[list[dict], dict]:
    root = root.resolve()
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    if manifest["status"] != "complete":
        raise ValueError("The exported bundle is incomplete")
    for name, digest in manifest["output_sha256"].items():
        if fingerprint(root / name) != digest:
            raise ValueError(f"Derived artifact changed: {name}")
    if verify_sources:
        for name, digest in {**manifest["input_sha256"], **manifest["code_sha256"],
                             "config/phase1_quality_rules.json": manifest["config_sha256"]}.items():
            if fingerprint(root / name) != digest:
                raise ValueError(f"Source, code, or policy changed; rebuild required: {name}")
    rows = read_typed_csv(root / manifest["dataset"], manifest["fields"])
    if len(rows) != manifest["rows"] or len({r["NACCID"] for r in rows}) != len(rows):
        raise ValueError("Exported row count or identifier uniqueness is inconsistent")
    for sample, spec in manifest["samples"].items():
        included = [r for r in rows if r[spec["flag"]]]
        if len(included) != spec["included"] or _ids_digest(included) != spec["sorted_identifier_sha256"]:
            raise ValueError(f"Sample membership changed: {sample}")
        for row in rows:
            if bool(row[spec["flag"]]) != (row[spec["reasons_field"]] == ""):
                raise ValueError(f"Eligibility and saved reasons disagree: {sample}")
    return rows, manifest


def make_report(bundle: dict) -> str:
    j = bundle["join"]
    lines = ["# اتصال و جریان نمونه — فاز یک", "",
             "تمام شمارها از دادهٔ خام و قواعد مصوب بازتولید شده‌اند؛ فایل‌های خام تغییر نکرده‌اند. جدول مرجع همهٔ افراد مشترک را نگه می‌دارد و انتخاب هر خروجی با پرچم همان خروجی است.", "",
             "## اتصال دو وجه", "", "| مورد | تعداد |", "|---|---:|",
             f"| ردیف UDS | {j['uds_rows']} |", f"| ردیف MRI | {j['mri_rows']} |",
             f"| افراد یکتای مشترک و جدول مرجع | {j['shared_unique_ids']} |",
             f"| شناسهٔ فقط UDS | {len(j['uds_only_ids'])} |", f"| شناسهٔ فقط MRI | {len(j['mri_only_ids'])} |", "",
             "اتصال یک‌به‌یک با NACCID است، نه موقعیت ردیف. NACCUDSD فردبه‌فرد به‌صورت عددی تطبیق داده شده و نسخهٔ UDS مرجع گروه‌بندی است؛ دو رشتهٔ خام برای ردگیری باقی‌اند. ماتریس نواحی به ردیف‌های افراد اضافه نشده است.", "",
             "## مجموعه‌های قابل استفاده", "", "| مجموعه | پرچم | داخل | خارج از این خروجی |", "|---|---|---:|---:|"]
    for name, sample in bundle["samples"].items():
        lines.append(f"| {name} | `{sample['flag']}` | {sample['included']} | {sample['not_included']} |")
    lines += ["", "مجموعه‌ها تو‌در‌تو و هم‌پوشان‌اند؛ شمار آن‌ها با هم جمع نمی‌شود. خارج‌بودن از یک خروجی، حذف از جدول مرجع یا تمام توصیف‌ها نیست. سناریوی حساسیت تعریف، شمار و خلاصهٔ توصیفی دارد؛ اثر یا مدل در آن هنوز مقایسه نشده است.", "",
              "## جریان مرحله‌ای هر شاخه", "",
              "هر شاخه از جمعیت والد نوشته‌شده آغاز می‌شود. تعداد کنارگذاشته‌شده بر اساس افراد باقی‌مانده در همان مرحله است؛ فرد چندمسئله‌ای دوباره در جمع حذف‌ها شمرده نمی‌شود.", "",
              "| شاخه | والد | گام | شرط | پیش از شرط | کنارگذاشته | باقی‌مانده |", "|---|---|---:|---|---:|---:|---:|"]
    for r in bundle["flow"]:
        lines.append(f"| {r['scenario']} | {r['parent_sample']} | {r['step']} | {r['description']} | {r['n_before']} | {r['n_removed']} | {r['n_after']} |")
    lines += ["", "## مخرج هر متغیر و خروجی", "",
              "مخرجِ درصد ناموجودی، جمعیت همان ردیف جدول است. صفر ناموجودی در یک نمونهٔ کامل انتخاب‌شده، دلیل صفر بودن گمشدگی در ورودی یا پیش از جایگذاری نیست.", "",
              "| مجموعه | متغیر کاری | جمعیت | قابل استفاده | غیرقابل استفاده | درصد غیرقابل استفاده |", "|---|---|---:|---:|---:|---:|"]
    for r in bundle["denominators"]:
        percent = "—" if r["percent_unusable"] is None else f"{r['percent_unusable']:.3f}"
        lines.append(f"| {r['sample']} | `{r['variable']}` | {r['n_population']} | {r['n_usable']} | {r['n_unusable']} | {percent} |")
    lines += ["", "## علت‌های عدم عضویت", "",
              "این جدول علت‌ها را بر اساس همهٔ افراد جدول مرجع می‌شمارد. یک فرد می‌تواند چند علت داشته باشد؛ جمع علت‌ها لزوماً تعداد افراد خارج از خروجی نیست. جدول جریان بالا، شمار بدون دوباره‌شماری را می‌دهد.", "",
              "| مجموعه | علت | تعداد افراد با این علت |", "|---|---|---:|"]
    for name, sample in bundle["samples"].items():
        for reason, count in sorted(sample["nonexclusive_reason_counts"].items()):
            lines.append(f"| {name} | `{reason}` | {count} |")
    lines += ["", "## قرارداد ذخیره و بازخوانی", "",
              "- [جدول مرجع افراد](../../data/processed/phase1_participants.csv): مقدار خام منتخب، مقدار کاری، علت، پرچم عضویت، پرچم IQR و شمارهٔ خط هر منبع.",
              "- [شناسنامهٔ قابل بررسی](../../data/processed/phase1_manifest.json): نوع تمام ستون‌ها، واحد، قرارداد ناموجودی، اثر انگشت ورودی/کد/قواعد/خروجی و شمار و اثر انگشت شناسه‌های هر مجموعه.",
              "- [جریان CSV](sample_flow.csv) و [مخرج‌ها CSV](denominators.csv): جدول‌های میانی بازتولیدپذیر برای گزارش و نوت‌بوک.",
              "- پرچم‌ها در CSV با ۱ و ۰ ذخیره می‌شوند. خانهٔ خالی در متغیر کاریِ nullable یعنی ناموجود؛ پرچم IQR خالی یعنی ارزیابی نشده، نه False. علتِ خالی یعنی برای آن خروجی علت عدم عضویت وجود ندارد.",
              "- رشته‌های خام بدون اصلاح حفظ شده‌اند. اعداد کاری با نمایش قابل بازخوانیِ بدون گردکردن ذخیره شده‌اند؛ خوانندهٔ پروژه انواع را از شناسنامه بازمی‌گرداند.",
              "- بازخوانی و مقایسهٔ تمام ردیف‌ها با دادهٔ حافظه انجام شده است؛ صفر، مقدار ناموجود و False از هم جدا می‌مانند.",
              "- اصلِ نامعلوم‌بودن جایگذاری، مراجعه و QC باقی است؛ ذخیرهٔ داده این اطلاعات را ایجاد نمی‌کند.",
              "- گروه فاقد MRI در فایل تحویلی وجود ندارد؛ بنابراین مقایسهٔ انتخاب چندوجهی با افراد فاقد MRI قابل انجام نیست.",
              "- میانگین کدهای گروه یا جنس، مدل، ضریب همبستگی و آزمون در این مرحله محاسبه نشده‌اند؛ نمودارهای توصیفی در گزارش شکل‌ها موجودند.", "",
              "## پیوندها", "",
              "[قواعد کیفیت](../../docs/QUALITY_RULES.md) · [راهنمای داده](../../data/README.md) · [نوت‌بوک](../../notebooks/phase1.ipynb) · [ممیزی](quality_audit.md)"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    bundle = build_dataset(args.root)
    manifest = export_dataset(args.root, bundle)
    rows, _ = load_dataset(args.root)
    print(json.dumps({"rows": len(rows), "columns": manifest["columns"],
                      "samples": {name: value["included"] for name, value in manifest["samples"].items()},
                      "round_trip_verified": True, "raw_inputs_unchanged": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
