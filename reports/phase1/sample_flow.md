# اتصال و جریان نمونه — فاز یک

تمام شمارها از دادهٔ خام و قواعد مصوب بازتولید شده‌اند؛ فایل‌های خام تغییر نکرده‌اند. جدول مرجع همهٔ افراد مشترک را نگه می‌دارد و انتخاب هر خروجی با پرچم همان خروجی است.

## اتصال دو وجه

| مورد | تعداد |
|---|---:|
| ردیف UDS | 1237 |
| ردیف MRI | 1237 |
| افراد یکتای مشترک و جدول مرجع | 1237 |
| شناسهٔ فقط UDS | 0 |
| شناسهٔ فقط MRI | 0 |

اتصال یک‌به‌یک با NACCID است، نه موقعیت ردیف. NACCUDSD فردبه‌فرد به‌صورت عددی تطبیق داده شده و نسخهٔ UDS مرجع گروه‌بندی است؛ دو رشتهٔ خام برای ردگیری باقی‌اند. ماتریس نواحی به ردیف‌های افراد اضافه نشده است.

## مجموعه‌های قابل استفاده

| مجموعه | پرچم | داخل | خارج از این خروجی |
|---|---|---:|---:|
| main_pair | `MAIN_PAIR_ELIGIBLE` | 1228 | 9 |
| main_common | `MAIN_COMMON_SAMPLE_ELIGIBLE` | 1226 | 11 |
| integer_pair | `INTEGER_SENSITIVITY_PAIR_ELIGIBLE` | 984 | 253 |
| integer_common | `INTEGER_SENSITIVITY_COMMON_ELIGIBLE` | 982 | 255 |

مجموعه‌ها تو‌در‌تو و هم‌پوشان‌اند؛ شمار آن‌ها با هم جمع نمی‌شود. خارج‌بودن از یک خروجی، حذف از جدول مرجع یا تمام توصیف‌ها نیست. سناریوی حساسیت تعریف، شمار و خلاصهٔ توصیفی دارد؛ اثر یا مدل در آن هنوز مقایسه نشده است.

## جریان مرحله‌ای هر شاخه

هر شاخه از جمعیت والد نوشته‌شده آغاز می‌شود. تعداد کنارگذاشته‌شده بر اساس افراد باقی‌مانده در همان مرحله است؛ فرد چندمسئله‌ای دوباره در جمع حذف‌ها شمرده نمی‌شود.

| شاخه | والد | گام | شرط | پیش از شرط | کنارگذاشته | باقی‌مانده |
|---|---|---:|---|---:|---:|---:|
| main_pair | all_shared | 0 | شروع این شاخه؛ با شاخه‌های دیگر جمع نشود | 1237 | 0 | 1237 |
| main_pair | all_shared | 1 | کنارگذاشتن کدهای ویژهٔ پاسخ از این خروجی، نه از جدول مرجع | 1237 | 4 | 1233 |
| main_pair | all_shared | 2 | نیاز به MoCA داخل دامنه طبق سیاست اصلی، شامل اعشار | 1233 | 5 | 1228 |
| main_pair | all_shared | 3 | نیاز به هر دو ضخامت قابل استفاده برای میانگین | 1228 | 0 | 1228 |
| main_common | main_pair | 0 | شروع این شاخه؛ با شاخه‌های دیگر جمع نشود | 1228 | 0 | 1228 |
| main_common | main_pair | 1 | نیاز به مقدار قابل استفادهٔ NACCAGE | 1228 | 0 | 1228 |
| main_common | main_pair | 2 | نیاز به مقدار قابل استفادهٔ SEX | 1228 | 0 | 1228 |
| main_common | main_pair | 3 | نیاز به مقدار قابل استفادهٔ EDUC | 1228 | 2 | 1226 |
| integer_pair | main_pair | 0 | شروع این شاخه؛ با شاخه‌های دیگر جمع نشود | 1228 | 0 | 1228 |
| integer_pair | main_pair | 1 | فقط در سناریوی حساسیت، کنارگذاشتن اعشار درون دامنه | 1228 | 244 | 984 |
| integer_common | integer_pair | 0 | شروع این شاخه؛ با شاخه‌های دیگر جمع نشود | 984 | 0 | 984 |
| integer_common | integer_pair | 1 | نیاز به مقدار قابل استفادهٔ NACCAGE | 984 | 0 | 984 |
| integer_common | integer_pair | 2 | نیاز به مقدار قابل استفادهٔ SEX | 984 | 0 | 984 |
| integer_common | integer_pair | 3 | نیاز به مقدار قابل استفادهٔ EDUC | 984 | 2 | 982 |

## مخرج هر متغیر و خروجی

مخرجِ درصد ناموجودی، جمعیت همان ردیف جدول است. صفر ناموجودی در یک نمونهٔ کامل انتخاب‌شده، دلیل صفر بودن گمشدگی در ورودی یا پیش از جایگذاری نیست.

| مجموعه | متغیر کاری | جمعیت | قابل استفاده | غیرقابل استفاده | درصد غیرقابل استفاده |
|---|---|---:|---:|---:|---:|
| all_shared | `MOCATOTS_ANALYSIS` | 1237 | 1228 | 9 | 0.728 |
| all_shared | `NACCAGE_ANALYSIS` | 1237 | 1237 | 0 | 0.000 |
| all_shared | `SEX_ANALYSIS` | 1237 | 1237 | 0 | 0.000 |
| all_shared | `EDUC_ANALYSIS` | 1237 | 1235 | 2 | 0.162 |
| all_shared | `NACCUDSD_ANALYSIS` | 1237 | 1237 | 0 | 0.000 |
| all_shared | `LH_ENTORHINAL_AVGTH_ANALYSIS` | 1237 | 1237 | 0 | 0.000 |
| all_shared | `RH_ENTORHINAL_AVGTH_ANALYSIS` | 1237 | 1237 | 0 | 0.000 |
| all_shared | `ENTORHINAL_THICKNESS_MEAN` | 1237 | 1237 | 0 | 0.000 |
| main_pair | `MOCATOTS_ANALYSIS` | 1228 | 1228 | 0 | 0.000 |
| main_pair | `NACCAGE_ANALYSIS` | 1228 | 1228 | 0 | 0.000 |
| main_pair | `SEX_ANALYSIS` | 1228 | 1228 | 0 | 0.000 |
| main_pair | `EDUC_ANALYSIS` | 1228 | 1226 | 2 | 0.163 |
| main_pair | `NACCUDSD_ANALYSIS` | 1228 | 1228 | 0 | 0.000 |
| main_pair | `LH_ENTORHINAL_AVGTH_ANALYSIS` | 1228 | 1228 | 0 | 0.000 |
| main_pair | `RH_ENTORHINAL_AVGTH_ANALYSIS` | 1228 | 1228 | 0 | 0.000 |
| main_pair | `ENTORHINAL_THICKNESS_MEAN` | 1228 | 1228 | 0 | 0.000 |
| main_common | `MOCATOTS_ANALYSIS` | 1226 | 1226 | 0 | 0.000 |
| main_common | `NACCAGE_ANALYSIS` | 1226 | 1226 | 0 | 0.000 |
| main_common | `SEX_ANALYSIS` | 1226 | 1226 | 0 | 0.000 |
| main_common | `EDUC_ANALYSIS` | 1226 | 1226 | 0 | 0.000 |
| main_common | `NACCUDSD_ANALYSIS` | 1226 | 1226 | 0 | 0.000 |
| main_common | `LH_ENTORHINAL_AVGTH_ANALYSIS` | 1226 | 1226 | 0 | 0.000 |
| main_common | `RH_ENTORHINAL_AVGTH_ANALYSIS` | 1226 | 1226 | 0 | 0.000 |
| main_common | `ENTORHINAL_THICKNESS_MEAN` | 1226 | 1226 | 0 | 0.000 |
| integer_pair | `MOCATOTS_ANALYSIS` | 984 | 984 | 0 | 0.000 |
| integer_pair | `NACCAGE_ANALYSIS` | 984 | 984 | 0 | 0.000 |
| integer_pair | `SEX_ANALYSIS` | 984 | 984 | 0 | 0.000 |
| integer_pair | `EDUC_ANALYSIS` | 984 | 982 | 2 | 0.203 |
| integer_pair | `NACCUDSD_ANALYSIS` | 984 | 984 | 0 | 0.000 |
| integer_pair | `LH_ENTORHINAL_AVGTH_ANALYSIS` | 984 | 984 | 0 | 0.000 |
| integer_pair | `RH_ENTORHINAL_AVGTH_ANALYSIS` | 984 | 984 | 0 | 0.000 |
| integer_pair | `ENTORHINAL_THICKNESS_MEAN` | 984 | 984 | 0 | 0.000 |
| integer_common | `MOCATOTS_ANALYSIS` | 982 | 982 | 0 | 0.000 |
| integer_common | `NACCAGE_ANALYSIS` | 982 | 982 | 0 | 0.000 |
| integer_common | `SEX_ANALYSIS` | 982 | 982 | 0 | 0.000 |
| integer_common | `EDUC_ANALYSIS` | 982 | 982 | 0 | 0.000 |
| integer_common | `NACCUDSD_ANALYSIS` | 982 | 982 | 0 | 0.000 |
| integer_common | `LH_ENTORHINAL_AVGTH_ANALYSIS` | 982 | 982 | 0 | 0.000 |
| integer_common | `RH_ENTORHINAL_AVGTH_ANALYSIS` | 982 | 982 | 0 | 0.000 |
| integer_common | `ENTORHINAL_THICKNESS_MEAN` | 982 | 982 | 0 | 0.000 |

## علت‌های عدم عضویت

این جدول علت‌ها را بر اساس همهٔ افراد جدول مرجع می‌شمارد. یک فرد می‌تواند چند علت داشته باشد؛ جمع علت‌ها لزوماً تعداد افراد خارج از خروجی نیست. جدول جریان بالا، شمار بدون دوباره‌شماری را می‌دهد.

| مجموعه | علت | تعداد افراد با این علت |
|---|---|---:|
| main_pair | `MOCA:known_special:test_not_administered` | 4 |
| main_pair | `MOCA:outside_reference_range` | 5 |
| main_common | `EDUC:known_special:unknown` | 2 |
| main_common | `MOCA:known_special:test_not_administered` | 4 |
| main_common | `MOCA:outside_reference_range` | 5 |
| integer_pair | `MOCA:fractional_in_range` | 244 |
| integer_pair | `MOCA:known_special:test_not_administered` | 4 |
| integer_pair | `MOCA:outside_reference_range` | 5 |
| integer_common | `EDUC:known_special:unknown` | 2 |
| integer_common | `MOCA:fractional_in_range` | 244 |
| integer_common | `MOCA:known_special:test_not_administered` | 4 |
| integer_common | `MOCA:outside_reference_range` | 5 |

## قرارداد ذخیره و بازخوانی

- [جدول مرجع افراد](../../data/processed/phase1_participants.csv): مقدار خام منتخب، مقدار کاری، علت، پرچم عضویت، پرچم IQR و شمارهٔ خط هر منبع.
- [شناسنامهٔ قابل بررسی](../../data/processed/phase1_manifest.json): نوع تمام ستون‌ها، واحد، قرارداد ناموجودی، اثر انگشت ورودی/کد/قواعد/خروجی و شمار و اثر انگشت شناسه‌های هر مجموعه.
- [جریان CSV](sample_flow.csv) و [مخرج‌ها CSV](denominators.csv): جدول‌های میانی بازتولیدپذیر برای گزارش و نوت‌بوک.
- پرچم‌ها در CSV با ۱ و ۰ ذخیره می‌شوند. خانهٔ خالی در متغیر کاریِ nullable یعنی ناموجود؛ پرچم IQR خالی یعنی ارزیابی نشده، نه False. علتِ خالی یعنی برای آن خروجی علت عدم عضویت وجود ندارد.
- رشته‌های خام بدون اصلاح حفظ شده‌اند. اعداد کاری با نمایش قابل بازخوانیِ بدون گردکردن ذخیره شده‌اند؛ خوانندهٔ پروژه انواع را از شناسنامه بازمی‌گرداند.
- بازخوانی و مقایسهٔ تمام ردیف‌ها با دادهٔ حافظه انجام شده است؛ صفر، مقدار ناموجود و False از هم جدا می‌مانند.
- اصلِ نامعلوم‌بودن جایگذاری، مراجعه و QC باقی است؛ ذخیرهٔ داده این اطلاعات را ایجاد نمی‌کند.
- گروه فاقد MRI در فایل تحویلی وجود ندارد؛ بنابراین مقایسهٔ انتخاب چندوجهی با افراد فاقد MRI قابل انجام نیست.
- میانگین کدهای گروه یا جنس، مدل، ضریب همبستگی و آزمون در این مرحله محاسبه نشده‌اند؛ نمودارهای توصیفی در گزارش شکل‌ها موجودند.

## پیوندها

[قواعد کیفیت](../../docs/QUALITY_RULES.md) · [راهنمای داده](../../data/README.md) · [نوت‌بوک](../../notebooks/phase1.ipynb) · [ممیزی](quality_audit.md)
