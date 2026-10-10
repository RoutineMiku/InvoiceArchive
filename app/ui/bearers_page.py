# -*- coding: utf-8 -*-
"""费用承担人管理页：增、删、改、查。"""
from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..config import BEARER_COLUMNS, BEARER_WIDTHS
from ..excel_store import ExcelError
from .bearer_dialog import BearerDialog
from .theme import DANGER, SUCCESS, TEXT_MUTED
from .widgets import Card


def open_in_explorer(path) -> None:
    """在资源管理器中定位文件 / 打开文件夹。"""
    path = str(path)
    try:
        if sys.platform.startswith("win"):
            if os.path.isfile(path):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            else:
                os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R" if os.path.isfile(path) else path])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path) or path])
    except Exception:  # noqa: BLE001
        pass


class BearersPage(QWidget):
    data_changed = Signal()

    def __init__(self, store, parent: QWidget | None = None):
        super().__init__(parent)
        self.store = store
        self._rows: list[dict] = []
        self._build_ui()
        self.reload()

    # ------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        card = Card("费用承担人名单", "数据保存在 data/费用承担人.xlsx")

        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.ed_search = QLineEdit()
        self.ed_search.setPlaceholderText("搜索姓名 / 部门 / 备注…")
        self.ed_search.setClearButtonEnabled(True)
        self.ed_search.textChanged.connect(self.reload)
        bar.addWidget(self.ed_search, 1)

        self.btn_add = QPushButton("新增")
        self.btn_add.setObjectName("Primary")
        self.btn_add.clicked.connect(self.add_item)
        self.btn_edit = QPushButton("编辑")
        self.btn_edit.clicked.connect(self.edit_item)
        self.btn_toggle = QPushButton("启用 / 停用")
        self.btn_toggle.clicked.connect(self.toggle_item)
        self.btn_del = QPushButton("删除")
        self.btn_del.setObjectName("Danger")
        self.btn_del.clicked.connect(self.delete_item)
        self.btn_open = QPushButton("打开 Excel")
        self.btn_open.setObjectName("Ghost")
        self.btn_open.clicked.connect(lambda: open_in_explorer(self.store.bearer_file))
        for b in (self.btn_add, self.btn_edit, self.btn_toggle, self.btn_del, self.btn_open):
            bar.addWidget(b)
        card.add_layout(bar)

        self.table = QTableWidget(0, len(BEARER_COLUMNS))
        self.table.setHorizontalHeaderLabels(BEARER_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_item)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        for i, w in enumerate(BEARER_WIDTHS):
            self.table.setColumnWidth(i, w * 10)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        card.add_widget(self.table)

        self.lb_stat = QLabel("")
        self.lb_stat.setObjectName("Muted")
        card.add_widget(self.lb_stat)

        root.addWidget(card, 1)

    # ------------------------------------------------------------ 数据
    def reload(self) -> None:
        keyword = self.ed_search.text().strip().lower()
        try:
            all_rows = self.store.list_bearers()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "读取失败", str(exc))
            return
        if keyword:
            self._rows = [
                r for r in all_rows
                if keyword in " ".join([
                    r.get("姓名", ""), r.get("部门", ""), r.get("备注", "")
                ]).lower()
            ]
        else:
            self._rows = all_rows

        self.table.setRowCount(0)
        for rec in self._rows:
            self._append(rec)
        active = sum(1 for r in all_rows if r.get("状态") != "停用")
        self.lb_stat.setText(
            f"共 {len(all_rows)} 位费用承担人，其中启用 {active} 位"
            + (f"；当前筛选出 {len(self._rows)} 条" if keyword else "")
        )

    def _append(self, rec: dict) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, col in enumerate(BEARER_COLUMNS):
            item = QTableWidgetItem(str(rec.get(col, "")))
            item.setToolTip(str(rec.get(col, "")))
            if col == "状态":
                item.setForeground(QBrush(QColor(
                    TEXT_MUTED if rec.get("状态") == "停用" else SUCCESS)))
                item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, c, item)

    def _selected_records(self) -> list[dict]:
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        return [self._rows[r] for r in rows if 0 <= r < len(self._rows)]

    # ------------------------------------------------------------ 操作
    def add_item(self) -> None:
        dlg = BearerDialog(self, "新增费用承担人")
        if dlg.exec() != BearerDialog.Accepted:
            return
        v = dlg.values()
        try:
            self.store.add_bearer(v["姓名"], v["部门"], v["状态"], v["备注"])
        except ExcelError as exc:
            QMessageBox.warning(self, "新增失败", str(exc))
            return
        self.reload()
        self.data_changed.emit()

    def edit_item(self) -> None:
        recs = self._selected_records()
        if len(recs) != 1:
            QMessageBox.information(self, "提示", "请先选中一行后再编辑。")
            return
        rec = recs[0]
        dlg = BearerDialog(self, f"编辑费用承担人 - {rec['姓名']}", rec)
        if dlg.exec() != BearerDialog.Accepted:
            return
        v = dlg.values()
        try:
            self.store.update_bearer(rec["_row"], v["姓名"], v["部门"],
                                     v["状态"], v["备注"])
        except ExcelError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self.reload()
        self.data_changed.emit()

    def toggle_item(self) -> None:
        recs = self._selected_records()
        if not recs:
            QMessageBox.information(self, "提示", "请先选中要启用/停用的记录。")
            return
        for rec in recs:
            new_status = "停用" if rec.get("状态") != "停用" else "启用"
            try:
                self.store.update_bearer(rec["_row"], rec["姓名"], rec.get("部门", ""),
                                         new_status, rec.get("备注", ""))
            except ExcelError as exc:
                QMessageBox.warning(self, "操作失败", str(exc))
                break
        self.reload()
        self.data_changed.emit()

    def delete_item(self) -> None:
        recs = self._selected_records()
        if not recs:
            QMessageBox.information(self, "提示", "请先选中要删除的记录。")
            return
        names = "、".join(r["姓名"] for r in recs[:6]) + ("…" if len(recs) > 6 else "")
        ans = QMessageBox.question(
            self, "确认删除",
            f"确定删除以下 {len(recs)} 位费用承担人吗？\n{names}\n\n"
            "（已归档的发票记录不会被删除，只是不再出现在下拉列表中）",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        try:
            for rec in sorted(recs, key=lambda r: r["_row"], reverse=True):
                self.store.delete_bearer(rec["_row"])
        except ExcelError as exc:
            QMessageBox.warning(self, "删除失败", str(exc))
        self.reload()
        self.data_changed.emit()
