"""
SpamGuard AI - Phase 1: Enron Dataset Inspection Script
Reads enron_spam_data.csv, reports schema, stats, issues, email vs SMS classification.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np

CSV_PATH = "dataset/enron_spam_data.csv"

def main():
    print("\n" + "=" * 70)
    print("  SpamGuard AI — PHASE 1: Enron Dataset Inspection Report")
    print("=" * 70)

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: File not found at {CSV_PATH}")
        return

    # --- 1. Load ---
    print(f"\n[1/7] Loading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"  Raw rows loaded: {len(df):,}")
    print(f"  Columns ({len(df.columns)}): {df.columns.tolist()}")

    # --- 2. Schema ---
    print("\n[2/7] Column Data Types & Non-Null Counts:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notna().sum()
        null_count = df[col].isna().sum()
        sample = repr(str(df[col].dropna().iloc[0])[:80]) if non_null > 0 else "N/A"
        print(f"  {col:<25} dtype={dtype:<10} non-null={non_null:<7} null={null_count:<7} sample={sample}")

    # --- 3. Label Distribution ---
    print("\n[3/7] Label / Spam Column Analysis:")
    # Try to identify the label column
    label_candidates = [c for c in df.columns if any(kw in c.lower() for kw in ["spam", "label", "class", "ham", "category"])]
    print(f"  Candidate label columns: {label_candidates}")
    for col in label_candidates:
        print(f"\n  Value counts for '{col}':")
        vc = df[col].value_counts(dropna=False)
        for val, cnt in vc.items():
            pct = cnt / len(df) * 100
            print(f"    {str(val):<20} {cnt:>8,} ({pct:.1f}%)")

    # --- 4. Missing Values ---
    print("\n[4/7] Missing Value Analysis:")
    total = len(df)
    for col in df.columns:
        null_count = df[col].isna().sum()
        empty_str = (df[col].astype(str).str.strip() == "").sum() if df[col].dtype == object else 0
        pct = null_count / total * 100
        print(f"  {col:<25} null={null_count:>6} ({pct:.1f}%)  empty_string={empty_str}")

    # --- 5. Duplicates ---
    print("\n[5/7] Duplicate Analysis:")
    # Identify text columns
    text_candidates = [c for c in df.columns if df[c].dtype == object and c.lower() not in ["spam", "label", "category", "class"]]
    print(f"  Text candidates: {text_candidates}")
    dup_full = df.duplicated().sum()
    print(f"  Fully duplicate rows: {dup_full:,}")
    for col in text_candidates[:3]:
        dup_col = df[col].duplicated().sum()
        pct = dup_col / total * 100
        print(f"  Duplicate '{col}' values: {dup_col:,} ({pct:.1f}%)")

    # --- 6. Text Length Analysis ---
    print("\n[6/7] Email Body / Subject Length Analysis:")
    for col in text_candidates[:4]:
        series = df[col].dropna().astype(str)
        lens = series.str.len()
        words = series.str.split().str.len()
        print(f"\n  Column: '{col}'")
        print(f"    Avg char length  : {lens.mean():.0f}")
        print(f"    Median char length: {lens.median():.0f}")
        print(f"    Max char length  : {lens.max():.0f}")
        print(f"    Min char length  : {lens.min():.0f}")
        print(f"    Avg word count   : {words.mean():.1f}")
        print(f"    Median word count: {words.median():.1f}")
        # Sample rows
        print(f"    5 sample texts:")
        for sample in series.head(5):
            print(f"      {repr(sample[:120])}")

    # --- 7. Email vs SMS Determination ---
    print("\n[7/7] Email vs SMS Content Classification:")
    # Heuristics: email indicators = "subject:", email addresses, long bodies
    # SMS indicators: short length < 160 chars, SMS abbrevs
    body_col = None
    for col in text_candidates:
        avg_len = df[col].dropna().astype(str).str.len().mean()
        if avg_len > 100:
            body_col = col
            break

    if body_col:
        series = df[body_col].dropna().astype(str)
        avg_len = series.str.len().mean()
        median_len = series.str.len().median()
        has_email_addr = series.str.contains(r"@", regex=False).mean() * 100
        has_subject = series.str.lower().str.contains(r"subject:", regex=False).mean() * 100
        has_multiline = (series.str.count("\n") > 2).mean() * 100
        short_msgs = (series.str.len() < 160).mean() * 100

        print(f"\n  Using column: '{body_col}' for analysis")
        print(f"  Average length: {avg_len:.0f} chars  |  Median: {median_len:.0f} chars")
        print(f"  % messages with '@' (email addr): {has_email_addr:.1f}%")
        print(f"  % messages with 'Subject:' keyword: {has_subject:.1f}%")
        print(f"  % messages with multi-line content (>2 newlines): {has_multiline:.1f}%")
        print(f"  % messages < 160 chars (SMS-like): {short_msgs:.1f}%")

        if avg_len > 300 or has_multiline > 30 or has_email_addr > 10:
            print("\n  VERDICT: These appear to be REAL EMAILS (multi-line, long, contains email-like content)")
        elif short_msgs > 60:
            print("\n  VERDICT: These appear to be SMS MESSAGES (short, under 160 chars)")
        else:
            print("\n  VERDICT: Mixed/unclear — further inspection required")
    else:
        print("  Could not determine body column for classification")

    print("\n" + "=" * 70)
    print("  PHASE 1 INSPECTION COMPLETE. No files modified.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

