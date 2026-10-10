# -*- coding: utf-8 -*-
"""发票归档页：上传 PDF → 选择费用承担人 → 自动识别并写入 Excel。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..config import (
    COL_AMOUNT,
    COL_BEARER,
    COL_EXPENSE,
    COL_INV_DATE,
    COL_INV_NO,
    COL_SELLER,
    DEFAULT_EXPENSE_TYPES,
    TIME_FMT,
)
from ..excel_store import ExcelError
from ..worker import ParseWorker
from .theme import DANGER, SUCCESS, TEXT_SUB, WARNING
from .widgets import Card, DropZone

# 本次识别结果表的列（前两列为展示用，其余与 Excel 列同名以便回写）
SESSION_COLUMNS = ["识别状态", "源文件名", COL_INV_NO, COL_INV_DATE,
                   COL_SELLER, COL_BEARER, COL_EXPENSE, COL_AMOUNT]
SESSION_WIDTHS = [170, 200, 180, 100, 240, 100, 100, 90]
FIRST_EDITABLE_COL = 2


class ArchivePage(QWidget):
    """主页面。"""

    goto_bearers = Signal()      # 请求跳转到「费用承担人」页
    data_changed = Signal()      # 归档数据发生变化

    def __init__(self, store, parent: QWidget | None = None):
        super().__init__(parent)
        self.store = store
        self.pending_files: list[str] = []
        self._worker: ParseWorker | None = None
        self._row_map: dict[int, int] = {}      # 表格行 -> Excel 行号
        self._session_rows: list[int] = []      # 本次写入的 Excel 行号（可撤销）
        self._loading = False

        self._build_ui()
        self.reload_bearers()

    # ============================================================ 界面搭建
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(self._build_upload_card(), 3)
        top.addWidget(self._build_option_card(), 2)
        root.addLayout(top)

        root.addWidget(self._build_result_card(), 1)

    # ---------------------------------------------------------- 上传卡片
    def _build_upload_card(self) -> Card:
        card = Card("① 上传发票 PDF", "支持批量，文件不会离开本机")
        self.drop_zone = DropZone()
        self.drop_zone.clicked.connect(self.choose_files)
        self.drop_zone.files_dropped.connect(self.add_files)
        card.add_widget(self.drop_zone)

        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.lb_count = QLabel("待处理文件：0 个")
        self.lb_count.setObjectName("Muted")
        bar.addWidget(self.lb_count)
        bar.addStretch(1)

        self.btn_add = QPushButton("选择文件")
        self.btn_add.clicked.connect(self.choose_files)
        self.btn_remove = QPushButton("移除选中")
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.clicked.connect(self.clear_files)
        for b in (self.btn_add, self.btn_remove, self.btn_clear):
            bar.addWidget(b)
        card.add_layout(bar)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setAlternatingRowColors(True)
        card.add_widget(self.file_list)
        return card

    # ---------------------------------------------------------- 参数卡片
    def _build_option_card(self) -> Card:
        card = Card("② 选择费用承担人", "归档前必须指定")

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        lb1 = QLabel("费用承担人")
        lb1.setFixedWidth(72)
        self.cmb_bearer = QComboBox()
        self.cmb_bearer.setMinimumWidth(150)
        self.btn_manage = QPushButton("管理")
        self.btn_manage.setObjectName("Ghost")
        self.btn_manage.clicked.connect(self.goto_bearers.emit)
        row1.addWidget(lb1)
        row1.addWidget(self.cmb_bearer, 1)
        row1.addWidget(self.btn_manage)
        card.add_layout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        lb2 = QLabel("费用类型")
        lb2.setFixedWidth(72)
        self.cmb_expense = QComboBox()
        self.cmb_expense.setEditable(True)
        self.cmb_expense.addItems(DEFAULT_EXPENSE_TYPES)
        row2.addWidget(lb2)
        row2.addWidget(self.cmb_expense, 1)
        card.add_layout(row2)

        tip = QLabel("提示：费用类型与支付时间、备注等列，归档后可在「归档记录」页随时修改。")
        tip.setObjectName("Muted")
        tip.setWordWrap(True)
        card.add_widget(tip)

        card.body.addStretch(1)

        self.btn_start = QPushButton("③ 开始识别并归档")
        self.btn_start.setObjectName("Primary")
        self.btn_start.setMinimumHeight(38)
        self.btn_start.clicked.connect(self.start_parse)
        card.add_widget(self.btn_start)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        card.add_widget(self.progress)

        self.lb_status = QLabel("等待上传发票…")
        self.lb_status.setObjectName("Muted")
        self.lb_status.setWordWrap(True)
        card.add_widget(self.lb_status)

        self.btn_undo = QPushButton("撤销本次归档")
        self.btn_undo.setObjectName("Danger")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo_session)
        card.add_widget(self.btn_undo)
        return card

    # ---------------------------------------------------------- 结果卡片
    def _build_result_card(self) -> Card:
        card = Card("本次识别结果", "表格内可直接修改，修改会同步保存到 Excel")

        bar = QHBoxLayout()
        bar.addStretch(1)
        self.lb_result = QLabel("暂无识别记录")
        self.lb_result.setObjectName("Muted")
        bar.addWidget(self.lb_result)
        btn_clear_tbl = QPushButton("清空结果表")
        btn_clear_tbl.clicked.connect(self.clear_results)
        bar.addWidget(btn_clear_tbl)
        card.add_layout(bar)

        self.table = QTableWidget(0, len(SESSION_COLUMNS))
        self.table.setHorizontalHeaderLabels(SESSION_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        for i, w in enumerate(SESSION_WIDTHS):
            self.table.setColumnWidth(i, w)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.itemChanged.connect(self._on_item_changed)
        card.add_widget(self.table)
        return card

    # ============================================================ 文件管理
    def choose_files(self) -> None:
        files = self.drop_zone.pick_files(self)
        if files:
            self.add_files(files)

    def add_files(self, files: list[str]) -> None:
        existing = {str(Path(f)).lower() for f in self.pending_files}
        added = 0
        for f in files:
            key = str(Path(f)).lower()
            if key in existing:
                continue
            existing.add(key)
            self.pending_files.append(f)
            item = QListWidgetItem(f"{Path(f).name}     —     {f}")
            item.setToolTip(f)
            self.file_list.addItem(item)
            added += 1
        self._refresh_count()
        if added:
            self.lb_status.setText(f"已添加 {added} 个文件，请选择费用承担人后点击「开始识别并归档」。")

    def remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.file_list.selectedIndexes()}, reverse=True)
        for r in rows:
            self.file_list.takeItem(r)
            if 0 <= r < len(self.pending_files):
                self.pending_files.pop(r)
        self._refresh_count()

    def clear_files(self) -> None:
        self.file_list.clear()
        self.pending_files.clear()
        self._refresh_count()

    def _refresh_count(self) -> None:
        n = len(self.pending_files)
        total_mb = 0.0
        for f in self.pending_files:
            try:
                total_mb += Path(f).stat().st_size / 1024 / 1024
            except OSError:
                pass
        self.lb_count.setText(f"待处理文件：{n} 个（约 {total_mb:.1f} MB）")
        self.btn_remove.setEnabled(n > 0)
        self.btn_clear.setEnabled(n > 0)

    # ============================================================ 承担人
    def reload_bearers(self, keep: str | None = None) -> None:
        keep = keep if keep is not None else self.cmb_bearer.currentText()
        self.cmb_bearer.blockSignals(True)
        self.cmb_bearer.clear()
        names = self.store.bearer_names(active_only=True)
        if names:
            self.cmb_bearer.addItems(names)
            if keep in names:
                self.cmb_bearer.setCurrentText(keep)
            self.cmb_bearer.setEnabled(True)
        else:
            self.cmb_bearer.addItem("（暂无费用承担人，请先添加）")
            self.cmb_bearer.setEnabled(False)
        self.cmb_bearer.blockSignals(False)

    # ============================================================ 识别主流程
    def start_parse(self) -> None:
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "正在识别中，请稍候…")
            return
        if not self.pending_files:
            QMessageBox.warning(self, "提示", "请先上传至少一个发票 PDF 文件。")
            return
        bearer = self.cmb_bearer.currentText().strip()
        if not self.cmb_bearer.isEnabled() or not bearer or bearer.startswith("（"):
            QMessageBox.warning(self, "提示", "请先在「费用承担人」页添加并选择费用承担人。")
            return

        self._session_rows.clear()
        self.btn_start.setEnabled(False)
        self.btn_undo.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self.pending_files))
        self.progress.setValue(0)
        self.lb_status.setText("开始识别…")

        self._worker = ParseWorker(list(self.pending_files), self)
        self._worker.parsed.connect(self._on_parsed)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, done: int, total: int, name: str) -> None:
        self.progress.setValue(done)
        self.lb_status.setText(f"正在识别（{done}/{total}）：{name}")

    def _on_parsed(self, info: dict) -> None:
        """每识别完一个文件立即写入 Excel 并展示。"""
        bearer = self.cmb_bearer.currentText().strip()
        expense = self.cmb_expense.currentText().strip()
        now = datetime.now().strftime(TIME_FMT)
        record = {
            COL_BEARER: bearer,
            COL_INV_NO: info.get(COL_INV_NO, ""),
            COL_INV_DATE: info.get(COL_INV_DATE, ""),
            COL_SELLER: info.get(COL_SELLER, ""),
            COL_AMOUNT: info.get(COL_AMOUNT, ""),
            COL_EXPENSE: expense,
            "支付时间": "",
            "备注": "",
            "识别时间": now,
            "源文件名": info.get("源文件名", ""),
        }
        excel_row: int | None = None
        err = ""
        try:
            excel_row = self.store.append_record(record)
            self._session_rows.append(excel_row)
        except ExcelError as exc:
            err = str(exc)

        status = info.get("识别状态", "")
        # 重复归档提醒（同一发票号码已写入过）
        inv_no = record[COL_INV_NO]
        if inv_no and not err:
            try:
                dup = self.store.has_invoice_no(inv_no)
            except Exception:  # noqa: BLE001
                dup = False
            if dup:
                status += f"；注意：发票号码 {inv_no} 此前已归档过，可能重复"
        if err:
            status = f"已识别但写入失败：{err}"
        self._append_result_row(status, info, record, excel_row, err)

    def _append_result_row(self, status: str, info: dict, record: dict,
                           excel_row: int | None, err: str) -> None:
        self._loading = True
        r = self.table.rowCount()
        self.table.insertRow(r)
        values = [
            status,
            info.get("源文件名", ""),
            record[COL_INV_NO],
            record[COL_INV_DATE],
            record[COL_SELLER],
            record[COL_BEARER],
            record[COL_EXPENSE],
            record[COL_AMOUNT],
        ]
        for c, val in enumerate(values):
            item = QTableWidgetItem(str(val))
            if c < FIRST_EDITABLE_COL:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if c == 0:
                color = SUCCESS if status.startswith("识别成功") else (
                    WARNING if status.startswith("部分") else DANGER)
                if "重复" in status or "注意" in status:
                    color = WARNING
                if err or status.startswith("未识别") or "失败" in status:
                    color = DANGER
                item.setForeground(QBrush(QColor(color)))
                f = QFont()
                f.setBold(True)
                item.setFont(f)
                item.setToolTip(status)
            if c >= FIRST_EDITABLE_COL:
                item.setToolTip("可直接双击修改，修改后会同步写入 Excel")
            self.table.setItem(r, c, item)
        if excel_row:
            self._row_map[r] = excel_row
        self._loading = False
        self.table.scrollToBottom()

    def _on_finished(self, results: list) -> None:
        self.btn_start.setEnabled(True)
        self.progress.setVisible(False)
        ok = sum(1 for r in results if r.get("识别状态") == "识别成功")
        part = sum(1 for r in results if str(r.get("识别状态", "")).startswith("部分"))
        fail = len(results) - ok - part
        self.lb_status.setText(
            f"本次共处理 {len(results)} 个文件：识别成功 {ok}，部分识别 {part}，需人工处理 {fail}。"
            "记录已写入 Excel。"
        )
        self.lb_result.setText(
            f"本次识别 {len(results)} 条，全部累计 {len(self.store.list_records())} 条"
        )
        if self._session_rows:
            self.btn_undo.setEnabled(True)
        self.pending_files.clear()
        self.file_list.clear()
        self._refresh_count()
        self.data_changed.emit()

    # ---------------------------------------------------------- 表格编辑
    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        col = item.column()
        if col < FIRST_EDITABLE_COL:
            return
        row = item.row()
        excel_row = self._row_map.get(row)
        col_name = SESSION_COLUMNS[col]
        value = item.text().strip()
        if excel_row:
            try:
                self.store.update_record(excel_row, {col_name: value})
            except ExcelError as exc:
                QMessageBox.warning(self, "保存失败", str(exc))
        self.lb_result.setText(f"已更新第 {row + 1} 行「{col_name}」为：{value or '（空）'}")
        self.data_changed.emit()

    def clear_results(self) -> None:
        self._loading = True
        self.table.setRowCount(0)
        self._loading = False
        self._row_map.clear()
        self._session_rows.clear()
        self.btn_undo.setEnabled(False)
        self.lb_result.setText("暂无识别记录")

    # ---------------------------------------------------------- 撤销
    def undo_session(self) -> None:
        rows = [r for r in self._session_rows if r]
        if not rows:
            return
        ans = QMessageBox.question(
            self, "确认撤销",
            f"将删除本次归档写入的 {len(rows)} 条记录，是否继续？\n"
            "（已归档到 Excel 的数据会被一并移除）",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        try:
            n = self.store.delete_records(rows)
        except ExcelError as exc:
            QMessageBox.warning(self, "撤销失败", str(exc))
            return
        self.clear_results()
        self.lb_status.setText(f"已撤销本次归档，删除 {n} 条记录。")
        self.data_changed.emit()

    # ---------------------------------------------------------- 外部调用
    def default_expense(self) -> str:
        return self.cmb_expense.currentText().strip()
