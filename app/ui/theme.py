# -*- coding: utf-8 -*-
"""界面主题（浅色）。集中管理配色与 QSS，方便统一调整。"""
from __future__ import annotations

# ---------------------------------------------------------------- 配色
PRIMARY = "#2563EB"
PRIMARY_DARK = "#1D4ED8"
PRIMARY_LIGHT = "#EFF4FF"
SUCCESS = "#16A34A"
SUCCESS_LIGHT = "#ECFDF3"
WARNING = "#D97706"
WARNING_LIGHT = "#FFF7ED"
DANGER = "#DC2626"
DANGER_LIGHT = "#FEF2F2"

BG = "#F3F5F9"
CARD = "#FFFFFF"
BORDER = "#E2E7EF"
TEXT = "#1F2937"
TEXT_SUB = "#6B7280"
TEXT_MUTED = "#9CA3AF"

FONT_FAMILY = '"Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", sans-serif'

QSS = f"""
* {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: {TEXT};
}}

QWidget#Root {{
    background: {BG};
}}

/* ---------------- 卡片 ---------------- */
QFrame#Card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QLabel#CardTitle {{
    font-size: 14px;
    font-weight: 600;
    color: {TEXT};
}}
QLabel#CardHint {{
    color: {TEXT_SUB};
    font-size: 12px;
}}
QLabel#PageTitle {{
    font-size: 18px;
    font-weight: 600;
}}
QLabel#Muted {{ color: {TEXT_SUB}; }}
QLabel#Danger {{ color: {DANGER}; }}
QLabel#Success {{ color: {SUCCESS}; }}
QLabel#StatValue {{
    font-size: 19px;
    font-weight: 700;
    color: {PRIMARY};
}}
QLabel#StatLabel {{ color: {TEXT_SUB}; font-size: 12px; }}

/* ---------------- 顶部标题栏 ---------------- */
QWidget#Header {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1E3A8A, stop:0.5 #2563EB, stop:1 #3B82F6);
}}
QLabel#AppTitle {{
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 600;
}}
QLabel#AppSubtitle {{
    color: #DBEAFE;
    font-size: 12px;
}}

/* ---------------- 按钮 ---------------- */
QPushButton {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 20px;
    color: {TEXT};
}}
QPushButton:hover {{ background: #F7F9FC; border-color: #C9D3E3; }}
QPushButton:pressed {{ background: #EDF1F7; }}
QPushButton:disabled {{ color: {TEXT_MUTED}; background: #F5F6F8; border-color: #E8EBF0; }}

QPushButton#Primary {{
    background: {PRIMARY};
    border: 1px solid {PRIMARY};
    color: #FFFFFF;
    font-weight: 600;
    padding: 8px 20px;
}}
QPushButton#Primary:hover {{ background: {PRIMARY_DARK}; border-color: {PRIMARY_DARK}; }}
QPushButton#Primary:pressed {{ background: #1E40AF; }}
QPushButton#Primary:disabled {{ background: #A9C2F2; border-color: #A9C2F2; color: #FFFFFF; }}

QPushButton#Ghost {{
    background: transparent;
    border: 1px solid #C7D6F5;
    color: {PRIMARY};
}}
QPushButton#Ghost:hover {{ background: {PRIMARY_LIGHT}; }}

QPushButton#Danger {{
    background: transparent;
    border: 1px solid #F3C0C0;
    color: {DANGER};
}}
QPushButton#Danger:hover {{ background: {DANGER_LIGHT}; }}

QPushButton#HeaderBtn {{
    background: rgba(255,255,255,0.16);
    border: 1px solid rgba(255,255,255,0.35);
    color: #FFFFFF;
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton#HeaderBtn:hover {{ background: rgba(255,255,255,0.28); }}

/* ---------------- 输入控件 ---------------- */
QLineEdit, QComboBox, QDateEdit, QPlainTextEdit, QTextEdit, QSpinBox {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 9px;
    min-height: 20px;
    selection-background-color: {PRIMARY};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus {{
    border: 1px solid {PRIMARY};
}}
QLineEdit:disabled, QComboBox:disabled {{
    background: #F5F6F8; color: {TEXT_MUTED};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_SUB};
    width: 0; height: 0; margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {CARD};
    border: 1px solid {BORDER};
    selection-background-color: {PRIMARY_LIGHT};
    selection-color: {TEXT};
    outline: none;
}}

/* ---------------- 表格 ---------------- */
QTableWidget, QTableView {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: #EDF1F7;
    selection-background-color: {PRIMARY_LIGHT};
    selection-color: {TEXT};
    alternate-background-color: #FAFBFD;
}}
QTableWidget::item, QTableView::item {{ padding: 4px 6px; }}
QHeaderView::section {{
    background: #F7F9FC;
    color: #374151;
    font-weight: 600;
    border: none;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    padding: 7px 8px;
}}
QHeaderView::section:last {{ border-right: none; }}
QTableCornerButton::section {{ background: #F7F9FC; border: none; }}

/* ---------------- 列表 ---------------- */
QListWidget {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    outline: none;
}}
QListWidget::item {{ padding: 6px 8px; border-bottom: 1px solid #F1F4F9; }}
QListWidget::item:selected {{ background: {PRIMARY_LIGHT}; color: {TEXT}; }}

/* ---------------- 选项卡 ---------------- */
QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{
    background: transparent;
    padding: 9px 22px;
    margin-right: 4px;
    border: none;
    border-bottom: 2px solid transparent;
    color: {TEXT_SUB};
    font-size: 13px;
}}
QTabBar::tab:hover {{ color: {PRIMARY}; }}
QTabBar::tab:selected {{
    color: {PRIMARY};
    font-weight: 600;
    border-bottom: 2px solid {PRIMARY};
}}

/* ---------------- 拖拽区 ---------------- */
QFrame#DropZone {{
    background: #FBFCFE;
    border: 2px dashed #BFCFE8;
    border-radius: 10px;
}}
QFrame#DropZone[dragging="true"] {{
    background: {PRIMARY_LIGHT};
    border: 2px dashed {PRIMARY};
}}
QLabel#DropIcon {{ font-size: 30px; color: {PRIMARY}; }}
QLabel#DropTitle {{ font-size: 14px; font-weight: 600; }}
QLabel#DropHint {{ color: {TEXT_SUB}; font-size: 12px; }}

/* ---------------- 进度条 ---------------- */
QProgressBar {{
    background: #E8EDF6;
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 5px; }}

/* ---------------- 滚动条 ---------------- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #CBD5E1; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #A9B7C9; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #CBD5E1; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------------- 其它 ---------------- */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
    background: {CARD};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: {TEXT_SUB};
}}
QStatusBar {{ background: transparent; color: {TEXT_SUB}; }}
QToolTip {{
    background: #1F2937; color: #FFFFFF;
    border: none; padding: 5px 8px; border-radius: 4px;
}}
QCheckBox::indicator, QRadioButton::indicator {{ width: 15px; height: 15px; }}
QMessageBox {{ background: {CARD}; }}
"""
