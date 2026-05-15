# gui/patient_list.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QMessageBox, QLabel, QFrame,
    QDialog, QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from services.patient_service import PatientService
from gui.patient_details_dialog import PatientDetailsDialog
from gui.patient_remedies_dialog import PatientRemediesDialog
from gui.patient_edit_dialog import PatientEditDialog
from gui.theme import (
    CLR_PRIMARY, CLR_PRIMARY_LIGHT, CLR_PRIMARY_DARK,
    CLR_WHITE, CLR_BORDER, CLR_ACCENT, CLR_DANGER, CLR_TEXT, CLR_BG
)


def _action_btn(text: str, bg: str, hover: str, w=88) -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedSize(w, 30)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: white;
            border: none;
            border-radius: 15px;
            font-weight: 600;
            font-size: 10px;
            padding: 0 6px;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {hover}; padding-top: 2px; }}
    """)
    return btn


def _center_widget(widget: QWidget) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    h = QHBoxLayout(w)
    h.setContentsMargins(4, 4, 4, 4)
    h.addStretch()
    h.addWidget(widget)
    h.addStretch()
    return w


class VisitLogDialog(QDialog):
    def __init__(self, patient_name, visits, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Visit Log — {patient_name}")
        self.setMinimumSize(340, 360)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        lbl = QLabel(f"Visit history for  <b>{patient_name}</b>")
        lbl.setStyleSheet(
            f"color:{CLR_PRIMARY}; font-size:13px; padding:6px;"
            f"background:{CLR_PRIMARY_LIGHT}; border-radius:4px;"
        )
        layout.addWidget(lbl)
        lst = QListWidget()
        lst.setStyleSheet(f"""
            QListWidget {{ border:1px solid {CLR_BORDER}; border-radius:6px; background:{CLR_WHITE}; }}
            QListWidget::item {{ padding:8px 12px; border-bottom:1px solid {CLR_BORDER}; }}
            QListWidget::item:hover {{ background:{CLR_PRIMARY_LIGHT}; }}
        """)
        if visits:
            for v in visits:
                date_str = (
                    v['visit_date'].strftime('%A, %d %B %Y  %H:%M')
                    if hasattr(v['visit_date'], 'strftime') else str(v['visit_date'])
                )
                item = QListWidgetItem(f"  \U0001f4c5  {date_str}")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                lst.addItem(item)
        else:
            item = QListWidgetItem("  No visits recorded yet.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            lst.addItem(item)
        layout.addWidget(lst)
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(110)
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(); row.addWidget(close_btn); row.addStretch()
        layout.addLayout(row)


class PatientList(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patient_service = PatientService()
        self._all_patients = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Title strip
        title_bar = QLabel("  \U0001f4cb  Patient Records")
        title_bar.setFixedHeight(42)
        title_bar.setStyleSheet(
            f"background:{CLR_PRIMARY_LIGHT}; color:{CLR_PRIMARY};"
            "font-size:14px; font-weight:700;"
            f"border-bottom:2px solid {CLR_BORDER}; padding-left:8px;"
        )
        outer.addWidget(title_bar)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(58)
        toolbar.setStyleSheet(
            f"background:{CLR_WHITE}; border-bottom:1px solid {CLR_BORDER};"
        )
        tb_row = QHBoxLayout(toolbar)
        tb_row.setContentsMargins(16, 0, 16, 0)
        tb_row.setSpacing(12)

        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("Search by name, ID or phone...")
        self.search_in.setFixedHeight(36)
        self.search_in.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {CLR_BORDER};
                border-radius: 18px;
                padding: 0 16px;
                font-size: 12px;
                background: {CLR_BG};
            }}
            QLineEdit:focus {{ border-color: {CLR_ACCENT}; background: white; }}
        """)
        self.search_in.textChanged.connect(self._live_search)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedSize(90, 34)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background:{CLR_PRIMARY_LIGHT}; color:{CLR_PRIMARY};
                border:1.5px solid {CLR_BORDER}; border-radius:17px;
                font-weight:700; font-size:11px;
            }}
            QPushButton:hover {{ background:{CLR_BORDER}; }}
        """)
        refresh_btn.clicked.connect(self.refresh)

        self.count_lbl = QLabel("—")
        self.count_lbl.setStyleSheet(
            f"color:{CLR_PRIMARY}; font-weight:700; font-size:12px;"
            "background:transparent; min-width:90px;"
        )
        self.count_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        tb_row.addWidget(self.search_in, 1)
        tb_row.addWidget(refresh_btn)
        tb_row.addWidget(self.count_lbl)
        outer.addWidget(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Patient ID", "Full Name", "Age", "Gender", "Phone",
            "View", "Remedies", "Edit / Delete"
        ])

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 55)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 115)
        self.table.setColumnWidth(7, 190)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: {CLR_WHITE};
                alternate-background-color: {CLR_PRIMARY_LIGHT};
                selection-background-color: #C8E6C9;
                selection-color: {CLR_TEXT};
                outline: none;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #E8F5EE;
            }}
            QHeaderView::section {{
                background-color: {CLR_PRIMARY};
                color: white;
                padding: 10px 10px;
                border: none;
                font-weight: 700;
                font-size: 11px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }}
        """)
        outer.addWidget(self.table)

        # Status bar
        status = QFrame()
        status.setFixedHeight(28)
        status.setStyleSheet(
            f"background:{CLR_PRIMARY_LIGHT}; border-top:1px solid {CLR_BORDER};"
        )
        st_row = QHBoxLayout(status)
        st_row.setContentsMargins(16, 0, 16, 0)
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet(
            f"color:{CLR_PRIMARY}; font-size:11px; background:transparent;"
        )
        st_row.addWidget(self.status_lbl)
        st_row.addStretch()
        outer.addWidget(status)

    def refresh(self):
        self._all_patients = self.patient_service.get_all_patients()
        self._fill_table(self._all_patients)
        self.status_lbl.setText(
            f"Last refreshed — {len(self._all_patients)} patient(s) loaded"
        )

    def _live_search(self, text):
        text = text.strip().lower()
        if not text:
            self._fill_table(self._all_patients)
            return
        filtered = [
            p for p in self._all_patients
            if text in (p.name or "").lower()
            or text in p.patient_id.lower()
            or text in (p.phone or "").lower()
        ]
        self._fill_table(filtered)
        self.status_lbl.setText(f"Search: {len(filtered)} match(es) found")

    def _fill_table(self, patients):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(patients))
        self.count_lbl.setText(
            f"{len(patients)} patient{'s' if len(patients) != 1 else ''}"
        )

        center = Qt.AlignmentFlag.AlignCenter
        left   = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        for row, p in enumerate(patients):

            def cell(text, align=left):
                item = QTableWidgetItem(str(text) if text else "\u2014")
                item.setTextAlignment(align)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                return item

            self.table.setItem(row, 0, cell(p.patient_id))
            self.table.setItem(row, 1, cell(p.name))
            self.table.setItem(row, 2, cell(p.age if p.age else None, center))
            self.table.setItem(row, 3, cell(p.gender, center))
            self.table.setItem(row, 4, cell(p.phone))

            # View
            view_btn = _action_btn("View", "#455A64", "#37474F", w=82)
            view_btn.clicked.connect(lambda _, pid=p.patient_id: self._view(pid))
            self.table.setCellWidget(row, 5, _center_widget(view_btn))

            # Remedies
            rem_btn = _action_btn("Remedies", "#1565C0", "#0D47A1", w=100)
            rem_btn.clicked.connect(lambda _, pid=p.patient_id: self._remedies(pid))
            self.table.setCellWidget(row, 6, _center_widget(rem_btn))

            # Edit + Delete pair
            edit_btn = _action_btn("Edit", CLR_ACCENT, "#1E7E34", w=76)
            edit_btn.clicked.connect(lambda _, pid=p.patient_id: self._edit(pid))

            del_btn = _action_btn("Delete", CLR_DANGER, "#922B21", w=76)
            del_btn.clicked.connect(lambda _, pid=p.patient_id: self._delete(pid))

            pair = QWidget()
            pair.setStyleSheet("background:transparent;")
            pair_row = QHBoxLayout(pair)
            pair_row.setContentsMargins(6, 4, 6, 4)
            pair_row.setSpacing(8)
            pair_row.addStretch()
            pair_row.addWidget(edit_btn)
            pair_row.addWidget(del_btn)
            pair_row.addStretch()
            self.table.setCellWidget(row, 7, pair)

        self.table.setSortingEnabled(True)

    def _view(self, patient_id):
        p = self.patient_service.get_patient(patient_id)
        if p:
            PatientDetailsDialog(p, self).exec()

    def _edit(self, patient_id):
        p = self.patient_service.get_patient(patient_id)
        if p:
            dlg = PatientEditDialog(p, self)
            if dlg.exec():
                self.refresh()

    def _remedies(self, patient_id):
        p = self.patient_service.get_patient(patient_id)
        if p:
            PatientRemediesDialog(p, self).exec()

    def _delete(self, patient_id):
        p = self.patient_service.get_patient(patient_id)
        name = p.name if p else patient_id
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Permanently delete <b>{name}</b>?<br><small>This cannot be undone.</small>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.patient_service.delete_patient(patient_id):
                self.status_lbl.setText(f"Patient '{name}' deleted.")
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Could not delete patient.")