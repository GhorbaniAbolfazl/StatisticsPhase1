"""Reproducible, non-destructive phase-one audit; Python standard library only.

The reference dictionary describes original NACC fields. The supplied teaching
subset has undocumented preprocessing. A reference mismatch is a review flag,
not evidence of its cause. No raw input is ever opened for writing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


INPUT_FILES = {
    "UDS": "data/udslong_imputed.csv",
    "MRI": "data/mriscanclean.csv",
    "ADJACENCY": "data/combined_adjacency_matrix.csv",
}
SELECTED = {
    "UDS": ["NACCID", "MOCATOTS", "NACCAGE", "SEX", "EDUC", "NACCUDSD"],
    "MRI": ["NACCID", "NACCUDSD", "LH_ENTORHINAL_AVGTH", "RH_ENTORHINAL_AVGTH"],
}
MISSING_TEXT = {"na", "nan", "null", "none", "n/a"}
STATUS_LABELS = {
    "reference_compatible": "سازگار با دامنهٔ مرجع",
    "known_special": "کد ویژه/مختلط مرجع",
    "ambiguous_special": "کد با ابهام مستندات",
    "off_grid_in_range": "اعشار خارج از گام مرجع ولی در بازه",
    "outside_reference_range": "خارج از بازهٔ مرجع",
    "unlisted_code": "خارج از مجموعهٔ کدهای مرجع",
    "excluded_reference_value": "مقدار مستثناشده در مرجع",
    "nonpositive_measurement": "اندازه‌گیری غیرمثبت",
    "blank": "خانهٔ خالی",
    "text_missing": "نشانگر متنی گمشدگی",
    "unparseable": "غیرقابل تبدیل به عدد",
    "nonfinite": "عدد نامتناهی یا NaN",
    "identifier_format": "قالب شناسه ناسازگار",
}


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if len(set(header)) != len(header):
            raise ValueError(f"Duplicate headers: {path.name}")
        rows = []
        for line, row in enumerate(reader, 2):
            if len(row) != len(header):
                raise ValueError(f"Wrong width at {path.name}:{line}")
            rows.append(dict(zip(header, row)))
    return header, rows


def classify(raw: str, rule: dict) -> tuple[str, float | None, str | None]:
    """Classify the stored value; do not coerce an invalid code to a valid code."""
    stripped = raw.strip()
    if not stripped:
        return "blank", None, None
    if stripped.lower() in MISSING_TEXT:
        return "text_missing", None, None
    if rule["kind"] == "identifier":
        return (
            ("reference_compatible", None, None)
            if re.fullmatch(rule["pattern"], raw)
            else ("identifier_format", None, None)
        )
    try:
        value = Decimal(stripped)
    except InvalidOperation:
        return "unparseable", None, None
    if not value.is_finite():
        return "nonfinite", None, None
    numeric = float(value)
    if not math.isfinite(numeric):
        return "nonfinite", None, None
    for code, reason in rule.get("special", {}).items():
        if value == Decimal(code):
            return "known_special", numeric, reason
    for code, reason in rule.get("ambiguous_special", {}).items():
        if value == Decimal(code):
            return "ambiguous_special", numeric, reason
    if rule["kind"] == "positive":
        if value <= 0:
            return "nonpositive_measurement", numeric, None
        return "reference_compatible", numeric, "numeric_usability_only"
    if rule["kind"] == "set":
        allowed = {Decimal(str(v)) for v in rule["values"]}
        return (
            ("reference_compatible", numeric, None)
            if value in allowed
            else ("unlisted_code", numeric, None)
        )
    if rule["kind"] != "range":
        raise ValueError(f"Unsupported rule kind: {rule['kind']}")
    lo, hi = Decimal(str(rule["minimum"])), Decimal(str(rule["maximum"]))
    if not lo <= value <= hi:
        return "outside_reference_range", numeric, None
    if value in {Decimal(str(v)) for v in rule.get("excluded_values", [])}:
        return "excluded_reference_value", numeric, None
    if rule.get("step") is not None:
        if (value - lo) % Decimal(str(rule["step"])) != 0:
            return "off_grid_in_range", numeric, None
    return "reference_compatible", numeric, None


def audit_table(label: str, header: list[str], rows: list[dict], rules: dict) -> dict:
    if set(header) != set(rules):
        raise ValueError(f"Incomplete rules for {label}: {set(header) ^ set(rules)}")
    profiles, events, statuses = [], [], {}
    for column in header:
        counts, kinds, exceptions = Counter(), Counter(), Counter()
        states, values = [], []
        for index, row in enumerate(rows):
            status, value, detail = classify(row[column], rules[column])
            counts[status] += 1
            states.append(status)
            if value is not None:
                values.append(value)
            if status != "reference_compatible":
                exceptions[(status, row[column], detail)] += 1
                if detail:
                    kinds[detail] += 1
                events.append({
                    "file": label, "csv_line": index + 2,
                    "NACCID": row.get("NACCID"), "column": column,
                    "raw": row[column], "status": status, "detail": detail,
                })
        if sum(counts.values()) != len(rows):
            raise AssertionError("The mutually exclusive status counts must partition rows")
        statuses[column] = states
        profiles.append({
            "column": column, "n": len(rows), "counts": dict(counts),
            "status_percent": {key: 100 * n / len(rows) for key, n in counts.items()} if rows else {},
            "special_kinds": dict(kinds), "distinct_stored_values": len({r[column] for r in rows}),
            "numeric_minimum_raw": min(values) if values else None,
            "numeric_maximum_raw": max(values) if values else None,
            "exception_values": [
                {"status": status, "raw": raw, "detail": detail, "n": n}
                for (status, raw, detail), n in sorted(exceptions.items(), key=lambda item: (-item[1], str(item[0])))
            ],
            "source": rules[column].get("source"),
        })
    return {"profiles": profiles, "events": events, "statuses": statuses}


def structural_check(label: str, header: list[str], rows: list[dict]) -> dict:
    ids = [row["NACCID"] for row in rows]
    duplicates = {key: n for key, n in Counter(ids).items() if n > 1}
    # Equal observed records do not prove that two identifiers are one person.
    no_id = [tuple(row[c] for c in header if c != "NACCID") for row in rows]
    return {
        "file": label, "rows": len(rows), "columns": len(header),
        "unique_ids": len(set(ids)), "duplicate_ids": duplicates,
        "duplicate_complete_rows": len(rows) - len({tuple(row[c] for c in header) for row in rows}),
        "equal_rows_excluding_identifier": len(rows) - len(set(no_id)),
        "empty_cells": sum(not v.strip() for row in rows for v in row.values()),
    }


def logical_checks(rows: list[dict], rules: dict) -> list[dict]:
    checks = []

    def check(name, columns, predicate, eligibility=None, source=None):
        evaluated, skipped, issues = 0, 0, []
        for line, row in enumerate(rows, 2):
            values = {}
            good = True
            for col in columns:
                status, value, detail = classify(row[col], rules[col])
                if status != "reference_compatible":
                    good = False
                    break
                values[col] = value
            if not good or (eligibility and not eligibility(values)):
                skipped += 1
                continue
            evaluated += 1
            if not predicate(values):
                issues.append({"NACCID": row["NACCID"], "csv_line": line, "values": values})
        checks.append({
            "name": name, "columns": columns, "evaluated": evaluated,
            "not_evaluated": skipped, "flagged": len(issues), "issues": issues,
            "source": source, "action": "Review only; do not overwrite or delete a person.",
        })

    cdr = ["MEMORY", "ORIENT", "JUDGMENT", "COMMUN", "HOMEHOBB", "PERSCARE"]
    check("CDRSUM_equals_six_boxes", cdr + ["CDRSUM"],
          lambda v: math.isclose(sum(v[c] for c in cdr), v["CDRSUM"], abs_tol=1e-9),
          source=rules["CDRSUM"]["source"])
    gds = "SATIS DROPACT EMPTY BORED SPIRITS AFRAID HAPPY HELPLESS STAYHOME MEMPROB WONDRFUL WRTHLESS ENERGY HOPELESS BETTER".split()
    check("GDS_complete_items_sum", ["NOGDS", "NACCGDS"] + gds,
          lambda v: math.isclose(sum(v[c] for c in gds), v["NACCGDS"], abs_tol=1e-9),
          lambda v: v["NOGDS"] == 0,
          source=rules["NACCGDS"]["source"])
    check("systolic_exceeds_diastolic", ["BPSYS", "BPDIAS"],
          lambda v: v["BPSYS"] > v["BPDIAS"], source=rules["BPSYS"]["source"])
    check("smoking_years_not_above_age", ["SMOKYRS", "NACCAGE"],
          lambda v: v["SMOKYRS"] <= v["NACCAGE"], source=rules["SMOKYRS"]["source"])
    check("quit_age_not_above_current_age", ["QUITSMOK", "NACCAGE"],
          lambda v: v["QUITSMOK"] <= v["NACCAGE"], source=rules["QUITSMOK"]["source"])
    check("medications_flag_matches_nonzero_count", ["ANYMEDS", "NACCAMD"],
          lambda v: (v["ANYMEDS"] == 1) == (v["NACCAMD"] > 0), source=rules["NACCAMD"]["source"])
    # NORMEXAM=2 combines age-related and other irrelevant abnormalities.
    # The public wording does not provide an unambiguous mapping for that code.
    check("neurological_summary_unambiguous_codes", ["NACCNREX", "NORMEXAM"],
          lambda v: v["NACCNREX"] == {0: 1, 1: 0}[v["NORMEXAM"]],
          lambda v: v["NORMEXAM"] in {0, 1},
          source=rules["NACCNREX"]["source"])

    # Severity=8 is a documented structural skip, not an unknown code.
    for symptom in "DEL HALL AGIT DEPD ANX ELAT APA DISN IRR MOT NITE APP".split():
        severity = symptom + "SEV"
        evaluated, skipped, issues = 0, 0, []
        for line, row in enumerate(rows, 2):
            s, sv, _ = classify(row[symptom], rules[symptom])
            t, tv, detail = classify(row[severity], rules[severity])
            eligible = s == "reference_compatible" and (
                t == "reference_compatible" or (t == "known_special" and detail == "not_applicable")
            )
            if not eligible:
                skipped += 1
                continue
            evaluated += 1
            if (sv == 0 and tv != 8) or (sv == 1 and tv == 8):
                issues.append({"NACCID": row["NACCID"], "csv_line": line,
                               "values": {symptom: sv, severity: tv}})
        checks.append({"name": f"{symptom}_severity_skip", "columns": [symptom, severity],
                       "evaluated": evaluated, "not_evaluated": skipped,
                       "flagged": len(issues), "issues": issues, "source": rules[severity]["source"],
                       "action": "Review only; do not overwrite or delete a person."})
    return checks


def iqr_review(column: str, ids: list[str], values: list[float]) -> dict:
    """Tukey flags using the inclusive/linear (type-7) sample quartiles."""
    if len(values) < 2:
        return {"column": column, "n": len(values), "status": "insufficient_values", "flagged": 0, "issues": []}
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    issues = [{"NACCID": key, "value": value} for key, value in zip(ids, values) if value < lower or value > upper]
    return {"column": column, "n": len(values), "status": "flags_only",
            "quartile_method": "inclusive_linear_type7", "q1": q1, "q3": q3,
            "iqr": iqr, "lower_fence": lower, "upper_fence": upper,
            "flagged": len(issues), "issues": issues,
            "action": "Retain; an IQR flag is not a recording error or imaging QC failure."}


def prepare_selected(uds: list[dict], mri: list[dict], config: dict) -> list[dict]:
    """In-memory selected-field view with flags; raw strings remain untouched."""
    if config["moca_fractional_policy"] != "retain_in_range_flag_and_integer_sensitivity":
        raise ValueError("The implemented policy must match the user's documented choice")
    uids = [r["NACCID"] for r in uds]
    mids = [r["NACCID"] for r in mri]
    if len(uids) != len(set(uids)) or len(mids) != len(set(mids)):
        raise ValueError("Ambiguous matching: duplicate person identifiers")
    by_id = {r["NACCID"]: r for r in mri}
    prepared = []
    for row in uds:
        key = row["NACCID"]
        image = by_id.get(key)
        score_status, score, detail = classify(row["MOCATOTS"], config["uds"]["MOCATOTS"])
        score_usable = score_status in {"reference_compatible", "off_grid_in_range"}
        result = {"NACCID": key, "MOCATOTS_RAW": row["MOCATOTS"],
                  "MOCATOTS_ANALYSIS": score if score_usable else None,
                  "MOCA_STATUS": score_status, "MOCA_DETAIL": detail,
                  "MOCA_FRACTIONAL_IN_RANGE": score_status == "off_grid_in_range",
                  "MRI_MATCHED": image is not None}
        for col in ["NACCAGE", "SEX", "EDUC", "NACCUDSD"]:
            state, value, why = classify(row[col], config["uds"][col])
            result[col + "_ANALYSIS"] = value if state == "reference_compatible" else None
            result[col + "_STATUS"] = state
            result[col + "_DETAIL"] = why
        left_name, right_name = config["selected"]["inputs"]
        for col in [left_name, right_name]:
            if image is None:
                result[col + "_ANALYSIS"] = None
                result[col + "_STATUS"] = "MRI_not_available"
            else:
                state, value, _ = classify(image[col], {"kind": "positive"})
                result[col + "_ANALYSIS"] = value if state == "reference_compatible" else None
                result[col + "_STATUS"] = state
        left, right = result[left_name + "_ANALYSIS"], result[right_name + "_ANALYSIS"]
        mean = (left + right) / 2 if left is not None and right is not None else None
        if mean is not None and not min(left, right) <= mean <= max(left, right):
            raise AssertionError("The bilateral mean must lie between its two inputs")
        result["ENTORHINAL_THICKNESS_MEAN"] = mean
        pair = score_usable and mean is not None
        common = pair and all(result[c + "_ANALYSIS"] is not None for c in config["selected"]["covariates"])
        result["MAIN_PAIR_ELIGIBLE"] = pair
        result["MAIN_COMMON_SAMPLE_ELIGIBLE"] = common
        result["INTEGER_SENSITIVITY_PAIR_ELIGIBLE"] = pair and score_status == "reference_compatible"
        result["INTEGER_SENSITIVITY_COMMON_ELIGIBLE"] = common and score_status == "reference_compatible"
        prepared.append(result)
    return prepared


def audit(root: Path) -> tuple[dict, list[dict], list[dict]]:
    root = root.resolve()
    config_path = root / "config/phase1_quality_rules.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    protected = [root / p for p in INPUT_FILES.values()] + [root / "docs/amarpr.pdf"]
    before = {str(p.relative_to(root)): fingerprint(p) for p in protected}
    uh, uds = load_table(root / INPUT_FILES["UDS"])
    mh, mri = load_table(root / INPUT_FILES["MRI"])
    if "NACCID" not in uh or "NACCID" not in mh:
        raise ValueError("Missing person identifier")
    ustructure, mstructure = structural_check("UDS", uh, uds), structural_check("MRI", mh, mri)
    if ustructure["duplicate_ids"] or mstructure["duplicate_ids"]:
        raise ValueError("Duplicate person identifiers require a documented decision")
    ua = audit_table("UDS", uh, uds, config["uds"])
    for label, rows, rule in (("UDS", uds, config["uds"]["NACCID"]),
                               ("MRI", mri, config["mri"]["NACCID"])):
        if any(classify(row["NACCID"], rule)[0] != "reference_compatible" for row in rows):
            raise ValueError(f"Invalid person identifier in {label}; matching requires valid, nonblank identifiers")
    mri_rules = {c: (config["mri"][c] if c in {"NACCID", "NACCUDSD"}
                    else {"kind": "positive", "source": config["mri"]["measurements"]["source"]}) for c in mh}
    if any(c not in {"NACCID", "NACCUDSD"} and re.fullmatch(r"(?:LH|RH)_.+_(?:GVOL|AVGTH)", c) is None for c in mh):
        raise ValueError("Unrecognized MRI measurement column")
    ma = audit_table("MRI", mh, mri, mri_rules)
    umap, mmap = {r["NACCID"]: r for r in uds}, {r["NACCID"]: r for r in mri}
    common_ids = set(umap) & set(mmap)
    label_mismatch = sorted(key for key in common_ids if float(umap[key]["NACCUDSD"]) != float(mmap[key]["NACCUDSD"]))
    if label_mismatch:
        raise ValueError("Conflicting cognitive-status labels require a documented decision")
    ah, ar = load_table(root / INPUT_FILES["ADJACENCY"])
    labels, row_labels = ah[1:], [row[ah[0]] for row in ar]
    if len(labels) != len(ar) or row_labels != labels:
        raise ValueError("Adjacency row/column labels must align")
    matrix = [[float(row[col]) for col in labels] for row in ar]
    canonical = lambda name: name.split("_", 1)[0] + "_" + name.split("_", 1)[1].replace("_", "").lower()
    expected = {("left_" if c.startswith("LH_") else "right_") + c[3:-5].lower() for c in mh if c.endswith("_GVOL")}
    if len(labels) != len(set(labels)) or {canonical(c) for c in labels} != expected:
        raise ValueError("Adjacency nodes must map one-to-one onto MRI regions")
    adj = {"rows": len(ar), "numeric_columns": len(labels),
           "all_binary": all(v in {0, 1} for row in matrix for v in row),
           "all_finite": all(math.isfinite(v) for row in matrix for v in row),
           "asymmetric_pairs": sum(matrix[i][j] != matrix[j][i] for i in range(len(labels)) for j in range(i)),
           "diagonal_ones": sum(matrix[i][i] == 1 for i in range(len(labels))),
           "nodes_mapped": len(expected), "use": "Structural description and node mapping only"}
    if not adj["all_binary"] or not adj["all_finite"] or adj["asymmetric_pairs"]:
        raise ValueError("Unexpected adjacency numeric structure")
    prepared = prepare_selected(uds, mri, config)
    eligibility = {"input_uds": len(uds), "input_mri": len(mri), "shared_ids": len(common_ids),
                   "only_uds": len(set(umap) - set(mmap)), "only_mri": len(set(mmap) - set(umap)),
                   "label_mismatches": len(label_mismatch),
                   "moca_usable_main": sum(r["MOCATOTS_ANALYSIS"] is not None for r in prepared),
                   "moca_fractional_retained": sum(r["MOCA_FRACTIONAL_IN_RANGE"] for r in prepared),
                   "bilateral_thickness_usable": sum(r["ENTORHINAL_THICKNESS_MEAN"] is not None for r in prepared),
                   "main_pair": sum(r["MAIN_PAIR_ELIGIBLE"] for r in prepared),
                   "main_common": sum(r["MAIN_COMMON_SAMPLE_ELIGIBLE"] for r in prepared),
                   "integer_sensitivity_pair": sum(r["INTEGER_SENSITIVITY_PAIR_ELIGIBLE"] for r in prepared),
                   "integer_sensitivity_common": sum(r["INTEGER_SENSITIVITY_COMMON_ELIGIBLE"] for r in prepared)}
    overlap_flags = {
        "moca_special": {r["NACCID"] for r in prepared if r["MOCA_STATUS"] == "known_special"},
        "moca_outside_range": {r["NACCID"] for r in prepared if r["MOCA_STATUS"] == "outside_reference_range"},
        "moca_fractional_retained": {r["NACCID"] for r in prepared if r["MOCA_FRACTIONAL_IN_RANGE"]},
        "education_unavailable": {r["NACCID"] for r in prepared if r["EDUC_ANALYSIS"] is None},
        "nonpositive_mri_measurement": {e["NACCID"] for e in ma["events"] if e["status"] == "nonpositive_measurement"},
    }
    overlaps = [{"a": a, "b": b, "n": len(overlap_flags[a] & overlap_flags[b])}
                for i, a in enumerate(overlap_flags) for b in list(overlap_flags)[i+1:]]
    outliers = []
    for column in ["MOCATOTS_ANALYSIS", "NACCAGE_ANALYSIS", "EDUC_ANALYSIS", "ENTORHINAL_THICKNESS_MEAN"]:
        pairs = [(r["NACCID"], r[column]) for r in prepared if r[column] is not None]
        outliers.append(iqr_review(column, [p[0] for p in pairs], [p[1] for p in pairs]))
    for col in mh:
        if col in {"NACCID", "NACCUDSD"}:
            continue
        pairs = [(r["NACCID"], float(r[col])) for i, r in enumerate(mri)
                 if ma["statuses"][col][i] == "reference_compatible"]
        outliers.append(iqr_review(col, [p[0] for p in pairs], [p[1] for p in pairs]))
    after = {str(p.relative_to(root)): fingerprint(p) for p in protected}
    if before != after:
        raise AssertionError("Protected input files changed during the audit")
    all_events = ua["events"] + ma["events"]
    report = {
        "schema_version": 1, "policy_reviewed_on": config["reviewed_on"],
        "config_sha256": fingerprint(config_path), "input_sha256": before,
        "input_files_unchanged": True,
        "scope": "Complete domain audit, logical review and in-memory selected-field preparation; no inferential analysis and no raw-data changes.",
        "structures": [ustructure, mstructure], "adjacency": adj,
        "reference_coverage": {"UDS": len(config["uds"]), "MRI": len(mri_rules)},
        "profiles": {"UDS": ua["profiles"], "MRI": ma["profiles"]},
        "event_totals": {"cells": len(all_events), "unique_person_ids": len({e["NACCID"] for e in all_events}),
                         "by_status": dict(Counter(e["status"] for e in all_events))},
        "logical_checks": logical_checks(uds, config["uds"]),
        "eligibility": eligibility, "flag_overlaps": overlaps, "outlier_reviews": outliers,
        "unknowns": ["TA extraction version", "visit selection and alignment", "original missingness", "imputation method and flags", "participant-specific imaging QC"],
        "ambiguities": ["NACCBMI reference table uses 888.8 while its derivation uses 888; classify the latter as explicitly ambiguous, not a substantive BMI."],
    }
    return report, prepared, all_events


def write_reports(root: Path, report: dict, events: list[dict]) -> list[Path]:
    """Write audit artifacts only; never export or overwrite a raw/clean dataset."""
    folder = root / "reports/phase1"
    folder.mkdir(parents=True, exist_ok=True)
    summary, issues, markdown = [folder / name for name in ("quality_audit.json", "quality_issues.json", "quality_audit.md")]
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    issues.write_text(json.dumps({"input_sha256": report["input_sha256"], "events": events}, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
    lines = [
        "# گزارش ممیزی کیفیت — فاز یک", "",
        "این گزارش با کد ممیزی از فایل‌های اولیه ساخته شده است. سازگاری با مرجع، QC بالینی یا اصالت نمره را اثبات نمی‌کند. دادهٔ خام تغییر نکرده است.", "",
        "قواعد: [QUALITY_RULES.md](../../docs/QUALITY_RULES.md). نوت‌بوک: [phase1.ipynb](../../notebooks/phase1.ipynb).", "",
        "## ساختار و پوشش", "",
        "| فایل | ردیف | ستون | شناسهٔ یکتا | شناسهٔ تکراری | خانهٔ خالی |", "|---|---:|---:|---:|---:|---:|",
    ]
    for s in report["structures"]:
        lines.append(f"| {s['file']} | {s['rows']} | {s['columns']} | {s['unique_ids']} | {len(s['duplicate_ids'])} | {s['empty_cells']} |")
    lines += ["", "هر ۱۸۰ ستون UDS و هر ۱۲۶ ستون MRI قاعدهٔ صریح دارد. برای MRI، سازگاری عددی فقط متناهی و مثبت بودن را نشان می‌دهد؛ حد بالای بالینی دلخواه اعمال نشده است.", "",
              "## قابلیت استفادهٔ متغیرهای اصلی", "", "| مجموعهٔ خروجی | تعداد |", "|---|---:|"]
    explanations = {"moca_usable_main": "MoCA قابل استفاده در تحلیل اصلی", "moca_fractional_retained": "اعشار درون دامنهٔ نگهداری‌شده با پرچم", "bilateral_thickness_usable": "میانگین ضخامت قابل محاسبه با هر دو طرف", "main_pair": "زوج MoCA و ضخامت برای تحلیل اصلی", "main_common": "نمونهٔ مشترک با سن، جنس و تحصیلات قابل استفاده", "integer_sensitivity_pair": "زوج‌ها در سناریوی حساسیت فقط صحیح‌ها", "integer_sensitivity_common": "نمونهٔ مشترک در سناریوی حساسیت فقط صحیح‌ها"}
    for key, label in explanations.items():
        lines.append(f"| {label} | {report['eligibility'][key]} |")
    lines += ["", "این‌ها مجموعه‌های متداخل برای خروجی‌های متفاوت‌اند و نباید با هم جمع شوند. این ممیزی خودش دادهٔ تحلیلی نهایی صادر نمی‌کند؛ اتصال ذخیره‌شده و مخرج خروجی‌ها در [گزارش جریان نمونه](sample_flow.md) مستند می‌شوند. فرد از تمام خلاصه‌ها حذف نمی‌شود.", "",
              "## کنترل‌های منطقی", "", "فقط ردیف دارای ورودی قابل ارزیابی بررسی شده است. ردیف ارزیابی‌نشده به معنی قبولی نیست. پرچم‌ها موجب بازنویسی، جمع‌زدن دوبارهٔ نمره یا حذف فرد نشده‌اند.", "",
              "| کنترل | ارزیابی‌شده | ارزیابی‌نشده | پرچم بازبینی |", "|---|---:|---:|---:|"]
    for c in report["logical_checks"]:
        lines.append(f"| `{c['name']}` | {c['evaluated']} | {c['not_evaluated']} | {c['flagged']} |")
    lines += ["", "تعریف و منبع هر کنترل، مقادیر ردیف‌های پرچم‌خورده و شرایط ارزیابی در JSON و کد ثبت است. وضعیت شناختی با CDRGLOB معادل فرض نشده و BMI از قد/وزن گرد‌شده برای اصلاح خودکار بازسازی نشده است.", "",
              "## مرور نقاط دورافتاده", "", "چارک‌ها با روش inclusive/linear (type 7) و حصار ۱٫۵ IQR، فقط روی مقادیر قابل استفادهٔ همان متغیر محاسبه شده‌اند. خارج حصار بودن خطای ثبت یا مجوز حذف نیست. تمام این مقدارها نگهداری شده‌اند.", "",
              "| متغیر | تعداد بررسی‌شده | تعداد خارج حصار |", "|---|---:|---:|"]
    for c in report["outlier_reviews"]:
        lines.append(f"| `{c['column']}` | {c['n']} | {c['flagged']} |")
    lines += ["", "## ممیزی ستون به ستون", "", "دسته‌های وضعیت در هر ردیف این جدول انحصاری‌اند و جمعشان برابر تعداد ورودی است. کد ویژه می‌تواند نامرتبط، پاسخ‌نداده، نامعلوم، فرم جایگزین یا دستهٔ مختلط باشد؛ همهٔ آن‌ها یک نوع گمشدگی نیستند."]
    for label in ("UDS", "MRI"):
        lines += ["", f"### {label}", "", "| ستون | سازگار با قاعده | کد ویژه/مختلط | ابهام مستندات | ناسازگاری/گمشدگی دیگر | منبع |", "|---|---:|---:|---:|---:|---|"]
        for p in report["profiles"][label]:
            c = p["counts"]
            compatible, special, ambiguous = [c.get(key, 0) for key in ("reference_compatible", "known_special", "ambiguous_special")]
            other = p["n"] - compatible - special - ambiguous
            lines.append(f"| `{p['column']}` | {compatible} | {special} | {ambiguous} | {other} | [مرجع]({p['source']}) |")
    lines += ["", "## ردگیری و محدودیت‌ها", "",
              "- [quality_audit.json](quality_audit.json): شمار و درصد وضعیت‌ها با مخرج هر ستون، فراوانی مقادیر مسئله‌دار، نتایج منطقی، حصارها و هم‌پوشانی پرچم‌ها.",
              "- [quality_issues.json](quality_issues.json): هر مقدار نیازمند توجه همراه نام فایل، شمارهٔ خط CSV (از ۲ برای اولین فرد)، شناسه، ستون، مقدار خام و علت؛ کدهای ویژه نیز برای ردگیری ثبت‌اند و الزاماً خطا نیستند.",
              "- گمشدگی پیش از جایگذاری، روش آماده‌سازی، تاریخ مراجعه/اسکن و QC اختصاصی همچنان معلوم نیستند؛ گزارش آن‌ها صفر اعلام نمی‌کند.",
              "- ناسازگاری جدول و توضیح کد NACCBMI در مرجع ثبت شده است؛ این متغیر وارد سؤال اصلی نشده و داده‌اش اصلاح نشده است.",
              "- درصد تجمیعی تمام سلول‌های ویژه، جای درصد فرد یا درصد گمشدگی هر متغیر نیست. یک فرد ممکن است چند پرچم داشته باشد.",
              "- نمودارها، آزمون‌ها و مدل‌های فازهای بعد هنوز در این مرحله تولید نشده‌اند.", "",
              "## اثر انگشت ورودی‌ها", "", "| فایل | SHA-256 |", "|---|---|"]
    for name, digest in report["input_sha256"].items():
        lines.append(f"| `{name}` | `{digest}` |")
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [summary, issues, markdown]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-reports", action="store_true", help="Write audit reports only; raw files remain unchanged")
    args = parser.parse_args()
    report, prepared, events = audit(args.root)
    if args.write_reports:
        write_reports(args.root, report, events)
    print(json.dumps({"eligibility": report["eligibility"], "event_totals": report["event_totals"],
                      "logical_checks": [{k: c[k] for k in ("name", "evaluated", "not_evaluated", "flagged")} for c in report["logical_checks"]],
                      "inputs_unchanged": report["input_files_unchanged"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
