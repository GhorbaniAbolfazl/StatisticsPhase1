"""Descriptive tables for the approved phase-one variables; standard library only.

Reads the verified participant export. No hypothesis tests, association measures,
models, clinical recoding, or changes to raw/participant files are performed.
Run from the project root: python3 -m src.phase1_descriptive
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path

from .phase1_dataset import DATA_PATH, MANIFEST_PATH, SAMPLE_FLAGS, load_dataset, write_csv
from .phase1_quality import fingerprint

NUMERIC = {
    "MOCATOTS_ANALYSIS": ("MoCA کاری", "score"),
    "NACCAGE_ANALYSIS": ("سن ثبت‌شده", "years"),
    "EDUC_ANALYSIS": ("سال‌های تحصیل", "years"),
    "LH_ENTORHINAL_AVGTH_ANALYSIS": ("ضخامت انتورینال چپ", "mm"),
    "RH_ENTORHINAL_AVGTH_ANALYSIS": ("ضخامت انتورینال راست", "mm"),
    "ENTORHINAL_THICKNESS_MEAN": ("میانگین ضخامت دو طرف", "mm"),
}
CATEGORIES = {
    "SEX_ANALYSIS": {1: "مرد", 2: "زن"},
    "NACCUDSD_ANALYSIS": {1: "طبیعی", 2: "اختلال بدون احراز MCI", 3: "MCI", 4: "دمانس"},
}
SAMPLE_LABELS = {
    "all_shared": "تمام افراد مشترک؛ استفاده از مقادیر کاری موجود هر متغیر",
    "main_pair": "زوج اصلی MoCA و MRI",
    "main_common": "نمونهٔ اصلی با هر سه متغیر همراه",
    "integer_pair": "زوج حساسیت فقط صحیح‌مقدار",
    "integer_common": "نمونهٔ مشترک حساسیت فقط صحیح‌مقدار",
}
OUT = "reports/phase1"
OUTPUTS = {
    "numeric": f"{OUT}/descriptive_numeric.csv",
    "categorical": f"{OUT}/descriptive_categorical.csv",
    "discrete": f"{OUT}/descriptive_discrete_frequencies.csv",
    "report": f"{OUT}/descriptive_statistics.md",
    "json": f"{OUT}/descriptive_statistics.json",
}


def percent(n: int, denominator: int) -> float | None:
    return 100 * n / denominator if denominator else None


def quantile(values: list[float], probability: float) -> float | None:
    """Linear/inclusive (type 7): h=(n-1)p; singleton returns its value."""
    if not 0 <= probability <= 1:
        raise ValueError("Quantile probability must be between zero and one")
    if not values:
        return None
    ordered = sorted(values)
    h = (len(ordered) - 1) * probability
    lo, hi = math.floor(h), math.ceil(h)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (h - lo)


def numeric_summary(values: list[float | None]) -> dict:
    usable = [v for v in values if v is not None]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in usable):
        raise ValueError("A quantitative summary needs finite measurements or None")
    n, total = len(usable), len(values)
    q1, med, q3 = [quantile(usable, p) for p in (.25, .5, .75)]
    return {
        "n_population": total, "n_usable": n, "n_unusable": total - n,
        "percent_unusable": percent(total - n, total), "n_distinct": len(set(usable)),
        "minimum": min(usable) if n else None, "maximum": max(usable) if n else None,
        "mean": statistics.fmean(usable) if n else None,
        "median": med, "sd_sample": statistics.stdev(usable) if n >= 2 else None,
        "q1": q1, "q3": q3, "iqr": q3 - q1 if n else None,
        "range": max(usable) - min(usable) if n else None,
    }


def categorical_frequencies(values: list[float | None], levels: dict) -> list[dict]:
    if any(v is not None and v not in levels for v in values):
        raise ValueError("Unlabelled categorical value; do not silently omit it")
    counts = Counter(values)
    n, available = len(values), len(values) - counts[None]
    rows = []
    for code, label in [*levels.items(), (None, "غیرقابل استفاده")]:
        count = counts[code]
        rows.append({
            "level_code": code, "level_label": label, "n_population": n,
            "n_available": available, "n_unusable": n - available, "count": count,
            "percent_of_population": percent(count, n),
            "percent_of_available": percent(count, available) if code is not None else None,
        })
    assert sum(r["count"] for r in rows) == n
    return rows


def _scope(sample: str, code: int | None = None) -> dict:
    return {"sample": sample, "stratum_variable": "NACCUDSD_ANALYSIS" if code is not None else "overall",
            "stratum_code": code, "stratum_label": CATEGORIES["NACCUDSD_ANALYSIS"][code] if code is not None else "همهٔ اعضای مجموعه"}


def summarize_rows(rows: list[dict]) -> dict:
    """Pure aggregation of selected, already prepared participant records."""
    populations = {"all_shared": rows}
    populations.update({sample: [r for r in rows if r[flag]] for sample, flag in SAMPLE_FLAGS.items()})
    numeric, categorical, discrete, score_details, reviews = [], [], [], [], []

    def add(population, sample, code=None):
        scope = _scope(sample, code)
        for col, (label, unit) in NUMERIC.items():
            numeric.append({**scope, "variable": col, "label": label, "unit": unit,
                            **numeric_summary([r[col] for r in population])})
        # Cognitive status is the grouping key, not a measured mean or a
        # redundant within-group frequency table of that same key.
        for col in CATEGORIES if code is None else ["SEX_ANALYSIS"]:
            categorical.extend({**scope, "variable": col, **f} for f in
                               categorical_frequencies([r[col] for r in population], CATEGORIES[col]))

    for sample, population in populations.items():
        add(population, sample)
        scores = [r["MOCATOTS_ANALYSIS"] for r in population if r["MOCATOTS_ANALYSIS"] is not None]
        fractional = sum(r["MOCA_FRACTIONAL_IN_RANGE"] for r in population)
        score_details.append({
            "sample": sample, "n_population": len(population), "n_usable": len(scores),
            "n_unusable": len(population)-len(scores), "n_fractional": fractional,
            "percent_fractional_of_usable": percent(fractional, len(scores)),
            "n_integer_valued": len(scores)-fractional,
            "n_at_zero": scores.count(0), "percent_at_zero_of_usable": percent(scores.count(0), len(scores)),
            "n_at_thirty": scores.count(30), "percent_at_thirty_of_usable": percent(scores.count(30), len(scores)),
        })

    # Chosen before examining group effects: compare MoCA and MRI on identical
    # people within each cognitive group, retaining the small code-2 group.
    for code in CATEGORIES["NACCUDSD_ANALYSIS"]:
        add([r for r in populations["main_pair"] if r["NACCUDSD_ANALYSIS"] == code], "main_pair", code)

    # Exact recorded values for discrete/rounded UDS variables; decimals are not
    # rounded into integer score bins. Missingness is an explicit separate row.
    for col in ("MOCATOTS_ANALYSIS", "NACCAGE_ANALYSIS", "EDUC_ANALYSIS"):
        counts = Counter(r[col] for r in rows)
        available = len(rows)-counts[None]
        cumulative = 0
        for value in [*sorted(v for v in counts if v is not None), None]:
            count = counts[value]
            if value is not None:
                cumulative += count
            discrete.append({
                "sample": "all_shared", "variable": col, "value": value,
                "value_status": "usable" if value is not None else "unusable",
                "integer_valued": float(value).is_integer() if value is not None else None,
                "n_population": len(rows), "n_available": available, "count": count,
                "percent_of_population": percent(count, len(rows)),
                "percent_of_available": percent(count, available) if value is not None else None,
                "cumulative_count_available": cumulative if value is not None else None,
                "cumulative_percent_available": percent(cumulative, available) if value is not None else None,
            })

    for col in NUMERIC:
        s = next(r for r in numeric if r["sample"] == "all_shared" and r["variable"] == col)
        lo = s["q1"]-1.5*s["iqr"] if s["n_usable"] else None
        hi = s["q3"]+1.5*s["iqr"] if s["n_usable"] else None
        values = [r[col] for r in rows if r[col] is not None]
        low = sum(v < lo for v in values)
        high = sum(v > hi for v in values)
        reviews.append({"variable": col, "n_usable": len(values), "not_evaluated": len(rows)-len(values),
                        "lower_fence": lo, "upper_fence": hi,
                        "below_fence": low, "above_fence": high, "flagged": low+high,
                        "percent_flagged_of_usable": percent(low+high, len(values))})
    return {"populations": {k: len(v) for k, v in populations.items()},
            "numeric": numeric, "categorical": categorical, "discrete": discrete,
            "score_details": score_details, "outlier_reviews": reviews}


def build_descriptive(root: Path) -> dict:
    rows, manifest = load_dataset(root)
    result = summarize_rows(rows)
    result["provenance"] = {
        "dataset": DATA_PATH, "dataset_sha256": fingerprint(root / DATA_PATH),
        "dataset_manifest": MANIFEST_PATH, "dataset_manifest_sha256": fingerprint(root / MANIFEST_PATH),
        "input_sha256": manifest["input_sha256"], "config_sha256": manifest["config_sha256"],
        "code_sha256": {"src/phase1_descriptive.py": fingerprint(root / "src/phase1_descriptive.py")},
    }
    result["methods"] = {
        "scope": "Six selected quantitative variables, SEX and cognitive-status categories; no search across all MRI measures.",
        "missing": "Available working values per variable; unusable values counted explicitly, no global deletion or new imputation.",
        "sd": "Sample standard deviation, denominator n-1; undefined for n<2.",
        "quantiles": "Linear/inclusive type 7, h=(n-1)p; singleton quantile equals its sole value.",
        "group_comparison": "Four NACCUDSD groups within main_pair; same participants for MoCA and MRI, variable-specific availability for covariates.",
        "percentages": "Both population and available-value denominators stored; unavailable category has no percent_of_available.",
        "outliers": "1.5 IQR review on all_shared usable values; strict outside-fence comparisons; no removal.",
        "precision": "Full numeric precision in JSON/CSV; display only rounded, mm to 3 and other summary measurements to 2 decimal places.",
        "weights": "Unweighted descriptions of the supplied subset; no population weights supplied.",
        "sensitivity": "Descriptive summaries of integer-score inclusion scenario only; no effect, CI, test or model comparison.",
    }
    return result


def fmt(value, digits=2):
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def table(headers, rows):
    def cell(v):
        return str(v).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(map(cell, headers)) + " |",
                      "| " + " | ".join(["---"]*len(headers)) + " |",
                      *["| " + " | ".join(map(cell, row)) + " |" for row in rows]])


def numeric_table(rows):
    return table(["متغیر / واحد", "جمعیت", "قابل استفاده", "غیرقابل استفاده (%)", "کمینه", "Q1", "میانه", "Q3", "بیشینه", "میانگین", "SD نمونه", "IQR"], [
        [f"{r['label']} / {r['unit']}", r["n_population"], r["n_usable"], f"{r['n_unusable']} ({fmt(r['percent_unusable'])})",
         *[fmt(r[k], 3 if r["unit"] == "mm" else 2) for k in ("minimum", "q1", "median", "q3", "maximum", "mean", "sd_sample", "iqr")]]
        for r in rows])


def interpret(result: dict) -> list[str]:
    def summary(col, sample="all_shared", group=None):
        return next(r for r in result["numeric"] if r["variable"] == col and r["sample"] == sample and r["stratum_code"] == group)
    moca, age, educ, thickness = [summary(c) for c in ("MOCATOTS_ANALYSIS", "NACCAGE_ANALYSIS", "EDUC_ANALYSIS", "ENTORHINAL_THICKNESS_MEAN")]
    score = result["score_details"][0]
    women = next(r for r in result["categorical"] if r["sample"] == "all_shared" and r["stratum_code"] is None and r["variable"] == "SEX_ANALYSIS" and r["level_code"] == 2)
    normal, mci, dementia = [summary("ENTORHINAL_THICKNESS_MEAN", "main_pair", g) for g in (1, 3, 4)]
    small = summary("ENTORHINAL_THICKNESS_MEAN", "main_pair", 2)
    group_moca = [summary("MOCATOTS_ANALYSIS", "main_pair", g) for g in (1, 3, 4)]
    integer = summary("MOCATOTS_ANALYSIS", "integer_pair")
    return [
        f"MoCA کاری {moca['n_usable']} مقدار قابل استفاده دارد؛ میانگین {fmt(moca['mean'])}، میانه {fmt(moca['median'])}، SD نمونه {fmt(moca['sd_sample'])} و نیمهٔ میانی بین {fmt(moca['q1'])} و {fmt(moca['q3'])} است. کمینه {fmt(moca['minimum'])} و بیشینه {fmt(moca['maximum'])} است. میانگین پایین‌تر از میانه و فاصلهٔ بیشتر کمینه از چارک اول، حضور مقادیر پایین در این خلاصه را نشان می‌دهند؛ شکل دقیق توزیع در نمودارهای همراه بررسی شده و نرمال‌بودن ادعا نمی‌شود.",
        f"در میان {score['n_usable']} MoCA قابل استفاده، {score['n_fractional']} مقدار اعشاری ({fmt(score['percent_fractional_of_usable'])}٪) نگه داشته شده است. نمرهٔ صفر {score['n_at_zero']} مورد ({fmt(score['percent_at_zero_of_usable'])}٪) و نمرهٔ ۳۰، {score['n_at_thirty']} مورد ({fmt(score['percent_at_thirty_of_usable'])}٪) دارد. این‌ها شمار در کران‌های نمره‌اند؛ برای اعلام اثر کف/سقف یا اصالت نمره کافی نیستند. جدول فراوانی اعشار را به صحیح گرد نمی‌کند.",
        f"سن ثبت‌شده میانگین {fmt(age['mean'])} سال و میانه {fmt(age['median'])} سال دارد؛ نصف میانی بین {fmt(age['q1'])} و {fmt(age['q3'])} سال است. تحصیلات با کنارگذاشتن دو کد نامعلوم در مقدار کاری، {educ['n_usable']} مقدار، میانگین {fmt(educ['mean'])} سال و میانه {fmt(educ['median'])} سال دارد. صفر سال تحصیل حفظ شده و ۹۹ وارد خلاصهٔ سال نشده است.",
        f"میانگین ضخامت دوطرفه برای {thickness['n_usable']} فرد موجود است: میانگین {fmt(thickness['mean'],3)} و میانه {fmt(thickness['median'],3)} mm، با SD نمونه {fmt(thickness['sd_sample'],3)} و IQR برابر {fmt(thickness['iqr'],3)} mm. این کمیت میانگین دو ضخامت است؛ میانگینِ SD چپ و راست جای SD خود شاخص را نمی‌گیرد و یک فرد به دو مشاهدهٔ مستقل تبدیل نشده است.",
        f"در کل زیرمجموعه، {women['count']} زن از {women['n_available']} کد جنس قابل استفاده وجود دارد ({fmt(women['percent_of_available'])}٪). کدهای جنس و وضعیت شناختی با شمار و درصد توصیف می‌شوند؛ میانگین آن‌ها تفسیر کمی ندارد. غلبهٔ گروه طبیعی در جدول وضعیت شناختی، ویژگی همین زیرمجموعه است و شیوع در جمعیت عمومی نیست.",
        f"در مجموعهٔ زوج اصلی، گروه‌های طبیعی، MCI و دمانس به‌ترتیب {normal['n_population']}، {mci['n_population']} و {dementia['n_population']} نفرند؛ میانگین ضخامت آن‌ها به‌ترتیب {fmt(normal['mean'],3)}، {fmt(mci['mean'],3)} و {fmt(dementia['mean'],3)} mm و میانگین MoCA به‌ترتیب {', '.join(fmt(r['mean']) for r in group_moca)} است. این اختلاف‌های مشاهده‌شده تعدیل نشده‌اند؛ توزیع سن، تحصیلات و جنس هم در جدول‌های گروهی نشان داده می‌شود. آزمون، معنی‌داری، اثر مستقل، علیت یا توان تشخیصی از این جدول نتیجه نمی‌شود؛ گروه دمانس به‌تنهایی علت اختصاصی آلزایمر را تعیین نمی‌کند.",
        f"گروه اختلال بدون احراز MCI با {small['n_population']} نفر حفظ شده است؛ میانگین ضخامت {fmt(small['mean'],3)} mm دارد. حجم کوچک و تفاوت ترکیب گروه‌ها اجازهٔ تعبیر سادهٔ گروه‌ها به‌عنوان یک روند یکنواخت یا مراحل پیشرفت همان افراد را نمی‌دهد. یک فرد در گروه هفت‌نفره {fmt(100/7)} واحد درصد از همان گروه را تشکیل می‌دهد.",
        f"سناریوی فقط صحیح‌مقدار {integer['n_usable']} نمره با میانگین {fmt(integer['mean'])} و میانه {fmt(integer['median'])} دارد؛ مجموعهٔ اصلی {moca['n_usable']} نمره با میانگین {fmt(moca['mean'])} دارد. ترکیب گروه‌های شناختی این دو مجموعه در جدول فراوانی هر نمونه قابل مشاهده است. اختلاف خلاصه‌ها پیامد تغییر افراد و مقادیرِ واردشده هم هست و اعتبار هیچ سیاست یا پایداری رابطهٔ MRI–MoCA را ثابت نمی‌کند. تحلیل حساسیت اثر در فاز مربوط هنوز باقی است.",
        "مرور IQR صرفاً نقاط خارج از حصار را می‌شمارد؛ هیچ‌یک حذف نشده‌اند. SD به مقدارهای دور حساس است و میانه/IQR در کنار میانگین/SD گزارش می‌شوند. از تقارن چند شاخص یا صفر بودن گمشدگیِ نمونهٔ کامل، نرمال‌بودن، صحت بالینی یا نبود گمشدگی اولیه نتیجه نمی‌شود.",
    ]


def report_sections(result: dict) -> dict[str, str]:
    sections = {}
    sections["methods"] = """## روش و دامنه

این مرحله شش متغیر کمی منتخب و جنس/وضعیت شناختی را توصیف می‌کند؛ متغیر جدیدی بر اساس نتیجه انتخاب نشده است. همهٔ خلاصه‌ها بدون وزن و محدود به زیرمجموعهٔ تحویلی‌اند. برای هر متغیر از مقادیر کاری قابل استفادهٔ همان جمعیت استفاده می‌شود؛ تعداد غیرقابل استفاده با مخرج جمعیت همان ردیف گزارش می‌شود. نبود یک متغیر فرد را از تمام خلاصه‌ها حذف نمی‌کند. گمشدگی قبل از آماده‌سازی TA قابل بازیابی نیست.

SD نمونه با مخرج n−1 محاسبه می‌شود؛ برای کمتر از دو مقدار تعریف نشده است. چارک‌ها از روش خطی/inclusive، نوع ۷، با h=(n−1)p به دست می‌آیند؛ درون‌یابی ممکن است حتی برای دادهٔ صحیح چارک اعشاری بدهد و به معنی افزودن رکورد اعشاری نیست. IQR=Q3−Q1؛ حداقل/حداکثر مقدار مشاهده‌شده‌اند، نه آستانهٔ اعتبار بالینی. برای متغیر طبقه‌ای میانگین و SD محاسبه نمی‌شود.

سن، سال تحصیل و ضخامت کمیت‌های عددی با واحد مشخص‌اند؛ میانگین/SD مرکز و پراکندگی را در همان واحد و میانه/IQR خلاصهٔ مقاوم‌تری در برابر مقادیر دور ارائه می‌کنند. MoCA یک نمرهٔ محدود است؛ میانگین/SD صرفاً خلاصهٔ عددی نمرهٔ کاری‌اند و «نمرهٔ دو برابر» به معنی «توان شناختی دو برابر» نیست. نامعلوم‌بودن آماده‌سازی نمره در تفسیر همهٔ شاخص‌های آن باقی می‌ماند. چارک و SD گروه بسیار کوچک قابل محاسبه‌اند، ولی به چند مشاهده وابسته‌اند.

درصد طبقه‌ای دو مخرج مشخص دارد: تمام اعضای مجموعه و فقط مقدارهای قابل استفاده. ردیف غیرقابل استفاده در شمار و درصد کل می‌آید و درصد از قابل استفاده برایش تعریف نمی‌شود. صفر، ناموجود و نتیجهٔ تعریف‌نشده یکی نیستند؛ «—» در نمایش یعنی تعریف نشده/قابل محاسبه نیست. CSV/JSON مقدار خالی/null دارند، نه صفر ساختگی. در نمایش، mm با سه و سایر خلاصه‌ها با دو رقم اعشار می‌آیند؛ ذخیره بدون گردکردن تحلیلی است و این نمایش ادعای دقت دستگاه نیست.

مقایسهٔ گروهی بر اساس NACCUDSD در زوج اصلی انجام می‌شود تا MoCA و MRI در هر گروه به افراد یکسان مربوط باشند. متغیرهای همراه مخرج معتبر خود را دارند. گروه کوچک حفظ می‌شود. خلاصهٔ کل و چهار مجموعهٔ هم‌پوشان جداست؛ شمارها جمع نمی‌شوند. این مرحله آزمون، همبستگی، فاصلهٔ اطمینان و مدل ندارد."""
    sections["overall"] = "## خلاصهٔ کمی در تمام افراد مشترک\n\n" + numeric_table([
        r for r in result["numeric"] if r["sample"] == "all_shared"])
    cat_parts = ["## فراوانی جنس و وضعیت شناختی با مخرج صریح"]
    for sample, label in SAMPLE_LABELS.items():
        cat_parts += ["### " + label, table(["متغیر", "کد", "طبقه", "جمعیت", "قابل استفاده", "تعداد طبقه", "% کل", "% قابل استفاده"], [
            [r["variable"], r["level_code"] if r["level_code"] is not None else "—", r["level_label"], r["n_population"], r["n_available"], r["count"], fmt(r["percent_of_population"]), fmt(r["percent_of_available"])]
            for r in result["categorical"] if r["sample"] == sample and r["stratum_code"] is None])]
    sections["categorical"] = "\n\n".join(cat_parts)
    group_parts = ["## مقایسهٔ توصیفی گروه‌های شناختی در زوج اصلی", "برای هر گروه، افراد دارای پاسخ و MRI یکسان‌اند؛ n تحصیلات می‌تواند کمتر باشد. اختلاف گروه‌ها تعدیل نشده است."]
    for code, label in CATEGORIES["NACCUDSD_ANALYSIS"].items():
        group_parts += [f"### کد {code}: {label}", numeric_table([r for r in result["numeric"] if r["stratum_code"] == code]),
                        table(["جنس", "جمعیت گروه", "قابل استفاده", "تعداد", "% گروه", "% قابل استفاده"], [
                            [r["level_label"], r["n_population"], r["n_available"], r["count"], fmt(r["percent_of_population"]), fmt(r["percent_of_available"])]
                            for r in result["categorical"] if r["stratum_code"] == code])]
    sections["groups"] = "\n\n".join(group_parts)
    sections["samples"] = "\n\n".join(["## خلاصهٔ کمی چهار مجموعهٔ قابل استفاده", "تفاوت این جدول‌ها هم به مقدارها و هم به ترکیب افراد مربوط است؛ مقایسهٔ اثر رابطه در سناریوی حساسیت انجام نشده است.", *[
        "### " + SAMPLE_LABELS[sample] + "\n\n" + numeric_table([r for r in result["numeric"] if r["sample"] == sample and r["stratum_code"] is None])
        for sample in SAMPLE_FLAGS]])
    sections["scores"] = "## جزئیات MoCA و کران‌های نمره\n\n" + table([
        "مجموعه", "جمعیت", "قابل استفاده", "غیرقابل استفاده", "صحیح‌مقدار", "اعشاری (% معتبر)", "صفر (% معتبر)", "۳۰ (% معتبر)"], [
        [r["sample"], r["n_population"], r["n_usable"], r["n_unusable"], r["n_integer_valued"],
         f"{r['n_fractional']} ({fmt(r['percent_fractional_of_usable'])})", f"{r['n_at_zero']} ({fmt(r['percent_at_zero_of_usable'])})", f"{r['n_at_thirty']} ({fmt(r['percent_at_thirty_of_usable'])})"]
        for r in result["score_details"]])
    sections["outliers"] = "## مرور نقاط خارج از حصار در کل مقادیر کاری\n\nحصارها فقط در تمام افراد مشترک و برای هر متغیر با مقادیر قابل بررسی خودش محاسبه شده‌اند؛ قاعدهٔ حذف نیستند. مساوی حصار، خارج حصار نیست. ارزیابی‌نشده با نبود دورافتادگی برابر نیست.\n\n" + table([
        "متغیر", "قابل بررسی", "ارزیابی نشده", "حصار پایین", "حصار بالا", "پایین‌تر", "بالاتر", "کل پرچم", "% قابل بررسی"], [
        [r["variable"], r["n_usable"], r["not_evaluated"], fmt(r["lower_fence"], 3), fmt(r["upper_fence"], 3), r["below_fence"], r["above_fence"], r["flagged"], fmt(r["percent_flagged_of_usable"])]
        for r in result["outlier_reviews"]])
    parts = ["## جدول دقیق فراوانی مقادیر UDS", "مخرج کل ۱۲۳۷ است؛ مخرج قابل استفاده در هر ردیف نوشته شده. مقدارهای اعشاری MoCA بدون گردکردن باقی‌اند. توزیع تجمعی فقط روی مقدارهای قابل استفاده و به ترتیب عددی است؛ ردیف ناموجود وارد تجمع نمی‌شود."]
    for col in ("MOCATOTS_ANALYSIS", "NACCAGE_ANALYSIS", "EDUC_ANALYSIS"):
        parts += ["### " + NUMERIC[col][0], table(["مقدار کاری", "قابل استفاده", "فراوانی", "% کل", "% قابل استفاده", "تجمع قابل استفاده (%)"], [
            [str(r["value"]) if r["value"] is not None else "غیرقابل استفاده", r["n_available"], r["count"], fmt(r["percent_of_population"]), fmt(r["percent_of_available"]), fmt(r["cumulative_percent_available"])]
            for r in result["discrete"] if r["variable"] == col])]
    sections["discrete"] = "\n\n".join(parts)
    sections["interpretation"] = "## تفسیر توصیفی و حدود آن\n\n" + "\n\n".join(interpret(result))
    sections["files"] = """## فایل‌ها و بازتولید

- [CSV خلاصه‌های کمی](descriptive_numeric.csv): شش متغیر در پنج مجموعه، و شش متغیر در چهار گروه زوج اصلی؛ ستون‌های دامنه، مرکز، پراکندگی و مخرج‌ها.
- [CSV فراوانی طبقه‌ای](descriptive_categorical.csv): جنس/وضعیت شناختی در پنج مجموعه و جنس در چهار گروه زوج اصلی، با دو مخرج درصد و ردیف غیرقابل استفاده.
- [CSV فراوانی دقیق](descriptive_discrete_frequencies.csv): MoCA، سن و تحصیلات در تمام افراد، شامل شمار و درصد تجمعی قابل استفاده و ردیف جداگانهٔ غیرقابل استفاده.
- [خروجی کامل JSON](descriptive_statistics.json): همهٔ جدول‌ها، جزئیات MoCA، IQR، روش و اثر انگشت منبع/کد/خروجی؛ هیچ شناسهٔ فردی به گزارش تجمیعی اضافه نمی‌شود.
- [نوت‌بوک](../../notebooks/phase1.ipynb) تمام این جدول‌ها و تفسیر را در خود دارد. [راهنمای داده](../../data/README.md)، [فرهنگ متغیرها](../../docs/SELECTED_VARIABLES.md) و [قواعد کیفیت](../../docs/QUALITY_RULES.md) تعریف ورودی و تصمیم‌ها را ثبت می‌کنند.

از ریشهٔ پروژه `python3 -m src.phase1_descriptive` را اجرا کنید؛ جدول مرجع و شناسنامهٔ مرحلهٔ ۶ باید موجود و با ورودی/کد/قواعد سازگار باشند. دستور فقط خروجی‌های توصیفی بالا را بازتولید می‌کند؛ برای ساخت همهٔ مراحل فعلی، تمام نوت‌بوک را از ابتدا اجرا کنید. کد فقط به کتابخانهٔ استاندارد Python نیاز دارد.

قرارداد CSVهای نتایج: `sample` مجموعه را تعیین می‌کند؛ `stratum_variable=overall` یعنی تمام اعضای همان مجموعه و کد گروه در این ردیف‌ها خالی است. `stratum_variable=NACCUDSD_ANALYSIS` یعنی ردیف به گروه شناختی با کد/نام نوشته‌شده مربوط است. کد طبقهٔ خالی در جدول طبقه‌ای، ردیف غیرقابل استفاده است؛ مقدار خالی در آمار عددی یعنی نتیجه تعریف نشده و به صفر تبدیل نمی‌شود. درصدها به مقیاس ۰ تا ۱۰۰ ذخیره شده‌اند. شمارها صحیح، واحدها در ستون جدا و متن‌ها UTF-8 هستند. ردیف فراوانیِ غیرقابل استفاده با `value_status=unusable` مشخص است؛ از مرتب‌کردن آن در میان مقدارهای عددی یا افزودن آن به تجمع قابل استفاده پرهیز شود. JSON انواع عدد/رشته/null و متادیتای روش را نگه می‌دارد. شمار ردیف‌های جدول‌های متفاوت را با هم جمع نکنید؛ آن‌ها خلاصه‌های هم‌پوشان‌اند.

نمودارها و بررسی تصویری توزیع در [گزارش شکل‌ها](figures.md) تکمیل شده‌اند. محدودیت انتخاب نمونه، جایگذاری نامعلوم، نبود گروه فاقد MRI و تطبیق زمانی نامعلوم همچنان برقرار است؛ این گزارش به‌تنهایی تحویل کامل فاز یک نیست."""
    return sections


def write_descriptive(root: Path, result: dict) -> dict:
    p = result["provenance"]
    protected = {**p["input_sha256"], p["dataset"]: p["dataset_sha256"],
                 p["dataset_manifest"]: p["dataset_manifest_sha256"],
                 "config/phase1_quality_rules.json": p["config_sha256"], **p["code_sha256"]}
    for name, digest in protected.items():
        if fingerprint(root / name) != digest:
            raise ValueError("Descriptive source changed; rebuild required: " + name)
    for key in ("numeric", "categorical", "discrete"):
        write_csv(root / OUTPUTS[key], result[key])
    report = "# آمار توصیفی منتخب — فاز یک، مسیر ج\n\n" + "\n\n".join(report_sections(result).values()) + "\n"
    (root / OUTPUTS["report"]).write_text(report, encoding="utf-8")
    for name, digest in protected.items():
        if fingerprint(root / name) != digest:
            raise AssertionError("Protected source changed during summary export: " + name)
    saved = {**result, "output_sha256": {path: fingerprint(root / path) for key, path in OUTPUTS.items() if key != "json"}}
    (root / OUTPUTS["json"]).write_text(json.dumps(saved, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = build_descriptive(args.root.resolve())
    write_descriptive(args.root.resolve(), result)
    print(json.dumps({"populations": result["populations"], "rows": {k: len(result[k]) for k in ("numeric", "categorical", "discrete")}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
