# gui/remedy_finder.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                              QHeaderView, QMessageBox, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt
from services.remedy_service import RemedyService

class RemedyFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.remedy_service = RemedyService()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Symptoms input
        layout.addWidget(QLabel("Enter symptoms (one per line):"))
        self.symptoms_edit = QTextEdit()
        self.symptoms_edit.setPlaceholderText("e.g.\nanxiety morning\nheadache on right side\n< Add more symptoms...")
        layout.addWidget(self.symptoms_edit)

        # Thermal type
        thermal_layout = QHBoxLayout()
        thermal_layout.addWidget(QLabel("Thermal type (optional):"))
        self.thermal_combo = QComboBox()
        self.thermal_combo.addItems(["", "HOT", "COLD"])
        thermal_layout.addWidget(self.thermal_combo)
        thermal_layout.addStretch()
        layout.addLayout(thermal_layout)

        # Number of results
        num_layout = QHBoxLayout()
        num_layout.addWidget(QLabel("Number of results:"))
        self.num_edit = QLineEdit("10")
        self.num_edit.setMaximumWidth(50)
        num_layout.addWidget(self.num_edit)
        num_layout.addStretch()
        layout.addLayout(num_layout)

        # Search button
        self.search_btn = QPushButton("Find Remedies")
        self.search_btn.clicked.connect(self.find_remedies)
        layout.addWidget(self.search_btn)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Remedy", "Abbrev", "Score %", "Match Level"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Legend
        legend = QLabel("Green: High (≥70%)  Yellow: Medium (≥40%)  Red: Low (<40%)")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(legend)

    def find_remedies(self):
        symptoms_text = self.symptoms_edit.toPlainText().strip()
        if not symptoms_text:
            QMessageBox.warning(self, "Input", "Please enter at least one symptom.")
            return

        symptoms = [line.strip() for line in symptoms_text.split('\n') if line.strip()]
        thermal = self.thermal_combo.currentText() or None
        try:
            top_n = int(self.num_edit.text())
        except ValueError:
            top_n = 10

        results = self.remedy_service.match_remedies(symptoms, thermal, top_n)
        if not results:
            QMessageBox.information(self, "No Results", "No matching remedies found.")
            self.table.setRowCount(0)
            return

        self.table.setRowCount(len(results))
        for i, (name, abbr, score, color) in enumerate(results):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(abbr))
            self.table.setItem(i, 2, QTableWidgetItem(f"{score:.1f}"))
            item = QTableWidgetItem(color.capitalize())
            if color == "green":
                item.setBackground(Qt.GlobalColor.green)
            elif color == "yellow":
                item.setBackground(Qt.GlobalColor.yellow)
            elif color == "red":
                item.setBackground(Qt.GlobalColor.red)
            self.table.setItem(i, 3, item)