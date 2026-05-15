# gui/patient_remedies_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QWidget, QFrame,
    QTabWidget, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from services.remedy_service import RemedyService
from gui.theme import CLR_PRIMARY, CLR_WHITE, CLR_BORDER, CLR_PRIMARY_LIGHT

# ── Constants ──────────────────────────────────────────────────────────────────
HEADERS = ["Rank", "Full Remedy Name", "Abbreviation",
           "Kent Grade", "Match %", "Priority", "Profile"]

MATCH_COLORS = {
    "green":  ("#E8F5E9", "#1B5E20"),
    "yellow": ("#FFFDE7", "#F57F17"),
    "red":    ("#FFEBEE", "#B71C1C"),
}
GRADE_DISPLAY = {
    3: ("★★★", "#1B5E20", "#C8E6C9"),
    2: ("★★☆", "#E65100", "#FFE0B2"),
    1: ("★☆☆", "#37474F", "#ECEFF1"),
}
PRIORITY_LABEL = {
    "green":  "High Priority",
    "yellow": "Consider",
    "red":    "Low Priority",
}

TABLE_STYLE = f"""
    QTableWidget {{
        border: none; background: {CLR_WHITE};
        alternate-background-color: {CLR_PRIMARY_LIGHT};
        outline: none; font-size: 12px;
    }}
    QTableWidget::item {{
        padding: 6px 10px;
        border-bottom: 1px solid #E8F5EE;
    }}
    QHeaderView::section {{
        background-color: {CLR_PRIMARY}; color: white;
        padding: 8px 10px; border: none;
        font-weight: 700; font-size: 11px;
    }}
"""


def _make_table() -> QTableWidget:
    t = QTableWidget()
    t.setColumnCount(len(HEADERS))
    t.setHorizontalHeaderLabels(HEADERS)
    hh = t.horizontalHeader()
    hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
    hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
    hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
    hh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
    t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(42)
    t.setShowGrid(False)
    t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    t.setStyleSheet(TABLE_STYLE)
    return t


def _fill_table(table: QTableWidget, results: list):
    table.setRowCount(len(results))
    for row, result in enumerate(results):
        if len(result) == 6:
            name, abbr, pct, color, grade, const_match = result
        else:
            name, abbr, pct, color = result[:4]
            grade, const_match = 1, "—"

        bg, fg = MATCH_COLORS.get(color, ("#FFF", "#000"))
        g_stars, g_fg, g_bg = GRADE_DISPLAY.get(
            grade, ("★☆☆", "#37474F", "#ECEFF1")
        )

        def _cell(text, bold=False, italic=False,
                  cell_bg=bg, cell_fg=fg,
                  align=Qt.AlignmentFlag.AlignLeft):
            item = QTableWidgetItem(str(text))
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QColor(cell_bg))
            item.setForeground(QColor(cell_fg))
            if bold or italic:
                f = QFont()
                f.setBold(bold)
                f.setItalic(italic)
                item.setFont(f)
            return item

        C = Qt.AlignmentFlag.AlignCenter

        # Store abbreviation in UserRole for relation lookup
        rank_item = _cell(f"#{row+1}", bold=True, align=C)
        rank_item.setData(Qt.ItemDataRole.UserRole, abbr)
        table.setItem(row, 0, rank_item)

        table.setItem(row, 1, _cell(
            name, bold=(grade == 3), italic=(grade == 2)
        ))
        table.setItem(row, 2, _cell(abbr, align=C))

        g_item = QTableWidgetItem(f"  {g_stars}  ")
        g_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        g_item.setBackground(QColor(g_bg))
        g_item.setForeground(QColor(g_fg))
        gf = QFont(); gf.setBold(True); gf.setPointSize(11)
        g_item.setFont(gf)
        table.setItem(row, 3, g_item)

        pf = QFont(); pf.setBold(True)
        pct_item = QTableWidgetItem(f"{pct:.1f}%")
        pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        pct_item.setBackground(QColor(bg))
        pct_item.setForeground(QColor(fg))
        pct_item.setFont(pf)
        table.setItem(row, 4, pct_item)

        table.setItem(row, 5, _cell(
            PRIORITY_LABEL.get(color, ""), align=C
        ))

        if "Constitutional" in const_match:
            c_bg, c_fg = "#E3F2FD", "#0D47A1"
        elif "Universal" in const_match:
            c_bg, c_fg = "#F3E5F5", "#4A148C"
        elif "No filter" in const_match:
            c_bg, c_fg = "#F5F5F5", "#424242"
        else:
            c_bg, c_fg = "#FFF9C4", "#827717"

        c_item = QTableWidgetItem(const_match)
        c_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        c_item.setBackground(QColor(c_bg))
        c_item.setForeground(QColor(c_fg))
        cf = QFont(); cf.setBold(True); cf.setPointSize(10)
        c_item.setFont(cf)
        table.setItem(row, 6, c_item)


class PatientRemediesDialog(QDialog):
    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.remedy_service = RemedyService()
        self.setWindowTitle(f"Remedies — {patient.name}")
        self.setMinimumSize(1020, 680)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setFixedHeight(62)
        hdr.setStyleSheet(f"background:{CLR_PRIMARY};")
        hr = QHBoxLayout(hdr)
        hr.setContentsMargins(20, 0, 20, 0)
        t = QLabel(f"🌿  Recommended Remedies — {self.patient.name}")
        t.setStyleSheet(f"color:{CLR_WHITE}; font-size:14px; font-weight:700;")
        parts = []
        if self.patient.thermal_type:
            parts.append(f"Thermal: {self.patient.thermal_type}")
        if self.patient.miasm:
            parts.append(f"Miasm: {self.patient.miasm}")
        if self.patient.complexion:
            parts.append(f"Complexion: {self.patient.complexion}")
        const_str = "  |  ".join(parts) if parts else "No constitutional filter"
        s = QLabel(f"Profile:  {const_str}  |  ID: {self.patient.patient_id}")
        s.setStyleSheet("color:rgba(255,255,255,0.70); font-size:11px;")
        col = QVBoxLayout(); col.setSpacing(2)
        col.addWidget(t); col.addWidget(s)
        hr.addLayout(col)
        layout.addWidget(hdr)

        # ── Legend ────────────────────────────────────────────────────
        legend = QFrame()
        legend.setFixedHeight(28)
        legend.setStyleSheet("background:#1B5E20;")
        leg_row = QHBoxLayout(legend)
        leg_row.setContentsMargins(16, 0, 16, 0)
        leg_row.setSpacing(20)
        for text in [
            "★★★ Grade 3 — Bold",
            "★★☆ Grade 2 — Italic",
            "★☆☆ Grade 1 — Plain",
            "🔵 Constitutional",
            "🟣 Universal",
            "💊 Click any remedy to see Complementary · Antidotes · Inimical · Follows Well",
        ]:
            l = QLabel(text)
            l.setStyleSheet("color:rgba(255,255,255,0.85); font-size:10px;")
            leg_row.addWidget(l)
        leg_row.addStretch()
        layout.addWidget(legend)

        # ── Main splitter: tables top, relations panel bottom ─────────
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Tab widget for constitutional / symptomatic
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabBar::tab {{
                background: #C8E6C9; color: #1B5E20;
                padding: 8px 20px; font-weight: 700;
                border-radius: 4px 4px 0 0;
            }}
            QTabBar::tab:selected {{
                background: {CLR_PRIMARY}; color: white;
            }}
            QTabWidget::pane {{ border: 1px solid {CLR_BORDER}; }}
        """)

        # Constitutional tab
        const_widget = QWidget()
        const_layout = QVBoxLayout(const_widget)
        const_layout.setContentsMargins(0, 0, 0, 0)
        self.const_info = QLabel(
            "  ✔  Constitutional remedies — sorted by Grade → Profile → Match %"
        )
        self.const_info.setFixedHeight(28)
        self.const_info.setStyleSheet(
            f"background:#E3F2FD; color:#0D47A1; font-weight:600;"
            f"font-size:11px; padding-left:10px;"
            f"border-bottom:1px solid {CLR_BORDER};"
        )
        const_layout.addWidget(self.const_info)
        self.const_table = _make_table()
        self.const_table.itemSelectionChanged.connect(
            lambda: self._on_row_selected(self.const_table)
        )
        const_layout.addWidget(self.const_table)
        self.tab_widget.addTab(const_widget, "🏆  Constitutional Matches")

        # Symptomatic tab
        symp_widget = QWidget()
        symp_layout = QVBoxLayout(symp_widget)
        symp_layout.setContentsMargins(0, 0, 0, 0)
        symp_info = QLabel(
            "  ℹ  Symptom-matched remedies — may not match constitutional profile"
        )
        symp_info.setFixedHeight(28)
        symp_info.setStyleSheet(
            f"background:#FFF9C4; color:#827717; font-weight:600;"
            f"font-size:11px; padding-left:10px;"
            f"border-bottom:1px solid {CLR_BORDER};"
        )
        symp_layout.addWidget(symp_info)
        self.symp_table = _make_table()
        self.symp_table.itemSelectionChanged.connect(
            lambda: self._on_row_selected(self.symp_table)
        )
        symp_layout.addWidget(self.symp_table)
        self.tab_widget.addTab(symp_widget, "📋  Symptom-Only Matches")

        main_splitter.addWidget(self.tab_widget)

        # ── Relations panel ───────────────────────────────────────────
        rel_panel = QWidget()
        rel_panel.setStyleSheet(f"background:{CLR_WHITE};")
        rel_layout = QVBoxLayout(rel_panel)
        rel_layout.setContentsMargins(0, 0, 0, 0)
        rel_layout.setSpacing(0)

        rel_header = QWidget()
        rel_header.setFixedHeight(30)
        rel_header.setStyleSheet(
            f"background:#37474F; border-top:2px solid #1B5E20;"
        )
        rh_row = QHBoxLayout(rel_header)
        rh_row.setContentsMargins(14, 0, 14, 0)
        self.rel_title = QLabel(
            "💊  Remedy Relationships — click a remedy above to view"
        )
        self.rel_title.setStyleSheet(
            "color:white; font-weight:700; font-size:11px; background:transparent;"
        )
        rh_row.addWidget(self.rel_title)
        rel_layout.addWidget(rel_header)

        # Four coloured boxes side by side
        boxes_row = QHBoxLayout()
        boxes_row.setContentsMargins(8, 6, 8, 6)
        boxes_row.setSpacing(8)

        self.rel_boxes = {}
        box_configs = [
            ('complementary', '🤝 Complementary',  '#E3F2FD', '#0D47A1'),
            ('follows_well',  '➡ Follows Well',    '#E8F5E9', '#1B5E20'),
            ('antidote',      '⚕ Antidotes',        '#FFF3E0', '#E65100'),
            ('inimical',      '⚠ Inimical',         '#FFEBEE', '#B71C1C'),
        ]
        for key, title, bg, fg in box_configs:
            box = QWidget()
            box.setStyleSheet(
                f"background:{bg}; border:1px solid {fg}; border-radius:6px;"
            )
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(8, 6, 8, 6)
            box_layout.setSpacing(4)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(
                f"color:{fg}; font-weight:800; font-size:11px; "
                "background:transparent; border:none;"
            )
            box_layout.addWidget(title_lbl)

            content = QTextEdit()
            content.setReadOnly(True)
            content.setStyleSheet(
                f"background:transparent; border:none; "
                "font-size:11px; color:#333;"
            )
            content.setFixedHeight(68)
            content.setPlaceholderText("—")
            box_layout.addWidget(content)

            self.rel_boxes[key] = content
            boxes_row.addWidget(box)

        rel_layout.addLayout(boxes_row)
        main_splitter.addWidget(rel_panel)

        main_splitter.setSizes([420, 180])
        layout.addWidget(main_splitter)

        # ── Footer ────────────────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(46)
        footer.setStyleSheet(
            f"background:{CLR_PRIMARY_LIGHT}; border-top:1px solid {CLR_BORDER};"
        )
        ft = QHBoxLayout(footer)
        ft.setContentsMargins(16, 0, 16, 0)
        for color, label in [
            ("#1B5E20", "🟢 High ≥70%"),
            ("#F57F17", "🟡 Medium ≥40%"),
            ("#B71C1C", "🔴 Low <40%"),
        ]:
            l = QLabel(label)
            l.setStyleSheet(
                f"color:{color}; font-weight:700; "
                "font-size:11px; background:transparent;"
            )
            ft.addWidget(l)
            ft.addSpacing(14)
        ft.addStretch()
        self.result_lbl = QLabel("")
        self.result_lbl.setStyleSheet(
            f"color:{CLR_PRIMARY}; font-size:11px; "
            "font-weight:600; background:transparent;"
        )
        ft.addWidget(self.result_lbl)
        ft.addSpacing(12)
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(90, 30)
        close_btn.setStyleSheet("""
            QPushButton { background:#1A6B3C; color:white; border:none;
                border-radius:5px; font-weight:700; }
            QPushButton:hover { background:#134E2C; }
        """)
        close_btn.clicked.connect(self.accept)
        ft.addWidget(close_btn)
        layout.addWidget(footer)

    # ── Load remedies ─────────────────────────────────────────────────
    def _load(self):
        symptoms = []
        for field in [
            self.patient.mental_symptoms,
            self.patient.body_issues,
            self.patient.modalities,
        ]:
            if field:
                symptoms.extend(
                    [s.strip() for s in field.split('\n') if s.strip()]
                )
        if self.patient.aggravation:
            symptoms.append(self.patient.aggravation)
        if self.patient.amelioration:
            symptoms.append(self.patient.amelioration)

        if not symptoms:
            QMessageBox.information(
                self, "No Symptoms",
                "This patient has no recorded symptoms.\n"
                "Please edit the patient and add symptoms first."
            )
            return

        results = self.remedy_service.match_remedies(
            symptoms     = symptoms,
            thermal_type = self.patient.thermal_type,
            miasm        = self.patient.miasm,
            complexion   = self.patient.complexion,
            top_n        = 20
        )

        constitutional = results.get('constitutional', [])
        symptomatic    = results.get('symptomatic',    [])

        if not constitutional and not symptomatic:
            QMessageBox.information(
                self, "No Matches",
                "No remedies found for this patient's symptoms."
            )
            return

        _fill_table(self.const_table, constitutional)
        _fill_table(self.symp_table,  symptomatic)

        self.const_info.setText(
            f"  ✔  {len(constitutional)} constitutional remedies — "
            f"sorted by Grade → Profile → Match %  |  "
            f"Thermal: {self.patient.thermal_type or '—'}  "
            f"Miasm: {self.patient.miasm or '—'}  "
            f"Complexion: {self.patient.complexion or '—'}"
        )
        self.tab_widget.setTabText(
            0, f"🏆  Constitutional  ({len(constitutional)})"
        )
        self.tab_widget.setTabText(
            1, f"📋  Symptom-Only  ({len(symptomatic)})"
        )
        total = len(constitutional) + len(symptomatic)
        self.result_lbl.setText(
            f"{total} total  |  {len(constitutional)} constitutional"
        )
        self.tab_widget.setCurrentIndex(0)

    # ── Relations panel ───────────────────────────────────────────────
    def _on_row_selected(self, table: QTableWidget):
        row = table.currentRow()
        if row < 0:
            return
        rank_item = table.item(row, 0)
        if not rank_item:
            return
        abbr = rank_item.data(Qt.ItemDataRole.UserRole)
        name_item = table.item(row, 1)
        name = name_item.text() if name_item else abbr

        self.rel_title.setText(
            f"💊  Remedy Relationships for:  {name}  ({abbr})"
        )

        relations = self.remedy_service.get_relations(abbr)

        for key, box in self.rel_boxes.items():
            entries = relations.get(key, [])
            if entries:
                lines = []
                for rel_abbr, rel_name, notes in entries:
                    line = f"• {rel_name} ({rel_abbr})"
                    if notes:
                        line += f"\n  {notes}"
                    lines.append(line)
                box.setText('\n'.join(lines))
            else:
                box.setText("None recorded in Materia Medica")