# gui/add_remedy_dialog.py
"""
Add Remedy Dialog — allows adding new remedies with full Kent hierarchy:
  Chapter → Rubric path → Remedy abbreviation + full name + grade
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QPushButton,
    QMessageBox, QLabel, QGroupBox, QTextEdit,
    QFrame, QWidget, QListWidget, QListWidgetItem,
    QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.database import Database
from gui.theme import (
    CLR_PRIMARY, CLR_PRIMARY_LIGHT, CLR_WHITE,
    CLR_BORDER, CLR_ACCENT, CLR_DANGER
)


class AddRemedyDialog(QDialog):

    # Kent's standard chapters
    CHAPTERS = [
        "MIND", "VERTIGO", "HEAD", "EYE", "EAR", "NOSE",
        "FACE", "MOUTH", "TEETH", "THROAT", "EXTERNAL THROAT",
        "STOMACH", "ABDOMEN", "RECTUM", "STOOL", "BLADDER",
        "KIDNEYS", "PROSTATE GLAND", "URETHRA", "GENITALIA MALE",
        "GENITALIA FEMALE", "LARYNX AND TRACHEA", "RESPIRATION",
        "COUGH", "EXPECTORATION", "CHEST", "BACK", "EXTREMITIES",
        "SLEEP", "CHILL", "FEVER", "PERSPIRATION", "SKIN",
        "GENERALITIES",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.setWindowTitle("Add Remedy to Kent's Repertory")
        self.setMinimumSize(780, 620)
        self._build_ui()
        self._load_chapters()

    # ── UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(50)
        hdr.setStyleSheet(f"background:{CLR_PRIMARY};")
        hr = QHBoxLayout(hdr)
        hr.setContentsMargins(20, 0, 20, 0)
        t = QLabel("＋  Add Remedy to Kent's Repertory")
        t.setStyleSheet(f"color:{CLR_WHITE}; font-size:14px; font-weight:700;")
        s = QLabel("Enter remedy details and the rubric it belongs to")
        s.setStyleSheet("color:rgba(255,255,255,0.65); font-size:11px;")
        col = QVBoxLayout(); col.setSpacing(1)
        col.addWidget(t); col.addWidget(s)
        hr.addLayout(col)
        layout.addWidget(hdr)

        # Body
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16)
        body_layout.setSpacing(14)

        # ── Remedy details ────────────────────────────────────────────
        rem_grp = QGroupBox("Remedy Details")
        rem_form = QFormLayout(rem_grp)
        rem_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        rem_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        rem_form.setHorizontalSpacing(16)
        rem_form.setVerticalSpacing(10)

        self.abbr_in = QLineEdit()
        self.abbr_in.setPlaceholderText("e.g. Sulph.  (must end with dot)")
        self.abbr_in.setFixedWidth(200)
        self.abbr_in.textChanged.connect(self._lookup_existing)
        rem_form.addRow("Abbreviation *:", self.abbr_in)

        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("e.g. Sulphur  or  Belladonna")
        rem_form.addRow("Full Latin Name *:", self.name_in)

        self.thermal_cb = QComboBox()
        self.thermal_cb.addItems(["", "HOT", "COLD"])
        self.thermal_cb.setFixedWidth(160)
        rem_form.addRow("Thermal Type:", self.thermal_cb)

        self.grade_cb = QComboBox()
        self.grade_cb.addItems([
            "1 — Plain (Occasionally indicated)",
            "2 — Italic (Frequently indicated)",
            "3 — Bold (Highest / Constitutional)",
        ])
        self.grade_cb.setFixedWidth(340)
        rem_form.addRow("Kent Grade *:", self.grade_cb)

        # Status label — shows if remedy already exists
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size:11px; font-style:italic;")
        rem_form.addRow("", self.status_lbl)

        body_layout.addWidget(rem_grp)

        # ── Rubric placement ──────────────────────────────────────────
        rub_grp = QGroupBox("Kent Hierarchy — Where does this remedy belong?")
        rub_layout = QVBoxLayout(rub_grp)
        rub_layout.setSpacing(10)

        # Chapter + rubric search
        search_row = QHBoxLayout()
        self.chapter_cb = QComboBox()
        self.chapter_cb.setFixedWidth(200)
        self.chapter_cb.currentTextChanged.connect(self._on_chapter_changed)

        self.rubric_search = QLineEdit()
        self.rubric_search.setPlaceholderText(
            "Type to search rubrics in selected chapter…"
        )
        self.rubric_search.textChanged.connect(self._search_rubrics)

        search_row.addWidget(QLabel("Chapter:"))
        search_row.addWidget(self.chapter_cb)
        search_row.addSpacing(12)
        search_row.addWidget(QLabel("Search Rubric:"))
        search_row.addWidget(self.rubric_search, 1)
        rub_layout.addLayout(search_row)

        # Rubric list
        self.rubric_list = QListWidget()
        self.rubric_list.setFixedHeight(160)
        self.rubric_list.setStyleSheet(f"""
            QListWidget {{
                border: 1.5px solid {CLR_BORDER};
                border-radius: 5px;
                background: {CLR_WHITE};
                font-size: 12px;
            }}
            QListWidget::item {{ padding: 5px 10px; }}
            QListWidget::item:selected {{
                background: {CLR_PRIMARY_LIGHT};
                color: {CLR_PRIMARY};
            }}
            QListWidget::item:hover {{ background: #F0FAF4; }}
        """)
        self.rubric_list.itemClicked.connect(self._on_rubric_selected)
        rub_layout.addWidget(self.rubric_list)

        # Selected rubric display
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Selected Rubric:"))
        self.selected_rubric_lbl = QLabel("None selected")
        self.selected_rubric_lbl.setStyleSheet(
            f"color:{CLR_PRIMARY}; font-weight:700; font-size:12px;"
        )
        self.selected_rubric_lbl.setWordWrap(True)
        self._selected_rubric_id = None
        sel_row.addWidget(self.selected_rubric_lbl, 1)
        rub_layout.addLayout(sel_row)

        # OR — new rubric path
        or_lbl = QLabel("── OR create a new rubric path ──")
        or_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        or_lbl.setStyleSheet(f"color:{CLR_PRIMARY}; font-size:11px; font-weight:600;")
        rub_layout.addWidget(or_lbl)

        new_row = QHBoxLayout()
        new_row.addWidget(QLabel("New Rubric Path:"))
        self.new_rubric_in = QLineEdit()
        self.new_rubric_in.setPlaceholderText(
            "e.g. MIND Anxiety health about  "
            "(chapter + space + full rubric text)"
        )
        new_row.addWidget(self.new_rubric_in, 1)
        rub_layout.addLayout(new_row)

        body_layout.addWidget(rub_grp)
        layout.addWidget(body)

        # ── Button bar ────────────────────────────────────────────────
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"background:{CLR_WHITE}; border-top:1px solid {CLR_BORDER};"
        )
        btn_row = QHBoxLayout(bar)
        btn_row.setContentsMargins(20, 0, 20, 0)

        save_btn = QPushButton("💾  Save Remedy")
        save_btn.setFixedHeight(34)
        save_btn.setMinimumWidth(150)
        save_btn.setStyleSheet("""
            QPushButton { background:#1A6B3C; color:white; border:none;
                          border-radius:5px; font-weight:700; font-size:12px; }
            QPushButton:hover { background:#134E2C; }
        """)
        save_btn.clicked.connect(self._save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.setStyleSheet(
            "background:#78909C; color:white; border:none;"
            "border-radius:5px; font-weight:600;"
        )
        cancel_btn.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addSpacing(10)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        layout.addWidget(bar)

    # ── Data loading ───────────────────────────────────────────────────
    def _load_chapters(self):
        self.chapter_cb.addItem("")
        for ch in self.CHAPTERS:
            self.chapter_cb.addItem(ch)

    def _on_chapter_changed(self, chapter):
        self.rubric_list.clear()
        self._selected_rubric_id = None
        self.selected_rubric_lbl.setText("None selected")
        if chapter:
            self._search_rubrics(self.rubric_search.text())

    def _search_rubrics(self, text):
        chapter = self.chapter_cb.currentText().strip()
        if not chapter:
            return
        self.rubric_list.clear()
        try:
            cur = self.db.get_cursor(dictionary=True)
            search = f"%{text}%" if text.strip() else "%"
            cur.execute(
                """SELECT r.id, r.path
                   FROM rubrics r
                   JOIN chapters c ON r.chapter_id = c.id
                   WHERE c.name = %s AND r.path LIKE %s
                   ORDER BY r.path ASC
                   LIMIT 80""",
                (chapter, search)
            )
            rows = cur.fetchall()
            cur.close()
            for row in rows:
                item = QListWidgetItem(row['path'])
                item.setData(Qt.ItemDataRole.UserRole, row['id'])
                self.rubric_list.addItem(item)
        except Exception as e:
            print(f"Rubric search error: {e}")

    def _on_rubric_selected(self, item):
        self._selected_rubric_id = item.data(Qt.ItemDataRole.UserRole)
        path = item.text()
        # Truncate for display if too long
        display = path if len(path) <= 80 else path[:77] + "…"
        self.selected_rubric_lbl.setText(display)
        self.selected_rubric_lbl.setStyleSheet(
            f"color:{CLR_ACCENT}; font-weight:700; font-size:12px;"
        )

    def _lookup_existing(self, text):
        """Show whether abbreviation already exists in DB."""
        text = text.strip()
        if not text:
            self.status_lbl.setText("")
            return
        try:
            cur = self.db.get_cursor(dictionary=True)
            cur.execute(
                "SELECT id, name FROM remedies WHERE abbreviation=%s", (text,)
            )
            row = cur.fetchone()
            cur.close()
            if row:
                name = row['name'] or text
                self.status_lbl.setText(
                    f"✔ Already in database as: {name} "
                    f"— will update name/thermal if changed"
                )
                self.status_lbl.setStyleSheet(
                    f"color:{CLR_ACCENT}; font-size:11px;"
                )
                if self.name_in.text() == "":
                    self.name_in.setText(name)
            else:
                self.status_lbl.setText("✦ New remedy — will be created")
                self.status_lbl.setStyleSheet(
                    f"color:{CLR_PRIMARY}; font-size:11px;"
                )
        except Exception:
            pass

    # ── Save ───────────────────────────────────────────────────────────
    def _save(self):
        abbr = self.abbr_in.text().strip()
        name = self.name_in.text().strip()
        grade = self.grade_cb.currentIndex() + 1  # 1, 2, or 3
        thermal = self.thermal_cb.currentText().strip() or None
        new_rubric_path = self.new_rubric_in.text().strip()

        # Validation
        if not abbr:
            QMessageBox.warning(self, "Validation", "Abbreviation is required.")
            return
        if not abbr.endswith('.'):
            QMessageBox.warning(
                self, "Validation",
                "Abbreviation must end with a dot  (e.g. Sulph.)"
            )
            return
        if not name:
            QMessageBox.warning(self, "Validation", "Full Latin name is required.")
            return
        if not self._selected_rubric_id and not new_rubric_path:
            QMessageBox.warning(
                self, "Validation",
                "Please select an existing rubric OR enter a new rubric path."
            )
            return

        try:
            cur = self.db.get_cursor(dictionary=False)

            # 1. Insert or update remedy
            cur.execute(
                "SELECT id FROM remedies WHERE abbreviation=%s", (abbr,)
            )
            existing = cur.fetchone()
            if existing:
                remedy_id = existing[0]
                cur.execute(
                    """UPDATE remedies SET name=%s, thermal_type=%s
                       WHERE id=%s""",
                    (name, thermal, remedy_id)
                )
            else:
                cur.execute(
                    """INSERT INTO remedies (abbreviation, name, thermal_type)
                       VALUES (%s, %s, %s)""",
                    (abbr, name, thermal)
                )
                remedy_id = cur.lastrowid

            # 2. Resolve rubric ID
            rubric_id = self._selected_rubric_id
            if not rubric_id and new_rubric_path:
                # Find or create chapter
                chapter_name = new_rubric_path.split()[0].upper()
                cur.execute(
                    "SELECT id FROM chapters WHERE name=%s", (chapter_name,)
                )
                ch_row = cur.fetchone()
                if ch_row:
                    chapter_id = ch_row[0]
                else:
                    cur.execute(
                        "INSERT INTO chapters (name) VALUES (%s)", (chapter_name,)
                    )
                    chapter_id = cur.lastrowid

                # Check if rubric path already exists
                cur.execute(
                    "SELECT id FROM rubrics WHERE path=%s", (new_rubric_path,)
                )
                rub_row = cur.fetchone()
                if rub_row:
                    rubric_id = rub_row[0]
                else:
                    cur.execute(
                        """INSERT INTO rubrics (chapter_id, path, level, parent_id)
                           VALUES (%s, %s, 1, NULL)""",
                        (chapter_id, new_rubric_path)
                    )
                    rubric_id = cur.lastrowid

            # 3. Link remedy to rubric with grade
            cur.execute(
                """INSERT INTO rubric_remedy (rubric_id, remedy_id, grade)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE grade=%s""",
                (rubric_id, remedy_id, grade, grade)
            )

            self.db.commit()
            cur.close()

            QMessageBox.information(
                self, "Saved",
                f"<b>{name}</b> ({abbr}) saved successfully!\n"
                f"Grade: {'★★★' if grade==3 else '★★☆' if grade==2 else '★☆☆'}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save remedy:\n{e}")
            self.db.rollback()