# -*- coding: utf-8 -*-
"""发票报销归档助手 —— 程序入口。

本地离线运行，数据以 Excel 形式保存在软件同目录的 data/ 文件夹内。
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

# 允许以 `python main.py` 直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import APP_NAME, APP_VERSION, DATA_DIR
from app.excel_store import ExcelStore
from app.ui.main_window import MainWindow


def build_icon() -> QIcon:
    """用代码画一个简单的应用图标，避免依赖外部图片资源。"""
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#2563EB"))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(2, 2, 60, 60, 14, 14)
    p.setPen(QColor("#FFFFFF"))
    f = QFont("Microsoft YaHei UI", 30, QFont.Bold)
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignCenter, "票")
    p.end()
    return QIcon(pix)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setWindowIcon(build_icon())

    # 保证数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        store = ExcelStore()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(
            None, "启动失败",
            f"无法初始化数据文件：\n{exc}\n\n"
            f"请确认软件目录可写，且 data 文件夹未被占用。\n路径：{DATA_DIR}",
        )
        return 1

    win = MainWindow(store)
    win.show()
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "程序异常", traceback.format_exc())
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        sys.exit(1)
