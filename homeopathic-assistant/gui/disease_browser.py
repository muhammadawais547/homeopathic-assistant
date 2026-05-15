# gui/disease_browser.py
"""
Disease Browser — shows frequently used remedies for specific diseases
organized by category: Mental, Joints, Fever, Digestive, Skin,
Respiratory, Female, Eye.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter,
    QLineEdit, QFrame, QTextEdit, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from services.remedy_service import RemedyService
from gui.theme import (
    CLR_PRIMARY, CLR_PRIMARY_LIGHT, CLR_WHITE,
    CLR_BORDER, CLR_ACCENT, CLR_TEXT
)

CATEGORY_ICONS = {
    'Mental':      '🧠',
    'Head':        '🔵',
    'Heart':       '❤️',
    'Urinary':     '💧',
    'Male':        '♂️',
    'Female':      '🌸',
    'Pediatric':   '👶',
    'Dental':      '🦷',
    'Ear':         '👂',
    'Nose':        '👃',
    'Throat':      '🔴',
    'Eye':         '👁️',
    'Joints':      '🦴',
    'Fever':       '🌡️',
    'Digestive':   '🍽️',
    'Skin':        '🩹',
    'Respiratory': '💨',
    'Liver':       '🟤',
    'Sleep':       '😴',
    'Injuries':    '🤕',
    'Nerves':      '⚡',
    'Endocrine':   '⚕️',
    'Addiction':   '🚫',
}

PRIORITY_COLORS = {
    1: ('#E8F5E9', '#1B5E20', '1st Line'),
    2: ('#FFF9C4', '#827717', '2nd Line'),
    3: ('#FFF3E0', '#E65100', 'Specific'),
}


class DiseaseBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remedy_service = RemedyService()
        self._build_ui()
        self._load_diseases()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Title
        title = QLabel("  💊  Disease & Remedy Browser")
        title.setFixedHeight(42)
        title.setStyleSheet(
            f"background:{CLR_PRIMARY_LIGHT}; color:{CLR_PRIMARY};"
            "font-size:14px; font-weight:700;"
            f"border-bottom:2px solid {CLR_BORDER}; padding-left:8px;"
        )
        outer.addWidget(title)

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
            "🔍  Search disease name (e.g. headache, fever, eczema)…"
        )
        self.search_in.setFixedHeight(32)
        self.search_in.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {CLR_BORDER};
                border-radius: 16px;
                padding: 0 16px;
                font-size: 12px;
                background: {CLR_PRIMARY_LIGHT};
            }}
            QLineEdit:focus {{ border-color:{CLR_ACCENT}; background:white; }}
        """)
        self.search_in.textChanged.connect(self._search)
        bar_row.addWidget(self.search_in)
        outer.addWidget(bar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: disease tree
        left = QWidget()
        left.setMinimumWidth(220)
        left.setMaximumWidth(280)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        tree_header = QLabel("  Disease Categories")
        tree_header.setFixedHeight(32)
        tree_header.setStyleSheet(
            f"background:{CLR_PRIMARY}; color:white; "
            "font-weight:700; font-size:11px; padding-left:8px;"
        )
        left_layout.addWidget(tree_header)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                border: none;
                background: {CLR_WHITE};
                font-size: 12px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 5px 8px;
                border-bottom: 1px solid {CLR_PRIMARY_LIGHT};
            }}
            QTreeWidget::item:selected {{
                background: {CLR_PRIMARY};
                color: white;
            }}
            QTreeWidget::item:hover {{
                background: {CLR_PRIMARY_LIGHT};
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: none;
            }}
        """)
        self.tree.itemClicked.connect(self._on_tree_click)
        left_layout.addWidget(self.tree)
        splitter.addWidget(left)

        # Right: remedies table + detail
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Disease title
        self.disease_label = QLabel("  Select a disease from the left panel")
        self.disease_label.setFixedHeight(36)
        self.disease_label.setStyleSheet(
            f"background:#E3F2FD; color:#0D47A1; "
            "font-weight:700; font-size:13px; padding-left:12px;"
            f"border-bottom:1px solid {CLR_BORDER};"
        )
        right_layout.addWidget(self.disease_label)

        # Remedy table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Priority", "Remedy Name", "Abbreviation",
            "Key Symptoms", "Modalities"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: {CLR_WHITE};
                alternate-background-color: {CLR_PRIMARY_LIGHT};
                outline: none; font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #E8F5EE;
            }}
            QHeaderView::section {{
                background-color: {CLR_PRIMARY};
                color: white; padding: 8px 10px;
                border: none; font-weight: 700; font-size: 11px;
            }}
        """)
        self.table.itemClicked.connect(self._show_notes)
        right_layout.addWidget(self.table)

        # Notes panel
        notes_frame = QFrame()
        notes_frame.setFixedHeight(90)
        notes_frame.setStyleSheet(
            f"background:#F8FFF9; border-top:2px solid {CLR_BORDER};"
        )
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(12, 6, 12, 6)
        self.notes_label = QLabel("Clinical Notes:")
        self.notes_label.setStyleSheet(
            f"color:{CLR_PRIMARY}; font-weight:700; font-size:11px;"
        )
        self.notes_text = QLabel("Click on a remedy to see clinical notes")
        self.notes_text.setWordWrap(True)
        self.notes_text.setStyleSheet("color:#333; font-size:12px;")
        notes_layout.addWidget(self.notes_label)
        notes_layout.addWidget(self.notes_text)
        right_layout.addWidget(notes_frame)

        splitter.addWidget(right)
        splitter.setSizes([240, 800])
        outer.addWidget(splitter)

        # Legend
        legend = QFrame()
        legend.setFixedHeight(30)
        legend.setStyleSheet(
            f"background:{CLR_PRIMARY_LIGHT}; border-top:1px solid {CLR_BORDER};"
        )
        leg_row = QHBoxLayout(legend)
        leg_row.setContentsMargins(16, 0, 16, 0)
        leg_row.setSpacing(20)
        for bg, fg, label in [
            ('#E8F5E9', '#1B5E20', '🟢 1st Line — Primary remedy'),
            ('#FFF9C4', '#827717', '🟡 2nd Line — Frequently used'),
            ('#FFF3E0', '#E65100', '🟠 Specific — For specific presentations'),
        ]:
            l = QLabel(label)
            l.setStyleSheet(
                f"color:{fg}; font-weight:700; font-size:10px; background:transparent;"
            )
            leg_row.addWidget(l)
        leg_row.addStretch()
        outer.addWidget(legend)

    def _load_diseases(self):
        rows = self.remedy_service.get_diseases()
        categories = {}
        for row in rows:
            cat  = row['category']
            dis  = row['disease_name']
            if cat not in categories:
                categories[cat] = []
            if dis not in categories[cat]:
                categories[cat].append(dis)

        self.tree.clear()
        for cat, diseases in sorted(categories.items()):
            icon = CATEGORY_ICONS.get(cat, '💊')
            cat_item = QTreeWidgetItem([f"{icon}  {cat}"])
            cat_item.setFont(0, QFont('Segoe UI', 11, QFont.Weight.Bold))
            cat_item.setForeground(0, QColor(CLR_PRIMARY))
            cat_item.setData(0, Qt.ItemDataRole.UserRole, None)
            self.tree.addTopLevelItem(cat_item)
            for disease in sorted(diseases):
                dis_item = QTreeWidgetItem([f"    {disease}"])
                dis_item.setData(0, Qt.ItemDataRole.UserRole, disease)
                cat_item.addChild(dis_item)
            cat_item.setExpanded(True)

    def _on_tree_click(self, item, col):
        disease = item.data(0, Qt.ItemDataRole.UserRole)
        if disease:
            self._show_disease(disease)

    def _show_disease(self, disease: str):
        remedies = self.remedy_service.get_disease_remedies(disease)
        self.disease_label.setText(
            f"  💊  {disease}  —  {len(remedies)} remedies"
        )
        self._fill_table(remedies)
        self.notes_text.setText("Click on a remedy to see clinical notes")
        self._current_remedies = remedies

    def _fill_table(self, remedies):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(remedies))

        for row, r in enumerate(remedies):
            priority = r.get('priority', 1)
            bg, fg, label = PRIORITY_COLORS.get(priority, ('#FFF','#000',''))

            def cell(text, bold=False, center=False):
                item = QTableWidgetItem(str(text) if text else '—')
                item.setBackground(QColor(bg))
                item.setForeground(QColor(fg))
                if bold:
                    f = QFont(); f.setBold(True)
                    item.setFont(f)
                if center:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return item

            self.table.setItem(row, 0, cell(label, center=True))
            self.table.setItem(row, 1, cell(r.get('full_name',''), bold=(priority==1)))
            self.table.setItem(row, 2, cell(r.get('remedy_abbr',''), center=True))
            self.table.setItem(row, 3, cell(r.get('symptoms','')))
            self.table.setItem(row, 4, cell(r.get('modalities','')))

        self.table.setSortingEnabled(True)

    def _show_notes(self, item):
        row = item.row()
        if hasattr(self, '_current_remedies') and row < len(self._current_remedies):
            r = self._current_remedies[row]
            name  = r.get('full_name', r.get('remedy_abbr',''))
            notes = r.get('notes','')
            self.notes_label.setText(f"Clinical Notes — {name}:")
            self.notes_text.setText(notes or 'No additional notes.')

    def _search(self, text: str):
        text = text.strip()
        if not text:
            self._load_diseases()
            return
        results = self.remedy_service.search_disease(text)
        if not results:
            self.table.setRowCount(0)
            self.disease_label.setText(f"  No diseases found for '{text}'")
            return
        # Show first match
        if results:
            self._show_disease(results[0]['disease_name'])
            self.disease_label.setText(
                f"  Search: '{text}' — {len(results)} diseases found"
            )