# gui/theme.py
"""
Central theme for Homeopathic Assistant.
Medical green / white — clean, clinical, professional.
"""

# Brand colours
CLR_PRIMARY       = "#1A6B3C"   # deep medical green
CLR_PRIMARY_DARK  = "#134E2C"   # hover / pressed
CLR_PRIMARY_LIGHT = "#E8F5EE"   # tinted backgrounds
CLR_ACCENT        = "#27AE60"   # bright green accent
CLR_DANGER        = "#C0392B"   # delete / error
CLR_DANGER_DARK   = "#922B21"
CLR_WARNING       = "#D4AC0D"   # yellow actions
CLR_PURPLE        = "#7D3C98"   # history / secondary actions
CLR_BORDER        = "#B2DFCC"   # subtle green border
CLR_TEXT          = "#1C2A1E"   # near-black text
CLR_MUTED         = "#6B8F72"   # secondary text
CLR_WHITE         = "#FFFFFF"
CLR_BG            = "#F4FAF6"   # page background
CLR_HEADER_BG     = "#1A6B3C"


MAIN_STYLESHEET = f"""
/* ── Global ── */
QWidget {{
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: {CLR_TEXT};
    background-color: {CLR_BG};
}}

QMainWindow {{
    background-color: {CLR_BG};
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {CLR_BORDER};
    background-color: {CLR_WHITE};
    border-radius: 0 6px 6px 6px;
}}
QTabBar::tab {{
    background-color: #D0EDD9;
    color: {CLR_PRIMARY_DARK};
    padding: 10px 22px;
    margin-right: 3px;
    border-radius: 6px 6px 0 0;
    font-weight: 600;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background-color: {CLR_PRIMARY};
    color: {CLR_WHITE};
}}
QTabBar::tab:hover:!selected {{
    background-color: #B2DFCC;
}}

/* ── GroupBox ── */
QGroupBox {{
    font-weight: 700;
    font-size: 12px;
    border: 1.5px solid {CLR_BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 8px;
    background-color: {CLR_WHITE};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {CLR_PRIMARY};
    background-color: {CLR_WHITE};
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    border: 1.5px solid {CLR_BORDER};
    border-radius: 5px;
    padding: 5px 8px;
    background-color: {CLR_WHITE};
    selection-background-color: {CLR_ACCENT};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {CLR_ACCENT};
    background-color: {CLR_PRIMARY_LIGHT};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 6px;
}}

/* ── Buttons (default — green) ── */
QPushButton {{
    background-color: {CLR_PRIMARY};
    color: {CLR_WHITE};
    border: none;
    padding: 7px 16px;
    border-radius: 5px;
    font-weight: 600;
    font-size: 12px;
    min-height: 28px;
}}
QPushButton:hover   {{ background-color: {CLR_PRIMARY_DARK}; color: {CLR_WHITE}; }}
QPushButton:pressed {{ background-color: #0D3D22;            color: {CLR_WHITE}; }}
QPushButton:disabled {{ background-color: #A8C8B2;           color: #E0EDE4; }}

/* Ensure buttons inside white frames/panels stay green */
QFrame QPushButton, QDialog QPushButton, QScrollArea QPushButton {{
    background-color: {CLR_PRIMARY};
    color: {CLR_WHITE};
}}
QFrame QPushButton:hover, QDialog QPushButton:hover {{
    background-color: {CLR_PRIMARY_DARK};
    color: {CLR_WHITE};
}}

/* ── Table ── */
QTableWidget {{
    border: 1px solid {CLR_BORDER};
    gridline-color: #D8EEE0;
    background-color: {CLR_WHITE};
    alternate-background-color: {CLR_PRIMARY_LIGHT};
    selection-background-color: #C1E8D0;
    selection-color: {CLR_TEXT};
}}
QTableWidget::item {{ padding: 4px 8px; }}
QHeaderView::section {{
    background-color: {CLR_PRIMARY};
    color: {CLR_WHITE};
    padding: 7px 8px;
    border: none;
    font-weight: 700;
    font-size: 12px;
}}

/* ── ScrollBar ── */
QScrollBar:vertical {{
    background: #E8F5EE;
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {CLR_ACCENT};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Radio buttons ── */
QRadioButton {{ spacing: 6px; background: transparent; }}
QRadioButton::indicator {{
    width: 14px; height: 14px;
    border: 2px solid {CLR_ACCENT};
    border-radius: 7px;
}}
QRadioButton::indicator:checked {{
    background-color: {CLR_ACCENT};
    border-color: {CLR_PRIMARY};
}}

/* ── Dialog ── */
QDialog {{
    background-color: {CLR_BG};
}}

/* ── MessageBox ── */
QMessageBox {{
    background-color: {CLR_WHITE};
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {CLR_BORDER};
    height: 2px;
}}

/* ── Tooltip ── */
QToolTip {{
    background-color: {CLR_PRIMARY};
    color: white;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
}}
"""

# Reusable button style overrides — explicit color+border on every btn to override inheritance
_B = "border:none; border-radius:5px; padding:6px 12px; font-weight:600; font-size:12px; color:white;"
BTN_DANGER   = f"background-color:{CLR_DANGER};  {_B}"
BTN_EDIT     = f"background-color:{CLR_ACCENT};  {_B}"
BTN_HISTORY  = f"background-color:{CLR_PURPLE};  {_B}"
BTN_CANCEL   = f"background-color:#78909C;       {_B}"
BTN_WARN     = f"background-color:{CLR_WARNING}; {_B}"
BTN_REMEDIES = f"background-color:#1565C0;       {_B}"  # deep blue for remedies