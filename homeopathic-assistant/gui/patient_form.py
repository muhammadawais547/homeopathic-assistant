# gui/patient_form.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QRadioButton, QPushButton,
    QMessageBox, QGroupBox, QSpinBox, QComboBox,
    QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from models.patient import Patient
from services.patient_service import PatientService
from gui.theme import CLR_PRIMARY, CLR_PRIMARY_LIGHT, CLR_WHITE, CLR_BORDER


class PatientForm(QWidget):
    patient_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.patient_service = PatientService()
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("  ➕  Register New Patient")
        title.setFixedHeight(38)
        title.setStyleSheet(
            f"background:{CLR_PRIMARY_LIGHT}; color:{CLR_PRIMARY};"
            "font-size:13px; font-weight:700;"
            f"border-bottom:1px solid {CLR_BORDER}; padding-left:8px;"
        )
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 18, 28, 18)
        layout.setSpacing(16)
        layout.addWidget(self._grp_basic())
        layout.addWidget(self._grp_medical())
        layout.addWidget(self._grp_symptoms())
        layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)

        bar = QFrame()
        bar.setFixedHeight(58)
        bar.setStyleSheet(
            f"background:{CLR_WHITE}; border-top:1px solid {CLR_BORDER};"
        )
        btn_row = QHBoxLayout(bar)
        btn_row.setContentsMargins(28, 0, 28, 0)

        self.save_btn = QPushButton("💾  Save Patient")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setMinimumWidth(160)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color:#1A6B3C; color:white; border:none;
                border-radius:5px; font-weight:700; font-size:12px; }
            QPushButton:hover  { background-color:#134E2C; color:white; }
            QPushButton:pressed { background-color:#0D3D22; color:white; }
        """)
        self.save_btn.clicked.connect(self._save)

        self.clear_btn = QPushButton("🗑  Clear Form")
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.setMinimumWidth(120)
        self.clear_btn.setStyleSheet(
            "background-color:#78909C; color:white; border:none;"
            "border-radius:5px; font-weight:600; font-size:12px;"
        )
        self.clear_btn.clicked.connect(self._clear)

        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        btn_row.addSpacing(10)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        outer.addWidget(bar)
        self.name_input.setFocus()

    def _form(self):
        f = QFormLayout()
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        f.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f.setHorizontalSpacing(18)
        f.setVerticalSpacing(10)
        return f

    def _grp_basic(self) -> QGroupBox:
        g = QGroupBox("Basic Information")
        f = self._form()
        g.setLayout(f)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full name")
        f.addRow("Name *:", self.name_input)

        self.age_input = QSpinBox()
        self.age_input.setRange(0, 150)
        self.age_input.setSuffix(" years")
        self.age_input.setSpecialValueText("Not set")
        self.age_input.setFixedWidth(160)
        f.addRow("Age:", self.age_input)

        g_row = QHBoxLayout()
        self.male_rb   = QRadioButton("Male")
        self.female_rb = QRadioButton("Female")
        self.other_rb  = QRadioButton("Other")
        for rb in [self.male_rb, self.female_rb, self.other_rb]:
            g_row.addWidget(rb)
        g_row.addStretch()
        f.addRow("Gender:", g_row)

        self.bp_input = QLineEdit()
        self.bp_input.setPlaceholderText("e.g. 120/80")
        self.bp_input.setFixedWidth(200)
        f.addRow("Blood Pressure:", self.bp_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        self.phone_input.setFixedWidth(260)
        f.addRow("Phone:", self.phone_input)

        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Street, city, postal code…")
        self.address_input.setFixedHeight(64)
        f.addRow("Address:", self.address_input)
        return g

    def _grp_medical(self) -> QGroupBox:
        g = QGroupBox("Medical & Constitutional Information")
        f = self._form()
        g.setLayout(f)

        self.complexion_cb = QComboBox()
        self.complexion_cb.addItems(
            ["", "Fair", "Medium", "Dark", "Olive", "Pale", "Ruddy"]
        )
        self.complexion_cb.setEditable(True)
        self.complexion_cb.setFixedWidth(220)
        f.addRow("Complexion:", self.complexion_cb)

        t_row = QHBoxLayout()
        self.hot_rb     = QRadioButton("HOT")
        self.cold_rb    = QRadioButton("COLD")
        self.therm_none = QRadioButton("Unknown")
        self.therm_none.setChecked(True)
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
            "Psora: functional/deficiency disorders, skin, anxiety\n"
            "Sycosis: excess/overgrowth, warts, pelvic disorders\n"
            "Syphilis: destruction, ulceration, bone pains\n"
            "Tubercular: respiratory, glands, emaciation"
        )
        f.addRow("Miasm:", self.miasm_cb)

        hint = QLabel(
            "ℹ  Miasm is the chronic disease background (Hahnemann). "
            "Used to filter remedy selection constitutionally."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "color:#6B8F72; font-size:10px; font-style:italic; background:transparent;"
        )
        f.addRow("", hint)

        self.med_hist_input = QTextEdit()
        self.med_hist_input.setPlaceholderText(
            "Past illnesses, surgeries, chronic conditions…"
        )
        self.med_hist_input.setFixedHeight(80)
        f.addRow("Medical History:", self.med_hist_input)
        return g

    def _grp_symptoms(self) -> QGroupBox:
        g = QGroupBox("Symptom Conditions")
        f = self._form()
        g.setLayout(f)

        # Mental Symptoms
        self.mental_input = QTextEdit()
        self.mental_input.setPlaceholderText(
            "e.g. anxiety, fear of death, restlessness, sadness…"
        )
        self.mental_input.setFixedHeight(68)
        f.addRow("Mental Symptoms:", self.mental_input)

        # Body Issues
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText(
            "e.g. headache, joint pain, burning in stomach, skin rash…"
        )
        self.body_input.setFixedHeight(68)
        f.addRow("Body Issues:", self.body_input)

        # Modalities
        self.modalities_input = QTextEdit()
        self.modalities_input.setPlaceholderText(
            "e.g. worse cold, worse night, better warmth, better rest…"
        )
        self.modalities_input.setFixedHeight(68)
        f.addRow("Modalities:", self.modalities_input)

        # Aggravation (replaces Pain Time)
        self.aggravation_input = QLineEdit()
        self.aggravation_input.setPlaceholderText(
            "e.g. worse after midnight, worse cold drinks, worse motion…"
        )
        f.addRow("Aggravation (< ):", self.aggravation_input)

        # Amelioration — new field
        self.amelioration_input = QLineEdit()
        self.amelioration_input.setPlaceholderText(
            "e.g. better warm drinks, better lying down, better pressure…"
        )
        f.addRow("Amelioration (> ):", self.amelioration_input)

        return g

    # ── Save ───────────────────────────────────────────────────────────
    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Patient name is required.")
            self.name_input.setFocus()
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

        patient = Patient(
            patient_id      = Patient.generate_id(),
            name            = name,
            gender          = gender,
            address         = self.address_input.toPlainText().strip() or None,
            phone           = self.phone_input.text().strip() or None,
            age             = self.age_input.value() or None,
            blood_pressure  = self.bp_input.text().strip() or None,
            complexion      = self.complexion_cb.currentText().strip() or None,
            thermal_type    = thermal,
            miasm           = self.miasm_cb.currentText().strip() or None,
            medical_history = self.med_hist_input.toPlainText().strip() or None,
            mental_symptoms = self.mental_input.toPlainText().strip() or None,
            body_issues     = self.body_input.toPlainText().strip() or None,
            modalities      = self.modalities_input.toPlainText().strip() or None,
            aggravation     = self.aggravation_input.text().strip() or None,
            amelioration    = self.amelioration_input.text().strip() or None,
        )

        if self.patient_service.add_patient(patient):
            QMessageBox.information(
                self, "Success",
                f"Patient <b>{name}</b> registered successfully!"
            )
            self._clear()
            self.patient_added.emit()
        else:
            QMessageBox.critical(
                self, "Error",
                "Failed to save patient. Check the console for details."
            )

    # ── Clear ──────────────────────────────────────────────────────────
    def _clear(self):
        self.name_input.clear()
        self.age_input.setValue(0)
        for rb in [self.male_rb, self.female_rb, self.other_rb]:
            rb.setAutoExclusive(False)
            rb.setChecked(False)
            rb.setAutoExclusive(True)
        self.bp_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
        self.complexion_cb.setCurrentIndex(0)
        self.therm_none.setChecked(True)
        self.miasm_cb.setCurrentIndex(0)
        self.med_hist_input.clear()
        self.mental_input.clear()
        self.body_input.clear()
        self.modalities_input.clear()
        self.aggravation_input.clear()
        self.amelioration_input.clear()
        self.name_input.setFocus()