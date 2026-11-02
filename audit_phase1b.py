"""
Phase 1 - Deep text stats on Enron dataset
"""
import sys, pandas as pd, numpy as np
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

df = pd.read_csv('dataset/enron_spam_data.csv', low_memory=False)
subj = df['Subject'].fillna('').astype(str)
msg  = df['Message'].fillna('').astype(str)

print("=== SUBJECT COLUMN ===")
print(f"Avg chars:    {subj.str.len().mean():.0f}")
print(f"Median chars: {subj.str.len().median():.0f}")
print(f"Max chars:    {subj.str.len().max():.0f}")
print(f"Null Subject: {df['Subject'].isna().sum()}")
print("Samples:")
for s in subj[subj.str.len() > 5].head(5):
    print(f"  {repr(s[:100])}")

print()
print("=== MESSAGE COLUMN ===")
print(f"Avg chars:     {msg.str.len().mean():.0f}")
print(f"Median chars:  {msg.str.len().median():.0f}")
print(f"Max chars:     {msg.str.len().max():.0f}")
print(f"Min chars:     {msg.str.len().min():.0f}")
print(f"Avg words:     {msg.str.split().str.len().mean():.1f}")
print(f"Median words:  {msg.str.split().str.len().median():.1f}")
print(f"Pct with @:    {msg.str.contains('@', regex=False).mean()*100:.1f}%")
print(f"Pct multi-NL:  {(msg.str.count(chr(10)) > 2).mean()*100:.1f}%")
print(f"Pct < 160c:    {(msg.str.len() < 160).mean()*100:.1f}%")
print(f"Pct > 500c:    {(msg.str.len() > 500).mean()*100:.1f}%")
print(f"Null Message:  {df['Message'].isna().sum()}")
print("Samples:")
for s in msg[msg.str.len() > 100].head(5):
    print(f"  {repr(s[:150])}")

print()
print("=== DUPLICATE ANALYSIS ===")
combined = subj + ' ||| ' + msg
dup_combined = combined.duplicated().sum()
dup_msg_only  = msg.duplicated().sum()
print(f"Duplicate Subject+Message: {dup_combined}")
print(f"Duplicate Message only:    {dup_msg_only}")

print()
print("=== CLASS BALANCE ===")
print(df['Spam/Ham'].value_counts())
print(f"Total rows:      {len(df)}")
rows_after_drop = df.dropna(subset=['Subject','Message'], how='all').shape[0]
print(f"Rows after dropping both-null: {rows_after_drop}")

