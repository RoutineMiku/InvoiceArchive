# -*- coding: utf-8 -*-
"""生成应用图标 app.ico（仅测试/构建用）。"""
import sys
from pathlib import Path

os_off = __import__("os")
os_off.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

qapp = QApplication.instance() or QApplication([])

pix = QPixmap(256, 256)
pix.fill(Qt.transparent)
p = QPainter(pix)
p.setRenderHint(QPainter.Antialiasing)
# 底板
grad = p.brush()
p.setBrush(QColor("#2563EB"))
p.setPen(Qt.NoPen)
p.drawRoundedRect(8, 8, 240, 240, 48, 48)
# 白色票据
p.setBrush(QColor("#FFFFFF"))
p.drawRoundedRect(64, 56, 128, 150, 12, 12)
p.setPen(QColor("#2563EB"))
p.setFont(QFont("Microsoft YaHei UI", 56, QFont.Bold))
p.drawText(pix.rect().adjusted(0, -14, 0, -14), Qt.AlignCenter, "票")
# 底部三条横线
p.setBrush(QColor("#BFDBFE"))
p.setPen(Qt.NoPen)
for i, w in enumerate((96, 72, 48)):
    p.drawRoundedRect(128 - w // 2, 172 + i * 14, w, 7, 3, 3)
p.end()

out = ROOT / "app.ico"
if not pix.save(str(out), "ICO"):
    print("ICO 保存失败")
    sys.exit(1)
print("图标已生成：", out, out.stat().st_size, "bytes")
