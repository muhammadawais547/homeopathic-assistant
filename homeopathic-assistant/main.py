# main.py
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow


def main():
    print("=" * 40)
    print("   Homeopathic Assistant")
    print("=" * 40)
    app = QApplication(sys.argv)
    app.setApplicationName("Homeopathic Assistant")
    app.setOrganizationName("HoemoeoClinic")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()