"""
SpamGuard AI - Phase 2: Enron Dataset Preparation
Cleans the Enron dataset, normalizes labels, combines subject+body,
removes duplicates and empties, saves to dataset/processed/enron_spam_cleaned.csv.
Original file is NOT modified.
"""
import sys, os, pandas as pd
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC  = "dataset/enron_spam_data.csv"
DST  = "dataset/processed/enron_spam_cleaned.csv"
os.makedirs("dataset/processed", exist_ok=True)

print("\n" + "=" * 65)
print("  SpamGuard AI — PHASE 2: Dataset Preparation")
print("=" * 65)

# ── 1. Load original ──────────────────────────────────────────────
df = pd.read_csv(SRC, low_memory=False)
print(f"\n[1/6] Loaded original: {len(df):,} rows | columns={df.columns.tolist()}")

# ── 2. Normalize label column ─────────────────────────────────────
df['label'] = df['Spam/Ham'].str.strip().str.lower()
valid_labels = df['label'].isin(['spam', 'ham'])
invalid = (~valid_labels).sum()
df = df[valid_labels].copy()
print(f"\n[2/6] Label normalization:")
print(f"  Rows with valid labels (spam/ham): {len(df):,}")
print(f"  Rows with unexpected label values: {invalid}")
print(f"  spam={df['label'].eq('spam').sum():,}  ham={df['label'].eq('ham').sum():,}")

# ── 3. Combine Subject + Message into 'text' ──────────────────────
df['Subject'] = df['Subject'].fillna('').astype(str).str.strip()
df['Message'] = df['Message'].fillna('').astype(str).str.strip()
df['text'] = (df['Subject'] + ' ' + df['Message']).str.strip()
print(f"\n[3/6] Combined Subject + Message into 'text' column")

# ── 4. Remove rows where combined text is empty ───────────────────
before = len(df)
df = df[df['text'].str.len() > 0].copy()
removed_empty = before - len(df)
print(f"\n[4/6] Removed empty text rows: {removed_empty}")
print(f"  Remaining: {len(df):,}")

# ── 5. Remove duplicate text rows ────────────────────────────────
before = len(df)
df = df.drop_duplicates(subset=['text'], keep='first').copy()
removed_dup = before - len(df)
print(f"\n[5/6] Removed duplicate text rows: {removed_dup:,}")
print(f"  Remaining: {len(df):,}")

# ── 6. Final stats and save ───────────────────────────────────────
spam_count = df['label'].eq('spam').sum()
ham_count  = df['label'].eq('ham').sum()
total      = len(df)
ratio      = spam_count / ham_count if ham_count > 0 else float('inf')

print(f"\n[6/6] Final cleaned dataset stats:")
print(f"  Total records : {total:,}")
print(f"  Spam (spam=1) : {spam_count:,} ({spam_count/total*100:.1f}%)")
print(f"  Ham  (ham=0)  : {ham_count:,} ({ham_count/total*100:.1f}%)")
print(f"  Spam/Ham ratio: {ratio:.2f}")

# Keep only the columns needed for ML
df_out = df[['label', 'text']].copy()
df_out.to_csv(DST, index=False)
file_size_kb = os.path.getsize(DST) // 1024
print(f"\n  ✅ Cleaned dataset saved to: {DST}")
print(f"  File size: {file_size_kb:,} KB")

print("\n" + "-" * 65)
print("  Sample rows from cleaned dataset:")
print("-" * 65)
for _, row in df_out.head(5).iterrows():
    print(f"  [{row['label'].upper():<4}] {repr(row['text'][:120])}")

print("\n  ORIGINAL FILE NOT MODIFIED: dataset/enron_spam_data.csv")
print("=" * 65 + "\n")

