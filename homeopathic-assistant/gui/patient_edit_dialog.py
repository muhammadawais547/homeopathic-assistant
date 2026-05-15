# gui/patient_edit_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QRadioButton, QPushButton,
    QMessageBox, QGroupBox, QSpinBox, QComboBox,
    QLabel, QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt

from models.patient import Patient
from services.patient_service import PatientService
from gui.theme import CLR_PRIMARY, CLR_PRIMARY_LIGHT, CLR_WHITE, CLR_BORDER


class PatientEditDialog(QDialog):
    def __init__(self, patient: Patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.patient_service = PatientService()
        self.setWindowTitle(f"Edit Patient — {patient.name}")
        self.setMinimumSize(680, 700)
        self._build_ui()
        self._populate()

    def _form(self):
        f = QFormLayout()
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        f.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f.setHorizontalSpacing(16)
        f.setVerticalSpacing(9)
        return f

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        hdr = QWidget()
        hdr.setFixedHeight(46)
        hdr.setStyleSheet(f"background:{CLR_PRIMARY};")
        hr = QHBoxLayout(hdr)
        hr.setContentsMargins(20, 0, 20, 0)
        lbl = QLabel(
            f"✏️  Editing: {self.patient.name}  "
            f"(ID: {self.patient.patient_id})"
        )
        lbl.setStyleSheet(
            f"color:{CLR_WHITE}; font-size:13px; font-weight:700;"
        )
        hr.addWidget(lbl)
        outer.addWidget(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(14)
        layout.addWidget(self._grp_basic())
        layout.addWidget(self._grp_medical())
        layout.addWidget(self._grp_symptoms())
        layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)

        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"background:{CLR_WHITE}; border-top:1px solid {CLR_BORDER};"
        )
        btn_row = QHBoxLayout(bar)
        btn_row.setContentsMargins(24, 0, 24, 0)

        save_btn = QPushButton("💾  Save Changes")
        save_btn.setFixedHeight(34)
        save_btn.setMinimumWidth(150)
        save_btn.setStyleSheet("""
            QPushButton { background-color:#1A6B3C; color:white; border:none;
                border-radius:5px; font-weight:700; font-size:12px; }
            QPushButton:hover  { background-color:#134E2C; color:white; }
            QPushButton:pressed { background-color:#0D3D22; color:white; }
        """)
        save_btn.clicked.connect(self._save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.setStyleSheet(
            "background-color:#78909C; color:white; border:none;"
            "border-radius:5px; font-weight:600;"
        )
        cancel_btn.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addSpacing(10)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        outer.addWidget(bar)

    def _grp_basic(self) -> QGroupBox:
        g = QGroupBox("Basic Information")
        f = self._form()
        g.setLayout(f)

        self.name_in = QLineEdit()
        f.addRow("Name *:", self.name_in)

        self.age_in = QSpinBox()
        self.age_in.setRange(0, 150)
        self.age_in.setSuffix(" years")
        self.age_in.setSpecialValueText("Not set")
        self.age_in.setFixedWidth(150)
        f.addRow("Age:", self.age_in)

        g_row = QHBoxLayout()
        self.male_rb   = QRadioButton("Male")
        self.female_rb = QRadioButton("Female")
        self.other_rb  = QRadioButton("Other")
        for rb in [self.male_rb, self.female_rb, self.other_rb]:
            g_row.addWidget(rb)
        g_row.addStretch()
        f.addRow("Gender:", g_row)

        self.bp_in = QLineEdit()
        self.bp_in.setPlaceholderText("e.g. 120/80")
        self.bp_in.setFixedWidth(200)
        f.addRow("Blood Pressure:", self.bp_in)

        self.phone_in = QLineEdit()
        self.phone_in.setFixedWidth(240)
        f.addRow("Phone:", self.phone_in)

        self.addr_in = QTextEdit()
        self.addr_in.setFixedHeight(60)
        f.addRow("Address:", self.addr_in)
        return g

    def _grp_medical(self) -> QGroupBox:
        g = QGroupBox("Medical & Constitutional Information")
        f = self._form()
        g.setLayout(f)

        self.complex_cb = QComboBox()
        self.complex_cb.addItems(
            ["", "Fair", "Medium", "Dark", "Olive", "Pale", "Ruddy"]
        )
        self.complex_cb.setEditable(True)
        self.complex_cb.setFixedWidth(220)
        f.addRow("Complexion:", self.complex_cb)

        t_row = QHBoxLayout()
        self.hot_rb     = QRadioButton("HOT")
        self.cold_rb    = QRadioButton("COLD")
        self.therm_none = QRadioButton("Unknown")
        for rb in [self.hot_rb, self.cold_rb, self.therm_none]:
            t_row.addWidget(rb)
        t_row.addStretch()
        f.addRow("Thermal Type:", t_row)

        self.miasm_cb = QComboBox()
        self.miasm_cb.addItems(
            ["", "Psora", "Sycosis", "Syphilis", "Tubercular"]
        )
        self.miasm_cb.setFixedWidth(220)
        self.miasm_cb.setToolTip(
            "Psora: functional/deficiency\nSycosis: excess/overgrowth\n"
            "Syphilis: destruction/ulceration\nTubercular: respiratory/glands"
        )
        f.addRow("Miasm:", self.miasm_cb)

        self.med_hist_in = QTextEdit()
        self.med_hist_in.setFixedHeight(76)
        f.addRow("Medical History:", self.med_hist_in)
        return g

    def _grp_symptoms(self) -> QGroupBox:
        g = QGroupBox("Symptom Conditions")
        f = self._form()
        g.setLayout(f)

        self.mental_in = QTextEdit()
        self.mental_in.setFixedHeight(64)
        f.addRow("Mental Symptoms:", self.mental_in)

        self.body_in = QTextEdit()
        self.body_in.setFixedHeight(64)
        f.addRow("Body Issues:", self.body_in)

        self.modalities_in = QTextEdit()
        self.modalities_in.setFixedHeight(64)
        f.addRow("Modalities:", self.modalities_in)

        self.aggravation_in = QLineEdit()
        self.aggravation_in.setPlaceholderText(
            "e.g. worse midnight, worse cold, worse motion…"
        )
        f.addRow("Aggravation (< ):", self.aggravation_in)

        self.amelioration_in = QLineEdit()
        self.amelioration_in.setPlaceholderText(
            "e.g. better warmth, better lying down, better pressure…"
        )
        f.addRow("Amelioration (> ):", self.amelioration_in)

        return g

    def _populate(self):
        p = self.patient
        self.name_in.setText(p.name or "")
        self.age_in.setValue(p.age or 0)

        if p.gender == "Male":      self.male_rb.setChecked(True)
        elif p.gender == "Female":  self.female_rb.setChecked(True)
        elif p.gender == "Other":   self.other_rb.setChecked(True)
        else:                       self.male_rb.setAutoExclusive(False)

        self.bp_in.setText(p.blood_pressure or "")
        self.phone_in.setText(p.phone or "")
        self.addr_in.setPlainText(p.address or "")

        idx = self.complex_cb.findText(p.complexion or "")
        self.complex_cb.setCurrentIndex(idx if idx >= 0 else 0)

        if p.thermal_type == "HOT":    self.hot_rb.setChecked(True)
        elif p.thermal_type == "COLD": self.cold_rb.setChecked(True)
        else:                          self.therm_none.setChecked(True)

        idx = self.miasm_cb.findText(p.miasm or "")
        self.miasm_cb.setCurrentIndex(idx if idx >= 0 else 0)

        self.med_hist_in.setPlainText(p.medical_history or "")
        self.mental_in.setPlainText(p.mental_symptoms or "")
        self.body_in.setPlainText(p.body_issues or "")
        self.modalities_in.setPlainText(p.modalities or "")
        self.aggravation_in.setText(p.aggravation or "")
        self.amelioration_in.setText(p.amelioration or "")

    def _save(self):
        name = self.name_in.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            return

        gender = (
            "Male"   if self.male_rb.isChecked()   else
            "Female" if self.female_rb.isChecked() else
            "Other"  if self.other_rb.isChecked()  else None
        )
        thermal = (
            "HOT"  if self.hot_rb.isChecked()  else
            "COLD" if self.cold_rb.isChecked() else None
        )

        updated = Patient(
            patient_id      = self.patient.patient_id,
            name            = name,
            gender          = gender,
            address         = self.addr_in.toPlainText().strip() or None,
            phone           = self.phone_in.text().strip() or None,
            age             = self.age_in.value() or None,
            blood_pressure  = self.bp_in.text().strip() or None,
            complexion      = self.complex_cb.currentText().strip() or None,
            thermal_type    = thermal,
            miasm           = self.miasm_cb.currentText().strip() or None,
            medical_history = self.med_hist_in.toPlainText().strip() or None,
            mental_symptoms = self.mental_in.toPlainText().strip() or None,
            body_issues     = self.body_in.toPlainText().strip() or None,
            modalities      = self.modalities_in.toPlainText().strip() or None,
            aggravation     = self.aggravation_in.text().strip() or None,
            amelioration    = self.amelioration_in.text().strip() or None,
        )

        if self.patient_service.update_patient(updated):
            QMessageBox.information(self, "Saved", "Patient updated successfully.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to update patient.")