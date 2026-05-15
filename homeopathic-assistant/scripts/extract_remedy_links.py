#!/usr/bin/env python3
"""
extract_remedy_links.py  —  Fixed version with case-insensitive lookup

ROOT CAUSE FIX:
  MySQL utf8mb4_0900_ai_ci collation is case-insensitive, so 'Bell.' == 'bell.'
  The remedy_map now maps BOTH the original case AND lowercase -> same remedy_id
  This way tokens like 'bell.', 'Bell.', 'BELL.' all resolve correctly.

Run from project root:
    python scripts/extract_remedy_links.py
"""

import re, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

# ── Connect ────────────────────────────────────────────────────────
try:
    conn    = mysql.connector.connect(**DB_CONFIG)
    cursor  = conn.cursor(dictionary=True)
    cursor2 = conn.cursor()
    print("MySQL connected.")
except Error as e:
    print(f"Connection error: {e}"); sys.exit(1)

# ── Step 1: Load remedies — case-insensitive lookup ────────────────
print("Loading remedies...")
cursor.execute("SELECT id, abbreviation FROM remedies")
remedy_map = {}   # lowercase_abbr -> remedy_id
for r in cursor.fetchall():
    # Store BOTH original case and lowercase -> same id
    # This handles 'Bell.' in DB matching 'bell.' in rubric paths
    remedy_map[r['abbreviation'].lower()] = r['id']
    remedy_map[r['abbreviation']]         = r['id']

print(f"  {len(remedy_map)} remedy lookup entries ({len(remedy_map)//2} remedies)")

# ── Step 2: Load existing links ────────────────────────────────────
print("Loading existing rubric_remedy links...")
cursor.execute("SELECT rubric_id, remedy_id FROM rubric_remedy")
existing = set((r['rubric_id'], r['remedy_id']) for r in cursor.fetchall())
print(f"  {len(existing)} existing links")

# ── Step 3: Regex for remedy tokens ───────────────────────────────
PATTERN = re.compile(r'\b([A-Za-z][a-zA-Z]{1,11}(?:-[a-zA-Z]{1,6})?)\.')

# Words to skip — common English/Latin words that match the pattern
SKIP = {
    'amel.','agg.','see.','the.','and.','from.','with.',
    'after.','before.','during.','worse.','better.',
    'morning.','evening.','night.','afternoon.',
    'left.','right.','side.','time.','when.','while.',
    'compare.','repertory.','preface.','library.',
    'etc.','ibid.','vol.','dr.','kent.','md.',
    'sensation.','condition.','complaints.','symptoms.',
    'children.','women.','patients.','persons.',
}

def is_remedy(token: str) -> bool:
    low = token.lower()
    if low in SKIP: return False
    if len(low) < 3 or len(low) > 14: return False
    if not re.search(r'[a-z]{2}', low): return False
    return True

def grade_from(token: str) -> int:
    base = token.rstrip('.')
    if base == base.upper() and len(base) > 1: return 3  # ALL-CAPS
    if base[0].isupper():                        return 2  # Title-case
    return 1                                               # lowercase

# ── Step 4: Scan ALL rubric path texts ────────────────────────────
# The rubric paths in DB contain remedy names embedded in them e.g.:
# "MIND ANXIETY evening kali-n., merc., Bell., sulph."
# We extract all remedy tokens from each path and link them
print("Scanning rubric path texts for remedy tokens...")

cursor.execute("SELECT COUNT(*) as cnt FROM rubrics")
total = cursor.fetchone()['cnt']
print(f"  {total} rubrics to scan")

BATCH    = 5000
COMMIT   = 20000
offset   = 0
buffer   = []
inserted = 0
scanned  = 0

while True:
    cursor.execute(
        "SELECT id, path FROM rubrics ORDER BY id LIMIT %s OFFSET %s",
        (BATCH, offset)
    )
    rows = cursor.fetchall()
    if not rows:
        break

    for row in rows:
        rid  = row['id']
        path = row['path'] or ''

        for m in PATTERN.finditer(path):
            tok = m.group(0)           # e.g. 'Bell.' or 'bell.'
            if not is_remedy(tok):
                continue

            # Case-insensitive lookup: try original, then lowercase
            rem_id = remedy_map.get(tok) or remedy_map.get(tok.lower())
            if rem_id is None:
                continue

            if (rid, rem_id) in existing:
                continue

            grade = grade_from(tok)
            buffer.append((rid, rem_id, grade))
            existing.add((rid, rem_id))

    scanned += len(rows)

    if len(buffer) >= COMMIT:
        cursor2.executemany(
            """INSERT IGNORE INTO rubric_remedy
               (rubric_id, remedy_id, grade) VALUES (%s,%s,%s)""",
            buffer
        )
        conn.commit()
        inserted += len(buffer)
        buffer = []
        print(f"  Scanned {scanned:,}/{total:,} | Inserted {inserted:,}...")

    offset += BATCH

# Flush remainder
if buffer:
    cursor2.executemany(
        """INSERT IGNORE INTO rubric_remedy
           (rubric_id, remedy_id, grade) VALUES (%s,%s,%s)""",
        buffer
    )
    conn.commit()
    inserted += len(buffer)

print(f"\nComplete: scanned {scanned:,} rubrics, inserted {inserted:,} new links")

# ── Step 5: Verify ────────────────────────────────────────────────
print("\n" + "="*65)
print("VERIFICATION — Key Remedy Rubric Counts")
print("="*65)

cursor.execute(
    """SELECT r.abbreviation, r.name,
              COUNT(rr.rubric_id) AS total,
              SUM(rr.grade=3) AS g3,
              SUM(rr.grade=2) AS g2,
              SUM(rr.grade=1) AS g1
       FROM remedies r
       LEFT JOIN rubric_remedy rr ON rr.remedy_id = r.id
       WHERE LOWER(r.abbreviation) IN (
           'sulph.','acon.','bell.','phos.','calc.',
           'lach.','merc.','carb-v.','ars.','bry.',
           'nux-v.','lyc.','sep.','sil.','puls.',
           'caust.','rhus-t.','nat-m.','cham.','ign.',
           'hep.','thuj.','zinc.','con.','graph.'
       )
       GROUP BY r.id, r.abbreviation, r.name
       ORDER BY total DESC"""
)
print(f"\n{'Abbr':<14} {'Full Name':<32} {'Total':>7}"
      f" {'G3':>5} {'G2':>5} {'G1':>5}")
print("-" * 70)
for r in cursor.fetchall():
    print(f"{r['abbreviation']:<14} {(r['name'] or ''):<32}"
          f" {r['total']:>7} {r['g3'] or 0:>5}"
          f" {r['g2'] or 0:>5} {r['g1'] or 0:>5}")

cursor.execute(
    """SELECT SUM(grade=3) g3, SUM(grade=2) g2,
              SUM(grade=1) g1, COUNT(*) t
       FROM rubric_remedy"""
)
r = cursor.fetchone()
print(f"\nGrade 3:{r['g3']:,}  Grade 2:{r['g2']:,}"
      f"  Grade 1:{r['g1']:,}  Total:{r['t']:,}")

cursor.close(); cursor2.close(); conn.close()
print("\nDone.")