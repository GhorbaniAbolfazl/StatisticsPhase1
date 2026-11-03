"""Build a Persian phase-one report from the executed notebook and verified outputs.

Run after the notebook: python3 scripts/build_phase1_pdf.py
The complete notebook runner also calls this builder. No statistical analysis,
raw-data changes or network access is performed here. Fonts are bundled/licensed.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from html import unescape
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab import Version as REPORTLAB_VERSION
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, Image, PageBreak, SimpleDocTemplate, Spacer, Table, TableStyle

REPORT_PATH = "reports/phase1.pdf"
MANIFEST_PATH = "reports/phase1/pdf_manifest.json"
REPORT_DATE = "2026-11-03"
FONT_FAMILY = "IRANSansX"
FONT_FILES = {
    "Fa": "assets/fonts/IranSansX(Pro)/iransansX family/IRANSansX-Regular.ttf",
    "FaBold": "assets/fonts/IranSansX(Pro)/iransansX family/IRANSansX-Bold.ttf",
}
FONT_LICENSE = "assets/fonts/IranSansX(Pro)/licenses.pdf"
INK = colors.HexColor("#19313E")
ACCENT = colors.HexColor("#087F8C")
MUTED = colors.HexColor("#53646D")
PALE = colors.HexColor("#EDF5F6")
RESHAPER = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notebook_digest(path: Path) -> str:
    """Execution timing metadata is not a change to report content."""
    book = json.loads(path.read_text(encoding="utf-8"))
    cells = [{k: c[k] for k in ("cell_type", "source", "execution_count", "outputs") if k in c}
             for c in book["cells"]]
    return hashlib.sha256(json.dumps(cells, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def report_inputs(root: Path) -> dict:
    names = ["scripts/build_phase1_pdf.py", "requirements.txt", "PROJECT_CARD.md",
             "docs/SELECTED_VARIABLES.md", "docs/QUALITY_RULES.md",
             "reports/phase1/conclusion.md", "reports/phase1/quality_audit.json",
             "reports/phase1/descriptive_statistics.json", "reports/phase1/figures_metadata.json",
             "data/processed/phase1_manifest.json", "reports/phase1/sample_flow.csv",
             "reports/phase1/denominators.csv", *FONT_FILES.values(), FONT_LICENSE]
    names += [f"reports/phase1/figures/{name}.png" for name in
              ("01_moca_distribution", "02_entorhinal_distribution", "03_cognitive_status", "04_group_comparison")]
    return {"file_sha256": {p: digest(root / p) for p in names},
            "notebook_content_sha256": notebook_digest(root / "notebooks/phase1.ipynb")}


def verify_report(root: Path) -> dict:
    meta = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    if meta["sources"] != report_inputs(root):
        raise ValueError("PDF sources changed; rebuild the Persian report")
    if digest(root / REPORT_PATH) != meta["pdf_sha256"]:
        raise ValueError("PDF bytes differ from the report manifest")
    verify_notebook_images(root)
    return {"pdf_pages": meta["pages"], "pdf_sources_verified": True,
            "pdf_sha256": meta["pdf_sha256"]}


def verify_notebook_images(root: Path) -> None:
    book = json.loads((root / "notebooks/phase1.ipynb").read_text(encoding="utf-8"))
    embedded = [hashlib.sha256(base64.b64decode(o["data"]["image/png"])).hexdigest()
                for c in book["cells"] for o in c.get("outputs", []) if "image/png" in o.get("data", {})]
    images = [digest(root / f"reports/phase1/figures/{name}.png") for name in
              ("01_moca_distribution", "02_entorhinal_distribution", "03_cognitive_status", "04_group_comparison")]
    if len(embedded) != 4 or sorted(embedded) != sorted(images):
        raise ValueError("Notebook images differ from the report figures; execute the full notebook")


def notebook_font_css(root: Path) -> str:
    """Style rendered notebook prose/tables; keep code and figure images intact.

    Embedded data URLs also work in a relocated, trusted notebook without
    installing the supplied fonts on the reader's computer.
    """
    faces = []
    for name, weight in (("Fa", 400), ("FaBold", 700)):
        data = base64.b64encode((root / FONT_FILES[name]).read_bytes()).decode("ascii")
        faces.append("@font-face{font-family:'Phase1IranSansX';font-style:normal;"
                     f"font-weight:{weight};src:url(data:font/ttf;base64,{data}) format('truetype');}}")
    selectors = ".jp-RenderedMarkdown,.jp-MarkdownOutput,.jp-RenderedHTMLCommon,.text_cell_render,.rendered_html"
    return ('<style id="phase1-report-font">' + ''.join(faces) +
            f":is({selectors}),:is({selectors}) :is(p,li,td,th,h1,h2,h3,h4,h5,h6,blockquote)"
            "{font-family:'Phase1IranSansX',sans-serif!important;}"
            f":is({selectors}) :is(code,pre){{font-family:monospace!important;}}"
            "</style>")


def clean(text: str) -> str:
    text = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", str(text))
    text = re.sub(r"<a[^>]*></a>", "", text)
    text = unescape(re.sub(r"</?(?:div|span)\b[^>]*>", "", text))
    text = text.replace("**", "").replace("`", "").replace("\u200e", "").strip()
    return re.sub(r"([۰-۹]+)[–-]([۰-۹]+)", r"\1 تا \2", text)


def notebook_title(markdown: str) -> str:
    """The first cell may start with an HTML direction wrapper, not a heading."""
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    if not match:
        raise ValueError("The notebook needs a level-one scientific title")
    return clean(match.group(1))


def visual(text: str) -> str:
    # A numeric-only table cell is LTR, even inside an RTL table. In prose,
    # isolate dates/ranges so bidi does not reverse their component order.
    if not re.search(r"[\u0620-\u064a\u0671-\u06d3]", text):
        return get_display(text, base_dir="L")
    text = re.sub(r"[0-9]+(?:[./×%-][0-9]+)+", lambda m: "\u202a"+m.group()+"\u202c", text)
    return get_display(RESHAPER.reshape(text), base_dir="R")


class PersianText(Flowable):
    """Wrap logical text first, then shape/reorder each line independently."""

    def __init__(self, text, size=10, bold=False, color=INK, align="right", leading=None, anchor=None, link=None):
        super().__init__()
        self.text = clean(text)
        self.size, self.font = size, "FaBold" if bold else "Fa"
        self.color, self.align = color, align
        self.leading = leading or size * 1.65
        self.lines = []
        self.anchor, self.link = anchor, link
        self.spaceAfter = 6

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.lines = []
        for paragraph in self.text.split("\n"):
            line = ""
            for token in paragraph.split():
                trial = (line + " " + token).strip()
                if line and pdfmetrics.stringWidth(visual(trial), self.font, self.size) > availWidth:
                    self.lines.append(line)
                    line = token
                else:
                    line = trial
                # A long identifier must not spill outside a narrow table cell.
                while pdfmetrics.stringWidth(visual(line), self.font, self.size) > availWidth:
                    cut = len(line) - 1
                    while cut > 1 and pdfmetrics.stringWidth(visual(line[:cut]), self.font, self.size) > availWidth:
                        cut -= 1
                    self.lines.append(line[:cut])
                    line = line[cut:]
            self.lines.append(line)
        self.height = max(1, len(self.lines)) * self.leading
        return self.width, self.height

    def split(self, availWidth, availHeight):
        self.wrap(availWidth, availHeight)
        fit = math.floor(availHeight / self.leading)
        if fit < 2 or len(self.lines) - fit < 2:
            return []
        def part(lines):
            return PersianText("\n".join(lines), self.size, self.font == "FaBold", self.color, self.align, self.leading)
        return [part(self.lines[:fit]), part(self.lines[fit:])]

    def draw(self):
        c = self.canv
        if self.anchor:
            # Numbered pages are emitted in ReportCanvas.save. Resolve page
            # references there, otherwise every bookmark targets physical page 1.
            c._page_bookmarks.append((self.anchor, self.text))
        c.setFillColor(self.color)
        c.setFont(self.font, self.size)
        for i, line in enumerate(self.lines):
            text = visual(line)
            y = self.height - self.size - i * self.leading
            if self.align == "center":
                c.drawCentredString(self.width / 2, y, text)
            elif self.align == "left":
                c.drawString(0, y, text)
            else:
                c.drawRightString(self.width, y, text)
        if self.link:
            rectangle = (0, 0, self.width, self.height)
            if self.link.startswith("#"):
                c.linkRect("", self.link[1:], rectangle, relative=1, thickness=0)
            else:
                c.linkURL(self.link, rectangle, relative=1, thickness=0)


class ReportCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        kwargs["invariant"] = 1
        super().__init__(*args, **kwargs)
        self.states = []
        self.page_count = 0
        self._page_bookmarks = []

    def showPage(self):
        self.states.append(dict(self.__dict__))
        self._startPage()
        self._page_bookmarks = []

    def save(self):
        states = self.states
        total = len(states)
        for state in states:
            self.__dict__.update(state)
            for key, title in self._page_bookmarks:
                self.bookmarkPage(key)
                self.addOutlineEntry(title, key, level=0)
            self.setStrokeColor(colors.HexColor("#D8E3E6"))
            self.setLineWidth(.5)
            self.line(43, 38, A4[0]-43, 38)
            self.setFont("Fa", 8)
            self.setFillColor(MUTED)
            self.drawRightString(A4[0]-43, 23, visual("آمار توصیفی | فاز یک | مسیر ج، NACC"))
            self.drawString(43, 23, f"{self._pageNumber} / {total}")
            super().showPage()
        self.page_count = total
        super().save()


def markdown_table(text: str) -> list[list[str]]:
    return [[clean(c.strip()) for c in line.strip().strip("|").split("|")]
            for line in text.splitlines() if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line)]


def build_report(root: Path) -> dict:
    root = root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from src.phase1_dataset import load_dataset
    from src.phase1_figures import FIGURES, build_plot_bundle, captions

    people, manifest = load_dataset(root)
    _, plot = build_plot_bundle(root)
    audit = json.loads((root / "reports/phase1/quality_audit.json").read_text(encoding="utf-8"))
    stats = json.loads((root / "reports/phase1/descriptive_statistics.json").read_text(encoding="utf-8"))
    # This narrative targets the supplied cohort. Stop instead of silently
    # applying its fixed descriptions to a changed dataset or quality policy.
    expected = {"all_shared": 1237, "main_pair": 1228, "main_common": 1226,
                "integer_pair": 984, "integer_common": 982}
    profiles = {p["column"]: p for p in audit["profiles"]["UDS"]}
    if (stats["populations"] != expected or
            profiles["MOCATOTS"]["counts"].get("known_special", 0) != 4 or
            profiles["MOCATOTS"]["counts"].get("outside_reference_range", 0) != 5 or
            profiles["MOCATOTS"]["counts"].get("off_grid_in_range", 0) != 244 or
            profiles["EDUC"]["counts"].get("known_special", 0) != 2 or
            audit["event_totals"]["by_status"].get("nonpositive_measurement", 0) != 2):
        raise ValueError("The supplied cohort changed; review report narratives before rebuilding")
    book = json.loads((root / "notebooks/phase1.ipynb").read_text(encoding="utf-8"))
    code = [c for c in book["cells"] if c["cell_type"] == "code"]
    if [c.get("execution_count") for c in code] != list(range(1, len(code)+1)):
        raise ValueError("The report requires the fully executed notebook")
    if any(o["output_type"] == "error" or (o["output_type"] == "stream" and o.get("name") == "stderr") for c in code for o in c.get("outputs", [])):
        raise ValueError("Review notebook errors/stderr before building the report")
    verify_notebook_images(root)
    sources = report_inputs(root)
    md = ["".join(c["source"]) for c in book["cells"] if c["cell_type"] == "markdown"]
    cell = lambda anchor: next(t for t in md if f'id="{anchor}"' in t)
    title = notebook_title(md[0])
    question = next(l[2:] for l in cell("question").splitlines() if l.startswith("> "))
    for name, file in FONT_FILES.items():
        pdfmetrics.registerFont(TTFont(name, str(root / file)))
    story = []
    width = A4[0] - 86

    def p(text, **kw):
        story.append(PersianText(text, **kw))

    def h(text, anchor=None):
        p(text, size=15, bold=True, color=ACCENT, anchor=anchor)
        story.append(Spacer(1, 9))

    def page(title):
        story.append(PageBreak())
        h(title, anchor="section-"+str(len(section_titles)))
        section_titles.append(title)

    def table(headers, rows, widths=None, size=9):
        widths = widths or [width/len(headers)]*len(headers)
        data = [[PersianText(v, size=size, bold=True, color=colors.white, leading=size*1.5) for v in reversed(headers)]]
        data += [[PersianText(str(v), size=size, leading=size*1.55) for v in reversed(row)] for row in rows]
        t = Table(data, colWidths=list(reversed(widths)), repeatRows=1, hAlign="RIGHT")
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 6),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                               ("TOPPADDING", (0, 0), (-1, -1), 5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                               ("LINEBELOW", (0, 0), (-1, 0), .5, ACCENT)]))
        story.extend([t, Spacer(1, 10)])

    def num(value, digits=2):
        return "تعریف‌نشده" if value is None else f"{value:.{digits}f}"

    def overall(col, sample="all_shared", group=None):
        return next(r for r in stats["numeric"] if r["variable"] == col and r["sample"] == sample and r["stratum_code"] == group)

    section_titles = ["چکیده و سؤال اصلی"]
    h("گزارش فاز یک پروژهٔ آمار", anchor="section-0")
    p("مسیر ج | زیرمجموعهٔ تحویلی NACC | UDS + MRI", color=MUTED, size=10)
    story.append(Spacer(1, 18))
    p(title, size=18, bold=True, leading=31)
    story.append(Spacer(1, 16))
    p("نسخهٔ گزارش: " + REPORT_DATE, size=9, color=MUTED)
    h("سؤال اصلی")
    p(question)
    h("چکیده")
    mo, th = overall("MOCATOTS_ANALYSIS"), overall("ENTORHINAL_THICKNESS_MEAN")
    p(f"این بررسی مشاهده‌ای، شناخت ساختار و کیفیت زیرمجموعهٔ تحویلی NACC و توصیف متغیرهای منتخب دو وجه را پوشش می‌دهد. هر فایل {len(people)} فرد یکتا دارد و اتصال با NACCID یک‌به‌یک است. میانگین حسابی ضخامت انتورینال چپ و راست، ویژگی اصلی MRI با واحد میلی‌متر است. MoCA کاری برای {mo['n_usable']} فرد قابل استفاده است؛ میانگین {num(mo['mean'])} و میانه {num(mo['median'])} دارد. میانگین ضخامت برای {th['n_usable']} فرد، میانگین {num(th['mean'],3)} و میانه {num(th['median'],3)} میلی‌متر دارد.")
    p("مقایسهٔ چهار گروه شناختی توصیفی و تعدیل‌نشده است. آماده‌سازی اولیه، سابقهٔ مراجعه، تطبیق زمانی و QC تصویربرداری معلوم نیستند. این گزارش جهت یا اندازهٔ رابطهٔ فردی و تعدیل‌شده، معنی‌داری، علیت یا تغییر طولی را برآورد نمی‌کند.")
    table(["جمعیت خروجی", "تعداد"], [["افراد مشترک",len(people)], ["زوج اصلی",manifest['samples']['main_pair']['included']], ["مشترک اصلی با سه متغیر همراه",manifest['samples']['main_common']['included']], ["زوج حساسیت فقط صحیح‌ها",manifest['samples']['integer_pair']['included']], ["مشترک حساسیت فقط صحیح‌ها",manifest['samples']['integer_common']['included']]], [width*.76,width*.24])
    p("مجموعه‌های بالا هم‌پوشان‌اند و جمع نمی‌شوند. گزارش، نوت‌بوک و دادهٔ مشتق همراه یک نسخهٔ تحویلی‌اند؛ آماده‌بودن محلی رسید ارسال نیست.", size=9)
    contents_position = len(story)

    page("۱. منشأ، طراحی مطالعه و واحد مشاهده")
    design = cell("study-design")
    for line in design.split("### نقشهٔ دو وجه")[0].splitlines():
        if line.startswith("- "):
            p("• " + line[2:])
    table(["وجه / فایل", "ردیف × ستون", "واحد هر ردیف"], [
        ["UDS / udslong_imputed.csv","1237 × 180","رکورد بالینی و شناختی فرد"],
        ["MRI / mriscanclean.csv","1237 × 126","اندازه‌گیری‌های تصویربرداری فرد"],
        ["ماتریس نواحی","62 × 62 عددی","ناحیهٔ مغز؛ نه فرد یا مراجعه"]], [width*.43,width*.20,width*.37])
    table(["فایل", "رکورد فعلی برای هر فرد", "تعداد افراد", "مراجعه‌های واقعی در منبع"],
          [["UDS",1,len(people),"نامعلوم"],["MRI",1,len(people),"نامعلوم"]],
          [width*.15,width*.26,width*.17,width*.42])
    p("UDS در بیست دستهٔ جمعیت‌شناختی، پزشکی، عملکردی، شناختی، تشخیصی و سایر حوزه‌های مرتبط معرفی شده است. MRI شامل ۳۱ نام ناحیه، دو نیمکره و دو کمیت است: ۶۲ حجم با واحد mm³ و ۶۲ ضخامت با واحد mm، همراه شناسه و وضعیت شناختی. نقشهٔ کامل تمام ستون‌ها در docs/DATA_MAP.md همراه پروژه است.")
    p("ساختار تحویل برای هر فرد با NACCID، یک رکورد UDS و یک رکورد MRI است. تاریخچهٔ مراجعه‌های منبع، تاریخ اسکن و فاصلهٔ زمانی دو وجه موجود نیستند؛ شمار رکوردهای تحویلی توزیع مراجعه‌های واقعی را بازسازی نمی‌کند. در ادامه، هر فرد حداکثر یک واحد تحلیلی دارد.")
    p("معیار انتخاب زیرمجموعه و وزن جمعیتی تحویلی معلوم نیست. تحلیل بدون وزن، توصیف همین فایل است؛ تصادفی‌بودن نمونه، نمایندگی جامعه و شیوع عمومی ادعا نمی‌شود. ماتریس نواحی با MRI تطبیق داده شده، اما شبکهٔ اختصاصی افراد یا تحلیل شبکه برای سؤال فعلی تعریف نشده است.")

    page("۲. متغیرها، مقیاس و شاخص منتخب")
    selected = markdown_table((root/"docs/SELECTED_VARIABLES.md").read_text(encoding="utf-8").split("## ۲.")[1].split("### تفاوت")[0])
    table(["متغیر", "تعریف / واحد", "نوع و نقش"], [[r[0],r[1],r[2]+"؛ "+r[3]] for r in selected[1:]], [width*.29,width*.39,width*.32], size=8.1)
    p("فرمول از پیش انتخاب‌شده:", bold=True)
    p("ENTORHINAL_THICKNESS_MEAN = (LH_ENTORHINAL_AVGTH + RH_ENTORHINAL_AVGTH) / 2", size=8.6, align="left")
    p("هر دو ضخامت باید متعلق به همان فرد، متناهی و مثبت باشند. واحد mm باقی می‌ماند؛ حجم یا سطح قشر وارد فرمول نمی‌شود و یک طرف به‌تنهایی جانشین میانگین نیست. عبور از این کنترل عددی، تأیید QC تصویربرداری نیست.")
    p("وجود اعشار یا پسوند .0 در CSV، متغیر طبقه‌ای را پیوسته نمی‌کند. فاصلهٔ کدهای وضعیت شناختی یکسان فرض نمی‌شود و میانگین کد جنس یا شناسه گزارش نشده است. MoCA نمرهٔ محدود است؛ دو برابرشدن نمره، دو برابرشدن توان شناختی نیست.")

    page("۳. ممیزی کیفیت و قواعد استفاده")
    table(["فایل", "ردیف", "ستون", "شناسهٔ یکتا", "شناسهٔ تکراری", "خانهٔ خالی"], [[r['file'],r['rows'],r['columns'],r['unique_ids'],len(r['duplicate_ids']),r['empty_cells']] for r in audit['structures']], size=8)
    p("تمام ۱۸۰ ستون UDS و ۱۲۶ ستون MRI با قواعد صریح بررسی شده‌اند. کدهای ویژه، مقادیر ناممکن، اعشار ناسازگار با گام، تکرار و ناسازگاری منطقی ثبت شده‌اند. نبود خانهٔ خالی به معنی نبود گمشدگی کدگذاری‌شده یا گمشدگی پیش از جایگذاری نیست.")
    table(["مسئلهٔ منتخب", "شمار", "تصمیم و دلیل"], [
        ["MoCA = 88",4,"یک یا چند آیتم یا کل آزمون اجرا نشده؛ پاسخ کاری غیرقابل استفاده و خام/علت محفوظ"],
        ["MoCA دیگر بالاتر از ۳۰",5,"خارج از دامنه؛ بدون برش به سقف، گردکردن یا جایگذاری"],
        ["اعشار MoCA در دامنه",244,"حفظ با پرچم در اصلی؛ سناریوی فقط صحیح‌ها جداست؛ اصالت نامعلوم"],
        ["EDUC = 99",2,"نامعلوم در متغیر کاری؛ فرد از خلاصه‌های مستقل حذف نمی‌شود"],
        ["حجم MRI برابر صفر",2,"پرچم بازبینی در ستون خارج از شاخص؛ عامل حذف فرد از تحلیل ضخامت نیست"]], [width*.25,width*.10,width*.65])
    labels={"known_special":"کد ویژه یا مختلط مرجع","unlisted_code":"کد خارج از مجموعهٔ مرجع","off_grid_in_range":"خارج از گام ولی در دامنه","outside_reference_range":"خارج از دامنه","nonpositive_measurement":"اندازه‌گیری غیرمثبت MRI"}
    table(["وضعیت سلولی", "شمار"], [[labels.get(k,k),v] for k,v in audit['event_totals']['by_status'].items()], [width*.76,width*.24])
    p(f"در مجموع {audit['event_totals']['cells']} رویداد سلولی ثبت شده است. این شمار شامل کدهای ویژهٔ مجاز است و تعداد خطا، افراد مستقل یا گمشدگی اولیه نیست. فایل ردگیری، شناسه، ستون، خط منبع، مقدار خام و علت را نگه می‌دارد. هیچ CSV اولیه بازنویسی نمی‌شود.", size=9)

    page("۴. کنترل‌های منطقی و نقاط غیرعادی")
    logical_labels=["برابری CDR با شش جزء","جمع GDS با اجزای کامل","فشار سیستولیک بالاتر از دیاستولیک","سال مصرف دخانیات در برابر سن","سن ترک در برابر سن فعلی","سازگاری پرچم و شمار دارو","معاینهٔ عصبی با کدهای بی‌ابهام"]
    checks=audit['logical_checks']
    rows=[[logical_labels[i],r['evaluated'],r['not_evaluated'],r['flagged']] for i,r in enumerate(checks[:7])]
    table(["کنترل", "ارزیابی‌شده", "ارزیابی‌نشده", "پرچم"],rows,[width*.49,width*.17,width*.20,width*.14],size=9)
    p("دوازده کنترل علامت و شدت NPI-Q نیز انجام شده‌اند؛ شمار هر کنترل در صفحهٔ بعد آمده است. ناموجودی علامت یا شدت، قبولی فرض نشده است.",size=9.5)
    p("کنترل فقط برای ورودی قابل ارزیابی اعمال شده است؛ ارزیابی‌نشده قبولی نیست. ناسازگاری، علت یا مقدار صحیح را مشخص نمی‌کند و به بازنویسی خودکار یا حذف فرد منجر نشده است.",size=9)
    table(["متغیر", "پرچم IQR", "ارزیابی‌نشده"], [[r['variable'].replace('_ANALYSIS',''),r['flagged'],r['not_evaluated']] for r in stats['outlier_reviews']], [width*.60,width*.20,width*.20],size=9)
    p("حصارهای ۱٫۵ IQR فقط برای مرورند. بیرون حصار بودن با خطای ثبت، شکست QC یا اثرگذاری در مدل برابر نیست. حصار کل نمونه با حصار درون هر گروه تفاوت دارد؛ هیچ‌کدام قاعدهٔ حذف نیست.",size=9)

    page("۴.۲. کنترل سازگاری علائم و شدت NPI-Q")
    symptom_labels = ["هذیان", "توهم", "بی‌قراری/پرخاشگری", "افسردگی", "اضطراب", "سرخوشی", "بی‌تفاوتی", "مهارگسیختگی", "تحریک‌پذیری", "رفتار حرکتی", "رفتار شبانه", "اشتها/خوردن"]
    table(["علامت", "ارزیابی‌شده", "ارزیابی‌نشده", "پرچم"],
          [[label,r['evaluated'],r['not_evaluated'],r['flagged']] for label,r in zip(symptom_labels,checks[7:])],
          [width*.43,width*.20,width*.22,width*.15])
    p("در هر ردیف، نبود علامت باید با شدت نامرتبط و وجود علامت با شدت قابل استفاده سازگار باشد. این کنترل، آزمون فرض آماری یا تأیید تشخیص نیست؛ هیچ مقدار خامی بر اساس آن اصلاح نشده است.")

    page("۵. اتصال، جریان نمونه و گمشدگی")
    p("اتصال با NACCID، مستقل از ترتیب ردیف‌ها و به‌صورت یک‌به‌یک انجام شده است. هر فایل ۱۲۳۷ شناسهٔ یکتا، اشتراک ۱۲۳۷ و فقط UDS/فقط MRI صفر دارد. وضعیت شناختی برای تک‌تک شناسه‌ها برابر است؛ نسخهٔ UDS مرجع گروه‌بندی است.")
    table(["شاخه", "شروع", "کنارگذاری مرحله‌ای", "باقی‌مانده"],[
        ["زوج اصلی",1237,"۴ کد ویژه، سپس ۵ نمرهٔ دیگر خارج از دامنه؛ ضخامت هر دو طرف موجود",1228],
        ["مشترک اصلی",1228,"۲ تحصیلات نامعلوم؛ سن و جنس قابل استفاده",1226],
        ["زوج حساسیت",1228,"۲۴۴ اعشار درون دامنه؛ فقط در این سناریو",984],
        ["مشترک حساسیت",984,"۲ تحصیلات نامعلوم",982]], [width*.23,width*.12,width*.51,width*.14])
    p("هر شاخه از جمعیت والد خودش شروع می‌شود؛ تعدادهای شاخه‌ها جمع نمی‌شوند. علت‌ها ممکن است هم‌پوشان باشند، ولی در جریان مرحله‌ای فرد دوباره در جمع حذف‌ها شمرده نشده است.")
    cols=["MOCATOTS_ANALYSIS","NACCAGE_ANALYSIS","SEX_ANALYSIS","EDUC_ANALYSIS","NACCUDSD_ANALYSIS","LH_ENTORHINAL_AVGTH_ANALYSIS","RH_ENTORHINAL_AVGTH_ANALYSIS","ENTORHINAL_THICKNESS_MEAN"]
    labels=["MoCA","سن","جنس","تحصیلات","وضعیت شناختی","ضخامت چپ","ضخامت راست","میانگین ضخامت"]
    table(["متغیر کاری", "مخرج", "قابل استفاده", "غیرقابل استفاده", "درصد غیرقابل استفاده"],[[label,len(people),sum(r[c] is not None for r in people),sum(r[c] is None for r in people),num(100*sum(r[c] is None for r in people)/len(people),3)] for c,label in zip(cols,labels)],size=8)
    p("تمام افراد MRI دارند؛ بنابراین مقایسهٔ ویژگی‌های UDS بین دارای/فاقد MRI در همین تحویل انجام‌پذیر نیست. این محدودیت به معنی نبود سوگیری انتخاب نیست. گمشدگی قبل از جایگذاری و روش آن نیز از نسخهٔ فعلی بازیابی نمی‌شود.")

    page("۶. توصیف متغیرهای کمی و طبقه‌ای")
    vals=[r for r in stats['numeric'] if r['sample']=='all_shared']
    table(["متغیر / واحد","معتبر","کمینه","بیشینه","میانگین","میانه","SD"],
          [[r['label']+' / '+r['unit'],r['n_usable'],*[num(r[k],3 if r['unit']=='mm' else 2) for k in ['minimum','maximum','mean','median','sd_sample']]] for r in vals],
          [width*.28,*([width*.12]*6)],size=9)
    table(["متغیر / واحد","Q1","Q3","IQR","دامنه"],
          [[r['label']+' / '+r['unit'],*[num(r[k],3 if r['unit']=='mm' else 2) for k in ['q1','q3','iqr','range']]] for r in vals],
          [width*.36,*([width*.16]*4)],size=9)
    p("SD با مخرج n-1 و چارک‌ها با درون‌یابی خطی نوع ۷ محاسبه شده‌اند. میانگین/SD و میانه/IQR در کنار هم ارائه شده‌اند؛ نمرهٔ محدود MoCA، آماده‌سازی نامعلوم و نقاط غیرعادی در تفسیر باقی‌اند. گردکردن فقط نمایشی است.")
    p("میانگین و SD به مقادیر دور حساس‌اند؛ میانه و IQR خلاصه‌های مقاوم‌تری هستند. این شاخص‌ها برای سن، سال تحصیل و ضخامت با واحد خودشان تفسیر می‌شوند. برای جنس، وضعیت شناختی و شناسه میانگین محاسبه نشده است.")

    page("۶.۲. فراوانی طبقه‌ای و جزئیات نمره")
    cat=[r for r in stats['categorical'] if r['sample']=='all_shared' and r['stratum_code'] is None]
    table(["متغیر","طبقه","تعداد","درصد کل","درصد معتبر"],[["جنس" if r['variable']=='SEX_ANALYSIS' else "وضعیت شناختی",r['level_label'],r['count'],num(r['percent_of_population']),num(r['percent_of_available'])] for r in cat], [width*.21,width*.28,width*.13,width*.19,width*.19])
    p("درصد کل و درصد معتبر مخرج جدا دارند؛ درصد معتبر برای ردیف غیرقابل استفاده تعریف نشده است. جدول فراوانی دقیق MoCA، سن و تحصیلات در نوت‌بوک و خروجی مستقل موجود است؛ اعشار MoCA به نمرهٔ صحیح گرد نشده‌اند. تجمع فقط برای مقادیر معتبر انجام شده است.")
    score=next(r for r in stats['score_details'] if r['sample']=='all_shared')
    p(f"MoCA: {score['n_fractional']} مقدار اعشاری درون دامنه، {score['n_integer_valued']} صحیح‌مقدار، {score['n_at_zero']} مقدار صفر و {score['n_at_thirty']} مقدار ۳۰ دارد. شمار کران‌ها به‌تنهایی اثر کف یا سقف را اثبات نمی‌کند.")

    page("۷. مقایسهٔ توصیفی چهار گروه شناختی")
    groups=plot['groups']
    for col,label,unit in [('MOCATOTS_ANALYSIS','MoCA کاری','score'),('ENTORHINAL_THICKNESS_MEAN','میانگین ضخامت','mm')]:
        p(label+' / '+unit,bold=True)
        gs=[overall(col,'main_pair',g['code']) for g in groups]
        table(["گروه","n","میانگین","میانه","SD","IQR"],[[g['label_fa'],s['n_usable'],*[num(s[k],3 if unit=='mm' else 2) for k in ['mean','median','sd_sample','iqr']]] for g,s in zip(groups,gs)],[width*.32,*([width*.136]*5)],size=8)
    p("MoCA و MRI در هر گروه به افراد یکسان زوج اصلی مربوط‌اند. اندازهٔ گروه‌ها ۸۴۲، ۷، ۲۵۱ و ۱۲۸ است. گروه هفت‌نفره حفظ شده و با MCI ادغام نشده است؛ شاخص‌های آن به چند مشاهده وابسته‌اند.")
    table(["گروه","سن: میانگین","تحصیلات: میانگین / n","مرد: تعداد / درصد گروه"],[[g['label_fa'],num(overall('NACCAGE_ANALYSIS','main_pair',g['code'])['mean']),num(overall('EDUC_ANALYSIS','main_pair',g['code'])['mean'])+' / '+str(overall('EDUC_ANALYSIS','main_pair',g['code'])['n_usable']),str(next(r for r in stats['categorical'] if r['sample']=='main_pair' and r['stratum_code']==g['code'] and r['variable']=='SEX_ANALYSIS' and r['level_code']==1)['count'])+' / '+num(next(r for r in stats['categorical'] if r['sample']=='main_pair' and r['stratum_code']==g['code'] and r['variable']=='SEX_ANALYSIS' and r['level_code']==1)['percent_of_population'])+'%'] for g in groups],[width*.31,width*.21,width*.24,width*.24],size=8)
    p("مرکز نمره و ضخامت در گروه دمانس نسبت به طبیعی پایین‌تر است، اما دامنه‌ها و بخشی از بازه‌های میانی هم‌پوشانی دارند و هر چهار گروه روند یکنواخت نمی‌سازند. سن، جنس و تحصیلات گروه‌ها هم یکسان نیست. این تفاوت‌ها تعدیل نشده‌اند؛ رابطهٔ فردی یا اثر مستقل ضخامت، معنی‌داری و علت بیماری از آن‌ها نتیجه نمی‌شود.")

    figure_captions=captions(plot)
    for i,(name,label) in enumerate(FIGURES.items(),1):
        page(f"۸.{i}. {label}")
        from PIL import Image as PILImage
        with PILImage.open(root/f'reports/phase1/figures/{name}.png') as im:
            iw,ih=im.size
        story.append(Image(str(root/f'reports/phase1/figures/{name}.png'),width=width,height=width*ih/iw))
        story.append(Spacer(1,15))
        for paragraph in figure_captions[name].split('\n\n'):
            p(paragraph,size=9.5)

    limitations=markdown_table(cell('limitations'))[1:]
    if len(limitations)!=12:
        raise ValueError('Expected the twelve documented limitations; review the PDF layout/content')
    for i in range(2):
        page('۹. محدودیت‌ها و پیامدها'+(' - ادامه' if i else ''))
        p('اطلاعات ناموجود حل‌شده یا صفر فرض نشده‌اند. موارد زیر دامنهٔ تفسیر و ادامهٔ تحلیل را مشخص می‌کنند.',size=9.5)
        table(['محدودیت','شاهد / اطلاعات ناموجود','پیامد'],limitations[i*6:(i+1)*6],[width*.24,width*.34,width*.42],size=8.6)

    page('۱۰. سؤال نهایی، ادامه و بازتولید')
    p('سؤال و شاخص انتخاب‌شده حفظ شده‌اند؛ پاسخ و ویژگی MRI در سطح فرد قابل اتصال‌اند و تعدادهای قابل استفاده روشن شده‌اند. این کفایت ساختاری امکان ادامه را نشان می‌دهد؛ تأیید فرضیهٔ علمی یا اصالت تمام اندازه‌گیری‌ها نیست. فرضیهٔ اولیهٔ همراهی ضخامت بیشتر با MoCA بالاتر، انتظار پیش از تحلیل است و با اختلاف‌های گروهی تأیید نشده است.')
    p('در فازهای بعد سه مدل با پاسخ و افراد یکسان مقایسه می‌شوند: UDS-only شامل سن، جنس و تحصیلات؛ MRI-only شامل میانگین ضخامت؛ و مدل ترکیبی. نمونهٔ مشترک فعلی ۱۲۲۶ نفر در اصلی و ۹۸۲ نفر در حساسیت است. صورت آزمون، کدگذاری و بررسی فرض‌های مدل در فاز مربوط تعیین می‌شوند؛ هنوز مدلی برازش نشده است.')
    p('سناریوی فقط صحیح‌مقدار نسخهٔ قبل از جایگذاری را بازسازی نمی‌کند. خلاصهٔ توصیفی و ترکیب آن موجود است؛ پایداری رابطه یا ضرایب هنوز مقایسه نشده است. تغییر معنادار سؤال پس از فاز یک باید با تیم دستیاری هماهنگ شود. روش ثبت مرکزی در اطلاعات موجود اعلام نشده است.')
    h('بازتولید و مدارک همراه')
    p('نوت‌بوک دارای متن، کد، جدول‌ها و چهار تصویر ذخیره‌شده، مدرک تفصیلی همراه این گزارش است. با Python 3.11 یا جدیدتر و وابستگی‌های requirements.txt، از ریشهٔ پروژه:')
    p('python3 scripts/run_phase1_notebook.py',size=9,align='left')
    p('اجرای کامل، خروجی‌های علمی و سپس همین PDF و شناسنامهٔ آن را می‌سازد. ساخت جداگانهٔ PDF از خروجی‌های سازگار:')
    p('python3 scripts/build_phase1_pdf.py',size=9,align='left')
    h('منابع')
    p('داک درس: docs/amarpr.pdf، صفحات ۳ تا ۸ و ۱۸ تا ۲۰. تعریف متغیرها و شمارهٔ دقیق صفحات در docs/SELECTED_VARIABLES.md و قواعد در docs/QUALITY_RULES.md همراه پروژه است.',size=9)
    p('NACC UDS Researcher’s Data Dictionary',size=10,align='left',color=ACCENT,link='https://files.alz.washington.edu/documentation/uds3-rdd.pdf')
    p('NACC MRI Researcher’s Data Dictionary',size=10,align='left',color=ACCENT,link='https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf')
    p('منابع شمارها و تفسیر: نوت‌بوک اجراشده، گزارش‌های ممیزی، جریان، آمار توصیفی، شکل‌ها و جمع‌بندی در reports/phase1. تاریخ دریافت ۱۰ اکتبر و اطلاعات تحویل TA به نقل از دانشجوست؛ سال، نسخه و آماده‌سازی نامعلوم‌اند.',size=9)

    contents = [PageBreak(), PersianText('راهنمای بخش‌ها',size=15,bold=True,color=ACCENT,anchor='contents'), Spacer(1,16),
                PersianText('نام هر بخش پیوند فعال به صفحهٔ همان بخش است. نشانک‌های PDF نیز برای جابه‌جایی در دسترس‌اند.',size=10),Spacer(1,12)]
    for index, section_title in enumerate(section_titles):
        contents.append(PersianText(section_title,size=10.5,color=ACCENT,link=f'#section-{index}'))
    story[contents_position:contents_position] = contents
    out=root/REPORT_PATH
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=out.parent,prefix='.phase1-report-',suffix='.pdf',delete=False) as handle:
        temporary=Path(handle.name)
    try:
        doc=SimpleDocTemplate(str(temporary),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=43,bottomMargin=54,
                              title=title,author='Statistics project - NACC',subject='Phase one: descriptive study, UDS and MRI',pageCompression=1)
        doc.build(story,canvasmaker=ReportCanvas)
        pages=doc.canv.page_count
        if sources!=report_inputs(root):
            raise ValueError('A report source changed during PDF generation')
        os.replace(temporary,out)
    finally:
        temporary.unlink(missing_ok=True)
    meta={'schema_version':1,'report':REPORT_PATH,'report_date':REPORT_DATE,'language':'fa',
          'pages':pages,'pdf_sha256':digest(out),'sources':sources,
          'font_family':FONT_FAMILY,'font_files':FONT_FILES,
          'reportlab_version':REPORTLAB_VERSION,'source_policy':'Scientific notebook content excludes execution timing metadata; raw data and numerical results are unchanged by PDF generation.',
          'scope':'Persian scientific phase-one report; descriptive only; not a submission receipt.'}
    (root/MANIFEST_PATH).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {'report':REPORT_PATH,**verify_report(root)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    print(json.dumps(build_report(args.root),ensure_ascii=False))
