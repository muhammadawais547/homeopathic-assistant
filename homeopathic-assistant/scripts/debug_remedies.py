#!/usr/bin/env python3
"""
debug_remedies.py - Updated to find Sulphur specifically
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from services.database import Database
from services.constitution import get_constitutional_filter, UNIVERSAL_REMEDIES

db = Database()
cursor = db.get_cursor()

symptoms = ['anxiety', 'fear of death', 'restlessness', 'burning pains', 'weakness']

# Step 1: Get rubric scores
rubric_scores = {}
for symptom in symptoms:
    cursor.execute(
        """SELECT id, level,
                  MATCH(path) AGAINST (%s IN NATURAL LANGUAGE MODE) AS relevance
           FROM rubrics
           WHERE MATCH(path) AGAINST (%s IN NATURAL LANGUAGE MODE)
           ORDER BY relevance DESC LIMIT 200""",
        (symptom, symptom)
    )
    for row in cursor.fetchall():
        weight = (row['relevance'] or 0) * (1 + (row['level'] or 0) * 0.1)
        rubric_scores[row['id']] = rubric_scores.get(row['id'], 0) + weight

print(f"Total rubrics scored: {len(rubric_scores)}")

# Step 2: NO LIMIT - get ALL remedy scores
ids = list(rubric_scores.keys())
placeholders = ','.join(['%s'] * len(ids))
cursor.execute(
    f"""SELECT rr.rubric_id, rr.remedy_id, rr.grade,
               r.abbreviation, r.name
        FROM rubric_remedy rr
        JOIN remedies r ON rr.remedy_id = r.id
        WHERE rr.rubric_id IN ({placeholders})""",
    ids
)
rows = cursor.fetchall()
print(f"Total rows from JOIN (no limit): {len(rows)}")

remedy_scores = {}
remedy_info   = {}
remedy_max_grade = {}
for row in rows:
    rid   = row['remedy_id']
    grade = row['grade'] or 1
    score = rubric_scores.get(row['rubric_id'], 0) * grade
    remedy_scores[rid] = remedy_scores.get(rid, 0) + score
    remedy_info[rid]   = (row['abbreviation'], row['name'] or row['abbreviation'])
    if rid not in remedy_max_grade or grade > remedy_max_grade[rid]:
        remedy_max_grade[rid] = grade

print(f"Unique remedies scored: {len(remedy_scores)}")

# Show top 20
sorted_r = sorted(remedy_scores.items(), key=lambda x: -x[1])
max_score = sorted_r[0][1] if sorted_r else 1
print("\nTop 20 remedies (no filter):")
for rem_id, score in sorted_r[:20]:
    abbr, name = remedy_info[rem_id]
    pct = (score / max_score) * 100
    grade = remedy_max_grade.get(rem_id, 1)
    stars = '★★★' if grade==3 else '★★☆' if grade==2 else '★☆☆'
    print(f"  {name:<35} ({abbr:<10}) {pct:5.1f}% {stars}")

# Step 3: Constitutional filter
print("\n--- With COLD+Psora+Pale filter ---")
allowed = get_constitutional_filter(thermal='COLD', miasm='Psora', complexion='Pale')
print(f"sulph. in UNIVERSAL: {'sulph.' in UNIVERSAL_REMEDIES}")
print(f"sulph. in allowed:   {'sulph.' in (allowed or set())}")

constitutional = []
symptomatic    = []
for rem_id, score in sorted_r:
    abbr, name = remedy_info[rem_id]
    abbr_lower = abbr.lower().strip()
    pct = (score / max_score) * 100
    grade = remedy_max_grade.get(rem_id, 1)
    if allowed is None or abbr_lower in UNIVERSAL_REMEDIES or abbr_lower in allowed:
        constitutional.append((name, abbr, pct, grade))
    else:
        symptomatic.append((name, abbr, pct, grade))

print(f"\nConstitutional matches: {len(constitutional)}")
for name, abbr, pct, grade in constitutional[:10]:
    stars = '★★★' if grade==3 else '★★☆' if grade==2 else '★☆☆'
    print(f"  {name:<35} ({abbr:<10}) {pct:5.1f}% {stars}")

print(f"\nSymptomatic only: {len(symptomatic)}")
for name, abbr, pct, grade in symptomatic[:5]:
    print(f"  {name:<35} ({abbr:<10}) {pct:5.1f}%")

# Step 4: Check if Sulphur specifically is in scored remedies
print("\n--- Sulphur check ---")
sulph_found = False
for rem_id, (abbr, name) in remedy_info.items():
    if 'sulph' in abbr.lower() or 'Sulphur' in name:
        score = remedy_scores.get(rem_id, 0)
        pct = (score / max_score) * 100
        grade = remedy_max_grade.get(rem_id, 1)
        in_univ = abbr.lower().strip() in UNIVERSAL_REMEDIES
        in_allowed = abbr.lower().strip() in (allowed or set())
        print(f"  {name} ({abbr}): score={score:.2f} pct={pct:.1f}% "
              f"grade={grade} universal={in_univ} in_allowed={in_allowed}")
        sulph_found = True
if not sulph_found:
    print("  Sulphur NOT found in scored remedies!")
    print("  Checking rubric_remedy directly...")
    cursor.execute(
        """SELECT COUNT(*) as cnt FROM rubric_remedy rr
           JOIN remedies r ON r.id = rr.remedy_id
           WHERE LOWER(r.abbreviation) = 'sulph.'
           AND rr.rubric_id IN ({})""".format(placeholders),
        ids
    )
    row = cursor.fetchone()
    print(f"  Sulphur links matching scored rubrics: {row['cnt']}")

cursor.close()
print("\nDone.")