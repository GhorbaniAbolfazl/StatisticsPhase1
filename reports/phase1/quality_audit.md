# گزارش ممیزی کیفیت — فاز یک

این گزارش با کد ممیزی از فایل‌های اولیه ساخته شده است. سازگاری با مرجع، QC بالینی یا اصالت نمره را اثبات نمی‌کند. دادهٔ خام تغییر نکرده است.

قواعد: [QUALITY_RULES.md](../../docs/QUALITY_RULES.md). نوت‌بوک: [phase1.ipynb](../../notebooks/phase1.ipynb).

## ساختار و پوشش

| فایل | ردیف | ستون | شناسهٔ یکتا | شناسهٔ تکراری | خانهٔ خالی |
|---|---:|---:|---:|---:|---:|
| UDS | 1237 | 180 | 1237 | 0 | 0 |
| MRI | 1237 | 126 | 1237 | 0 | 0 |

هر ۱۸۰ ستون UDS و هر ۱۲۶ ستون MRI قاعدهٔ صریح دارد. برای MRI، سازگاری عددی فقط متناهی و مثبت بودن را نشان می‌دهد؛ حد بالای بالینی دلخواه اعمال نشده است.

## قابلیت استفادهٔ متغیرهای اصلی

| مجموعهٔ خروجی | تعداد |
|---|---:|
| MoCA قابل استفاده در تحلیل اصلی | 1228 |
| اعشار درون دامنهٔ نگهداری‌شده با پرچم | 244 |
| میانگین ضخامت قابل محاسبه با هر دو طرف | 1237 |
| زوج MoCA و ضخامت برای تحلیل اصلی | 1228 |
| نمونهٔ مشترک با سن، جنس و تحصیلات قابل استفاده | 1226 |
| زوج‌ها در سناریوی حساسیت فقط صحیح‌ها | 984 |
| نمونهٔ مشترک در سناریوی حساسیت فقط صحیح‌ها | 982 |

این‌ها مجموعه‌های متداخل برای خروجی‌های متفاوت‌اند و نباید با هم جمع شوند. این ممیزی خودش دادهٔ تحلیلی نهایی صادر نمی‌کند؛ اتصال ذخیره‌شده و مخرج خروجی‌ها در [گزارش جریان نمونه](sample_flow.md) مستند می‌شوند. فرد از تمام خلاصه‌ها حذف نمی‌شود.

## کنترل‌های منطقی

فقط ردیف دارای ورودی قابل ارزیابی بررسی شده است. ردیف ارزیابی‌نشده به معنی قبولی نیست. پرچم‌ها موجب بازنویسی، جمع‌زدن دوبارهٔ نمره یا حذف فرد نشده‌اند.

| کنترل | ارزیابی‌شده | ارزیابی‌نشده | پرچم بازبینی |
|---|---:|---:|---:|
| `CDRSUM_equals_six_boxes` | 1237 | 0 | 0 |
| `GDS_complete_items_sum` | 1197 | 40 | 0 |
| `systolic_exceeds_diastolic` | 1081 | 156 | 0 |
| `smoking_years_not_above_age` | 1196 | 41 | 0 |
| `quit_age_not_above_current_age` | 395 | 842 | 0 |
| `medications_flag_matches_nonzero_count` | 1235 | 2 | 0 |
| `neurological_summary_unambiguous_codes` | 884 | 353 | 16 |
| `DEL_severity_skip` | 1220 | 17 | 0 |
| `HALL_severity_skip` | 1235 | 2 | 0 |
| `AGIT_severity_skip` | 1182 | 55 | 0 |
| `DEPD_severity_skip` | 1177 | 60 | 0 |
| `ANX_severity_skip` | 1182 | 55 | 0 |
| `ELAT_severity_skip` | 1220 | 17 | 0 |
| `APA_severity_skip` | 1210 | 27 | 0 |
| `DISN_severity_skip` | 1210 | 27 | 0 |
| `IRR_severity_skip` | 1179 | 58 | 0 |
| `MOT_severity_skip` | 1233 | 4 | 0 |
| `NITE_severity_skip` | 1191 | 46 | 0 |
| `APP_severity_skip` | 1197 | 40 | 0 |

تعریف و منبع هر کنترل، مقادیر ردیف‌های پرچم‌خورده و شرایط ارزیابی در JSON و کد ثبت است. وضعیت شناختی با CDRGLOB معادل فرض نشده و BMI از قد/وزن گرد‌شده برای اصلاح خودکار بازسازی نشده است.

## مرور نقاط دورافتاده

چارک‌ها با روش inclusive/linear (type 7) و حصار ۱٫۵ IQR، فقط روی مقادیر قابل استفادهٔ همان متغیر محاسبه شده‌اند. خارج حصار بودن خطای ثبت یا مجوز حذف نیست. تمام این مقدارها نگهداری شده‌اند.

| متغیر | تعداد بررسی‌شده | تعداد خارج حصار |
|---|---:|---:|
| `MOCATOTS_ANALYSIS` | 1228 | 76 |
| `NACCAGE_ANALYSIS` | 1237 | 13 |
| `EDUC_ANALYSIS` | 1235 | 12 |
| `ENTORHINAL_THICKNESS_MEAN` | 1237 | 22 |
| `LH_CAUDALANTERIORCINGULATE_GVOL` | 1237 | 15 |
| `RH_CAUDALANTERIORCINGULATE_GVOL` | 1237 | 19 |
| `LH_CAUDALANTERIORCINGULATE_AVGTH` | 1237 | 28 |
| `RH_CAUDALANTERIORCINGULATE_AVGTH` | 1237 | 28 |
| `LH_CAUDALMIDDLEFRONTAL_GVOL` | 1237 | 24 |
| `RH_CAUDALMIDDLEFRONTAL_GVOL` | 1237 | 27 |
| `LH_CAUDALMIDDLEFRONTAL_AVGTH` | 1237 | 39 |
| `RH_CAUDALMIDDLEFRONTAL_AVGTH` | 1237 | 30 |
| `LH_CUNEUS_GVOL` | 1237 | 16 |
| `RH_CUNEUS_GVOL` | 1237 | 25 |
| `LH_CUNEUS_AVGTH` | 1237 | 25 |
| `RH_CUNEUS_AVGTH` | 1237 | 16 |
| `LH_ENTORHINAL_GVOL` | 1236 | 31 |
| `RH_ENTORHINAL_GVOL` | 1237 | 35 |
| `LH_ENTORHINAL_AVGTH` | 1237 | 28 |
| `RH_ENTORHINAL_AVGTH` | 1237 | 30 |
| `LH_FUSIFORM_GVOL` | 1237 | 35 |
| `RH_FUSIFORM_GVOL` | 1237 | 33 |
| `LH_FUSIFORM_AVGTH` | 1237 | 50 |
| `RH_FUSIFORM_AVGTH` | 1237 | 60 |
| `LH_INFERIORPARIETAL_GVOL` | 1237 | 25 |
| `RH_INFERIORPARIETAL_GVOL` | 1237 | 38 |
| `LH_INFERIORPARIETAL_AVGTH` | 1237 | 46 |
| `RH_INFERIORPARIETAL_AVGTH` | 1237 | 51 |
| `LH_INFERIORTEMPORAL_GVOL` | 1237 | 29 |
| `RH_INFERIORTEMPORAL_GVOL` | 1237 | 29 |
| `LH_INFERIORTEMPORAL_AVGTH` | 1237 | 42 |
| `RH_INFERIORTEMPORAL_AVGTH` | 1237 | 37 |
| `LH_ISTHMUSCINGULATE_GVOL` | 1237 | 30 |
| `RH_ISTHMUSCINGULATE_GVOL` | 1237 | 26 |
| `LH_ISTHMUSCINGULATE_AVGTH` | 1237 | 17 |
| `RH_ISTHMUSCINGULATE_AVGTH` | 1237 | 23 |
| `LH_LATERALOCCIPITAL_GVOL` | 1237 | 25 |
| `RH_LATERALOCCIPITAL_GVOL` | 1237 | 18 |
| `LH_LATERALOCCIPITAL_AVGTH` | 1237 | 21 |
| `RH_LATERALOCCIPITAL_AVGTH` | 1237 | 29 |
| `LH_LATERALORBITOFRONTAL_GVOL` | 1237 | 22 |
| `RH_LATERALORBITOFRONTAL_GVOL` | 1237 | 19 |
| `LH_LATERALORBITOFRONTAL_AVGTH` | 1237 | 23 |
| `RH_LATERALORBITOFRONTAL_AVGTH` | 1237 | 22 |
| `LH_LINGUAL_GVOL` | 1237 | 22 |
| `RH_LINGUAL_GVOL` | 1237 | 38 |
| `LH_LINGUAL_AVGTH` | 1237 | 11 |
| `RH_LINGUAL_AVGTH` | 1237 | 16 |
| `LH_MEDIALORBITOFRONTAL_GVOL` | 1237 | 26 |
| `RH_MEDIALORBITOFRONTAL_GVOL` | 1237 | 22 |
| `LH_MEDIALORBITOFRONTAL_AVGTH` | 1237 | 44 |
| `RH_MEDIALORBITOFRONTAL_AVGTH` | 1237 | 38 |
| `LH_MIDDLETEMPORAL_GVOL` | 1237 | 30 |
| `RH_MIDDLETEMPORAL_GVOL` | 1237 | 25 |
| `LH_MIDDLETEMPORAL_AVGTH` | 1237 | 46 |
| `RH_MIDDLETEMPORAL_AVGTH` | 1237 | 37 |
| `LH_PARAHIPPOCAMPAL_GVOL` | 1237 | 26 |
| `RH_PARAHIPPOCAMPAL_GVOL` | 1237 | 25 |
| `LH_PARAHIPPOCAMPAL_AVGTH` | 1237 | 10 |
| `RH_PARAHIPPOCAMPAL_AVGTH` | 1237 | 17 |
| `LH_PARACENTRAL_GVOL` | 1237 | 24 |
| `RH_PARACENTRAL_GVOL` | 1237 | 28 |
| `LH_PARACENTRAL_AVGTH` | 1237 | 34 |
| `RH_PARACENTRAL_AVGTH` | 1237 | 36 |
| `LH_PARSOPERCULARIS_GVOL` | 1237 | 34 |
| `RH_PARSOPERCULARIS_GVOL` | 1237 | 37 |
| `LH_PARSOPERCULARIS_AVGTH` | 1237 | 23 |
| `RH_PARSOPERCULARIS_AVGTH` | 1237 | 26 |
| `LH_PARSORBITALIS_GVOL` | 1237 | 26 |
| `RH_PARSORBITALIS_GVOL` | 1237 | 24 |
| `LH_PARSORBITALIS_AVGTH` | 1237 | 20 |
| `RH_PARSORBITALIS_AVGTH` | 1237 | 26 |
| `LH_PARSTRIANGULARIS_GVOL` | 1237 | 37 |
| `RH_PARSTRIANGULARIS_GVOL` | 1237 | 44 |
| `LH_PARSTRIANGULARIS_AVGTH` | 1237 | 15 |
| `RH_PARSTRIANGULARIS_AVGTH` | 1237 | 26 |
| `LH_PERICALCARINE_GVOL` | 1237 | 13 |
| `RH_PERICALCARINE_GVOL` | 1237 | 24 |
| `LH_PERICALCARINE_AVGTH` | 1237 | 20 |
| `RH_PERICALCARINE_AVGTH` | 1237 | 14 |
| `LH_POSTCENTRAL_GVOL` | 1237 | 24 |
| `RH_POSTCENTRAL_GVOL` | 1237 | 19 |
| `LH_POSTCENTRAL_AVGTH` | 1237 | 12 |
| `RH_POSTCENTRAL_AVGTH` | 1237 | 23 |
| `LH_POSTERIORCINGULATE_GVOL` | 1236 | 30 |
| `RH_POSTERIORCINGULATE_GVOL` | 1237 | 39 |
| `LH_POSTERIORCINGULATE_AVGTH` | 1237 | 24 |
| `RH_POSTERIORCINGULATE_AVGTH` | 1237 | 26 |
| `LH_PRECENTRAL_GVOL` | 1237 | 18 |
| `RH_PRECENTRAL_GVOL` | 1237 | 26 |
| `LH_PRECENTRAL_AVGTH` | 1237 | 35 |
| `RH_PRECENTRAL_AVGTH` | 1237 | 33 |
| `LH_PRECUNEUS_GVOL` | 1237 | 33 |
| `RH_PRECUNEUS_GVOL` | 1237 | 28 |
| `LH_PRECUNEUS_AVGTH` | 1237 | 33 |
| `RH_PRECUNEUS_AVGTH` | 1237 | 36 |
| `LH_ROSTRALANTERIORCINGULATE_GVOL` | 1237 | 13 |
| `RH_ROSTRALANTERIORCINGULATE_GVOL` | 1237 | 15 |
| `LH_ROSTRALANTERIORCINGULATE_AVGTH` | 1237 | 22 |
| `RH_ROSTRALANTERIORCINGULATE_AVGTH` | 1237 | 33 |
| `LH_ROSTRALMIDDLEFRONTAL_GVOL` | 1237 | 35 |
| `RH_ROSTRALMIDDLEFRONTAL_GVOL` | 1237 | 33 |
| `LH_ROSTRALMIDDLEFRONTAL_AVGTH` | 1237 | 19 |
| `RH_ROSTRALMIDDLEFRONTAL_AVGTH` | 1237 | 28 |
| `LH_SUPERIORFRONTAL_GVOL` | 1237 | 25 |
| `RH_SUPERIORFRONTAL_GVOL` | 1237 | 26 |
| `LH_SUPERIORFRONTAL_AVGTH` | 1237 | 22 |
| `RH_SUPERIORFRONTAL_AVGTH` | 1237 | 22 |
| `LH_SUPERIORPARIETAL_GVOL` | 1237 | 25 |
| `RH_SUPERIORPARIETAL_GVOL` | 1237 | 15 |
| `LH_SUPERIORPARIETAL_AVGTH` | 1237 | 43 |
| `RH_SUPERIORPARIETAL_AVGTH` | 1237 | 38 |
| `LH_SUPERIORTEMPORAL_GVOL` | 1237 | 20 |
| `RH_SUPERIORTEMPORAL_GVOL` | 1237 | 32 |
| `LH_SUPERIORTEMPORAL_AVGTH` | 1237 | 29 |
| `RH_SUPERIORTEMPORAL_AVGTH` | 1237 | 34 |
| `LH_SUPRAMARGINAL_GVOL` | 1237 | 27 |
| `RH_SUPRAMARGINAL_GVOL` | 1237 | 23 |
| `LH_SUPRAMARGINAL_AVGTH` | 1237 | 34 |
| `RH_SUPRAMARGINAL_AVGTH` | 1237 | 32 |
| `LH_TRANSVERSETEMPORAL_GVOL` | 1237 | 34 |
| `RH_TRANSVERSETEMPORAL_GVOL` | 1237 | 39 |
| `LH_TRANSVERSETEMPORAL_AVGTH` | 1237 | 27 |
| `RH_TRANSVERSETEMPORAL_AVGTH` | 1237 | 25 |
| `LH_INSULA_GVOL` | 1237 | 21 |
| `RH_INSULA_GVOL` | 1237 | 26 |
| `LH_INSULA_AVGTH` | 1237 | 24 |
| `RH_INSULA_AVGTH` | 1237 | 24 |

## ممیزی ستون به ستون

دسته‌های وضعیت در هر ردیف این جدول انحصاری‌اند و جمعشان برابر تعداد ورودی است. کد ویژه می‌تواند نامرتبط، پاسخ‌نداده، نامعلوم، فرم جایگزین یا دستهٔ مختلط باشد؛ همهٔ آن‌ها یک نوع گمشدگی نیستند.

### UDS

| ستون | سازگار با قاعده | کد ویژه/مختلط | ابهام مستندات | ناسازگاری/گمشدگی دیگر | منبع |
|---|---:|---:|---:|---:|---|
| `NACCID` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=41) |
| `SEX` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=49) |
| `HISPANIC` | 1228 | 9 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=49) |
| `HISPOR` | 76 | 1161 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=50) |
| `RACE` | 1234 | 3 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=50) |
| `PRIMLANG` | 1236 | 1 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=52) |
| `EDUC` | 1235 | 2 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=53) |
| `MARISTAT` | 1234 | 3 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=53) |
| `NACCLIVS` | 1234 | 3 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=54) |
| `INDEPEND` | 1235 | 2 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=54) |
| `RESIDENC` | 1235 | 2 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=54) |
| `NACCNIHR` | 1225 | 12 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=56) |
| `NACCAGE` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=55) |
| `NACCFAM` | 1115 | 117 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=65) |
| `NACCMOM` | 1232 | 0 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=67) |
| `NACCDAD` | 1235 | 1 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=68) |
| `NACCAM` | 402 | 830 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=70) |
| `NACCAMS` | 8 | 1206 | 0 | 23 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=70) |
| `NACCFM` | 413 | 818 | 0 | 6 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=71) |
| `NACCFMS` | 1 | 1236 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=72) |
| `NACCOM` | 419 | 812 | 0 | 6 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=73) |
| `NACCOMS` | 0 | 1237 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=73) |
| `NACCFADM` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=69) |
| `NACCFFTD` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=71) |
| `ANYMEDS` | 1236 | 0 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=75) |
| `TOBAC30` | 1227 | 5 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=97) |
| `TOBAC100` | 1200 | 13 | 0 | 24 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=97) |
| `SMOKYRS` | 1196 | 22 | 0 | 19 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=97) |
| `PACKSPER` | 1186 | 28 | 0 | 23 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=98) |
| `QUITSMOK` | 395 | 818 | 0 | 24 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=98) |
| `CVHATT` | 1229 | 3 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=100) |
| `CVAFIB` | 1227 | 5 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=101) |
| `CVANGIO` | 1232 | 2 | 0 | 3 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=101) |
| `CVBYPASS` | 1234 | 2 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=101) |
| `CVPACDEF` | 1235 | 2 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=102) |
| `CVCHF` | 1233 | 4 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=102) |
| `CVOTHR` | 1229 | 4 | 0 | 4 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=103) |
| `CBSTROKE` | 1231 | 3 | 0 | 3 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=104) |
| `CBTIA` | 1225 | 10 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=105) |
| `SEIZURES` | 1232 | 5 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=107) |
| `NACCTBI` | 1204 | 14 | 0 | 19 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=123) |
| `TBI` | 1063 | 10 | 0 | 164 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=108) |
| `TBIBRIEF` | 1133 | 7 | 0 | 97 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=108) |
| `TBIEXTEN` | 1160 | 11 | 0 | 66 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=109) |
| `TBIWOLOS` | 1144 | 6 | 0 | 87 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=110) |
| `DIABETES` | 1217 | 8 | 0 | 12 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=111) |
| `DIABTYPE` | 106 | 1119 | 0 | 12 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=112) |
| `HYPERTEN` | 1204 | 11 | 0 | 22 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=112) |
| `HYPERCHO` | 1198 | 14 | 0 | 25 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=113) |
| `B12DEF` | 1154 | 69 | 0 | 14 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=113) |
| `THYROID` | 1203 | 20 | 0 | 14 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=114) |
| `ARTHRIT` | 980 | 10 | 0 | 247 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=114) |
| `ARTHTYPE` | 451 | 538 | 0 | 248 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=114) |
| `ARTHUPEX` | 995 | 10 | 0 | 232 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=115) |
| `ARTHLOEX` | 1008 | 10 | 0 | 219 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=115) |
| `ARTHSPIN` | 1040 | 10 | 0 | 187 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=116) |
| `ARTHUNK` | 1210 | 10 | 0 | 17 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=116) |
| `INCONTU` | 1224 | 2 | 0 | 11 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=116) |
| `INCONTF` | 1230 | 2 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=117) |
| `APNEA` | 1024 | 39 | 0 | 174 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=117) |
| `RBD` | 1155 | 34 | 0 | 48 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=117) |
| `INSOMN` | 1087 | 6 | 0 | 144 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=118) |
| `OTHSLEEP` | 1176 | 13 | 0 | 48 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=118) |
| `ALCOHOL` | 1230 | 4 | 0 | 3 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=119) |
| `ABUSOTHR` | 1234 | 3 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=119) |
| `PTSD` | 1195 | 4 | 0 | 38 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=120) |
| `BIPOLAR` | 1228 | 2 | 0 | 7 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=120) |
| `SCHIZ` | 1229 | 1 | 0 | 7 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=120) |
| `DEP2YRS` | 1206 | 15 | 0 | 16 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=121) |
| `DEPOTHR` | 1197 | 22 | 0 | 18 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=121) |
| `ANXIETY` | 1075 | 9 | 0 | 153 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=121) |
| `OCD` | 1219 | 6 | 0 | 12 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=122) |
| `NPSYDEV` | 1189 | 7 | 0 | 41 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=122) |
| `PSYCDIS` | 1233 | 3 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=122) |
| `NACCAAAS` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=78) |
| `NACCAANX` | 1236 | 0 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=91) |
| `NACCAC` | 1235 | 0 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=87) |
| `NACCACEI` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=77) |
| `NACCADEP` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=89) |
| `NACCAHTN` | 1235 | 0 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=75) |
| `NACCAMD` | 1235 | 0 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=75) |
| `NACCANGI` | 1235 | 0 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=82) |
| `NACCAPSY` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=90) |
| `NACCBETA` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=79) |
| `NACCCCBS` | 1235 | 0 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=80) |
| `NACCDBMD` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=95) |
| `NACCDIUR` | 1235 | 0 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=81) |
| `NACCEMD` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=94) |
| `NACCEPMD` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=94) |
| `NACCHTNC` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=76) |
| `NACCLIPL` | 1235 | 0 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=83) |
| `NACCNSD` | 1235 | 0 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=84) |
| `NACCPDMD` | 1236 | 0 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=93) |
| `NACCVASD` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=82) |
| `HEIGHT` | 1137 | 100 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=124) |
| `WEIGHT` | 1114 | 97 | 0 | 26 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=124) |
| `BPSYS` | 1081 | 106 | 0 | 50 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=125) |
| `BPDIAS` | 1081 | 106 | 0 | 50 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=125) |
| `HRATE` | 1088 | 99 | 0 | 50 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=128) |
| `VISION` | 1208 | 21 | 0 | 8 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=128) |
| `VISCORR` | 1210 | 19 | 0 | 8 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=128) |
| `VISWCORR` | 997 | 221 | 0 | 19 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=128) |
| `HEARING` | 1207 | 21 | 0 | 9 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=129) |
| `HEARAID` | 1209 | 21 | 0 | 7 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=129) |
| `HEARWAID` | 142 | 1077 | 0 | 18 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=129) |
| `NACCBMI` | 1106 | 126 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=124) |
| `NACCNREX` | 1215 | 0 | 0 | 22 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=181) |
| `NORMEXAM` | 1075 | 0 | 0 | 162 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=181) |
| `NPIQINF` | 1175 | 0 | 0 | 62 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=157) |
| `DEL` | 1220 | 2 | 0 | 15 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=157) |
| `DELSEV` | 21 | 1200 | 0 | 16 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=158) |
| `HALL` | 1235 | 2 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=158) |
| `HALLSEV` | 14 | 1223 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=159) |
| `AGIT` | 1185 | 1 | 0 | 51 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=159) |
| `AGITSEV` | 106 | 1079 | 0 | 52 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=160) |
| `DEPD` | 1178 | 4 | 0 | 55 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=160) |
| `DEPDSEV` | 233 | 945 | 0 | 59 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=161) |
| `ANX` | 1182 | 2 | 0 | 53 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=161) |
| `ANXSEV` | 188 | 995 | 0 | 54 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=162) |
| `ELAT` | 1220 | 1 | 0 | 16 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=162) |
| `ELATSEV` | 18 | 1203 | 0 | 16 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=163) |
| `APA` | 1210 | 2 | 0 | 25 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=163) |
| `APASEV` | 119 | 1093 | 0 | 25 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=164) |
| `DISN` | 1211 | 2 | 0 | 24 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=164) |
| `DISNSEV` | 74 | 1138 | 0 | 25 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=165) |
| `IRR` | 1180 | 1 | 0 | 56 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=165) |
| `IRRSEV` | 193 | 987 | 0 | 57 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=166) |
| `MOT` | 1233 | 4 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=166) |
| `MOTSEV` | 56 | 1181 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=167) |
| `NITE` | 1192 | 20 | 0 | 25 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=167) |
| `NITESEV` | 159 | 1047 | 0 | 31 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=168) |
| `APP` | 1197 | 4 | 0 | 36 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=168) |
| `APPSEV` | 103 | 1096 | 0 | 38 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=169) |
| `NOGDS` | 1236 | 0 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=170) |
| `SATIS` | 1223 | 5 | 0 | 9 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=170) |
| `DROPACT` | 1223 | 5 | 0 | 9 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=170) |
| `EMPTY` | 1224 | 6 | 0 | 7 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=171) |
| `BORED` | 1222 | 5 | 0 | 10 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=171) |
| `SPIRITS` | 1223 | 5 | 0 | 9 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=171) |
| `AFRAID` | 1223 | 9 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=172) |
| `HAPPY` | 1222 | 5 | 0 | 10 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=172) |
| `HELPLESS` | 1223 | 5 | 0 | 9 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=172) |
| `STAYHOME` | 1218 | 11 | 0 | 8 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=173) |
| `MEMPROB` | 1213 | 14 | 0 | 10 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=173) |
| `WONDRFUL` | 1224 | 6 | 0 | 7 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=173) |
| `WRTHLESS` | 1223 | 5 | 0 | 9 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=174) |
| `ENERGY` | 1221 | 6 | 0 | 10 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=174) |
| `HOPELESS` | 1226 | 7 | 0 | 4 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=174) |
| `BETTER` | 1227 | 6 | 0 | 4 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=175) |
| `NACCGDS` | 1223 | 5 | 0 | 9 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=175) |
| `BILLS` | 1155 | 63 | 0 | 19 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=176) |
| `TAXES` | 1108 | 108 | 0 | 21 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=176) |
| `SHOPPING` | 1217 | 14 | 0 | 6 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=177) |
| `GAMES` | 1179 | 51 | 0 | 7 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=177) |
| `STOVE` | 1228 | 7 | 0 | 2 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=178) |
| `MEALPREP` | 1185 | 38 | 0 | 14 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=178) |
| `EVENTS` | 1224 | 7 | 0 | 6 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=179) |
| `PAYATTN` | 1216 | 8 | 0 | 13 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=179) |
| `REMDATES` | 1212 | 4 | 0 | 21 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=180) |
| `TRAVEL` | 1215 | 4 | 0 | 18 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=180) |
| `DECSUB` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=196) |
| `ANIMALS` | 1225 | 11 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=226) |
| `VEG` | 1222 | 14 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=226) |
| `TRAILA` | 1167 | 21 | 0 | 49 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=227) |
| `TRAILARR` | 1163 | 21 | 0 | 53 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=227) |
| `TRAILALI` | 1211 | 21 | 0 | 5 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=228) |
| `TRAILB` | 1134 | 55 | 0 | 48 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=228) |
| `TRAILBRR` | 1113 | 55 | 0 | 69 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=229) |
| `TRAILBLI` | 1161 | 55 | 0 | 21 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=229) |
| `MOCATOTS` | 984 | 4 | 0 | 249 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=238) |
| `NACCAPOE` | 959 | 278 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/rdd-genetic-data.pdf#page=6) |
| `NACCUDSD` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=269) |
| `MEMORY` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=154) |
| `ORIENT` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=154) |
| `JUDGMENT` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=154) |
| `COMMUN` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=154) |
| `HOMEHOBB` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=154) |
| `PERSCARE` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=155) |
| `CDRSUM` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=155) |
| `CDRGLOB` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=155) |

### MRI

| ستون | سازگار با قاعده | کد ویژه/مختلط | ابهام مستندات | ناسازگاری/گمشدگی دیگر | منبع |
|---|---:|---:|---:|---:|---|
| `NACCID` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=41) |
| `LH_CAUDALANTERIORCINGULATE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_CAUDALANTERIORCINGULATE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_CAUDALANTERIORCINGULATE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_CAUDALANTERIORCINGULATE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_CAUDALMIDDLEFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_CAUDALMIDDLEFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_CAUDALMIDDLEFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_CAUDALMIDDLEFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_CUNEUS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_CUNEUS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_CUNEUS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_CUNEUS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_ENTORHINAL_GVOL` | 1236 | 0 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_ENTORHINAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_ENTORHINAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_ENTORHINAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_FUSIFORM_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_FUSIFORM_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_FUSIFORM_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_FUSIFORM_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_INFERIORPARIETAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_INFERIORPARIETAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_INFERIORPARIETAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_INFERIORPARIETAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_INFERIORTEMPORAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_INFERIORTEMPORAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_INFERIORTEMPORAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_INFERIORTEMPORAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_ISTHMUSCINGULATE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_ISTHMUSCINGULATE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_ISTHMUSCINGULATE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_ISTHMUSCINGULATE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_LATERALOCCIPITAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_LATERALOCCIPITAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_LATERALOCCIPITAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_LATERALOCCIPITAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_LATERALORBITOFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_LATERALORBITOFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_LATERALORBITOFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_LATERALORBITOFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_LINGUAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_LINGUAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_LINGUAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_LINGUAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_MEDIALORBITOFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_MEDIALORBITOFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_MEDIALORBITOFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_MEDIALORBITOFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_MIDDLETEMPORAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_MIDDLETEMPORAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_MIDDLETEMPORAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_MIDDLETEMPORAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARAHIPPOCAMPAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARAHIPPOCAMPAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARAHIPPOCAMPAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARAHIPPOCAMPAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARACENTRAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARACENTRAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARACENTRAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARACENTRAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARSOPERCULARIS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARSOPERCULARIS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARSOPERCULARIS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARSOPERCULARIS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARSORBITALIS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARSORBITALIS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARSORBITALIS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARSORBITALIS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARSTRIANGULARIS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARSTRIANGULARIS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PARSTRIANGULARIS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PARSTRIANGULARIS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PERICALCARINE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PERICALCARINE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PERICALCARINE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PERICALCARINE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_POSTCENTRAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_POSTCENTRAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_POSTCENTRAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_POSTCENTRAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_POSTERIORCINGULATE_GVOL` | 1236 | 0 | 0 | 1 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_POSTERIORCINGULATE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_POSTERIORCINGULATE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_POSTERIORCINGULATE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PRECENTRAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PRECENTRAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PRECENTRAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PRECENTRAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PRECUNEUS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PRECUNEUS_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_PRECUNEUS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_PRECUNEUS_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_ROSTRALANTERIORCINGULATE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_ROSTRALANTERIORCINGULATE_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_ROSTRALANTERIORCINGULATE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_ROSTRALANTERIORCINGULATE_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_ROSTRALMIDDLEFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_ROSTRALMIDDLEFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_ROSTRALMIDDLEFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_ROSTRALMIDDLEFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_SUPERIORFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_SUPERIORFRONTAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_SUPERIORFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_SUPERIORFRONTAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_SUPERIORPARIETAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_SUPERIORPARIETAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_SUPERIORPARIETAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_SUPERIORPARIETAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_SUPERIORTEMPORAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_SUPERIORTEMPORAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_SUPERIORTEMPORAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_SUPERIORTEMPORAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_SUPRAMARGINAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_SUPRAMARGINAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_SUPRAMARGINAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_SUPRAMARGINAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_TRANSVERSETEMPORAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_TRANSVERSETEMPORAL_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_TRANSVERSETEMPORAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_TRANSVERSETEMPORAL_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_INSULA_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_INSULA_GVOL` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `LH_INSULA_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `RH_INSULA_AVGTH` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/SCAN-MRI-Imaging-RDD.pdf) |
| `NACCUDSD` | 1237 | 0 | 0 | 0 | [مرجع](https://files.alz.washington.edu/documentation/uds3-rdd.pdf#page=269) |

## ردگیری و محدودیت‌ها

- [quality_audit.json](quality_audit.json): شمار و درصد وضعیت‌ها با مخرج هر ستون، فراوانی مقادیر مسئله‌دار، نتایج منطقی، حصارها و هم‌پوشانی پرچم‌ها.
- [quality_issues.json](quality_issues.json): هر مقدار نیازمند توجه همراه نام فایل، شمارهٔ خط CSV (از ۲ برای اولین فرد)، شناسه، ستون، مقدار خام و علت؛ کدهای ویژه نیز برای ردگیری ثبت‌اند و الزاماً خطا نیستند.
- گمشدگی پیش از جایگذاری، روش آماده‌سازی، تاریخ مراجعه/اسکن و QC اختصاصی همچنان معلوم نیستند؛ گزارش آن‌ها صفر اعلام نمی‌کند.
- ناسازگاری جدول و توضیح کد NACCBMI در مرجع ثبت شده است؛ این متغیر وارد سؤال اصلی نشده و داده‌اش اصلاح نشده است.
- درصد تجمیعی تمام سلول‌های ویژه، جای درصد فرد یا درصد گمشدگی هر متغیر نیست. یک فرد ممکن است چند پرچم داشته باشد.
- نمودارها، آزمون‌ها و مدل‌های فازهای بعد هنوز در این مرحله تولید نشده‌اند.

## اثر انگشت ورودی‌ها

| فایل | SHA-256 |
|---|---|
| `data/udslong_imputed.csv` | `8bcd0180d1b593092f7b2f7777281f59c4a6e9c3b2b041b5d2a33ed13be55e63` |
| `data/mriscanclean.csv` | `3a2b34f7902592705f75ce3ad4c4fab68880470f01e7b9eb9823a799dc092e72` |
| `data/combined_adjacency_matrix.csv` | `f7a0ed04de23f8e2c91555376f839d0fcbcf9a20d24f4c294b76ef18bc470671` |
| `docs/amarpr.pdf` | `ede1706ab440f1ae737a71afaf0a37438112e7b010e6a5118b8f334b4c0d03e3` |
