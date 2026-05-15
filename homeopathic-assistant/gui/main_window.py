# gui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout,
    QWidget, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.patient_form import PatientForm
from gui.patient_list import PatientList
from gui.remedy_browser import RemedyBrowser
from gui.disease_browser import DiseaseBrowser
from gui.add_remedy_dialog import AddRemedyDialog
from gui.theme import MAIN_STYLESHEET, CLR_HEADER_BG, CLR_WHITE, CLR_PRIMARY_LIGHT, CLR_BORDER


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Homeopathic Assistant")
        self.setMinimumSize(1150, 800)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(62)
        header.setStyleSheet(f"background-color: {CLR_HEADER_BG};")
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(24, 0, 24, 0)

        icon_lbl = QLabel("🌿")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        icon_lbl.setStyleSheet("background:transparent;")

        title_lbl = QLabel("Homeopathic Assistant")
        title_lbl.setStyleSheet(
            f"color:{CLR_WHITE}; font-size:20px; font-weight:700;"
            "background:transparent; letter-spacing:1px;"
        )
        sub_lbl = QLabel("Patient & Remedy Management System — Kent's Repertory")
        sub_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.65); font-size:11px; background:transparent;"
        )
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.addWidget(title_lbl)
        text_col.addWidget(sub_lbl)

        # Add Remedy button in header
        add_remedy_btn = QLabel("＋ Add Remedy")
        add_remedy_btn.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(255,255,255,0.15);
                border: 1px solid rgba(255,255,255,0.35);
                border-radius: 14px;
                padding: 5px 14px;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel:hover { background-color: rgba(255,255,255,0.25); }
        """)
        add_remedy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_remedy_btn.mousePressEvent = lambda e: self._open_add_remedy()

        h_row.addWidget(icon_lbl)
        h_row.addSpacing(10)
        h_row.addLayout(text_col)
        h_row.addStretch()
        h_row.addWidget(add_remedy_btn)
        layout.addWidget(header)

        # ── Tabs ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.patient_form    = PatientForm()
        self.patient_list    = PatientList()
        self.remedy_browser  = RemedyBrowser()
        self.disease_browser = DiseaseBrowser()

        self.tabs.addTab(self.patient_form,    "➕  Add Patient")
        self.tabs.addTab(self.patient_list,    "📋  Patients")
        self.tabs.addTab(self.remedy_browser,  "📚  Remedy Browser")
        self.tabs.addTab(self.disease_browser, "💊  Diseases")

        layout.addWidget(self.tabs)

        # ── Wire signals ──────────────────────────────────────────────
        # patient_added → refresh list immediately + switch to Patients tab
        self.patient_form.patient_added.connect(self._on_patient_added)

    def _on_patient_added(self):
        """Called immediately after a patient is saved successfully."""
        self.patient_list.refresh()          # force immediate reload
        self.tabs.setCurrentIndex(1)         # switch to Patients tab

    def _open_add_remedy(self):
        dlg = AddRemedyDialog(self)
        if dlg.exec():
            self.remedy_browser._load()      # refresh remedy browser after adding