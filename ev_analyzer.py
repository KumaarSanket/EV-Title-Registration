#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║    ELECTRIC VEHICLE DATA — COMPREHENSIVE CSV ANALYZER           ║
╚══════════════════════════════════════════════════════════════════╝

Produces a full EDA report covering:
  1. File information            6. Text quality checks
  2. Dataset overview            7. Data quality report
  3. Column-by-column analysis   8. Memory usage by column
  4. Numeric statistics          9. Cleaning recommendations
  5. Date analysis

INSTALL DEPENDENCIES FIRST:
    pip install pandas numpy chardet

THEN RUN:
    python ev_analyzer.py
"""

import os, sys, re, warnings
from datetime import datetime

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")


# ═══════════════════════════════════════════════════════════════════
#   ★  CONFIGURATION  — edit only this block if needed
# ═══════════════════════════════════════════════════════════════════

FILE_PATH = (
    r"C:\Users\kumar_\Desktop\KS\Analytics\PROJECTS"
    r"\Electric Vehicle Population"
    r"\Electric_Vehicle_Title_and_Registration_Activity_20260623.csv"
)

# Columns treated as numeric for Section 4
NUMERIC_COLS = [
    "Sale Price",
    "Electric Range",
    "Model Year",
    "Odometer Reading",
]

# Columns treated as dates for Section 5
DATE_COLS = [
    "Sale Date",
    "Transaction Date",
]

# If a column has ≤ this many unique values → print ALL in report
# If more → print Top 20 and save a CSV to UV_FOLDER
HIGH_CARD_THRESHOLD = 50

REPORT_FILE = "EV_Analysis_Report.txt"   # main report output
UV_FOLDER   = "unique_values"            # folder for unique-value CSVs

# ═══════════════════════════════════════════════════════════════════


# ── tiny helpers ────────────────────────────────────────────────────

def human_size(b):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.2f} {u}"
        b /= 1024


def detect_encoding(path, sample_bytes=200_000):
    try:
        import chardet
        with open(path, "rb") as fh:
            raw = fh.read(sample_bytes)
        r = chardet.detect(raw)
        return (r.get("encoding") or "utf-8"), r.get("confidence", 0.0)
    except ImportError:
        print("  ℹ  chardet not installed — defaulting to utf-8")
        return "utf-8", None


def safe_fname(col):
    """Turn a column name into a filesystem-safe stem (max 60 chars)."""
    return re.sub(r"\W+", "_", str(col))[:60]


# ── Logger: tees output to console AND the report file ──────────────

class Log:
    def __init__(self, path):
        self._fh = open(path, "w", encoding="utf-8")

    def __call__(self, msg=""):
        print(msg)
        self._fh.write(str(msg) + "\n")

    def close(self):
        self._fh.close()


# ══════════════════════════════════════════════════════════════════════
#   MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    if not os.path.exists(FILE_PATH):
        sys.exit(
            f"\n❌  File not found:\n    {FILE_PATH}"
            "\n\n    Check the FILE_PATH variable at the top of this script.\n"
        )

    os.makedirs(UV_FOLDER, exist_ok=True)
    started = datetime.now()
    log = Log(REPORT_FILE)

    W = 80                               # report width

    def hr(ch="─", n=W):
        return ch * n

    def section(title):
        log("\n" + hr("═"))
        log(f"  {title}")
        log(hr("═"))

    # ── header ────────────────────────────────────────────────────
    log(hr("═"))
    log("   ELECTRIC VEHICLE DATA  ·  COMPREHENSIVE ANALYSIS REPORT")
    log(f"   Generated : {started.strftime('%Y-%m-%d  %H:%M:%S')}")
    log(hr("═"))

    # ─────────────────────────────────────────────────────────────
    # 1. FILE INFORMATION
    # ─────────────────────────────────────────────────────────────
    section("1 ·  FILE INFORMATION")

    raw_bytes = os.path.getsize(FILE_PATH)
    enc, conf = detect_encoding(FILE_PATH)
    conf_str  = f"  (confidence {conf:.0%})" if conf is not None else ""

    log(f"  File Name  : {os.path.basename(FILE_PATH)}")
    log(f"  Full Path  : {FILE_PATH}")
    log(f"  File Size  : {human_size(raw_bytes)}  ({raw_bytes:,} bytes)")
    log(f"  Encoding   : {enc}{conf_str}")

    # ─── LOAD ─────────────────────────────────────────────────────
    log(f"\n  ⏳  Loading file …  (may take 30–120 s for a 1 GB file)")
    t0 = datetime.now()

    try:
        df = pd.read_csv(FILE_PATH, encoding=enc, low_memory=False)
    except UnicodeDecodeError as e:
        log(f"  ⚠  {enc} failed ({e})  →  retrying with latin-1")
        df = pd.read_csv(FILE_PATH, encoding="latin-1", low_memory=False)
    except Exception as e:
        log(f"  ⚠  Error: {e}  →  retrying with latin-1")
        df = pd.read_csv(FILE_PATH, encoding="latin-1", low_memory=False)

    load_s     = (datetime.now() - t0).total_seconds()
    rows, cols = df.shape
    mem_mb     = df.memory_usage(deep=True).sum() / 1_048_576

    log(f"  Load Time  : {load_s:.1f} s")
    log(f"  Rows       : {rows:,}")
    log(f"  Columns    : {cols}")
    log(f"  RAM Usage  : {mem_mb:.2f} MB")

    # ─────────────────────────────────────────────────────────────
    # 2. DATASET OVERVIEW
    # ─────────────────────────────────────────────────────────────
    section("2 ·  DATASET OVERVIEW")

    dup_n   = int(df.duplicated().sum())
    dup_pct = dup_n / rows * 100
    tot_cel = rows * cols
    tot_mis = int(df.isna().sum().sum())
    mis_pct = tot_mis / tot_cel * 100

    log(f"  Shape                : {rows:,} rows  ×  {cols} columns")
    log(f"  Duplicate Rows       : {dup_n:,}  ({dup_pct:.2f} %)")
    log(f"  Total Cells          : {tot_cel:,}")
    log(f"  Total Missing Cells  : {tot_mis:,}  ({mis_pct:.2f} %)")

    log(f"\n  {'#':>3}  {'Column Name':<55}  {'Dtype':<12}  {'Missing':>10}")
    log("  " + hr("-", 76))
    for i, c in enumerate(df.columns, 1):
        mc  = int(df[c].isna().sum())
        mcp = mc / rows * 100
        log(f"  {i:>3}. {c:<55}  {str(df[c].dtype):<12}  {mc:>6,} ({mcp:.1f}%)")

    # ─────────────────────────────────────────────────────────────
    # 3. COLUMN-BY-COLUMN ANALYSIS
    # ─────────────────────────────────────────────────────────────
    section("3 ·  COLUMN-BY-COLUMN ANALYSIS")

    for col in df.columns:
        s        = df[col]
        dtype    = s.dtype
        n_miss   = int(s.isna().sum())
        miss_pct = n_miss / rows * 100
        n_valid  = int(s.notna().sum())
        n_uniq   = int(s.nunique())

        log("")
        log("  ┌" + hr("─", W - 4))
        log(f"  │  COLUMN : {col}")
        log("  ├" + hr("─", W - 4))
        log(f"  │  Data Type          : {dtype}")
        log(f"  │  Missing Values     : {n_miss:,}  ({miss_pct:.2f} %)")
        log(f"  │  Non-Null Values    : {n_valid:,}")
        log(f"  │  Unique Values      : {n_uniq:,}")

        if n_valid == 0:
            log("  └" + hr("─", W - 4))
            continue

        # Most frequent value
        vc = s.value_counts(dropna=True)
        top_v, top_c = vc.index[0], int(vc.iloc[0])
        top_pct = top_c / n_valid * 100
        log(f"  │  Most Frequent      : {str(top_v)[:50]!r}  ({top_c:,}×  {top_pct:.1f} %)")

        # String-specific metrics
        if dtype == object:
            ss   = s.dropna().astype(str)
            lens = ss.str.len()
            samp = ss.sample(min(5, n_valid), random_state=42).tolist()
            log(f"  │  Length min/max/avg : {int(lens.min())} / {int(lens.max())} / {lens.mean():.1f}")
            log(f"  │  Sample Values      : {samp}")

        is_numeric_col = np.issubdtype(dtype, np.number)

        # Unique value listing
        if n_uniq <= HIGH_CARD_THRESHOLD:
            log(f"  │  All Unique Values  ({n_uniq} total):")
            for val, cnt in vc.items():
                pct = cnt / n_valid * 100
                log(f"  │      {str(val):<46}  {cnt:>8,}  ({pct:.1f} %)")
        elif is_numeric_col:
            log(f"  │  (Numeric column — full stats in Section 4)")
        else:
            log(f"  │  Top 20 of {n_uniq:,} unique values:")
            for val, cnt in vc.head(20).items():
                pct = cnt / n_valid * 100
                log(f"  │      {str(val):<46}  {cnt:>8,}  ({pct:.1f} %)")
            uv_csv = os.path.join(UV_FOLDER, safe_fname(col) + "_unique.csv")
            pd.DataFrame({"value": vc.index, "count": vc.values}).to_csv(
                uv_csv, index=False
            )
            log(f"  │  → Full list ({n_uniq:,} rows) saved → {uv_csv}")

        log("  └" + hr("─", W - 4))

    # ─────────────────────────────────────────────────────────────
    # 4. NUMERIC COLUMN ANALYSIS
    # ─────────────────────────────────────────────────────────────
    section("4 ·  NUMERIC COLUMN ANALYSIS")

    for col in NUMERIC_COLS:
        if col not in df.columns:
            log(f"\n  ⚠  '{col}' not found in dataset — skipped")
            continue

        raw_s = df[col]
        s     = pd.to_numeric(raw_s, errors="coerce")
        v     = s.dropna()
        n_ok  = len(v)
        n_bad = int(raw_s.notna().sum()) - n_ok

        log(f"\n  Column : {col}")
        log("  " + hr("-", 55))

        if n_ok == 0:
            log("  No valid numeric values found.")
            continue

        q25, q75 = v.quantile(0.25), v.quantile(0.75)
        iqr      = q75 - q25
        out_lo   = q25 - 1.5 * iqr
        out_hi   = q75 + 1.5 * iqr
        n_out    = int(((v < out_lo) | (v > out_hi)).sum())

        log(f"  Valid count          : {n_ok:,}")
        log(f"  Non-numeric / NaN    : {n_bad:,}")
        log(f"  Min                  : {v.min():,.4f}")
        log(f"  Max                  : {v.max():,.4f}")
        log(f"  Mean                 : {v.mean():,.4f}")
        log(f"  Median               : {v.median():,.4f}")
        log(f"  Std Dev              : {v.std():,.4f}")
        log(f"  Variance             : {v.var():,.4f}")
        log(f"  Q1  (25 %)           : {q25:,.4f}")
        log(f"  Q3  (75 %)           : {q75:,.4f}")
        log(f"  IQR                  : {iqr:,.4f}")
        log(f"  Outliers (IQR rule)  : {n_out:,}")
        log(f"  Negative values      : {int((v < 0).sum()):,}")
        log(f"  Zero values          : {int((v == 0).sum()):,}")

    # ─────────────────────────────────────────────────────────────
    # 5. DATE COLUMN ANALYSIS
    # ─────────────────────────────────────────────────────────────
    section("5 ·  DATE COLUMN ANALYSIS")

    MONTH_NAMES = {
        1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun",
        7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec",
    }

    for col in DATE_COLS:
        if col not in df.columns:
            log(f"\n  ⚠  '{col}' not found in dataset — skipped")
            continue

        raw_s = df[col]
        ds    = pd.to_datetime(raw_s, errors="coerce", infer_datetime_format=True)
        valid = ds.dropna()
        n_inv = int(raw_s.notna().sum()) - len(valid)

        log(f"\n  Column : {col}")
        log("  " + hr("-", 55))

        if len(valid) == 0:
            log("  No valid dates found.")
            continue

        years  = sorted(valid.dt.year.unique())
        months = sorted(valid.dt.month.unique())

        log(f"  Valid dates          : {len(valid):,}")
        log(f"  Invalid / unparsed   : {n_inv:,}")
        log(f"  Earliest             : {valid.min().date()}")
        log(f"  Latest               : {valid.max().date()}")
        log(f"  Years present        : {years}")
        log(f"  Months present       : {[MONTH_NAMES[m] for m in months]}")

        # Year distribution bar chart (text)
        log("  Year distribution:")
        yr_vc = valid.dt.year.value_counts().sort_index()
        max_c = yr_vc.max()
        for yr, cnt in yr_vc.items():
            bar = "█" * max(1, int(cnt / max_c * 40))
            log(f"      {yr}  {cnt:>9,}  {bar}")

    # ─────────────────────────────────────────────────────────────
    # 6. TEXT QUALITY CHECKS
    # ─────────────────────────────────────────────────────────────
    section("6 ·  TEXT QUALITY CHECKS")
    log("  (checks leading/trailing spaces, blank strings, case issues)\n")

    any_issue = False
    for col in df.select_dtypes(include="object").columns:
        ss = df[col].dropna().astype(str)
        if len(ss) == 0:
            continue

        lead  = int(ss.str.startswith(" ").sum())
        trail = int(ss.str.endswith(" ").sum())
        blank = int((ss.str.strip() == "").sum())
        upper = int(ss.str.isupper().sum())
        lower = int(ss.str.islower().sum())
        alpha = ss.str.contains("[a-zA-Z]", na=False, regex=True)
        mixed = int((~ss.str.isupper() & ~ss.str.islower() & alpha).sum())

        if any([lead, trail, blank, upper, lower, mixed]):
            any_issue = True
            log(f"  Column : {col}")
            log(f"    Leading spaces    : {lead:,}")
            log(f"    Trailing spaces   : {trail:,}")
            log(f"    Blank strings     : {blank:,}")
            log(f"    ALL UPPER rows    : {upper:,}")
            log(f"    all lower rows    : {lower:,}")
            log(f"    Mixed case rows   : {mixed:,}")
            log("")

    if not any_issue:
        log("  ✅  No whitespace / case issues detected.")

    # ─────────────────────────────────────────────────────────────
    # 7. DATA QUALITY REPORT
    # ─────────────────────────────────────────────────────────────
    section("7 ·  DATA QUALITY REPORT")

    def dq(label, n, note=""):
        flag = "⚠ " if n > 0 else "✅"
        suffix = f"  ← {note}" if note else ""
        log(f"  {flag}  {label:<52}  {n:>10,}{suffix}")

    log("")

    # Duplicate VINs
    if "VIN (1-10)" in df.columns:
        dq("Duplicate VINs (1-10)", int(df["VIN (1-10)"].duplicated().sum()))

    # Impossible Model Years
    if "Model Year" in df.columns:
        yr = pd.to_numeric(df["Model Year"], errors="coerce")
        dq(
            "Impossible Model Years (<1900 or >2030)",
            int(((yr < 1900) | (yr > 2030)).sum()),
        )

    # Negative Sale Prices
    if "Sale Price" in df.columns:
        sp = pd.to_numeric(df["Sale Price"], errors="coerce")
        dq("Negative Sale Prices", int((sp < 0).sum()))

    # Invalid Postal Codes
    if "Postal Code" in df.columns:
        pc = df["Postal Code"].fillna("").astype(str)
        dq(
            "Invalid Postal Codes (not exactly 5 digits)",
            int((~pc.str.match(r"^\d{5}$")).sum()),
        )

    # Missing City / State
    if "City"  in df.columns: dq("Missing City",  int(df["City"].isna().sum()))
    if "State" in df.columns: dq("Missing State", int(df["State"].isna().sum()))

    # Electric Range issues
    if "Electric Range" in df.columns:
        er = pd.to_numeric(df["Electric Range"], errors="coerce")
        dq("Negative Electric Range",        int((er < 0).sum()))
        dq("Zero Electric Range",            int((er == 0).sum()))
        dq("Extreme Electric Range (>1000)", int((er > 1000).sum()))

    # Blank strings (non-NaN but empty after strip)
    log("\n  Blank string values (empty but NOT NaN) by column:")
    found_blank = False
    for col in df.select_dtypes(include="object").columns:
        b = int((df[col].fillna("").astype(str).str.strip() == "").sum())
        if b:
            found_blank = True
            log(f"    ⚠   {col:<55}  {b:>10,}")
    if not found_blank:
        log("    ✅  None found.")

    # ─────────────────────────────────────────────────────────────
    # 8. MEMORY USAGE BY COLUMN
    # ─────────────────────────────────────────────────────────────
    section("8 ·  MEMORY USAGE BY COLUMN")

    mem = df.memory_usage(deep=True).drop("Index").sort_values(ascending=False)
    log(f"  {'Column':<55}  {'Size (KB)':>10}")
    log("  " + hr("-", 68))
    for col, b in mem.items():
        log(f"  {col:<55}  {b/1024:>10.1f}")
    log(f"\n  TOTAL IN-MEMORY:  {mem.sum() / 1_048_576:.2f} MB")

    # ─────────────────────────────────────────────────────────────
    # 9. CLEANING RECOMMENDATIONS
    # ─────────────────────────────────────────────────────────────
    section("9 ·  CLEANING RECOMMENDATIONS")
    recs = []

    if dup_n:
        recs.append(
            f"• {dup_n:,} duplicate rows detected.\n"
            f"  → df.drop_duplicates(inplace=True)"
        )

    miss_cols = df.columns[df.isna().any()].tolist()
    if miss_cols:
        sample = ", ".join(f"'{c}'" for c in miss_cols[:4])
        ellipsis = " …" if len(miss_cols) > 4 else ""
        recs.append(
            f"• Missing values in {len(miss_cols)} column(s): {sample}{ellipsis}\n"
            f"  → Use df[col].fillna(value) or df.dropna(subset=[col])"
        )

    for col in df.select_dtypes(include="object").columns:
        ss = df[col].dropna().astype(str)
        if ss.str.startswith(" ").any() or ss.str.endswith(" ").any():
            recs.append(
                "• Whitespace found in one or more text columns.\n"
                "  → df[col] = df[col].str.strip()   (apply to each affected column)"
            )
            break

    if "Sale Price" in df.columns:
        sp = pd.to_numeric(df["Sale Price"], errors="coerce")
        if (sp < 0).any():
            recs.append(
                "• Negative Sale Prices found — investigate or remove.\n"
                "  → df = df[df['Sale Price'] >= 0]"
            )

    if "Model Year" in df.columns:
        yr = pd.to_numeric(df["Model Year"], errors="coerce")
        if ((yr < 1900) | (yr > 2030)).any():
            recs.append(
                "• Impossible Model Year values found.\n"
                "  → df = df[df['Model Year'].between(1900, 2030)]"
            )

    if "Postal Code" in df.columns:
        pc = df["Postal Code"].fillna("").astype(str)
        if (~pc.str.match(r"^\d{5}$")).any():
            recs.append(
                "• Invalid postal codes (non-5-digit) found.\n"
                "  → df['Postal Code'] = df['Postal Code'].astype(str).str.zfill(5)"
            )

    if "VIN (1-10)" in df.columns and df["VIN (1-10)"].duplicated().any():
        recs.append(
            "• Duplicate VIN (1-10) values found — check if intentional.\n"
            "  → df.drop_duplicates(subset=['VIN (1-10)'], inplace=True)"
        )

    if not recs:
        recs.append("✅ No major issues detected — data looks clean!")

    for r in recs:
        log(f"\n  {r}")

    # ── FOOTER ────────────────────────────────────────────────────
    elapsed = (datetime.now() - started).total_seconds()
    log("\n" + hr("═"))
    log(f"  ✅  ANALYSIS COMPLETE  |  Total time : {elapsed:.1f} s")
    log(f"  📄  Report saved to   : {REPORT_FILE}")
    log(f"  📁  Unique value CSVs : {UV_FOLDER}{os.sep}")
    log(hr("═"))

    log.close()
    print(f"\n✅  Done!  Full report → {REPORT_FILE}")
    print(f"📁  Unique value CSVs → {UV_FOLDER}{os.sep}\n")


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
