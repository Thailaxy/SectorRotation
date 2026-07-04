# spec.md — US Sector & Theme Rotation Tracker

> **สถานะเอกสาร:** Draft v1.0 · เขียนขึ้นเพื่อส่งต่อให้ engineer / AI เขียนโค้ดต่อ
> **ระดับผู้อ่านเป้าหมาย:** engineer จบใหม่ประสบการณ์ ~3 เดือน — อ่านแล้วต้องสร้างโปรเจกต์ต่อได้เอง
> **ภาษาในเอกสาร:** อธิบายแนวคิดเป็นภาษาไทย, ส่วนโค้ด/ชื่อฟิลด์/config เป็นภาษาอังกฤษ (มาตรฐานสากล)
> **ภาษาใน source code comment:** ภาษาไทย (ตามที่เจ้าของโปรเจกต์ต้องการ)

---

## 0. TL;DR (อ่าน 1 นาที)

เราจะสร้าง **เว็บ dashboard** ที่แสดงว่า "เงินในตลาดหุ้นสหรัฐกำลังหมุน (rotate) เข้า-ออกกลุ่มอุตสาหกรรม/ธีมไหน"
โดยดึงราคาปิดรายวัน (EOD) ของ ETF/หุ้น ~36 ธีม → คำนวณตัวชี้วัด (RS-Ratio, RS-Momentum, breadth, ผลตอบแทน)
→ เซฟเป็นไฟล์ `data.json` → หน้าเว็บนิ่ง (static) อ่านไฟล์นี้มาวาดกราฟ

- **ต้นทุน:** ฟรี 100% (GitHub Actions + GitHub Pages)
- **ไม่มี backend server, ไม่มี database** — เป็น static site ที่ข้อมูลอัปเดตวันละครั้งโดยอัตโนมัติ
- **ผู้ใช้:** เจ้าของ + เพื่อน (เปิดดูได้ ไม่ต้อง login)
- **สองภาษา:** สลับ EN/TH ได้ทั้งหน้า
- **คำเตือน:** เครื่องมือนี้เพื่อ "สังเกตการณ์/เรียนรู้" ไม่ใช่คำแนะนำซื้อขาย (ต้องมี disclaimer ชัดเจนบนหน้าเว็บ)

---

## 1. Goals & Non-Goals (เป้าหมาย และสิ่งที่จะไม่ทำ)

### 1.1 Goals
1. แสดง "โซนการหมุน" ของแต่ละธีมบน Relative Rotation Graph (RRG): Leading / Weakening / Lagging / Improving
2. แสดง Heatmap ผลตอบแทน (1D / 1W / 1M / 3M / 1M vs SPY) เรียงลำดับได้
3. แสดง Breadth (% สมาชิกในธีมที่ราคายืนเหนือเส้นค่าเฉลี่ย 20 วัน) + Dollar Volume Ratio
4. แสดง "Momentum Playbook" จัดกลุ่มธีมตามโซน พร้อมสีสุขภาพ breadth
5. แสดง Appendix: ธีมนี้ประกอบด้วย ETF/หุ้นตัวไหนบ้าง
6. สลับภาษา EN/TH ได้ทั้งหน้า
7. ใช้งานบนมือถือได้ (responsive)
8. อัปเดตข้อมูลอัตโนมัติวันละครั้งหลังตลาดสหรัฐปิด

### 1.2 Non-Goals (จะ *ไม่* ทำในโปรเจกต์นี้)
- ❌ ไม่ทำระบบซื้อขายอัตโนมัติ / ไม่เชื่อมต่อโบรกเกอร์
- ❌ ไม่ให้ "คำแนะนำซื้อขายรายตัว" (แสดงข้อมูลดิบ + framework เท่านั้น)
- ❌ ไม่มีระบบสมาชิก/login (Phase 1-2)
- ❌ ไม่ทำ real-time / intraday (ใช้ราคาสิ้นวันพอ)
- ❌ ไม่ทำระบบแจ้งเตือน (เลื่อนไป Phase 3)

---

## 2. Glossary — อภิธานศัพท์ (ต้องเข้าใจก่อนเริ่ม)

| คำ | ความหมาย (ไทย) |
|---|---|
| **Sector Rotation** | การที่เงินลงทุนไหลจากกลุ่มอุตสาหกรรมหนึ่งไปอีกกลุ่ม ตามภาวะตลาด/เศรษฐกิจ |
| **Theme (ธีม)** | ตะกร้าหุ้น/ETF ที่จัดกลุ่มตามแนวคิด เช่น Semiconductors, Genomics, Defense |
| **Benchmark** | ตัวเปรียบเทียบ = **SPY** (ETF ที่อิงดัชนี S&P 500 = ตลาดโดยรวม) |
| **RS (Relative Strength)** | ความแข็งแรงเทียบตลาด = ราคาธีม ÷ ราคา benchmark |
| **RS-Ratio (แกน X)** | RS ที่ normalize รอบค่า 100 · >100 = แข็งกว่าตลาด, <100 = อ่อนกว่าตลาด |
| **RS-Momentum (แกน Y)** | โมเมนตัม (อัตราเร่ง) ของ RS-Ratio · >100 = กำลังแรงขึ้น, <100 = กำลังอ่อนลง |
| **RRG (Relative Rotation Graph)** | กราฟ scatter แกน X=RS-Ratio, Y=RS-Momentum แบ่ง 4 โซน + "หาง (tail)" ย้อนหลัง 8 สัปดาห์ |
| **Leading** | โซนขวาบน: แข็งและยังแรงขึ้น (RS-Ratio≥100, RS-Momentum≥100) |
| **Weakening** | โซนขวาล่าง: ยังแข็งแต่แผ่ว (RS-Ratio≥100, RS-Momentum<100) |
| **Lagging** | โซนซ้ายล่าง: อ่อนและยังแย่ลง (RS-Ratio<100, RS-Momentum<100) |
| **Improving** | โซนซ้ายบน: ยังอ่อนแต่กำลังฟื้น (RS-Ratio<100, RS-Momentum≥100) |
| **20DMA** | เส้นค่าเฉลี่ยเคลื่อนที่ราคาปิด 20 วัน (20-Day Moving Average) |
| **Breadth** | % ของหุ้นสมาชิกในธีมที่ราคายืน "เหนือ" เส้น 20DMA (ยิ่งสูง = แข็งทั่วถึง) |
| **Dollar Volume Ratio** | (มูลค่าซื้อขายเฉลี่ย 5 วันล่าสุด) ÷ (เฉลี่ย 20 วัน) · >1 = เงินไหลเข้าเร่งขึ้น |
| **Equal-weight** | ถ่วงน้ำหนักหุ้นในตะกร้าเท่ากันทุกตัว (ต่างจาก ETF จริงที่ถ่วงตาม market cap) |
| **EOD (End of Day)** | ข้อมูลราคาปิดสิ้นวัน |

> **⚠️ หมายเหตุสำคัญที่ต้องแสดงบนหน้าเว็บ:** การคำนวณของเราใช้ **equal-weight** (หุ้นทุกตัวน้ำหนักเท่ากัน)
> ในขณะที่ ETF จริงส่วนใหญ่เป็น **market-cap weight** (เช่น SMH ที่ NVDA กินสัดส่วนใหญ่)
> ดังนั้นตัวเลขของเราอาจต่างจากราคา ETF จริง — ใช้เพื่อดูทิศทาง rotation ไม่ใช่ผลตอบแทนที่แท้จริง

---

## 3. Personas & Use Cases

- **P1 เจ้าของ (นักลงทุนระยะยาว):** เปิดดูสัปดาห์ละครั้งเพื่อสังเกตว่าธีมที่ตนถือ (เช่น Semiconductors ผ่าน SMH) อยู่โซนไหน
- **P2 เพื่อน:** เปิดลิงก์ดู ไม่ต้อง login อยากได้หน้าที่โหลดเร็วและเข้าใจง่าย
- **Use case หลัก:** "ตอนนี้เงินกำลังหมุนเข้า/ออกกลุ่มไหน และธีมที่ฉันสนใจอยู่โซนไหนของวงจร"

---

## 4. Scope by Phase (ขอบเขตแบ่งเป็นเฟส)

### Phase 1 — MVP (ทำก่อน เห็นผลไว)
- Data pipeline: ดึงราคา → คำนวณ **ผลตอบแทน (returns)** + **breadth** + **dollar volume ratio**
- หน้าเว็บ: **Heatmap table** + **Breadth & Volume table** + **Appendix**
- EN/TH toggle
- Responsive
- GitHub Actions รันรายวัน + deploy GitHub Pages
- Disclaimer

### Phase 2 — Full Dashboard
- เพิ่มการคำนวณ **RS-Ratio / RS-Momentum**
- หน้าเว็บ: **RRG chart** (scatter + tail 8 สัปดาห์) + **Momentum Playbook** (4 การ์ดตามโซน)
- ป้าย "📍 You hold this / คุณถืออยู่" บนธีมที่ผู้ใช้กำหนดใน config (เริ่มที่ Semiconductors)

### Phase 3 — Future (ยังไม่ทำตอนนี้ แค่บันทึกไว้)
- ระบบแจ้งเตือน (อีเมล/LINE) เมื่อธีมเปลี่ยนโซน
- ติดตามพอร์ตส่วนตัว (สัดส่วนการถือครองจริง)
- เก็บ historical snapshot เพื่อดูการเคลื่อนที่ย้อนหลังไกลขึ้น

---

## 5. System Architecture (สถาปัตยกรรมระบบ)

```
                    ┌──────────────────────────────────────┐
   ทุกวัน 22:30 UTC  │        GitHub Actions (cron)          │
   (หลังตลาดปิด) ───▶│  1. checkout repo                    │
                    │  2. setup python 3.11                 │
                    │  3. pip install -r requirements.txt   │
                    │  4. python -m pipeline.run            │
                    │     - ดึงราคา (yfinance)               │
                    │     - อ่าน cache CSV เดิม (ถ้า yahoo ล่ม)│
                    │     - คำนวณ metrics ทั้งหมด             │
                    │     - เขียน web/public/data.json       │
                    │  5. git commit data.json + cache       │
                    │  6. deploy → Firebase Hosting          │
                    └───────────────┬──────────────────────┘
                                    │ (deploy static site)
                                    ▼
                    ┌──────────────────────────────────────┐
                    │     Firebase Hosting (โฮสต์ฟรี)         │
                    │   index.html + app.js + data.json     │
                    │   URL: sectorrotation-546e0.web.app    │
                    └───────────────┬──────────────────────┘
                                    │ HTTPS (global CDN)
                                    ▼
                    ┌──────────────────────────────────────┐
                    │  Browser (ผู้ใช้ + เพื่อน, มือถือ/PC)   │
                    │  โหลด data.json → วาด RRG/Heatmap ด้วย │
                    │  ECharts + สลับภาษา EN/TH             │
                    └──────────────────────────────────────┘
```

**หลักการสำคัญ:** ทุกอย่างที่ "หนัก" (ดึงข้อมูล + คำนวณ) ทำใน GitHub Actions วันละครั้ง
ส่วน browser แค่โหลดไฟล์ `data.json` ที่คำนวณเสร็จแล้ว → เว็บเบา โหลดเร็ว ไม่ต้องมี server

---

## 6. Tech Stack (เทคโนโลยีที่กำหนดแน่นอน)

### 6.1 Data / Compute (backend batch)
| ส่วน | เครื่องมือ | เวอร์ชันแนะนำ | เหตุผล |
|---|---|---|---|
| ภาษา | **Python** | 3.11 | มาตรฐาน data, มี lib ครบ |
| ดึงราคา | **yfinance** | ล่าสุด | ฟรี ไม่ต้อง API key |
| คำนวณ | **pandas**, **numpy** | ล่าสุด | จัดการ time-series |
| config | **PyYAML** | ล่าสุด | อ่าน config.yaml |
| test | **pytest** | ล่าสุด | unit test สูตรคำนวณ |

### 6.2 Frontend (static site)
| ส่วน | เครื่องมือ | เหตุผล |
|---|---|---|
| โครงหน้า | **HTML5 + CSS (vanilla)** | ไม่ต้อง build tool ซับซ้อน เหมาะมือใหม่ |
| logic | **JavaScript (vanilla ES6)** | ไม่ต้องมี framework ใน Phase 1-2 |
| กราฟ | **Apache ECharts** (โหลดผ่าน CDN) | ฟรี, ทำ scatter+heatmap สวย, docs ดี |
| สไตล์ | CSS variables (dark theme) | ปรับสีง่าย |

> **ทำไมไม่ใช้ React/Vue?** เพื่อลด learning curve สำหรับ engineer ใหม่ และไม่ต้องตั้ง build pipeline
> ถ้าอนาคตซับซ้อนขึ้น (Phase 3) ค่อยพิจารณาเปลี่ยนได้

### 6.3 CI/CD & Hosting
| ส่วน | เครื่องมือ | โควตาฟรี |
|---|---|---|
| อัตโนมัติ | **GitHub Actions** | 2,000 นาที/เดือน (ใช้จริง ~90 นาที/เดือน) |
| โฮสต์ | **Firebase Hosting** | ฟรีไม่จำกัด บน Spark plan (10 GB storage, 360 MB/day transfer) |

> **หมายเหตุ:** ก่อนหน้านี้ใช้ GitHub Pages แต่ย้ายมา Firebase Hosting แล้วเพื่อ global CDN + cache-control ละเอียดกว่า + จัดการ custom domain ง่ายกว่า
> **ตั้งค่า deploy (ทำครั้งเดียว):** สร้าง service account ชื่อ `github-actions-deploy` ใน Google Cloud Console ให้ role **Firebase Hosting Admin** (ขั้นต่ำ) แล้ว generate JSON key เก็บเป็น GitHub Actions secret ชื่อ `FIREBASE_SERVICE_ACCOUNT`

---

## 7. Repository Structure (โครงสร้างไฟล์)

```
rotation-tracker/
├── README.md                  # วิธีติดตั้ง+รัน (ภาษาไทย)
├── spec.md                    # เอกสารนี้
├── requirements.txt           # dependency ของ python
├── config.yaml                # ค่า parameter ทั้งหมด (แก้ได้โดยไม่ต้องแตะโค้ด)
├── data/
│   └── universe.yaml          # นิยามธีม + รายชื่อ ETF/หุ้น (ดูภาคผนวก A)
├── cache/                     # ราคาย้อนหลัง (CSV) เก็บกันวันที่ yahoo ล่ม
│   └── prices.csv
├── pipeline/                  # โค้ดฝั่ง python
│   ├── __init__.py
│   ├── run.py                 # entry point: ดึง->คำนวณ->เขียน json
│   ├── fetch.py               # ดึงราคา yfinance + จัดการ cache
│   ├── metrics.py             # สูตรคำนวณทั้งหมด (returns, breadth, RRG)
│   └── build_json.py          # ประกอบ data.json ตาม schema
├── tests/
│   ├── test_metrics.py        # unit test สูตร (ใช้ข้อมูลปลอมที่รู้คำตอบ)
│   └── fixtures/              # ข้อมูลตัวอย่างสำหรับ test
├── web/
│   └── public/                # <== โฟลเดอร์ที่ GitHub Pages เสิร์ฟ
│       ├── index.html
│       ├── styles.css
│       ├── app.js             # โหลด data.json + วาดกราฟ + toggle ภาษา
│       ├── i18n.js            # ข้อความ 2 ภาษา (en/th)
│       └── data.json          # <== ไฟล์ผลลัพธ์ (สร้างโดย pipeline)
└── .github/
    └── workflows/
        └── daily.yml          # GitHub Actions cron
```

---

## 8. Data Layer (ชั้นข้อมูล)

### 8.1 Universe (จักรวาลของธีม)
- เก็บใน `data/universe.yaml` (โครงสร้างเต็มอยู่ **ภาคผนวก A**)
- แต่ละธีมมี: `id`, `name_en`, `name_th`, `type` (`theme` หรือ `sector_etf`), `constituents` (list ของ ticker), `ref_etfs` (list ETF อ้างอิงสำหรับ Appendix)
- **Sector ETF** (เช่น XLK, XLF) เป็น ticker เดียว → ไม่มี breadth (แสดงป้าย "ETF")
- **Theme** (เช่น Semiconductors) เป็นตะกร้าหุ้นหลายตัว → คำนวณ breadth ได้

### 8.2 การดึงราคา (fetch.py)
- ใช้ `yfinance.download()` ดึง `Close` และ `Volume` รายวัน ย้อนหลัง **อย่างน้อย 400 วันปฏิทิน** (พอสำหรับ 3M return + normalize RRG 52 สัปดาห์)
- ดึงทุก ticker ที่ปรากฏใน universe + `SPY` (benchmark)
- **การจัดการ cache/ความทนทาน (สำคัญมาก เพราะ yahoo ไม่เป็นทางการ):**
  1. โหลด `cache/prices.csv` เดิมเข้ามาก่อน
  2. พยายามดึงข้อมูลใหม่จาก yfinance (ใส่ retry 3 ครั้ง, เว้น 5 วินาที)
  3. ถ้า ticker ไหนดึงไม่ได้ → ใช้ค่าจาก cache แทน + log warning
  4. ถ้าดึงได้ → merge เข้ากับ cache แล้วเขียนทับ `cache/prices.csv`
  5. ถ้า ticker ไหน "ทั้งดึงไม่ได้ และไม่มีใน cache" → mark ธีมนั้น `data_ok: false` ใน json (frontend แสดงป้าย "ข้อมูลไม่ครบ")

### 8.3 การเตรียมข้อมูล
- ทำ forward-fill สำหรับวันหยุด/ค่าหาย (จำกัดไม่เกิน 2 วัน) 
- Return ทั้งหมดคำนวณจาก **plain close** (yfinance `auto_adjust=False`, ใช้คอลัมน์ `Close` ซึ่ง split-adjusted แต่ไม่ dividend-adjusted)
  เพื่อให้ตัวเลข % ตรงกับกราฟราคาที่แสดงบนหน้า Yahoo Finance เอง — ถ้าใช้ `auto_adjust=True`/`Adj Close`
  (total return รวมเงินปันผล) ตัวเลขจะต่างจากที่ Yahoo แสดงในช่วงที่มี ex-dividend date อยู่ในหน้าต่างช่วงเวลานั้น

---

## 9. Calculation Specifications (สูตรคำนวณ — pseudo-code)

> ทุก parameter อยู่ใน `config.yaml` (ดูค่า default ในภาคผนวก B) เพื่อให้ปรับได้โดยไม่ต้องแก้โค้ด

### 9.1 ผลตอบแทน (Returns) — ใช้ราคารายวัน
สำหรับ **แต่ละหุ้นสมาชิก** คำนวณผลตอบแทนตามช่วง แล้ว **equal-weight = ค่าเฉลี่ย (mean) ของสมาชิก**:
```
def period_return(close_series, n_trading_days):
    # ผลตอบแทน % จาก n วันทำการก่อนหน้า ถึงวันล่าสุด
    return (close_series[-1] / close_series[-1 - n_trading_days] - 1) * 100

# จำนวนวันทำการโดยประมาณ
n_1D = 1 ; n_1W = 5 ; n_1M = 21 ; n_3M = 63

theme_return_1M = mean([ period_return(close[t], n_1M) for t in constituents ])
# สำหรับ sector_etf (ticker เดียว) ก็คือ period_return ของ ticker นั้น

# 1M vs SPY = ผลตอบแทน 1M ของธีม - ผลตอบแทน 1M ของ SPY
one_month_vs_spy = theme_return_1M - period_return(close["SPY"], n_1M)
```

### 9.2 Breadth (% เหนือ 20DMA) — เฉพาะ type == theme
```
def pct_above_ma(constituents, ma_window=20):
    count_above = 0
    for t in constituents:
        ma = close[t].rolling(ma_window).mean()[-1]
        if close[t][-1] > ma:
            count_above += 1
    return count_above / len(constituents) * 100
```

### 9.3 Dollar Volume Ratio (5D/20D)
```
def dollar_vol_ratio(constituents, short=5, long=20):
    ratios = []
    for t in constituents:
        dv = close[t] * volume[t]          # มูลค่าซื้อขายรายวัน
        r = dv.rolling(short).mean()[-1] / dv.rolling(long).mean()[-1]
        ratios.append(r)
    return mean(ratios)                    # equal-weight เฉลี่ยของสมาชิก
```

### 9.4 RS-Ratio & RS-Momentum (RRG) — Phase 2
> **หมายเหตุ:** สูตร JdK ต้นฉบับของ StockCharts เป็นสูตรลิขสิทธิ์ (proprietary)
> เราใช้ **การประมาณแบบ z-score normalization** ที่ให้ผลใกล้เคียงและ reproducible ได้ 100%
> ผู้ implement ต้องทำตามสูตรนี้เป๊ะ เพื่อให้ผลตรงกันทุกครั้ง

ขั้นตอน (ทำบนราคา **รายสัปดาห์** — resample เป็นราคาปิดวันศุกร์):
```
# ราคาของธีม = ราคาเฉลี่ย equal-weight (normalize แต่ละหุ้นเป็น index ฐาน 100 ก่อนเฉลี่ย)
theme_price_weekly[w]  = mean([ normalize_to_100(close[t]) for t in constituents ]) resample weekly
bench_price_weekly[w]  = close["SPY"] resample weekly

RS      = theme_price_weekly / bench_price_weekly           # relative strength ดิบ
RS_sm   = EMA(RS, span = cfg.rrg_smoothing)                 # ทำให้เนียน (default span=10)

# --- RS-Ratio: normalize รอบค่า 100 ---
mean_r  = RS_sm.rolling(cfg.rrg_lookback_weeks).mean()      # default 52
std_r   = RS_sm.rolling(cfg.rrg_lookback_weeks).std()
z_ratio = (RS_sm - mean_r) / std_r
RS_Ratio = 100 + cfg.rrg_scale * z_ratio                   # default scale=10  -> ช่วงราว 70..140

# --- RS-Momentum: อัตราการเปลี่ยนแปลงของ RS-Ratio ---
mom     = RS_Ratio - RS_Ratio.shift(1)                     # การเปลี่ยนรายสัปดาห์
mean_m  = mom.rolling(cfg.rrg_lookback_weeks).mean()
std_m   = mom.rolling(cfg.rrg_lookback_weeks).std()
z_mom   = (mom - mean_m) / std_m
RS_Momentum = 100 + cfg.rrg_scale * z_mom

# เก็บ "หาง" 8 จุดสุดท้าย (8 สัปดาห์) ต่อธีม สำหรับวาด RRG
tail = last cfg.rrg_tail_weeks points of (RS_Ratio, RS_Momentum)   # default 8
```

### 9.5 การจัดโซน (Quadrant classification)
```
def classify(rs_ratio_latest, rs_momentum_latest):
    if rs_ratio >= 100 and rs_momentum >= 100: return "leading"
    if rs_ratio >= 100 and rs_momentum <  100: return "weakening"
    if rs_ratio <  100 and rs_momentum <  100: return "lagging"
    return "improving"   # rs_ratio < 100 and rs_momentum >= 100
```

### 9.6 Momentum Playbook (การจัดการ์ด 4 โซน)
- จัดธีมเข้ากล่องตาม quadrant
- ในแต่ละกล่อง **เรียงตาม `one_month_vs_spy` มาก→น้อย**
- แต่ละธีมมี "สีสุขภาพ breadth": `green >= 50%`, `yellow 30–50%`, `red < 30%`, `type==sector_etf → "ETF"` (ไม่มีสี breadth)

---

## 10. data.json Schema (สัญญาข้อมูลระหว่าง pipeline ↔ frontend)

> นี่คือ "contract" ที่สำคัญที่สุด — frontend พึ่งพา schema นี้ ห้ามเปลี่ยนชื่อ field โดยไม่แก้ทั้งสองฝั่ง

```jsonc
{
  "generated_at": "2026-07-02T22:35:00Z",   // เวลาที่ pipeline รัน (UTC, ISO8601)
  "as_of_date": "2026-07-02",               // วันที่ของราคาปิดล่าสุด
  "benchmark": "SPY",
  "benchmark_return_1M": -1.53,              // ผลตอบแทน 1M ของ benchmark (%)
  "config": {                                // สำเนา parameter ที่ใช้ (เพื่อ transparency)
    "rrg_tail_weeks": 8, "breadth_ma": 20, "rrg_scale": 10
  },
  "user_holdings": ["semiconductors"],       // ธีมที่ผู้ใช้ถือ (ใส่ป้าย 📍)
  "themes": [
    {
      "id": "semiconductors",
      "name_en": "Semiconductors",
      "name_th": "เซมิคอนดักเตอร์",
      "type": "theme",                       // "theme" | "sector_etf"
      "data_ok": true,                       // false = ข้อมูลไม่ครบ
      "quadrant": "weakening",               // leading|weakening|lagging|improving
      "returns": {                           // หน่วย: %
        "d1": -4.72, "w1": -7.08, "m1": -7.30, "m3": 78.58, "m1_vs_spy": -5.60
      },
      "breadth_pct": 12.5,                   // null ถ้า type == sector_etf
      "dollar_vol_ratio": 0.85,
      "rrg": {                               // null ใน Phase 1
        "ratio": 96.2, "momentum": 92.4,     // จุดล่าสุด
        "tail": [                            // 8 จุด เก่า->ใหม่
          {"ratio": 108.1, "momentum": 111.0},
          // ... รวม 8 จุด
          {"ratio": 96.2, "momentum": 92.4}
        ]
      },
      "constituents": ["NVDA","AMD","AVGO","TSM","QCOM","TXN","INTC","MRVL"],
      "ref_etfs": [
        {"ticker":"SMH","label_en":"VanEck Semiconductor","label_th":"VanEck Semiconductor"},
        {"ticker":"SOXX","label_en":"iShares Semiconductor","label_th":"iShares Semiconductor"}
      ]
    }
    // ... ธีมอื่นๆ
  ],
  "warnings": ["QUANTUM: ticker QBTS ใช้ cache (yahoo ดึงไม่ได้)"]  // log เตือน
}
```

---

## 11. Frontend Specification

### 11.1 โครงหน้า (บนลงล่าง)
1. **Header:** ชื่อ "US Sector & Theme Rotation Tracker" · วันที่ข้อมูล (`as_of_date`) · ผลตอบแทน SPY · **ปุ่ม toggle EN/TH** (มุมขวาบน)
2. **RRG chart** (Phase 2) — ซ้าย · **Heatmap table** — ขวา (บนมือถือวางซ้อนกัน)
3. **Momentum Playbook** (Phase 2) — 4 การ์ด: Leading / Improving / Weakening / Lagging
4. **Breadth & Volume table** (Phase 1)
5. **Appendix** — การ์ดต่อธีม แสดง ref_etfs + constituents
6. **Footer:** disclaimer (ดูข้อ 15) + note เรื่อง equal-weight vs market-weight

### 11.2 Component: Heatmap Table
- แถว = ธีม, คอลัมน์ = 1D% / 1W% / 1M% / 3M% / 1M vs SPY
- ปุ่มเรียง: `เรียงตาม 1M` (default) / 1W / 1D / 1M vs SPY (คลิกสลับได้)
- แต่ละธีมมี badge สีตาม quadrant (green=leading, blue=improving, amber=weakening, red=lagging)
- สีพื้นเซลล์: ค่าบวก=เขียว, ลบ=แดง, เข้มตามขนาด (color scale)

### 11.3 Component: RRG Chart (ECharts scatter) — Phase 2
- แกน X = RS-Ratio (ช่วงราว 70–150), Y = RS-Momentum (70–140)
- เส้นแบ่ง 4 โซนที่ค่า 100,100 · ระบายสีพื้นหลัง 4 โซน (เขียว/ฟ้า/เหลือง/แดงอ่อน)
- แต่ละธีม = เส้น "หาง" 8 จุด + จุดใหญ่ที่ปลาย (จุดล่าสุด)
- hover จุด → tooltip: ชื่อธีม, RS-Ratio, RS-Momentum, quadrant
- คลิกธีม → ไฮไลต์เส้นนั้น (จางเส้นอื่น)
- ปุ่มกรอง: `ธีม` / `Sector ETF` / `ทั้งหมด`

### 11.4 Component: Momentum Playbook (Phase 2)
- 4 การ์ดสีตามโซน · ในการ์ดลิสต์ธีม เรียงตาม 1M vs SPY
- แต่ละบรรทัด: ชื่อ + ค่า 1M vs SPY + badge breadth (`B 100%` สีเขียว/เหลือง/แดง หรือ `ETF`)

### 11.5 Component: Breadth & Volume Table (Phase 1)
- แถบ (bar) แนวนอนแสดง % เหนือ 20DMA + ตัวเลข % + Dollar Vol Ratio
- สีแถบ: green ≥50%, yellow 30–50%, red <30%

### 11.6 i18n (EN/TH toggle)
- ไฟล์ `i18n.js` เก็บ dict: `{ en: {...}, th: {...} }` ครอบคลุมข้อความ UI ทุกจุด (หัวข้อ, ปุ่ม, tooltip, disclaimer)
- ชื่อธีมใช้ `name_en` / `name_th` จาก data.json
- state ภาษาปัจจุบันเก็บใน `localStorage` (จำค่าไว้เมื่อกลับมาเปิดใหม่)
- default = TH · ตัวเลข/สีไม่เปลี่ยนตามภาษา เปลี่ยนเฉพาะข้อความ

### 11.7 Responsive
- Breakpoint: `>= 1024px` = 2 คอลัมน์ (RRG | Heatmap) · `< 1024px` = คอลัมน์เดียวเรียงลง
- ตารางบนมือถือ = scroll แนวนอนได้ · font/ระยะห่างปรับให้อ่านง่าย
- แตะจุดใน RRG บนมือถือได้ (touch)

### 11.8 Design tokens (dark theme — CSS variables)
```
--bg: #0d1117 ; --panel: #161b22 ; --text: #e6edf3 ; --muted: #8b949e
--leading: #22c55e ; --improving: #3b82f6 ; --weakening: #f59e0b ; --lagging: #ef4444
--pos: #22c55e ; --neg: #ef4444
```

---

## 12. CI/CD — GitHub Actions (`.github/workflows/daily.yml`)

> มี 2 workflows: `daily.yml` (รัน pipeline + deploy รายวัน) และ `deploy-site.yml` (deploy frontend เมื่อมี push)
> ทั้งคู่ deploy ไป Firebase Hosting ผ่าน `FirebaseExtended/action-hosting-deploy@v0` ที่อ่าน secret `FIREBASE_SERVICE_ACCOUNT`

```yaml
name: daily-update
on:
  schedule:
    - cron: "30 22 * * 1-5"   # จ-ศ 22:30 UTC (หลังตลาดสหรัฐปิด) — ปรับตาม DST เองถ้าจำเป็น
  workflow_dispatch: {}       # กดรันเองได้จากหน้า GitHub
permissions:
  contents: write             # ให้ commit data.json + cache ได้
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: python -m pipeline.run        # ดึง+คำนวณ+เขียน web/public/data.json
      - name: commit updated data
        run: |
          git config user.name "rotation-bot"
          git config user.email "bot@users.noreply.github.com"
          git add web/public/data.json
          if [ -d "cache" ]; then git add cache/; fi
          git commit -m "chore: daily data update ($(date -u +%F))" || echo "no changes"
          git push
      # NOTE: git push ด้วย GITHUB_TOKEN ไม่ trigger workflow อื่น (กันลูป) —
      # เลยต้อง deploy Firebase ตรงนี้เลย ไม่ใช่พึ่ง deploy-site.yml
      - name: Deploy to Firebase Hosting (live channel)
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: ${{ secrets.GITHUB_TOKEN }}
          firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
          projectId: sectorrotation-546e0
          channelId: live
```

> **หมายเหตุ DST:** ตลาดสหรัฐปิด 16:00 ET = 20:00 UTC (ช่วง summer/EDT) หรือ 21:00 UTC (winter/EST)
> ตั้ง cron ที่ 22:30 UTC เพื่อเผื่อทั้งสองกรณี · เอกสารในโค้ดต้องอธิบายจุดนี้
>
> **ทำไม `daily.yml` จึง deploy เอง ไม่พึ่ง `deploy-site.yml`?** เพราะ `git push` ที่ทำด้วย
> `GITHUB_TOKEN` เริ่มต้นถูกออกแบบให้ *ไม่* trigger workflow อื่น (กันลูป) ถ้าปล่อยให้ push
> ไป trigger `deploy-site.yml` การอัปเดตข้อมูลรายวันจะไม่ถูก deploy เลย

---

## 13. Local Development (วิธีรันบนเครื่องตัวเอง)

```bash
git clone <repo>
cd rotation-tracker
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
python -m pipeline.run                              # สร้าง web/public/data.json
cd web/public && python -m http.server 8000         # เปิด http://localhost:8000
pytest                                              # รัน unit test
```
> README.md ต้องมีขั้นตอนนี้เป็นภาษาไทย พร้อมภาพ/คำอธิบายสำหรับมือใหม่

---

## 14. Testing & Acceptance Criteria (เกณฑ์ตรวจรับงาน)

### 14.1 Unit tests (pytest, ใช้ข้อมูลปลอมที่รู้คำตอบล่วงหน้า)
- `test_period_return`: ราคา 100→110 ให้ผล +10.00%
- `test_breadth`: 8 หุ้น 4 ตัวเหนือ MA ให้ 50.0%
- `test_dollar_vol_ratio`: กรณีคุมค่า ให้ค่าตามคำนวณมือ
- `test_classify`: ทดสอบครบ 4 quadrant ที่ขอบ 100/100
- `test_rrg_reproducible`: ป้อน series เดิม 2 ครั้ง ต้องได้ค่าเท่ากันเป๊ะ

### 14.2 Acceptance — Phase 1 (ถือว่าเสร็จเมื่อ)
- [ ] รัน `python -m pipeline.run` แล้วได้ `data.json` ครบทุกธีม ตาม schema ข้อ 10
- [ ] เปิดหน้าเว็บเห็น Heatmap + Breadth table + Appendix ถูกต้อง
- [ ] toggle EN/TH เปลี่ยนข้อความทั้งหน้า และจำค่าใน localStorage
- [ ] ใช้งานได้บนจอมือถือ (< 480px) โดยไม่ล้น
- [ ] GitHub Actions รันสำเร็จ + deploy ขึ้น GitHub Pages เปิดได้จริง
- [ ] มี disclaimer + note equal-weight แสดงชัดเจน
- [ ] เมื่อ yahoo ดึง ticker ไม่ได้ ระบบใช้ cache และไม่ crash

### 14.3 Acceptance — Phase 2 (เพิ่มเติมจาก Phase 1)
- [ ] RRG แสดงหาง 8 สัปดาห์ ต่อธีม + แบ่ง 4 โซนถูกต้อง + hover/click ทำงาน
- [ ] Momentum Playbook จัดกลุ่ม 4 โซน เรียงตาม 1M vs SPY + สี breadth ถูก
- [ ] ป้าย 📍 ปรากฏบนธีมใน `user_holdings`
- [ ] quadrant ที่แสดงตรงกับตำแหน่งบน RRG

---

## 15. Disclaimer (ต้องแสดงบนหน้าเว็บ — ทั้ง EN/TH)

**TH:** "ข้อมูลบนหน้านี้เป็นเครื่องมือเพื่อการศึกษาและสังเกตการณ์เท่านั้น ไม่ใช่คำแนะนำการลงทุนหรือคำแนะนำซื้อขายรายตัว การคำนวณใช้ตะกร้าแบบ equal-weight ซึ่งอาจต่างจาก ETF จริงที่ถ่วงตาม market cap การลงทุนมีความเสี่ยง ผู้ลงทุนควรศึกษาข้อมูลและปรึกษาผู้เชี่ยวชาญที่มีใบอนุญาตก่อนตัดสินใจ"

**EN:** "This dashboard is for educational and observational purposes only. It is not investment advice or a recommendation to buy/sell any security. Calculations use equal-weight baskets, which may differ from real ETFs (market-cap weighted). Investing involves risk; consult a licensed professional before making decisions."

---

## 16. Error Handling & Edge Cases

| กรณี | วิธีจัดการ |
|---|---|
| yahoo ดึง ticker บางตัวไม่ได้ | ใช้ cache + ใส่ warning ใน json |
| ธีมมีข้อมูลไม่ครบ | `data_ok=false` + frontend แสดงป้ายเทา "ข้อมูลไม่ครบ" |
| ประวัติราคาสั้นกว่า 3M | ช่อง m3 = null, frontend แสดง "–" |
| RRG ยังคำนวณไม่ได้ (ประวัติ < 52 สัปดาห์) | `rrg=null`, ธีมไม่ขึ้นบน RRG แต่ยังอยู่ใน heatmap |
| หารด้วยศูนย์ / NaN | คืน null และ log; ห้าม crash pipeline ทั้งชุด |
| ETF จ่ายปันผล/แตกพาร์ | ใช้ `auto_adjust=False` + คอลัมน์ `Close` (split-adjusted, ไม่รวมปันผล — ตรงกับกราฟราคาของ Yahoo) |

---

## 17. ภาคผนวก A — Universe (ตะกร้าธีม + constituents)

> เก็บใน `data/universe.yaml` · `type: theme` มี breadth · `type: sector_etf` เป็น ticker เดียว
> รายชื่อ constituents/ref_etfs อ้างอิงจากหน้า Appendix ของ dashboard ต้นฉบับ

**Themes (type: theme, equal-weight ของ constituents):**
| id | name_en | constituents | ref_etfs |
|---|---|---|---|
| semiconductors | Semiconductors | NVDA, AMD, AVGO, TSM, QCOM, TXN, INTC, MRVL | SMH, SOXX |
| semi_equip_memory | Semi Equip & Memory | MU, WDC, STX, AMAT, LRCX, KLAC, ASML | (SMH) |
| software | Software | MSFT, ORCL, CRM, ADBE, NOW, PLTR, INTU, SNPS, CDNS | IGV, XSW |
| mag7 | Mag 7 | AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA | MAGS |
| cybersecurity | Cybersecurity | CRWD, PANW, FTNT, ZS, OKTA | CIBR, HACK, BUG |
| genomics | Genomics | CRSP, EDIT, BEAM, NTLA, ILMN, RXRX, TWST, PACB | ARKG, IDNA |
| biotech_large | Biotech Large | AMGN, GILD, VRTX, REGN, BIIB | IBB, XBI |
| pharma_managed_care | Pharma & Managed Care | LLY, UNH, JNJ, MRK, ABBV, PFE | IHE, XLV |
| defense | Defense | LMT, RTX, NOC, GD, LHX | ITA, XAR, PPA |
| energy | Energy | XOM, CVX, COP, SLB, EOG | XLE, XOP, OIH |
| banks_brokers | Banks & Brokers | JPM, GS, MS, BAC, WFC | KBWB, KBE, IAI |
| staples | Staples | PG, KO, PEP, COST, WMT | XLP |
| utilities_power | Utilities & Power | NEE, DUK, SO, VST, CEG | XLU, GRID |
| materials | Materials | LIN, FCX, NUE, SHW, APD | XLB |
| ai_infra_datacenter | AI Infra & Data Center | VRT, ETN, ANET, SMCI, DELL, CIEN | AIQ, DTCR, GRID |
| quantum | Quantum | IONQ, RGTI, QBTS | QTUM |
| nuclear_uranium | Nuclear & Uranium | CCJ, OKLO, SMR, LEU, BWXT | URA, NLR, URNM |
| gold_miners | Gold Miners | NEM, AEM, GOLD, WPM | GDX, GDXJ, GLD |
| solar | Solar | FSLR, ENPH, NXT, RUN | TAN, ICLN |
| crypto_linked | Crypto-linked | COIN, MSTR, HOOD, MARA, RIOT | IBIT, DAPP, WGMI |
| space_drones | Space & Drones | RKLB, ASTS, AVAV, KTOS, LUNR | ARKX, UFO |
| china_tech_adr | China Tech ADR | BABA, PDD, BIDU, JD, BEKE | KWEB, CQQQ |
| homebuilders | Homebuilders | DHI, LEN, PHM, TOL, NVR | ITB, XHB |
| travel_airlines | Travel & Airlines | BKNG, ABNB, MAR, DAL, UAL, RCL | JETS, PEJ |
| fintech_payments | Fintech & Payments | V, MA, PYPL, AXP, COF | IPAY, FINX |

**Sector ETFs (type: sector_etf, ticker เดียว, ไม่มี breadth):**
| id | name_en | ticker |
|---|---|---|
| xlk | Tech (XLK) | XLK |
| xlf | Financials (XLF) | XLF |
| xlv | Health Care (XLV) | XLV |
| xle | Energy (XLE) | XLE |
| xli | Industrials (XLI) | XLI |
| xlu | Utilities (XLU) | XLU |
| xlp | Staples (XLP) | XLP |
| xlre | Real Estate (XLRE) | XLRE |
| xlb | Materials (XLB) | XLB |
| xly | Cons Discret (XLY) | XLY |
| xlc | Comm Svcs (XLC) | XLC |

> **หมายเหตุ:** บางธีมชื่อซ้ำกับ sector ETF (เช่น "Staples" theme กับ "Staples (XLP)") — ถือเป็นคนละรายการ
> theme = ตะกร้าหุ้น equal-weight, sector_etf = ETF ตัวเดียว · ตรงตาม dashboard ต้นฉบับ
> ก่อน production ควร verify ticker ทุกตัวว่ายัง trade อยู่ (บางตัวอาจ delist/เปลี่ยนชื่อ)

---

## 18. ภาคผนวก B — config.yaml (ค่า default)

```yaml
benchmark: SPY
history_days: 400            # จำนวนวันปฏิทินที่ดึงย้อนหลัง

returns:
  d1: 1
  w1: 5
  m1: 21
  m3: 63

breadth:
  ma_window: 20              # 20DMA

dollar_volume:
  short: 5
  long: 20

rrg:
  smoothing: 10              # span ของ EMA (สัปดาห์)
  lookback_weeks: 52         # หน้าต่าง normalize (z-score)
  scale: 10                  # ตัวคูณ z-score (คุมช่วงค่าให้ราว 70..140)
  tail_weeks: 8              # จำนวนจุดหางบน RRG

breadth_health:              # เกณฑ์สีใน Playbook
  green_min: 50
  yellow_min: 30

user_holdings:               # ธีมที่ผู้ใช้ถือ (ใส่ป้าย 📍)
  - semiconductors

fetch:
  retries: 3
  retry_wait_sec: 5
```

---

## 19. Open Questions / TODO ก่อนเริ่มโค้ด
1. ยืนยันรายชื่อ constituents ล่าสุด (บาง ticker อาจเปลี่ยน เช่น GOOG/GOOGL, ผู้เล่นใหม่)
2. ยืนยันโดเมน: จะใช้ `username.github.io/rotation-tracker` หรือ custom domain?
3. ค่า `rrg.scale` = 10 เป็นค่าเริ่มต้น — ปรับหลังเห็นผลจริงให้ช่วงกราฟสวยเหมือนต้นฉบับ
4. Phase 3: ช่องทางแจ้งเตือน (LINE Notify กำลังจะปิด — พิจารณา LINE Messaging API / อีเมล / Telegram)

---
*จบเอกสาร spec.md v1.0*
