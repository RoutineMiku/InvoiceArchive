# -*- coding: utf-8 -*-
"""后台识别线程：避免批量识别 PDF 时界面卡死。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .invoice_parser import parse_invoice


class ParseWorker(QThread):
    """逐个识别 PDF，实时把结果抛回主线程。"""

    progress = Signal(int, int, str)   # 已完成数, 总数, 当前文件名
    parsed = Signal(dict)              # 单条识别结果
    finished_all = Signal(list)        # 全部结果

    def __init__(self, files: list[str], parent=None):
        super().__init__(parent)
        self.files = list(files)
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:  # noqa: D102
        results: list[dict] = []
        total = len(self.files)
        for idx, f in enumerate(self.files, start=1):
            if self._cancel:
                break
            name = Path(f).name
            try:
                info = parse_invoice(f)
            except Exception as exc:  # noqa: BLE001
                info = {
                    "发票号码": "", "开票日期": "", "销售方公司名称": "",
                    "价税合计": "", "识别状态": f"识别异常：{exc}", "解析器": "",
                }
            info["源文件名"] = name
            info["_path"] = f
            results.append(info)
            self.parsed.emit(info)
            self.progress.emit(idx, total, name)
        self.finished_all.emit(results)
