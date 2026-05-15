# gui/consultation_history_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QSplitter, QWidget
)
from PyQt6.QtCore import Qt
from services.patient_service import PatientService


class ConsultationHistoryDialog(QDialog):
    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.patient_service = PatientService()
        self.setWindowTitle(f"Consultation History — {patient.name}")
        self.setMinimumSize(750, 550)
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(
            f"<b>{self.patient.name}</b> &nbsp;|&nbsp; "
            f"ID: {self.patient.patient_id} &nbsp;|&nbsp; "
            f"Age: {self.patient.age or '—'} &nbsp;|&nbsp; "
            f"Phone: {self.patient.phone or '—'}"
        )
        header.setStyleSheet(
            "background:#ecf0f1; padding:8px; border-radius:4px; font-size:13px;"
        )
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # ── Top: consultations table ──────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Date", "Thermal Type", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._show_detail)
        splitter.addWidget(self.table)

        # ── Bottom: detail panel ──────────────────────────────────────
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 4, 0, 0)
        detail_layout.addWidget(QLabel("<b>Consultation Detail</b>"))
        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)
        self.detail_box.setPlaceholderText("Select a consultation above to view details…")
        detail_layout.addWidget(self.detail_box)
        splitter.addWidget(detail_widget)

        splitter.setSizes([300, 220])
        layout.addWidget(splitter)

        # ── Close button ──────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def load_history(self):
        self._consultations = self.patient_service.get_consultations(
            self.patient.patient_id
        )
        self.table.setRowCount(len(self._consultations))
        for row, c in enumerate(self._consultations):
            date_str = (
                c['consultation_date'].strftime('%Y-%m-%d')
                if hasattr(c['consultation_date'], 'strftime')
                else str(c['consultation_date'])
            )
            self.table.setItem(row, 0, QTableWidgetItem(date_str))
            self.table.setItem(row, 1, QTableWidgetItem(c['thermal_type'] or '—'))
            self.table.setItem(row, 2, QTableWidgetItem(c['notes'] or ''))

        if self._consultations:
            self.table.selectRow(0)

    def _show_detail(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._consultations):
            return
        c = self._consultations[row]

        lines = []
        fields = [
            ("Mental Symptoms",  c.get('mental_symptoms')),
            ("Body Issues",      c.get('body_issues')),
            ("Modalities",       c.get('modalities')),
            ("Pain Information", c.get('pain_information')),
            ("Pain Time",        c.get('pain_time')),
            ("Notes",            c.get('notes')),
        ]
        for label, value in fields:
            if value:
                lines.append(f"【{label}】\n{value}\n")

        self.detail_box.setText(
            '\n'.join(lines) if lines else "No details recorded for this consultation."
        )