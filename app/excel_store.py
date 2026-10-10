# -*- coding: utf-8 -*-
"""Excel 数据层。

两张表都以本地 .xlsx 文件形式存在，与软件放在同一目录（data/）：
  1. 费用承担人.xlsx      —— 费用承担人的增删改查
  2. 发票报销归档.xlsx    —— 每次识别后自动追加一条记录

所有写盘操作均为「先写临时文件、再原子替换」，避免中途断电/异常导致表损坏；
同时每次写盘前自动保留一份当日备份到 data/backup/。
"""
from __future__ import annotations

import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .config import (
    BACKUP_DIR,
    BEARER_COLUMNS,
    BEARER_FILE,
    BEARER_WIDTHS,
    RECORD_COLUMNS,
    RECORD_FILE,
    RECORD_WIDTHS,
)

# ------------------------------------------------------------------ 样式常量
HEADER_FILL = PatternFill("solid", fgColor="1F6FEB")
HEADER_FONT = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
CELL_FONT = Font(name="微软雅黑", size=10)
ZEBRA_FILL = PatternFill("solid", fgColor="F4F7FB")

_thin = Side(style="thin", color="D6DCE5")
BORDER = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=False)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=False)


class ExcelError(RuntimeError):
    """Excel 读写异常（多为文件被 Excel 占用）。"""


def _atomic_save(wb: Workbook, path: Path) -> None:
    """先写临时文件再原子替换，保证不会写出半个损坏的 xlsx。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".writing.xlsx")
    try:
        wb.save(tmp)
    except PermissionError as exc:  # pragma: no cover
        raise ExcelError(f"无法写入临时文件：{tmp}") from exc
    try:
        os.replace(tmp, path)
    except PermissionError as exc:
        tmp.unlink(missing_ok=True)
        raise ExcelError(
            f"文件正被占用，保存失败：{path.name}\n请先关闭用 Excel 打开的这个文件后重试。"
        ) from exc


def _backup(path: Path) -> None:
    """每次改动前做一份当日备份，最多保留最近 30 份。"""
    if not path.exists():
        return
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d")
        target = BACKUP_DIR / f"{path.stem}_{stamp}{path.suffix}"
        shutil.copy2(path, target)
        files = sorted(BACKUP_DIR.glob(f"{path.stem}_*{path.suffix}"))
        for old in files[:-30]:
            old.unlink(missing_ok=True)
    except Exception:  # 备份失败不应阻断主流程
        pass


def _style_sheet(ws, columns: list[str], widths: list[int]) -> None:
    """写入表头并设置列宽、样式、冻结窗格。"""
    for idx, (name, width) in enumerate(zip(columns, widths), start=1):
        cell = ws.cell(row=1, column=idx, value=name)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.row_dimensions[1].height = 26
    ws.freeze_panes = "A2"


def _write_row(ws, row_idx: int, values: list[Any], zebra: bool = False) -> None:
    for col, value in enumerate(values, start=1):
        cell = ws.cell(row=row_idx, column=col, value=value)
        cell.font = CELL_FONT
        cell.border = BORDER
        cell.alignment = LEFT
        if isinstance(value, str) and value.isdigit() and len(value) >= 12:
            # 长数字（发票号码）强制文本格式，防止科学计数法
            cell.number_format = "@"
        if zebra:
            cell.fill = ZEBRA_FILL


class ExcelStore:
    """费用承担人 + 归档记录的统一读写入口（线程安全）。"""

    def __init__(self, bearer_file: Path | None = None, record_file: Path | None = None):
        self.bearer_file = Path(bearer_file or BEARER_FILE)
        self.record_file = Path(record_file or RECORD_FILE)
        self._lock = threading.RLock()
        self.bearer_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_bearer_file()
        self._ensure_record_file()

    # ------------------------------------------------------------ 初始化
    def _ensure_bearer_file(self) -> None:
        if self.bearer_file.exists():
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "费用承担人"
        _style_sheet(ws, BEARER_COLUMNS, BEARER_WIDTHS)
        _atomic_save(wb, self.bearer_file)

    def _ensure_record_file(self) -> None:
        if self.record_file.exists():
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "报销归档明细"
        _style_sheet(ws, RECORD_COLUMNS, RECORD_WIDTHS)
        _atomic_save(wb, self.record_file)

    # ============================================================ 费用承担人
    def list_bearers(self) -> list[dict]:
        """读取全部费用承担人，附带 _row（Excel 行号）。"""
        with self._lock:
            wb = load_workbook(self.bearer_file)
            ws = wb.active
            out: list[dict] = []
            for row in ws.iter_rows(min_row=2, values_only=False):
                values = [c.value for c in row]
                if not any(v not in (None, "") for v in values):
                    continue
                rec = {col: ("" if v is None else str(v).strip())
                       for col, v in zip(BEARER_COLUMNS, values)}
                rec["_row"] = row[0].row
                out.append(rec)
            wb.close()
            return out

    def bearer_names(self, active_only: bool = True) -> list[str]:
        names = []
        for b in self.list_bearers():
            if active_only and b.get("状态") == "停用":
                continue
            if b.get("姓名"):
                names.append(b["姓名"])
        return names

    def add_bearer(self, name: str, dept: str = "", status: str = "启用",
                   note: str = "") -> None:
        name = (name or "").strip()
        if not name:
            raise ExcelError("姓名不能为空。")
        with self._lock:
            if any(b["姓名"] == name for b in self.list_bearers()):
                raise ExcelError(f"费用承担人「{name}」已存在。")
            _backup(self.bearer_file)
            wb = load_workbook(self.bearer_file)
            ws = wb.active
            r = ws.max_row + 1
            created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _write_row(ws, r, [name, dept, status or "启用", note, created],
                       zebra=(r % 2 == 0))
            _atomic_save(wb, self.bearer_file)
            wb.close()

    def update_bearer(self, row: int, name: str, dept: str, status: str,
                      note: str) -> None:
        name = (name or "").strip()
        if not name:
            raise ExcelError("姓名不能为空。")
        with self._lock:
            others = [b for b in self.list_bearers()
                      if b["_row"] != row and b["姓名"] == name]
            if others:
                raise ExcelError(f"费用承担人「{name}」已存在。")
            _backup(self.bearer_file)
            wb = load_workbook(self.bearer_file)
            ws = wb.active
            created = ws.cell(row=row, column=5).value or ""
            _write_row(ws, row, [name, dept, status, note, created],
                       zebra=(row % 2 == 0))
            _atomic_save(wb, self.bearer_file)
            wb.close()

    def delete_bearer(self, row: int) -> None:
        with self._lock:
            _backup(self.bearer_file)
            wb = load_workbook(self.bearer_file)
            ws = wb.active
            ws.delete_rows(row, 1)
            _atomic_save(wb, self.bearer_file)
            wb.close()

    # ============================================================ 归档记录
    def list_records(self) -> list[dict]:
        with self._lock:
            wb = load_workbook(self.record_file)
            ws = wb.active
            out: list[dict] = []
            for row in ws.iter_rows(min_row=2, values_only=False):
                values = [c.value for c in row]
                if not any(v not in (None, "") for v in values):
                    continue
                rec = {col: ("" if v is None else str(v).strip())
                       for col, v in zip(RECORD_COLUMNS, values)}
                rec["_row"] = row[0].row
                out.append(rec)
            wb.close()
            return out

    def next_seq(self) -> int:
        records = self.list_records()
        seqs = []
        for r in records:
            try:
                seqs.append(int(float(r.get("序号") or 0)))
            except (TypeError, ValueError):
                continue
        return (max(seqs) + 1) if seqs else 1

    def has_invoice_no(self, invoice_no: str) -> bool:
        if not invoice_no:
            return False
        return any(r.get("发票号码") == invoice_no for r in self.list_records())

    def append_record(self, record: dict, seq: int | None = None,
                      write_back: bool = True) -> int:
        """追加一条归档记录，返回写入的 Excel 行号。"""
        with self._lock:
            if seq is None:
                seq = self.next_seq()
            values = [
                seq,
                record.get("费用承担人", ""),
                record.get("发票号码", ""),
                record.get("开票日期", ""),
                record.get("销售方公司名称", ""),
                record.get("价税合计", ""),
                record.get("费用类型", ""),
                record.get("支付时间", ""),
                record.get("备注", ""),
                record.get("识别时间", ""),
                record.get("源文件名", ""),
            ]
            if write_back:
                _backup(self.record_file)
            wb = load_workbook(self.record_file)
            ws = wb.active
            r = ws.max_row + 1
            _write_row(ws, r, values, zebra=(r % 2 == 0))
            _atomic_save(wb, self.record_file)
            wb.close()
            return r

    def update_record(self, row: int, fields: dict) -> None:
        """按列名更新一行中的若干字段。"""
        if not fields:
            return
        with self._lock:
            _backup(self.record_file)
            wb = load_workbook(self.record_file)
            ws = wb.active
            for col_name, value in fields.items():
                if col_name not in RECORD_COLUMNS:
                    continue
                col_idx = RECORD_COLUMNS.index(col_name) + 1
                cell = ws.cell(row=row, column=col_idx)
                cell.value = "" if value is None else value
                cell.font = CELL_FONT
                cell.border = BORDER
                cell.alignment = LEFT
            _atomic_save(wb, self.record_file)
            wb.close()

    def delete_records(self, rows: list[int]) -> int:
        """删除若干行（按行号从大到小删除，避免行号错位）。"""
        rows = sorted({int(r) for r in rows}, reverse=True)
        if not rows:
            return 0
        with self._lock:
            _backup(self.record_file)
            wb = load_workbook(self.record_file)
            ws = wb.active
            for r in rows:
                if r >= 2:
                    ws.delete_rows(r, 1)
            _atomic_save(wb, self.record_file)
            wb.close()
            return len(rows)

    # ----------------------------------------------------------- 统计
    def summarize(self, records: list[dict] | None = None) -> dict:
        records = self.list_records() if records is None else records
        total = 0.0
        for r in records:
            try:
                total += float(str(r.get("价税合计") or "0").replace(",", ""))
            except ValueError:
                continue
        return {"count": len(records), "amount": total}
