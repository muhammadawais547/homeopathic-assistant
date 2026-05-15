#!/usr/bin/env python3
"""
Import Kent's Repertory (kent.txt) into MySQL database.
Run this script once to populate the tables.
"""

import re
import mysql.connector
from mysql.connector import Error
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

# MySQL connection
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("Connected to MySQL.")
except Error as e:
    print(f"Error connecting to MySQL: {e}")
    sys.exit(1)

# Helper functions
def get_remedy_id(abbr):
    """Get remedy ID from abbreviation, insert if not exists."""
    if len(abbr) > 20:
        print(f"Warning: abbreviation too long, truncating: {abbr}")
        abbr = abbr[:20]
    cursor.execute("SELECT id FROM remedies WHERE abbreviation = %s", (abbr,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        cursor.execute("INSERT INTO remedies (abbreviation) VALUES (%s)", (abbr,))
        return cursor.lastrowid

def get_chapter_id(chapter_name):
    """Get chapter ID from name, insert if not exists."""
    if len(chapter_name) > 255:
        print(f"Warning: chapter name too long, truncating: {chapter_name[:100]}...")
        chapter_name = chapter_name[:255]
    cursor.execute("SELECT id FROM chapters WHERE name = %s", (chapter_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        cursor.execute("INSERT INTO chapters (name) VALUES (%s)", (chapter_name,))
        return cursor.lastrowid

def insert_rubric(chapter_id, path, level, parent_id, remedy_ids):
    """Insert a rubric and link remedies."""
    if len(path) > 65535:  # TEXT limit
        print(f"Warning: path too long, truncating: {path[:100]}...")
        path = path[:65535]
    cursor.execute(
        "INSERT INTO rubrics (chapter_id, path, level, parent_id) VALUES (%s, %s, %s, %s)",
        (chapter_id, path, level, parent_id)
    )
    rubric_id = cursor.lastrowid
    for rem_id in remedy_ids:
        cursor.execute(
            "INSERT IGNORE INTO rubric_remedy (rubric_id, remedy_id) VALUES (%s, %s)",
            (rubric_id, rem_id)
        )
    return rubric_id

def extract_remedies(line):
    """Extract remedy abbreviations (e.g., 'Acon.', 'Bell.', 'Acon-c.')."""
    # Pattern matches things like "Acon.", "Bell.", "Acon-c.", "Agar-ph."
    pattern = re.compile(r'\b([A-Z][a-z]{1,2}(?:-[a-z]{1,2})?\.)')
    return pattern.findall(line)

def get_indent(line):
    """Return number of leading spaces."""
    return len(line) - len(line.lstrip(' '))

# Main parsing
def main():
    filename = 'kent.txt'
    if not os.path.exists(filename):
        print(f"Error: {filename} not found in current directory.")
        sys.exit(1)

    print("Starting import of Kent's Repertory...")
    line_count = 0
    commit_interval = 1000

    current_chapter = None
    current_chapter_id = None
    stack = []  # list of (indent, rubric_id, path)

    with open(filename, 'r', encoding='latin-1') as f:
        for raw_line in f:
            line = raw_line.rstrip('\n')
            line_count += 1
            if line_count % 10000 == 0:
                print(f"Processed {line_count} lines...")

            if not line.strip():
                continue

            # Chapter headings: all caps and end with a period
            if line.isupper() and line.endswith('.'):
                current_chapter = line[:-1].strip()
                # Some chapter names may be long; we'll store full name
                current_chapter_id = get_chapter_id(current_chapter)
                stack = []  # new chapter resets hierarchy
                continue

            indent = get_indent(line)
            stripped = line.strip()

            # Check for remedy abbreviations
            remedies = extract_remedies(stripped)
            if remedies:
                # This line contains remedies – find the rubric they belong to
                if not stack:
                    # No rubric on stack – this can happen if file starts with remedies before any rubric.
                    # We'll create a dummy rubric under the current chapter.
                    print(f"Warning: remedies without rubric at line {line_count}, skipping.")
                    continue
                rubric_id = stack[-1][1]
                for abbr in remedies:
                    rem_id = get_remedy_id(abbr)
                    cursor.execute(
                        "INSERT IGNORE INTO rubric_remedy (rubric_id, remedy_id) VALUES (%s, %s)",
                        (rubric_id, rem_id)
                    )
                continue

            # If we get here, it's a rubric heading line
            # Adjust stack based on indentation
            while stack and stack[-1][0] >= indent:
                stack.pop()
            parent_id = stack[-1][1] if stack else None
            level = len(stack) + 1

            # Build full path by combining parent path and current rubric text
            if stack:
                parent_path = stack[-1][2]
                full_path = parent_path + ' ' + stripped
            else:
                # First-level rubric under chapter
                full_path = current_chapter + ' ' + stripped if current_chapter else stripped

            # Insert the rubric (remedy_ids empty for now – remedies will be added later when we encounter them)
            try:
                cursor.execute(
                    "INSERT INTO rubrics (chapter_id, path, level, parent_id) VALUES (%s, %s, %s, %s)",
                    (current_chapter_id, full_path, level, parent_id)
                )
            except mysql.connector.Error as err:
                print(f"Error at line {line_count}: {err}")
                print(f"Skipping line: {line}")
                continue

            rubric_id = cursor.lastrowid
            stack.append((indent, rubric_id, full_path))

            # Commit periodically
            if line_count % commit_interval == 0:
                conn.commit()
                print(f"Committed up to line {line_count}.")

    # Final commit
    conn.commit()
    print(f"Import completed. Total lines processed: {line_count}")

if __name__ == '__main__':
    main()
    cursor.close()
    conn.close()
    
# After import, set name = abbreviation for all remedies
cursor.execute("UPDATE remedies SET name = abbreviation WHERE name IS NULL")
conn.commit()
print("Updated remedy names with abbreviations.")