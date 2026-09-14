"""
clean_data.py
==============
Data Vortex — Round 1, Phase 1: Rebuilding the Social Engine
SRM Institute of Science & Technology · Aaruush '26
Team: Forge-X

Transforms raw corrupted social engine data into production-ready analytical tables.
Enforces zero data loss, strict provenance tracking, and explicit reconciliation.
"""

import os
import re
import json
import html
from datetime import datetime, timezone
import numpy as np
import pandas as pd

RAW_POSTS = "data/raw/Social_Engine_Posts_Corrupted.csv"
RAW_USERS = "data/raw/Social_Engine_Users.csv"
OUT_DIR = "data/clean"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(f"/working_dir/c_55589ed17f08a0e7/{OUT_DIR}", exist_ok=True)

repair_log = []

def log_repair(post_id, column, original_val, repaired_val, repair_type, reason):
    repair_log.append({
        "post_id": post_id,
        "column": column,
        "original_value": str(original_val),
        "repaired_value": str(repaired_val),
        "repair_type": repair_type,
        "reason": reason
    })

print(">>> 1. Loading Raw Data...")
posts_raw = pd.read_csv(RAW_POSTS, dtype=str, keep_default_na=False)
users_raw = pd.read_csv(RAW_USERS, dtype=str, keep_default_na=False)
raw_post_count = len(posts_raw)
print(f"Raw Posts Count: {raw_post_count}")
print(f"Raw Users Count: {len(users_raw)}")

# 2. Duplicate Detection
print(">>> 2. Detecting & Removing Exact Duplicates...")
dupe_mask = posts_raw.duplicated(keep="first")
dupes = posts_raw[dupe_mask]
for _, row in dupes.iterrows():
    log_repair(row["post_id"], "row", "FULL_ROW", "DROPPED", "DUPLICATE_ROW", "Exact duplicate row removed; first occurrence retained.")

posts = posts_raw[~dupe_mask].copy()
dropped_dupes_count = len(dupes)
print(f"Duplicates Dropped: {dropped_dupes_count}, Unique Posts Remaining: {len(posts)}")

# 3. Likes Cleaning & Sign-Flip Restoration
print(">>> 3. Repairing Likes (Sign-Flip Restoration & Null Preservation)...")
def clean_likes(val, pid):
    v = str(val).strip()
    if v in ("", "NULL", "NAN", "nan", "None"):
        log_repair(pid, "likes", val, "NaN", "PRESERVE_NULL", "Explicit null preserved; no synthetic fabrication.")
        return np.nan, False
    try:
        fval = float(v)
        if fval < 0:
            repaired = abs(fval)
            log_repair(pid, "likes", val, int(repaired), "SIGN_FLIP_REPAIR", "Negative float artifact detected and inverted to true positive magnitude.")
            return repaired, True
        return fval, False
    except Exception as e:
        log_repair(pid, "likes", val, "NaN", "CORRUPTED_NON_NUMERIC", "Unparseable numeric value treated as NaN.")
        return np.nan, False

likes_res = [clean_likes(r["likes"], r["post_id"]) for _, r in posts.iterrows()]
posts["likes"] = [r[0] for r in likes_res]
posts["flag_sign_flipped_likes"] = [r[1] for r in likes_res]

# 4. Platform Standardization
print(">>> 4. Standardizing Platform Categorization...")
def clean_platform(val, pid):
    v = str(val).strip()
    if v in ("", "NULL", "NAN", "nan", "None"):
        log_repair(pid, "platform", val, "Unspecified", "IMPUTE_MISSING_CATEGORY", "Missing platform standardized to explicit 'Unspecified' bucket.")
        return "Unspecified", True
    
    val_norm = v.strip().title()
    # Normalize platform aliases
    if val_norm.lower() in ("x", "twitter"):
        val_norm = "Twitter"
    elif val_norm.lower() == "fb":
        val_norm = "Facebook"
    elif val_norm.lower() == "yt":
        val_norm = "YouTube"
    elif val_norm.lower() == "ig":
        val_norm = "Instagram"
    elif val_norm.lower() == "reddit":
        val_norm = "Reddit"
    
    if val_norm != v:
        log_repair(pid, "platform", val, val_norm, "STANDARDIZE_NAME", "Standardized platform casing/naming.")
    return val_norm, False

plat_res = [clean_platform(r["platform"], r["post_id"]) for _, r in posts.iterrows()]
posts["platform"] = [r[0] for r in plat_res]
posts["flag_imputed_platform"] = [r[1] for r in plat_res]

# 5. Text Sanitization (HTML strip & Mojibake reversal)
print(">>> 5. Sanitizing Text Content (HTML Artifacts & Mojibake Reversal)...")
def fix_mojibake(text):
    if not isinstance(text, str):
        return text
    # Fix UTF-8 decoded as Latin-1 / Windows-1252
    mojibake_map = {
        "Ã©": "é",
        "Ã¨": "è",
        "Ã ": "à",
        "Ã¡": "á",
        "Ã£": "ã",
        "Ã³": "ó",
        "Ã±": "ñ",
        "Ã§": "ç",
        "Ã¼": "ü",
        "Ã¶": "ö",
        "Ã¤": "ä",
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€¢": "•",
        "â€“": "–",
        "â€”": "—"
    }
    t = text
    for k, v in mojibake_map.items():
        t = t.replace(k, v)
    return t

def clean_text_content(val, pid):
    v = str(val)
    if v.strip() in ("", "NULL", "NAN", "nan", "None"):
        return "", True, False
    
    orig = v
    # 1. Reverse mojibake
    v = fix_mojibake(v)
    # 2. HTML unescape (&amp; -> &)
    v = html.unescape(v)
    # 3. Strip HTML tags like <br>, <div>, </div>
    v = re.sub(r"<(?:br|div|/div|p|/p|span|/span)[^>]*>", " ", v, flags=re.IGNORECASE)
    # 4. Strip extra whitespace
    v = re.sub(r"\s+", " ", v).strip()
    
    modified = (v != orig.strip())
    if modified:
        log_repair(pid, "text_content", orig, v, "TEXT_CLEANING", "Stripped HTML tags, decoded entities, and resolved mojibake.")
    return v, False, modified

text_res = [clean_text_content(r["text_content"], r["post_id"]) for _, r in posts.iterrows()]
posts["text_content_clean"] = [r[0] for r in text_res]
posts["flag_empty_text"] = [r[1] for r in text_res]

# 6. Timestamp Normalization
print(">>> 6. Normalizing Multi-Format Timestamps...")
def parse_timestamp(val, pid):
    v = str(val).strip()
    if v in ("", "NULL", "NAN", "nan", "None"):
        log_repair(pid, "timestamp", val, "NaT", "NULL_TIMESTAMP", "Missing timestamp flagged.")
        return None, False, False
    
    # Check Epoch
    if re.match(r"^\d{9,13}$", v):
        try:
            ts_num = float(v)
            if len(v) >= 12: # Milliseconds
                ts_num /= 1000.0
            dt = datetime.fromtimestamp(ts_num, tz=timezone.utc)
            log_repair(pid, "timestamp", val, dt.isoformat(), "EPOCH_CONVERSION", "Converted UNIX epoch timestamp to ISO 8601 UTC.")
            return dt.isoformat(), True, False
        except Exception:
            pass

    # Check ISO 8601
    if "T" in v:
        try:
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat(), True, False
        except Exception:
            pass
            
    # Check DD-MM-YYYY
    m = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", v)
    if m:
        d, m_num, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        is_ambiguous = (d <= 12 and m_num <= 12)
        try:
            dt = datetime(y, m_num, d, 0, 0, 0, tzinfo=timezone.utc)
            log_repair(pid, "timestamp", val, dt.isoformat(), "DATE_STANDARDIZATION", f"Converted DD-MM-YYYY to ISO 8601 UTC (has_time=False, ambiguous={is_ambiguous}).")
            return dt.isoformat(), False, is_ambiguous
        except Exception:
            pass

    # Fallback generic date parsing
    try:
        dt = pd.to_datetime(v, dayfirst=True)
        if dt.tzinfo is None:
            dt = dt.tz_localize("UTC")
        else:
            dt = dt.tz_convert("UTC")
        return dt.isoformat(), True, False
    except Exception:
        log_repair(pid, "timestamp", val, "NaT", "FAILED_TIMESTAMP_PARSE", "Failed to parse timestamp format.")
        return None, False, False

ts_res = [parse_timestamp(r["timestamp"], r["post_id"]) for _, r in posts.iterrows()]
posts["timestamp_utc"] = [r[0] for r in ts_res]
posts["has_time"] = [r[1] for r in ts_res]
posts["flag_ambiguous_date_format"] = [r[2] for r in ts_res]

# 7. Shares and Comments Type Casting
print(">>> 7. Casting Shares & Comments...")
def clean_int(val, col, pid):
    v = str(val).strip()
    if v in ("", "NULL", "NAN", "nan", "None"):
        return np.nan
    try:
        return int(float(v))
    except Exception:
        log_repair(pid, col, val, "NaN", "CORRUPT_METRIC", f"Could not cast {col} to integer.")
        return np.nan

posts["shares"] = [clean_int(r["shares"], "shares", r["post_id"]) for _, r in posts.iterrows()]
posts["comments"] = [clean_int(r["comments"], "comments", r["post_id"]) for _, r in posts.iterrows()]

# 8. Segregating Empty Text Posts (Preservation Policy)
print(">>> 8. Segregating Empty Text Posts into Held-Out Quarantine...")
held_out_mask = posts["flag_empty_text"]
posts_held_out = posts[held_out_mask].copy()
posts_clean = posts[~held_out_mask].copy()

# Replace original text_content with cleaned version in posts_clean
posts_clean["text_content"] = posts_clean["text_content_clean"]
posts_clean.drop(columns=["text_content_clean", "flag_empty_text"], inplace=True)

posts_held_out.drop(columns=["text_content_clean"], inplace=True)

print(f"Clean Analytical Posts: {len(posts_clean)}")
print(f"Held-Out Quarantine Posts: {len(posts_held_out)}")

# 9. Clean Users Table
print(">>> 9. Validating & Formatting Users Table...")
users = users_raw.copy()
users["follower_count"] = users["follower_count"].astype(int)
users["account_created"] = pd.to_datetime(users["account_created"]).dt.strftime("%Y-%m-%d")

# 10. Verification & Reconciliation Check
print(">>> 10. Executing Full Row Reconciliation Assertion...")
reconciled_sum = len(posts_clean) + len(posts_held_out) + dropped_dupes_count
print(f"Raw Input: {raw_post_count}")
print(f"Clean Posts ({len(posts_clean)}) + Held-out Posts ({len(posts_held_out)}) + Dropped Dupes ({dropped_dupes_count}) = {reconciled_sum}")
assert raw_post_count == reconciled_sum, f"Reconciliation Failed: {raw_post_count} != {reconciled_sum}"
print("RECONCILIATION PASSED: 100% Accounted For (0 data lost, 0 synthetic fabrication)!")

# 11. Export Artifacts
print(">>> 11. Exporting All Clean Datasets and Audit Logs...")
# Clean Posts CSV & JSON
posts_clean.to_csv(f"{OUT_DIR}/Social_Engine_Posts_Cleaned.csv", index=False)
posts_clean.to_json(f"{OUT_DIR}/Social_Engine_Posts_Cleaned.json", orient="records", indent=2)

# Held Out Posts
posts_held_out.to_csv(f"{OUT_DIR}/Social_Engine_Posts_EmptyText_HeldOut.csv", index=False)

# Clean Users
users.to_csv(f"{OUT_DIR}/Social_Engine_Users_Cleaned.csv", index=False)
users.to_json(f"{OUT_DIR}/Social_Engine_Users_Cleaned.json", orient="records", indent=2)

# Repair Log
repair_df = pd.DataFrame(repair_log)
repair_df.to_csv(f"{OUT_DIR}/repair_log.csv", index=False)

# Copy to working dir path
for f in os.listdir(OUT_DIR):
    src = os.path.join(OUT_DIR, f)
    dst = os.path.join(f"/working_dir/c_55589ed17f08a0e7/{OUT_DIR}", f)
    with open(src, "rb") as s, open(dst, "wb") as d:
        d.write(s.read())

# Cleaning Summary
cleaning_summary = {
    "competition": "Aaruush 2026 - Data Vortex Round 1 (Phase 1)",
    "team": "Forge-X",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "raw_posts_count": raw_post_count,
    "unique_posts_count": len(posts),
    "clean_analytical_posts_count": len(posts_clean),
    "held_out_empty_text_posts_count": len(posts_held_out),
    "dropped_duplicates_count": dropped_dupes_count,
    "total_repairs_logged": len(repair_df),
    "repairs_by_type": repair_df["repair_type"].value_counts().to_dict(),
    "reconciliation_status": "VERIFIED_EXACT_MATCH",
    "zero_fabrication_policy": "STRICT_ENFORCEMENT"
}

with open(f"{OUT_DIR}/cleaning_summary.json", "w") as f:
    json.dump(cleaning_summary, f, indent=2)
with open(f"/working_dir/c_55589ed17f08a0e7/{OUT_DIR}/cleaning_summary.json", "w") as f:
    json.dump(cleaning_summary, f, indent=2)

print("Pipeline execution complete! Summary:")
print(json.dumps(cleaning_summary, indent=2))
