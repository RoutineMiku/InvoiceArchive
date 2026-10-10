# -*- coding: utf-8 -*-
"""通用界面小组件：卡片容器、PDF 拖拽上传区。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class Card(QFrame):
    """白色圆角卡片容器，带标题与右侧操作区。"""

    def __init__(self, title: str = "", hint: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(16, 14, 16, 14)
        self._outer.setSpacing(10)

        self.header = QHBoxLayout()
        self.header.setSpacing(8)
        if title:
            lb = QLabel(title)
            lb.setObjectName("CardTitle")
            self.header.addWidget(lb)
        if hint:
            hb = QLabel(hint)
            hb.setObjectName("CardHint")
            self.header.addWidget(hb)
        self.header.addStretch(1)
        self._outer.addLayout(self.header)

        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        self._outer.addLayout(self.body)

    def add_widget(self, w: QWidget) -> None:
        self.body.addWidget(w)

    def add_layout(self, layout) -> None:
        self.body.addLayout(layout)


class DropZone(QFrame):
    """发票 PDF 拖拽 / 点击选择区域。"""

    files_dropped = Signal(list)   # List[str]
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("dragging", "false")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignCenter)

        self.icon = QLabel("＋")
        self.icon.setObjectName("DropIcon")
        self.icon.setAlignment(Qt.AlignCenter)

        self.title = QLabel("拖拽发票 PDF 到此处，或点击选择文件")
        self.title.setObjectName("DropTitle")
        self.title.setAlignment(Qt.AlignCenter)

        self.hint = QLabel("支持一次选择 / 拖入多个 PDF 文件，也可直接拖入文件夹")
        self.hint.setObjectName("DropHint")
        self.hint.setAlignment(Qt.AlignCenter)

        lay.addWidget(self.icon)
        lay.addWidget(self.title)
        lay.addWidget(self.hint)

    # ------------------------------------------------------ 拖拽
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_dragging(True)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._set_dragging(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        self._set_dragging(False)
        paths: list[str] = []
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_dir():
                paths.extend(str(f) for f in sorted(p.rglob("*.pdf")))
                paths.extend(str(f) for f in sorted(p.rglob("*.PDF")))
            elif p.suffix.lower() == ".pdf":
                paths.append(str(p))
        # 去重且保持顺序
        seen, uniq = set(), []
        for p in paths:
            key = str(Path(p)).lower()
            if key not in seen:
                seen.add(key)
                uniq.append(p)
        if uniq:
            self.files_dropped.emit(uniq)
        event.acceptProposedAction()

    def _set_dragging(self, flag: bool) -> None:
        self.setProperty("dragging", "true" if flag else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    # ------------------------------------------------------ 点击
    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def pick_files(self, parent: QWidget | None = None) -> list[str]:
        files, _ = QFileDialog.getOpenFileNames(
            parent or self, "选择发票 PDF 文件", "", "PDF 文件 (*.pdf);;所有文件 (*.*)"
        )
        return files
