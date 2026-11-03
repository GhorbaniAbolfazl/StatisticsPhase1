"""Four descriptive phase-one figures, with auditable bin/group summaries.

Run: python3 -m src.phase1_figures. Source CSVs, the participant table, and
descriptive tables are read only. No tests of association or models are fitted.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np

from .phase1_dataset import DATA_PATH, MANIFEST_PATH, load_dataset
from .phase1_descriptive import OUTPUTS as DESCRIPTIVE_OUTPUTS
from .phase1_descriptive import build_descriptive, numeric_summary
from .phase1_quality import fingerprint

OUT = "reports/phase1"
FIGURE_DIR = f"{OUT}/figures"
REPORT_PATH = f"{OUT}/figures.md"
METADATA_PATH = f"{OUT}/figures_metadata.json"
FIGURES = {
    "01_moca_distribution": "توزیع نمرهٔ کاری MoCA",
    "02_entorhinal_distribution": "توزیع میانگین ضخامت انتورینال",
    "03_cognitive_status": "فراوانی وضعیت‌های شناختی در زیرمجموعه",
    "04_group_comparison": "مقایسهٔ توصیفی شناخت و ضخامت در گروه‌ها",
}
GROUPS = {
    1: ("Normal cognition", "طبیعی", "#0072B2"),
    2: ("Impaired, not MCI", "اختلال بدون احراز MCI", "#E69F00"),
    3: ("MCI", "MCI", "#009E73"),
    4: ("Dementia", "دمانس", "#CC79A7"),
}
JITTER_SEED = 20261031


def histogram_counts(values: list[float], edges: list[float]) -> list[int]:
    """Left closed/right open bins, final right edge included; never drop data."""
    if len(edges) < 2 or any(not math.isfinite(x) for x in edges) or any(b <= a for a, b in zip(edges, edges[1:])):
        raise ValueError("Histogram edges must be finite and strictly increasing")
    if any(not math.isfinite(v) or v < edges[0] or v > edges[-1] for v in values):
        raise ValueError("Histogram limits would omit a measurement")
    counts = np.histogram(values, bins=edges)[0].astype(int).tolist()
    if sum(counts) != len(values):
        raise AssertionError("Histogram lost an observation")
    return counts


def box_summary(values: list[float]) -> dict:
    if not values:
        raise ValueError("An empty group needs an explicit visual representation")
    s = numeric_summary(values)
    lower, upper = s["q1"] - 1.5*s["iqr"], s["q3"] + 1.5*s["iqr"]
    inside = [v for v in values if lower <= v <= upper]
    return {"n": len(values), "mean": s["mean"], "med": s["median"], "q1": s["q1"], "q3": s["q3"],
            "lower_fence": lower, "upper_fence": upper,
            "whislo": min(inside), "whishi": max(inside),
            "minimum": min(values), "maximum": max(values),
            "n_outside_group_fences": sum(v < lower or v > upper for v in values)}


def prepare_plot_data(rows: list[dict]) -> dict:
    scores = [r["MOCATOTS_ANALYSIS"] for r in rows if r["MOCATOTS_ANALYSIS"] is not None]
    integer = [r["MOCATOTS_ANALYSIS"] for r in rows if r["MOCATOTS_ANALYSIS"] is not None and not r["MOCA_FRACTIONAL_IN_RANGE"]]
    fractional = [r["MOCATOTS_ANALYSIS"] for r in rows if r["MOCA_FRACTIONAL_IN_RANGE"]]
    if len(integer) + len(fractional) != len(scores):
        raise ValueError("MoCA preparation flags do not partition usable scores")
    thickness = [r["ENTORHINAL_THICKNESS_MEAN"] for r in rows if r["ENTORHINAL_THICKNESS_MEAN"] is not None]
    score_edges = list(range(0, 32, 2))
    thickness_edges = np.linspace(0, 4.2, 43).tolist()
    pair = [r for r in rows if r["MAIN_PAIR_ELIGIBLE"]]
    if any(r["NACCUDSD_ANALYSIS"] not in GROUPS for r in rows):
        raise ValueError("A missing or unlabelled cognitive group needs an explicit plotting decision")
    groups = []
    for code, (english, persian, color) in GROUPS.items():
        selected = [r for r in pair if r["NACCUDSD_ANALYSIS"] == code]
        if any(r["MOCATOTS_ANALYSIS"] is None or r["ENTORHINAL_THICKNESS_MEAN"] is None for r in selected):
            raise ValueError("Paired comparison includes an unavailable measurement")
        groups.append({"code": code, "label": english, "label_fa": persian, "color": color,
                       "n_all_shared": sum(r["NACCUDSD_ANALYSIS"] == code for r in rows),
                       "n_main_pair": len(selected),
                       "moca": box_summary([r["MOCATOTS_ANALYSIS"] for r in selected]),
                       "thickness": box_summary([r["ENTORHINAL_THICKNESS_MEAN"] for r in selected])})
    if sum(g["n_main_pair"] for g in groups) != len(pair):
        raise AssertionError("Paired observations were lost in group allocation")
    return {"n_all_shared": len(rows), "n_main_pair": len(pair), "groups": groups,
            "moca": {"n_usable": len(scores), "n_unusable": len(rows)-len(scores),
                     "n_integer": len(integer), "n_fractional": len(fractional),
                     "edges": score_edges, "integer_counts": histogram_counts(integer, score_edges),
                     "fractional_counts": histogram_counts(fractional, score_edges),
                     "summary": numeric_summary(scores)},
            "thickness": {"n_usable": len(thickness), "n_unusable": len(rows)-len(thickness),
                          "edges": thickness_edges, "counts": histogram_counts(thickness, thickness_edges),
                          "summary": numeric_summary(thickness)}}


def build_plot_bundle(root: Path) -> tuple[list[dict], dict]:
    rows, manifest = load_dataset(root)
    descriptive = build_descriptive(root)
    stored = json.loads((root / DESCRIPTIVE_OUTPUTS["json"]).read_text(encoding="utf-8"))
    if any(stored[key] != descriptive[key] for key in descriptive):
        raise ValueError("Descriptive outputs are stale; rebuild before plotting")
    for path, digest in stored["output_sha256"].items():
        if fingerprint(root / path) != digest:
            raise ValueError("A descriptive output changed: " + path)
    data = prepare_plot_data(rows)
    protected = {**manifest["input_sha256"], DATA_PATH: fingerprint(root / DATA_PATH),
                 MANIFEST_PATH: fingerprint(root / MANIFEST_PATH),
                 **{path: fingerprint(root / path) for path in DESCRIPTIVE_OUTPUTS.values()}}
    data["provenance"] = {"protected_sha256": protected,
                          "code_sha256": {"src/phase1_figures.py": fingerprint(root / "src/phase1_figures.py")}}
    data["design"] = {
        "figure_count": 4, "formats": ["png", "svg"], "png_dpi": 300,
        "labels_language": "English labels inside figures, Persian captions/interpretation",
        "histogram_intervals": "[left,right), final interval includes right endpoint; no rounding of individual scores",
        "moca_bin_width_score": 2, "thickness_bin_width_mm": .1,
        "box_quantiles": "Linear/inclusive type 7; box Q1-Q3, central line median; whiskers most extreme observed values within 1.5 IQR group fences",
        "raw_points": "All paired participants in both panels; no vertical jitter, no outlier deletion; x jitter only for visibility",
        "horizontal_jitter_seed": JITTER_SEED, "horizontal_jitter_half_width": .14,
        "group_box_width": .55, "group_order": [1, 2, 3, 4],
        "axes": {"moca_x": [-.3, 30.3], "thickness_x": [0, 4.2],
                 "group_moca_y": [-.75, 30.75], "group_thickness_y": [0, 4.2]},
        "inference": "Descriptive only; no regression, correlation, p-values, confidence intervals, KDE or normal fit",
    }
    return rows, data


def captions(data: dict) -> dict[str, str]:
    m, t = data["moca"], data["thickness"]
    g = data["groups"]
    sizes = "، ".join(str(x["n_main_pair"]) for x in g)
    return {
        "01_moca_distribution": f"""**هدف و خواندن شکل:** توزیع نمرهٔ کاری UDS با هیستوگرامِ شمار افراد و بازه‌های ثابت دو امتیازی نمایش داده شده است. دو بخش ستون‌ها مکمل هم‌اند: {m['n_integer']} صحیح‌مقدار و {m['n_fractional']} اعشاری درون دامنه، مجموعاً {m['n_usable']} نفر. رنگ و هاشور هر دو به تشخیص بخش اعشاری کمک می‌کنند؛ صحیح‌بودن اصالت نمره را اثبات نمی‌کند. هر بازه از چپ بسته و از راست باز است؛ بازهٔ آخر شامل ۳۰ است. اعشار به نمرهٔ صحیح گرد نشده‌اند. {m['n_unusable']} پاسخ غیرقابل استفاده از {data['n_all_shared']} فرد در نمودار نمره وارد نیستند و در جدول مرجع باقی‌اند؛ چهار کد ۸۸ به معنی اجرا نشدن یک یا چند آیتم یا کل آزمون و پنج نمرهٔ دیگر خارج از دامنه‌اند.

**تفسیر توصیفی:** تراکم عمده در نمره‌های بالاتر و امتداد توزیع به سمت نمره‌های پایین دیده می‌شود؛ میانگین {m['summary']['mean']:.2f} پایین‌تر از میانهٔ {m['summary']['median']:.2f} است. یک مقدار صفر و ۴۷ مقدار ۳۰ در دامنهٔ کامل حفظ شده‌اند. شکل به پهنای بازه وابسته است؛ از ظاهر آن، نرمال‌بودن، اثر کف/سقف یا علت آماده‌سازی نتیجه نمی‌شود. این نمودار دو توزیع با اندازهٔ متفاوت را به‌عنوان نمونه‌های مستقل مقایسه نمی‌کند؛ دو جزء جمع‌شوندهٔ همان نمونه را نشان می‌دهد.""",
        "02_entorhinal_distribution": f"""**هدف و خواندن شکل:** توزیع متغیر اصلی MRI، یعنی میانگین حسابی ضخامت چپ و راست، برای {t['n_usable']} فرد با بازه‌های ۰٫۱۰ میلی‌متری و محور شمار نمایش داده شده است؛ مقدار غیرقابل استفاده {t['n_unusable']} مورد است. محور افقی از صفر تا ۴٫۲ mm را پوشش می‌دهد و تمام مقدارهای مشاهده‌شده، از {t['summary']['minimum']:.3f} تا {t['summary']['maximum']:.3f}، داخل آن‌اند. خط‌های راهنما میانگین و میانه‌اند؛ آستانهٔ بالینی نیستند. میانگین و میانه از تمام مقادیر کاری محاسبه شده‌اند، نه از مرکز ستون‌ها.

**تفسیر توصیفی:** عمدهٔ ضخامت‌ها پیرامون ۳ mm قرار دارند و امتداد به سمت مقادیر پایین‌تر دیده می‌شود؛ میانگین {t['summary']['mean']:.3f} و میانه {t['summary']['median']:.3f} mm است. مقدارهای پایین حذف یا محورشان بریده نشده است. ظاهر توزیع، موفقیت QC یا نرمال‌بودن را ثابت نمی‌کند؛ نسخه و روش پردازش اولیهٔ MRI نامعلوم باقی است. دو نیمکره به دو فرد مستقل تبدیل نشده‌اند.""",
        "03_cognitive_status": f"""**هدف و خواندن شکل:** نمودار میله‌ای افقی، فراوانی چهار کد NACCUDSD در تمام {data['n_all_shared']} فرد مشترک را نشان می‌دهد؛ درصد نوشته‌شده کنار هر میله، تعداد همان گروه تقسیم بر همین مخرج است. کد غیرقابل استفاده در این متغیر صفر مورد است. ترتیب کدها حفظ شده، محور شمار از صفر شروع می‌شود و گروه کوچک با برچسب و هاشور قابل تشخیص است. MCI یعنی اختلال شناختی خفیف؛ «اختلال بدون احراز MCI» گروه مستقل کد ۲ است.

**تفسیر توصیفی:** گروه طبیعی با {g[0]['n_all_shared']} نفر بیشترین فراوانی را دارد؛ گروه کد ۲ با {g[1]['n_all_shared']} نفر حفظ شده و با MCI ادغام نشده است. این درصدها ترکیب زیرمجموعهٔ تحویلی‌اند و شیوع جمعیت عمومی نیستند. دمانس به‌تنهایی علت اختصاصی آلزایمر را مشخص نمی‌کند. تعدادهای این شکل با شکل مقایسهٔ زوج اصلی متفاوت‌اند، چون جمعیت مبنا متفاوت است.""",
        "04_group_comparison": f"""**هدف و خواندن شکل:** دو پنل برای MoCA و میانگین ضخامت روی همان {data['n_main_pair']} فرد زوج اصلی رسم شده‌اند؛ تعداد چهار گروه به ترتیب {sizes} است. جعبه از Q1 تا Q3 و خط داخل آن میانه است. سبیل‌ها تا دورترین مقدار مشاهده‌شدهٔ داخل حصار ۱٫۵ IQR همان گروه می‌روند؛ سبیل کمینه/بیشینه یا فاصلهٔ اطمینان نیست. همهٔ نقاط، شامل نقاط بیرون سبیل، رسم شده‌اند و نماد تکراری جداگانه برای دورافتاده‌ها افزوده نشده است. جابه‌جایی کوچک فقط افقی با بذر ثابت {JITTER_SEED} برای کاهش هم‌پوشانی است؛ نمره و ضخامت عمودی تغییر نکرده‌اند. رنگ/ترتیب گروه‌ها با شکل فراوانی هماهنگ است؛ عرض جعبه‌ها برابر است و اندازهٔ نمونه را کد نمی‌کند.

**تفسیر توصیفی:** مرکز MoCA و ضخامت در گروه دمانس نسبت به گروه طبیعی پایین‌تر دیده می‌شود، اما دامنه‌های مشاهده‌شده و بخشی از بازه‌های میانی هم‌پوشانی دارند. گروه اختلال بدون احراز MCI فقط هفت نفر دارد و الگویی یکنواخت در همهٔ چهار گروه ایجاد نمی‌شود؛ پراکندگی این گروه با n کوچک باید محتاطانه خوانده شود. این نمایش مقطعی و تعدیل‌نشده است؛ تفاوت سن، جنس و تحصیلات در جدول‌های مرحلهٔ ۷ آمده است. از این شکل، اثر مستقل ضخامت، معنی‌داری، علیت، توان تشخیصی یا تغییر طولی افراد نتیجه نمی‌شود. حصارهای درون‌گروهی این جعبه‌ها با پرچم‌های IQR کل نمونه در ممیزی تفاوت دامنه دارند؛ هیچ‌یک قاعدهٔ حذف نیست.""",
    }


def render_figures(root: Path, rows: list[dict], data: dict) -> dict:
    # Use writable caches without changing HOME or creating project cache files.
    cache = Path(tempfile.gettempdir()) / "statistics-matplotlib-cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache / "matplotlib"))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache / "xdg"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    from matplotlib.text import Text

    target = root / FIGURE_DIR
    target.mkdir(parents=True, exist_ok=True)
    visual_checks, exported = {}, []

    def axes_style(ax):
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#D9DFE4", linewidth=.6)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors="#263442")

    def heading(fig, title, subtitle, left=.09):
        fig.text(left, .955, title, fontsize=16, fontweight="bold", va="top", color="#172B3A")
        fig.text(left, .895, subtitle, fontsize=10.5, va="top", color="#425466")

    def save(fig, name):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        box = fig.bbox
        outside = []
        for artist in fig.findobj(match=Text):
            if not artist.get_visible() or not artist.get_text().strip():
                continue
            extent = artist.get_window_extent(renderer)
            if extent.x0 < box.x0-1 or extent.y0 < box.y0-1 or extent.x1 > box.x1+1 or extent.y1 > box.y1+1:
                outside.append(artist.get_text())
        if outside:
            raise ValueError("Text extends beyond figure canvas: " + repr(outside))
        visual_checks[name] = {"text_within_canvas": True, "axes": len(fig.axes),
                               "figure_inches": list(fig.get_size_inches()),
                               "raw_points_per_panel": [len(c.get_offsets()) for ax in fig.axes for c in ax.collections if hasattr(c, "get_offsets")]}
        for extension in ("png", "svg"):
            path = target / (name + "." + extension)
            fig.savefig(path, dpi=300, facecolor="white", metadata={"Date": None} if extension == "svg" else {"Software": "Statistics phase one / Matplotlib"})
            exported.append(path.relative_to(root).as_posix())
        plt.close(fig)

    # A notebook's light/dark theme must not change the saved scientific figures.
    style = {**dict(plt.rcParamsDefault), "font.family": "DejaVu Sans", "font.size": 12,
             "axes.labelsize": 12, "axes.facecolor": "white", "figure.facecolor": "white",
             "text.color": "#172B3A", "axes.labelcolor": "#172B3A",
             "xtick.color": "#263442", "ytick.color": "#263442",
             "legend.fontsize": 11, "svg.hashsalt": "statistics-phase1-figures-v1", "svg.fonttype": "none"}
    with plt.rc_context(style):
        m = data["moca"]
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.subplots_adjust(left=.09, right=.97, bottom=.20, top=.80)
        heading(fig, "MoCA score distribution", f"Supplied subset | usable n={m['n_usable']:,} of {data['n_all_shared']:,} | bin width: 2 score points")
        edges = np.array(m["edges"])
        a = np.array(m["integer_counts"])
        ax.bar(edges[:-1], a, width=np.diff(edges), align="edge", color="#4C5D73", edgecolor="white", linewidth=.6, label=f"Integer-valued (n={m['n_integer']:,})")
        ax.bar(edges[:-1], m["fractional_counts"], bottom=a, width=np.diff(edges), align="edge", color="#E69F00", hatch="///", edgecolor="white", linewidth=.6, label=f"Fractional (n={m['n_fractional']:,})")
        ax.axvline(m["summary"]["mean"], color="#A63529", linestyle="--", linewidth=1.7, label=f"Mean {m['summary']['mean']:.2f}")
        ax.axvline(m["summary"]["median"], color="#0072B2", linestyle=":", linewidth=2, label=f"Median {m['summary']['median']:.2f}")
        ax.set(xlabel="Prepared MoCA score (0-30)", ylabel="Participants", xlim=(-.3, 30.3), ylim=(0, None))
        ax.set_xticks(range(0, 31, 5))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        axes_style(ax)
        ax.legend(loc="upper left", frameon=False)
        fig.text(.09, .075, "9 scores unusable: 4 special codes and 5 other out-of-range values. Raw records are retained.", fontsize=9)
        fig.text(.09, .038, "Fractional values are not rounded. Bins are [left, right), except the final bin includes 30.", fontsize=9)
        save(fig, "01_moca_distribution")

        t = data["thickness"]
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.subplots_adjust(left=.09, right=.97, bottom=.20, top=.80)
        heading(fig, "Bilateral entorhinal thickness distribution", f"Supplied subset | usable n={t['n_usable']:,} of {data['n_all_shared']:,} | bin width: 0.10 mm")
        edges = np.array(t["edges"])
        ax.bar(edges[:-1], t["counts"], width=np.diff(edges), align="edge", color="#0072B2", edgecolor="white", linewidth=.5)
        ax.axvline(t["summary"]["mean"], color="#A63529", linestyle="--", linewidth=1.7, label=f"Mean {t['summary']['mean']:.3f} mm")
        ax.axvline(t["summary"]["median"], color="#172B3A", linestyle=":", linewidth=2, label=f"Median {t['summary']['median']:.3f} mm")
        ax.set(xlabel="Mean left/right entorhinal cortical thickness (mm)", ylabel="Participants", xlim=(0, 4.2), ylim=(0, None))
        ax.set_xticks(np.arange(0, 4.1, .5))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        axes_style(ax)
        ax.legend(loc="upper left", frameon=False)
        fig.text(.09, .075, "0 unusable thickness means. All observed values are shown; no outlier removal or normal fit.", fontsize=9)
        fig.text(.09, .038, "One mean per participant; both hemispheres must have a usable thickness measurement.", fontsize=9)
        save(fig, "02_entorhinal_distribution")

        fig, ax = plt.subplots(figsize=(10, 5.8))
        fig.subplots_adjust(left=.25, right=.96, bottom=.20, top=.80)
        heading(fig, "Cognitive status in the supplied subset", f"All shared participants | n={data['n_all_shared']:,} | unavailable status codes: 0", left=.055)
        groups = data["groups"]
        counts = [g["n_all_shared"] for g in groups]
        bars = ax.barh(range(4), counts, color=[g["color"] for g in groups], height=.60)
        bars[1].set_hatch("///")
        bars[1].set_edgecolor("#6A4A00")
        ax.set_yticks(range(4), [g["label"] for g in groups])
        ax.invert_yaxis()
        ax.set_xlim(0, max(counts)*1.20)
        ax.set_xticks(np.arange(0, max(counts)*1.20 + 1, 200))
        ax.set_xlabel("Participants")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", color="#D9DFE4", linewidth=.6)
        ax.set_axisbelow(True)
        for i, count in enumerate(counts):
            ax.text(count+max(counts)*.016, i, f"{count:,} ({100*count/data['n_all_shared']:.2f}%)", va="center", fontsize=10.5)
        fig.text(.055, .075, "Percentages use all 1,237 shared participants. The seven-person group is retained.", fontsize=9)
        fig.text(.055, .038, "MCI: mild cognitive impairment. Dementia status alone does not establish Alzheimer's disease.", fontsize=9)
        save(fig, "03_cognitive_status")

        fig, axs = plt.subplots(1, 2, figsize=(11, 6.8))
        fig.subplots_adjust(left=.075, right=.975, bottom=.27, top=.77, wspace=.28)
        heading(fig, "Cognition and entorhinal thickness by cognitive status", f"Main paired sample | n={data['n_main_pair']:,} | same participants in both panels | unadjusted descriptions", left=.07)
        pair = [r for r in rows if r["MAIN_PAIR_ELIGIBLE"]]
        rng = np.random.default_rng(JITTER_SEED)
        positions = {g["code"]: i+1+rng.uniform(-.14, .14, g["n_main_pair"]) for i, g in enumerate(groups)}
        for ax, column, key, title, ylabel, limits in [
            (axs[0], "MOCATOTS_ANALYSIS", "moca", "A. MoCA", "Prepared MoCA score (0-30)", (-.75, 30.75)),
            (axs[1], "ENTORHINAL_THICKNESS_MEAN", "thickness", "B. Bilateral entorhinal thickness", "Mean cortical thickness (mm)", (0, 4.2)),
        ]:
            for i, group in enumerate(groups, 1):
                values = [r[column] for r in pair if r["NACCUDSD_ANALYSIS"] == group["code"]]
                artists = ax.bxp([group[key]], positions=[i], widths=.55, showfliers=False, patch_artist=True,
                                 boxprops={"facecolor": group["color"], "alpha": .22, "edgecolor": "#263442"},
                                 medianprops={"color": "#172B3A", "linewidth": 2},
                                 whiskerprops={"color": "#526272"}, capprops={"color": "#526272"}, manage_ticks=False)
                if group["code"] == 2:
                    artists["boxes"][0].set_hatch("///")
                ax.scatter(positions[group["code"]], values, s=10, color=group["color"],
                           alpha=.85 if group["n_main_pair"] < 10 else .26, linewidths=0, zorder=3)
            labels = [g["label"].replace(", ", ",\n") + f"\nn={g['n_main_pair']:,}" for g in groups]
            ax.set_xticks(range(1, 5), labels, fontsize=11)
            ax.set(ylabel=ylabel, xlim=(.5, 4.5), ylim=limits)
            ax.set_title(title, fontsize=12)
            ax.set_yticks(np.arange(0, 31, 5) if key == "moca" else np.arange(0, 4.1, .5))
            axes_style(ax)
        fig.text(.07, .115, "Box: Q1-Q3; line: median; whiskers: observations within 1.5 IQR group fences. All raw points are shown.", fontsize=9)
        fig.text(.07, .078, "Horizontal jitter only; vertical measurements unchanged. Box widths are equal; n is shown for every group.", fontsize=9)
        fig.text(.07, .041, "The n=7 group is small. Groups overlap; differences are not adjusted for age, sex or education.", fontsize=9)
        save(fig, "04_group_comparison")

    return {"files": exported, "visual_checks": visual_checks,
            "versions": {"numpy": np.__version__, "matplotlib": matplotlib.__version__}}


def write_figures(root: Path, rows: list[dict], data: dict) -> dict:
    protected = {**data["provenance"]["protected_sha256"], **data["provenance"]["code_sha256"]}
    if any(fingerprint(root / p) != h for p, h in protected.items()):
        raise ValueError("A figure input changed before export")
    rendered = render_figures(root, rows, data)
    lines = ["# نمودارهای فاز یک — مسیر ج", "",
             "چهار شکل توصیفی با PNG با وضوح ۳۰۰ dpi و SVG برداری تهیه شده‌اند. عنوان/محورها انگلیسی و توضیح‌ها فارسی‌اند. جمعیت هر شکل و علت تفاوت تعدادها صریح است؛ داده‌ها و قواعد تغییر نکرده‌اند.", "",
             "## انتخاب شکل و قواعد مشترک", "",
             "دو هیستوگرام برای دو متغیر کمی اصلی، میله‌ای برای وضعیت طبقه‌ای و شکل دوپنلی جعبه/نقاط برای مقایسهٔ دو وجه در چهار گروه انتخاب شده‌اند. محورهای شمار از صفرند، دامنهٔ کامل مقادیر نمایش داده می‌شود و مدل، منحنی نرمال، KDE، آزمون، علامت معنی‌داری یا فاصلهٔ اطمینان اضافه نشده است. رنگ‌ها همراه نام، ترتیب، هاشور و نوع خط به کار رفته‌اند؛ اطلاعات فقط به رنگ وابسته نیست.", ""]
    for number, (name, title) in enumerate(FIGURES.items(), 1):
        lines += [f"## شکل {number} — {title}", "", f"![{title}](figures/{name}.png)", "",
                  captions(data)[name], "", f"[PNG با وضوح کامل](figures/{name}.png) · [SVG برداری](figures/{name}.svg)", ""]
    lines += ["## بازتولید و ردگیری", "",
              "از ریشهٔ پروژه `python3 -m src.phase1_figures` را اجرا کنید. جدول مرجع و خروجی توصیفی سازگار باید از مراحل قبل موجود باشند؛ اجرای همهٔ نوت‌بوک مراحل فعلی را به ترتیب بازتولید می‌کند. وابستگی‌های رسم در requirements.txt ثبت شده‌اند. فایل‌های خام، جدول مرجع و گزارش‌های توصیفی در این دستور فقط خوانده می‌شوند.", "",
              "[متادیتای شکل‌ها](figures_metadata.json) مرز و شمار هر بازه، خلاصهٔ جعبه‌های گروهی، دامنهٔ محورها، بذر جابه‌جایی افقی، اندازه/قالب شکل، نسخهٔ کتابخانه‌ها و اثر انگشت منبع/کد/خروجی را نگه می‌دارد. هندسهٔ متن نسبت به بوم کنترل و هر چهار PNG به‌صورت تصویری بازبینی شده‌اند. خروجی‌های بیتی دقیق به نسخهٔ کتابخانه/قلم/محیط هم وابسته‌اند.", "",
              "[آمار توصیفی](descriptive_statistics.md) · [جریان نمونه](sample_flow.md) · [نوت‌بوک](../../notebooks/phase1.ipynb) · [قواعد کیفیت](../../docs/QUALITY_RULES.md)"]
    (root / REPORT_PATH).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if any(fingerprint(root / p) != h for p, h in protected.items()):
        raise AssertionError("Protected files changed during figure export")
    metadata = {**data, **rendered,
                "output_sha256": {p: fingerprint(root / p) for p in [*rendered["files"], REPORT_PATH]}}
    (root / METADATA_PATH).write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    rows, data = build_plot_bundle(root)
    metadata = write_figures(root, rows, data)
    print(json.dumps({"figures": len(FIGURES), "image_files": len(metadata["files"]),
                      "main_pair": data["n_main_pair"], "text_within_canvas": all(x["text_within_canvas"] for x in metadata["visual_checks"].values())}))


if __name__ == "__main__":
    main()
