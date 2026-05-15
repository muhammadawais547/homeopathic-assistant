# gui/patient_details_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from gui.theme import CLR_PRIMARY, CLR_PRIMARY_LIGHT, CLR_WHITE, CLR_BORDER, CLR_MUTED


def _section(title: str) -> QLabel:
    lbl = QLabel(title)
    lbl.setStyleSheet(
        f"color:{CLR_PRIMARY}; font-weight:700; font-size:12px;"
        f"border-bottom:1.5px solid {CLR_BORDER}; padding-bottom:3px;"
        "margin-top:10px;"
    )
    return lbl


def _row_widgets(label: str, value: str):
    k = QLabel(label)
    k.setStyleSheet(
        f"color:{CLR_MUTED}; font-size:11px; font-weight:600;"
    )
    k.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
    v = QLabel(value or "—")
    v.setWordWrap(True)
    v.setStyleSheet("color:#1C2A1E; font-size:12px;")
    return k, v


class PatientDetailsDialog(QDialog):
    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.setWindowTitle(f"Patient Details — {patient.name}")
        self.setMinimumSize(560, 640)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(56)
        hdr.setStyleSheet(f"background:{CLR_PRIMARY};")
        hdr_row = QHBoxLayout(hdr)
        hdr_row.setContentsMargins(20, 0, 20, 0)
        t = QLabel(f"🧑‍⚕️  {self.patient.name}")
        t.setStyleSheet(
            f"color:{CLR_WHITE}; font-size:15px; font-weight:700;"
        )
        s = QLabel(f"ID: {self.patient.patient_id}")
        s.setStyleSheet("color:rgba(255,255,255,0.7); font-size:11px;")
        col = QVBoxLayout(); col.setSpacing(1)
        col.addWidget(t); col.addWidget(s)
        hdr_row.addLayout(col)
        layout.addWidget(hdr)

        # Scroll body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none; background:white;}")
        body = QWidget()
        body.setStyleSheet(f"background:{CLR_WHITE};")
        g = QGridLayout(body)
        g.setContentsMargins(24, 16, 24, 16)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(7)
        g.setColumnMinimumWidth(0, 150)
        g.setColumnStretch(1, 1)

        p = self.patient
        rows_data = [
            ("── Basic Information ──", None),
            ("Name:",           p.name),
            ("Age:",            str(p.age) if p.age else None),
            ("Gender:",         p.gender),
            ("Blood Pressure:", p.blood_pressure),
            ("Phone:",          p.phone),
            ("Address:",        p.address),
            ("── Constitutional ──", None),
            ("Complexion:",     p.complexion),
            ("Thermal Type:",   p.thermal_type),
            ("Miasm:",          p.miasm),
            ("── Medical ──", None),
            ("Medical History:", p.medical_history),
            ("── Symptoms ──", None),
            ("Mental Symptoms:", p.mental_symptoms),
            ("Body Issues:",     p.body_issues),
            ("Modalities:",      p.modalities),
            ("Aggravation (<):", p.aggravation),
            ("Amelioration (>):", p.amelioration),
        ]

        r = 0
        for label, value in rows_data:
            if value is None and label.startswith("──"):
                sec = _section(label.replace("──", "").strip())
                g.addWidget(sec, r, 0, 1, 2)
            else:
                k, v = _row_widgets(label, value)
                g.addWidget(k, r, 0)
                g.addWidget(v, r, 1)
            r += 1

        scroll.setWidget(body)
        layout.addWidget(scroll)

        footer = QFrame()
        footer.setFixedHeight(52)
        footer.setStyleSheet(
            f"background:{CLR_WHITE}; border-top:1px solid {CLR_BORDER};"
        )
        ft_row = QHBoxLayout(footer)
        ft_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        ft_row.addWidget(close_btn)
        ft_row.addStretch()
        layout.addWidget(footer)