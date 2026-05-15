#!/usr/bin/env python3
"""
convert_oorep.py
Converts OOREP PostgreSQL dump to MySQL for homoeo database.
Keeps all patient data. Replaces rubrics/remedies/rubric_remedy.

Run from project root:
    python scripts/convert_oorep.py

Place oorep.sql in Downloads folder (default) or edit SQL_FILE below.
"""

import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Config ─────────────────────────────────────────────────────────
SQL_FILE   = r'C:\Users\dell\Downloads\oorep.sql'
REPERTORY  = 'publicum'  # English Kent repertory prefix
OUT_FILE   = 'scripts/import_oorep.sql'

# ── Read dump ─────────────────────────────────────────────────────
print(f"Reading {SQL_FILE}...")
with open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
print(f"  {len(content)/1024/1024:.1f} MB read")

# ── Helper: extract table data ────────────────────────────────────
def extract_table(name):
    """Extract all rows from a PostgreSQL COPY block."""
    pattern = (r'COPY public\.' + name +
               r'[^\n]*\n(.*?)\n\\\.') 
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        print(f"  WARNING: table '{name}' not found")
        return []
    rows = []
    for line in m.group(1).split('\n'):
        if line.strip():
            rows.append(line.split('\t'))
    return rows

def col_names(name):
    m = re.search(r'COPY public\.' + name + r' \(([^)]+)\)', content)
    return [c.strip() for c in m.group(1).split(',')] if m else []

# ── Extract tables ────────────────────────────────────────────────
print("Extracting chapters...")
chapter_rows = extract_table('chapter')
chapter_cols = col_names('chapter')
print(f"  {len(chapter_rows)} chapters")

print("Extracting rubrics...")
rubric_rows = extract_table('rubric')
rubric_cols = col_names('rubric')
print(f"  {len(rubric_rows)} rubrics total")

print("Extracting remedies...")
remedy_rows = extract_table('remedy')
remedy_cols = col_names('remedy')
print(f"  {len(remedy_rows)} remedies")

print("Extracting rubricremedy...")
rr_rows = extract_table('rubricremedy')
rr_cols = col_names('rubricremedy')
print(f"  {len(rr_rows)} rubric-remedy links total")

print("Extracting remedyinfo...")
ri_rows  = extract_table('remedyinfo')
ri_cols  = col_names('remedyinfo')
print(f"  {len(ri_rows)} remedy info rows")

# ── Inspect columns ────────────────────────────────────────────────
print(f"\nChapter columns:     {chapter_cols}")
print(f"Rubric columns:      {rubric_cols}")
print(f"Remedy columns:      {remedy_cols}")
print(f"RubricRemedy columns:{rr_cols}")
print(f"RemedyInfo columns:  {ri_cols}")

# ── Check available repertory prefixes ────────────────────────────
abbrev_idx = rubric_cols.index('abbrev') if 'abbrev' in rubric_cols else 0
prefixes = set(r[abbrev_idx] for r in rubric_rows if len(r) > abbrev_idx)
print(f"\nAvailable repertory prefixes: {sorted(prefixes)[:20]}")

# Filter to English Kent
en_rubrics = [r for r in rubric_rows
              if len(r) > abbrev_idx and r[abbrev_idx] == REPERTORY]
print(f"English Kent rubrics (kent-en): {len(en_rubrics)}")

if len(en_rubrics) == 0:
    print("\nNo 'kent-en' rubrics found. Trying other prefixes...")
    for prefix in sorted(prefixes):
        count = sum(1 for r in rubric_rows
                    if len(r) > abbrev_idx and r[abbrev_idx] == prefix)
        print(f"  {prefix}: {count} rubrics")
    print("\nEdit REPERTORY variable at top of script to match correct prefix")
    sys.exit(1)

# ── Map rubric columns ────────────────────────────────────────────
def rcol(row, name):
    """Get value from rubric row by column name."""
    try:
        idx = rubric_cols.index(name)
        val = row[idx] if idx < len(row) else ''
        return '' if val in ('\\N', 'NULL', None) else val
    except ValueError:
        return ''

# ── Build chapter mapping: chapter_id -> chapter_name ─────────────
chap_id_col   = chapter_cols.index('id')     if 'id'     in chapter_cols else 1
chap_abbr_col = chapter_cols.index('abbrev') if 'abbrev' in chapter_cols else 0
chap_text_col = chapter_cols.index('textt')  if 'textt'  in chapter_cols else 2

chapter_map = {}  # id -> name
for row in chapter_rows:
    if len(row) > max(chap_id_col, chap_text_col):
        cid   = row[chap_id_col].strip()
        ctext = row[chap_text_col].strip()
        cabbr = row[chap_abbr_col].strip() if len(row) > chap_abbr_col else ''
        name  = ctext if ctext and ctext != '\\N' else cabbr
        if cid and name:
            chapter_map[cid] = name

print(f"\nChapters mapped: {len(chapter_map)}")
for cid, name in list(chapter_map.items())[:10]:
    print(f"  {cid}: {name}")

# ── Build remedy mapping: oorep_id -> (abbrev, name) ──────────────
rem_id_col   = remedy_cols.index('id')          if 'id'          in remedy_cols else 0
rem_abbr_col = remedy_cols.index('nameabbrev')  if 'nameabbrev'  in remedy_cols else 1
rem_name_col = remedy_cols.index('namelong')    if 'namelong'    in remedy_cols else 2

oorep_remedy_map = {}  # oorep_id -> (abbrev, fullname)
for row in remedy_rows:
    if len(row) > max(rem_id_col, rem_abbr_col, rem_name_col):
        rid   = row[rem_id_col].strip()
        abbr  = row[rem_abbr_col].strip()
        name  = row[rem_name_col].strip()
        if rid and abbr:
            name = '' if name == '\\N' else name
            oorep_remedy_map[rid] = (abbr, name or abbr)

print(f"\nRemedies mapped: {len(oorep_remedy_map)}")

# ── Get rubricremedy column indices ───────────────────────────────
# Common formats: (rubricid, remedyid, weight) or (abbrev, rubricid, remedyid, weight)
print(f"\nRubricRemedy sample rows:")
for row in rr_rows[:5]:
    print(f"  {row}")

# Detect column positions
rr_rubric_col = -1
rr_remedy_col = -1
rr_weight_col = -1
rr_abbrev_col = -1

for i, col in enumerate(rr_cols):
    col_l = col.strip().lower()
    if 'rubric' in col_l and 'id' in col_l:
        rr_rubric_col = i
    elif 'remedy' in col_l and 'id' in col_l:
        rr_remedy_col = i
    elif 'weight' in col_l or 'grade' in col_l or 'degree' in col_l:
        rr_weight_col = i
    elif col_l == 'abbrev':
        rr_abbrev_col = i

print(f"\nRubricRemedy column mapping:")
print(f"  rubric_id col: {rr_rubric_col} ({rr_cols[rr_rubric_col] if rr_rubric_col>=0 else 'NOT FOUND'})")
print(f"  remedy_id col: {rr_remedy_col} ({rr_cols[rr_remedy_col] if rr_remedy_col>=0 else 'NOT FOUND'})")
print(f"  weight col:    {rr_weight_col} ({rr_cols[rr_weight_col] if rr_weight_col>=0 else 'NOT FOUND'})")
print(f"  abbrev col:    {rr_abbrev_col} ({rr_cols[rr_abbrev_col] if rr_abbrev_col>=0 else 'NOT FOUND'})")

# ── Filter rubricremedy to kent-en only ───────────────────────────
if rr_abbrev_col >= 0:
    en_rr = [r for r in rr_rows
             if len(r) > rr_abbrev_col and r[rr_abbrev_col] == REPERTORY]
    print(f"\nEnglish Kent rubricremedy links: {len(en_rr)}")
else:
    # No abbrev column — need to filter by rubric IDs
    en_rubric_ids = set(rcol(r, 'id') for r in en_rubrics)
    en_rr = [r for r in rr_rows
             if rr_rubric_col >= 0 and len(r) > rr_rubric_col
             and r[rr_rubric_col] in en_rubric_ids]
    print(f"\nFiltered by rubric IDs: {len(en_rr)} links")

# ── Write MySQL import script ─────────────────────────────────────
print(f"\nWriting {OUT_FILE}...")

def esc(s):
    """Escape string for MySQL."""
    if not s or s in ('\\N', 'NULL'):
        return 'NULL'
    s = str(s).replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    return f"'{s}'"

lines = []
lines.append("-- ============================================================")
lines.append("--  import_oorep.sql")
lines.append("--  Converted from OOREP PostgreSQL dump")
lines.append(f"--  Source: {REPERTORY} (English Kent's Repertory)")
lines.append("--  Keeps all patient data. Replaces rubrics/remedies.")
lines.append("-- ============================================================")
lines.append("")
lines.append("USE homoeo;")
lines.append("SET FOREIGN_KEY_CHECKS = 0;")
lines.append("SET autocommit = 0;")
lines.append("")

# Clear old data
lines.append("-- Clear old Kent data")
lines.append("TRUNCATE TABLE rubric_remedy;")
lines.append("TRUNCATE TABLE rubrics;")
lines.append("TRUNCATE TABLE chapters;")
lines.append("TRUNCATE TABLE remedy_relations;")
lines.append("-- Keep: patients, patient_visits, remedies")
lines.append("")

# Insert chapters
lines.append("-- ── Chapters ───────────────────────────────────────────────")
seen_chaps = set()
for cid, cname in chapter_map.items():
    if cname and cname not in seen_chaps:
        seen_chaps.add(cname)
        lines.append(
            f"INSERT IGNORE INTO chapters (id, name) VALUES ({esc(cid)}, {esc(cname)});"
        )
lines.append(f"-- {len(chapter_map)} chapters inserted")
lines.append("COMMIT;")
lines.append("")

# Insert rubrics
lines.append("-- ── Rubrics ────────────────────────────────────────────────")
lines.append("-- English Kent only")

fullpath_col  = rubric_cols.index('fullpath') if 'fullpath' in rubric_cols else -1
path_col      = rubric_cols.index('path')     if 'path'     in rubric_cols else -1
textt_col     = rubric_cols.index('textt')    if 'textt'    in rubric_cols else -1
id_col        = rubric_cols.index('id')       if 'id'       in rubric_cols else 1
chapter_id_col= rubric_cols.index('chapterid') if 'chapterid' in rubric_cols else -1
mother_col    = rubric_cols.index('mother')   if 'mother'   in rubric_cols else -1

batch = []
rubric_id_map = {}  # oorep_id -> mysql_auto_id (we use oorep id directly)

for row in en_rubrics:
    if len(row) <= id_col:
        continue

    rid     = rcol(row, 'id')
    chap_id = rcol(row, 'chapterid')
    parent  = rcol(row, 'mother')

    # Build path: prefer fullpath, then path, then textt
    full  = rcol(row, 'fullpath')
    path  = rcol(row, 'path')
    textt = rcol(row, 'textt')
    final_path = full or path or textt or ''

    if not final_path or not rid:
        continue

    rubric_id_map[rid] = rid

    batch.append(
        f"({esc(rid)},{esc(chap_id) if chap_id else 'NULL'},"
        f"{esc(final_path)},1,"
        f"{esc(parent) if parent else 'NULL'})"
    )

    if len(batch) >= 1000:
        lines.append(
            "INSERT IGNORE INTO rubrics (id,chapter_id,path,level,parent_id) VALUES"
        )
        lines.append(',\n'.join(batch) + ';')
        lines.append("COMMIT;")
        batch = []

if batch:
    lines.append(
        "INSERT IGNORE INTO rubrics (id,chapter_id,path,level,parent_id) VALUES"
    )
    lines.append(',\n'.join(batch) + ';')
    lines.append("COMMIT;")

lines.append(f"-- {len(en_rubrics)} rubrics inserted")
lines.append("")

# Update remedies with correct names from oorep
lines.append("-- ── Update remedy names from OOREP ─────────────────────────")
for rid, (abbr, name) in oorep_remedy_map.items():
    if name and name != abbr:
        lines.append(
            f"UPDATE remedies SET name={esc(name)} "
            f"WHERE abbreviation={esc(abbr)} OR LOWER(abbreviation)={esc(abbr.lower())};"
        )
lines.append("COMMIT;")
lines.append("")

# Insert rubricremedy with grades
lines.append("-- ── Rubric-Remedy links with grades ────────────────────────")

batch = []
skipped = 0
inserted_count = 0

for row in en_rr:
    if rr_rubric_col < 0 or rr_remedy_col < 0:
        break
    if len(row) <= max(rr_rubric_col, rr_remedy_col):
        continue

    rubric_id = row[rr_rubric_col].strip()
    remedy_id_oorep = row[rr_remedy_col].strip()

    # Grade/weight: OOREP uses 1,2,3 or 4 (4=highest in some versions)
    grade = 1
    if rr_weight_col >= 0 and len(row) > rr_weight_col:
        try:
            w = int(row[rr_weight_col].strip())
            grade = min(w, 3)  # cap at 3
        except (ValueError, IndexError):
            grade = 1

    if rubric_id not in rubric_id_map:
        skipped += 1
        continue

    # Find MySQL remedy id by abbreviation
    if remedy_id_oorep in oorep_remedy_map:
        abbr, _ = oorep_remedy_map[remedy_id_oorep]
        batch.append(
            f"((SELECT id FROM remedies WHERE "
            f"abbreviation={esc(abbr)} OR "
            f"LOWER(abbreviation)={esc(abbr.lower())} LIMIT 1),"
            f"(SELECT id FROM rubrics WHERE id={esc(rubric_id)} LIMIT 1),"
            f"{grade})"
        )
        inserted_count += 1
    else:
        skipped += 1

    if len(batch) >= 500:
        lines.append(
            "INSERT IGNORE INTO rubric_remedy (remedy_id, rubric_id, grade) VALUES"
        )
        lines.append(',\n'.join(batch) + ';')
        lines.append("COMMIT;")
        batch = []

if batch:
    lines.append(
        "INSERT IGNORE INTO rubric_remedy (remedy_id, rubric_id, grade) VALUES"
    )
    lines.append(',\n'.join(batch) + ';')
    lines.append("COMMIT;")

lines.append(f"-- {inserted_count} links inserted, {skipped} skipped")
lines.append("")
lines.append("SET FOREIGN_KEY_CHECKS = 1;")
lines.append("")

# Verification queries
lines.append("-- ── Verification ───────────────────────────────────────────")
lines.append("SELECT COUNT(*) as chapters FROM chapters;")
lines.append("SELECT COUNT(*) as rubrics FROM rubrics;")
lines.append("SELECT COUNT(*) as remedies FROM remedies;")
lines.append("SELECT COUNT(*) as links FROM rubric_remedy;")
lines.append("""SELECT r.abbreviation, r.name,
       COUNT(rr.rubric_id) as links,
       SUM(rr.grade=3) as g3,
       SUM(rr.grade=2) as g2,
       SUM(rr.grade=1) as g1
FROM remedies r
LEFT JOIN rubric_remedy rr ON rr.remedy_id = r.id
WHERE LOWER(r.abbreviation) IN (
    'sulph.','acon.','bell.','phos.','calc.',
    'lach.','merc.','carb-v.','ars.','bry.',
    'nux-v.','lyc.','sep.','sil.','puls.'
)
GROUP BY r.id ORDER BY links DESC;""")

# Write file
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

size = os.path.getsize(OUT_FILE) / (1024*1024)
print(f"Written: {OUT_FILE} ({size:.1f} MB)")
print(f"  Rubrics : {len(en_rubrics)}")
print(f"  Links   : {inserted_count}")
print(f"  Skipped : {skipped}")
print()
print("Next step: run the generated SQL in MySQL Workbench:")
print(f"  {OUT_FILE}")