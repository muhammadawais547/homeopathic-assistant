# gui/remedy_browser.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel,
    QTextEdit, QSplitter, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from services.remedy_service import RemedyService
from gui.theme import CLR_PRIMARY, CLR_PRIMARY_LIGHT, CLR_WHITE, CLR_BORDER


class RemedyBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remedy_service = RemedyService()
        self._all_remedies = []
        self._build_ui()
        self._load()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Title
        title_bar = QLabel("  📚  Remedy Browser — Kent's Repertory")
        title_bar.setFixedHeight(42)
        title_bar.setStyleSheet(
            f"background:{CLR_PRIMARY_LIGHT}; color:{CLR_PRIMARY};"
            "font-size:14px; font-weight:700;"
            f"border-bottom:2px solid {CLR_BORDER}; padding-left:8px;"
        )
        outer.addWidget(title_bar)

        # Search bar
        bar = QFrame()
        bar.setFixedHeight(50)
        bar.setStyleSheet(
            f"background:{CLR_WHITE}; border-bottom:1px solid {CLR_BORDER};"
        )
        bar_row = QHBoxLayout(bar)
        bar_row.setContentsMargins(16, 0, 16, 0)

        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText(
            "🔍  Filter by abbreviation or full Latin name…"
        )
        self.search_in.setFixedHeight(30)
        self.search_in.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {CLR_BORDER};
                border-radius: 15px;
                padding: 0 14px;
                font-size: 12px;
                background: {CLR_PRIMARY_LIGHT};
            }}
            QLineEdit:focus {{ border-color: #27AE60; background: white; }}
        """)
        self.search_in.textChanged.connect(self._filter)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(
            f"color:{CLR_PRIMARY}; font-weight:700; font-size:12px;"
            " background:transparent;"
        )
        bar_row.addWidget(self.search_in, 1)
        bar_row.addSpacing(12)
        bar_row.addWidget(self.count_lbl)
        outer.addWidget(bar)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: remedy table — 4 cols
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Abbreviation", "Full Latin Name", "Grade", "Rubrics"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: {CLR_WHITE};
                alternate-background-color: {CLR_PRIMARY_LIGHT};
                outline: none; font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 5px 10px;
                border-bottom: 1px solid #E8F5EE;
            }}
            QHeaderView::section {{
                background-color: {CLR_PRIMARY};
                color: white; padding: 8px 10px;
                border: none; font-weight: 700; font-size: 11px;
            }}
        """)
        self.table.itemSelectionChanged.connect(self._show_rubrics)
        splitter.addWidget(self.table)

        # Bottom: rubric detail panel
        detail_frame = QWidget()
        detail_frame.setStyleSheet(f"background:{CLR_WHITE};")
        dl = QVBoxLayout(detail_frame)
        dl.setContentsMargins(12, 8, 12, 8)
        dl.setSpacing(4)

        self.detail_header = QLabel(
            "Select a remedy above to view its rubrics from Kent's Repertory"
        )
        self.detail_header.setStyleSheet(
            f"color:{CLR_PRIMARY}; font-weight:700; font-size:12px;"
            " background:transparent;"
        )

        leg = QLabel(
            "  ★★★ Grade 3 = Bold (Highest confirmed)    "
            "★★☆ Grade 2 = Italic (Frequently indicated)    "
            "★☆☆ Grade 1 = Plain (Occasionally indicated)"
        )
        leg.setStyleSheet(
            "color:#555; font-size:10px; background:#F5F5F5;"
            "padding:3px 6px; border-radius:4px;"
        )

        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)
        self.detail_box.setStyleSheet(f"""
            QTextEdit {{
                background: {CLR_WHITE};
                border: 1px solid {CLR_BORDER};
                border-radius: 5px;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        self.detail_box.setPlaceholderText(
            "Associated rubrics will appear here…"
        )
        dl.addWidget(self.detail_header)
        dl.addWidget(leg)
        dl.addWidget(self.detail_box)
        splitter.addWidget(detail_frame)

        splitter.setSizes([420, 220])
        outer.addWidget(splitter)

    def _load(self):
        """Load all remedies sorted by rubric count descending."""
        try:
            cursor = self.remedy_service.db.get_cursor()
            cursor.execute(
                """SELECT r.abbreviation,
                          CASE WHEN r.name IS NOT NULL
                               AND r.name != r.abbreviation
                               THEN r.name ELSE r.abbreviation END AS name,
                          COUNT(rr.rubric_id) AS rubric_count
                   FROM remedies r
                   LEFT JOIN rubric_remedy rr ON rr.remedy_id = r.id
                   GROUP BY r.id, r.abbreviation, r.name
                   ORDER BY rubric_count DESC, r.abbreviation ASC"""
            )
            self._all_remedies = cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(f"RemedyBrowser load error: {e}")
            self._all_remedies = []
        self._fill_table(self._all_remedies)

    def _filter(self, text: str):
        text = text.strip().lower()
        if not text:
            self._fill_table(self._all_remedies)
            return
        filtered = [
            r for r in self._all_remedies
            if text in (r['abbreviation'] or "").lower()
            or text in (r['name'] or "").lower()
        ]
        self._fill_table(filtered)

    def _fill_table(self, remedies):
        # Known grade-3 remedies for display
        grade3 = {
            'sulph.','phos.','sep.','lyc.','puls.','ars.',
            'nux-v.','lach.','bell.','calc.','nat-m.','sil.',
            'merc.','bry.','acon.','caust.','rhus-t.','carb-v.',
            'kali-c.','chin.','graph.','stram.','verat.',
            'hyos.','ign.','cham.','hep.','thuj.','con.','zinc.',
        }
        grade2 = {
            'alum.','am-c.','anac.','ant-t.','arg-n.','agar.',
            'aur.','bar-c.','berb.','bov.','canth.','caps.',
            'carb-an.','cocc.','colch.','coloc.','dig.','dros.',
            'dulc.','ferr.','gels.','glon.','kali-bi.','kreos.',
            'mag-c.','mag-m.','mez.','mur-ac.','nat-c.','nat-s.',
            'nit-ac.','op.','petr.','phos-ac.','plat.','plb.',
            'psor.','spig.','staph.','sul-ac.','tarent.',
            'arn.','chel.','ip.','led.',
        }

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(remedies))
        self.count_lbl.setText(
            f"{len(remedies)} remed{'ies' if len(remedies) != 1 else 'y'}"
        )

        for row, rem in enumerate(remedies):
            abbr  = rem['abbreviation'] or ""
            name  = rem['name'] or abbr
            count = rem.get('rubric_count', 0) or 0
            abbr_lower = abbr.lower()

            # Grade display
            if abbr_lower in grade3:
                stars, g_fg, g_bg = "★★★", "#1B5E20", "#C8E6C9"
            elif abbr_lower in grade2:
                stars, g_fg, g_bg = "★★☆", "#E65100", "#FFE0B2"
            else:
                stars, g_fg, g_bg = "★☆☆", "#546E7A", "#ECEFF1"

            # Row background: remedies with rubrics get white, others get pale
            if count > 0:
                row_bg  = None   # use alternating default
                count_fg = "#1B5E20"
                count_str = f"{count:,}"
            else:
                row_bg   = "#F9F9F9"
                count_fg = "#AAAAAA"
                count_str = "—"

            # Abbreviation
            a_item = QTableWidgetItem(abbr)
            a_item.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
            if row_bg:
                a_item.setBackground(QColor(row_bg))
                a_item.setForeground(QColor("#BBBBBB"))
            self.table.setItem(row, 0, a_item)

            # Name
            n_item = QTableWidgetItem(name)
            if abbr_lower in grade3:
                f = QFont(); f.setBold(True); f.setPointSize(11)
                n_item.setFont(f)
            elif abbr_lower in grade2:
                f = QFont(); f.setItalic(True)
                n_item.setFont(f)
            if row_bg:
                n_item.setBackground(QColor(row_bg))
                n_item.setForeground(QColor("#BBBBBB"))
            self.table.setItem(row, 1, n_item)

            # Grade badge
            g_item = QTableWidgetItem(f"  {stars}  ")
            g_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            g_item.setBackground(QColor(g_bg))
            g_item.setForeground(QColor(g_fg))
            gf = QFont(); gf.setBold(True)
            g_item.setFont(gf)
            self.table.setItem(row, 2, g_item)

            # Rubric count
            c_item = QTableWidgetItem(count_str)
            c_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cf = QFont(); cf.setBold(count > 0)
            c_item.setFont(cf)
            c_item.setForeground(QColor(count_fg))
            if row_bg:
                c_item.setBackground(QColor(row_bg))
            self.table.setItem(row, 3, c_item)

        self.table.setSortingEnabled(True)

    def _show_rubrics(self):
        sel = self.table.currentRow()
        if sel < 0:
            return
        abbr_item = self.table.item(sel, 0)
        name_item = self.table.item(sel, 1)
        if not abbr_item:
            return
        abbr = abbr_item.text()
        name = name_item.text() if name_item else abbr
        count_item = self.table.item(sel, 3)
        count = count_item.text() if count_item else "0"

        self.detail_header.setText(
            f"Rubrics for:  {name}  ({abbr})  "
            f"— {count} rubrics in Kent's Repertory"
        )

        rubrics = self.remedy_service.get_rubrics_for_remedy(abbr, limit=150)
        if rubrics:
            lines = []
            for r in rubrics:
                grade = r.get('grade', 1)
                prefix = "★★★" if grade == 3 else "★★☆" if grade == 2 else "★☆☆"
                lines.append(f"{prefix}  {r['path']}")
            if len(rubrics) == 150:
                lines.append(f"\n… showing first 150 of {count} rubrics")
            self.detail_box.setText('\n'.join(lines))
        else:
            self.detail_box.setText(
                "No rubrics found for this remedy in the database.\n"
                "This remedy may be from supplementary sources not in Kent's core repertory."
            )