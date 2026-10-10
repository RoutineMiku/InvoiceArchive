# -*- coding: utf-8 -*-
"""主窗口。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..config import APP_NAME, APP_VERSION, DATA_DIR
from .archive_page import ArchivePage
from .bearers_page import BearersPage, open_in_explorer
from .records_page import RecordsPage
from .theme import QSS

HELP_TEXT = """【使用流程】

第 1 步  上传发票
    在「发票归档」页，把发票 PDF 拖进虚线框（可一次多个，也可直接拖入整个文件夹），
    或点击虚线框选择文件。

第 2 步  选择费用承担人
    在右侧下拉框中选择本次发票的费用承担人。
    名单可在「费用承担人」页随时新增 / 编辑 / 停用 / 删除，
    数据保存在 data/费用承担人.xlsx。

第 3 步  开始识别并归档
    点击「开始识别并归档」，软件会自动读取每张发票 PDF 并识别：
        发票号码、开票日期、销售方公司名称、价税合计
    同时把「费用承担人」「识别时间」一并写入 Excel，每次识别都会自动追加一行。

第 4 步  补充与修改
    识别结果表格中可直接双击修改任意字段，修改会立即写回 Excel。
    「支付时间 / 费用类型 / 备注」等列可在「归档记录」页随时修改；
    也可多选后一键批量设置支付时间。

数据文件
    data/费用承担人.xlsx        费用承担人名单
    data/发票报销归档.xlsx      归档明细（每次识别自动追加）
    data/backup/                每次改动前的自动备份（保留最近 30 份）

说明
    · 全部识别与存储都在本机完成，不联网、不上传任何文件。
    · 若某张发票是扫描图片（没有文字层），软件会提示无法自动识别，
      此时可在结果表格中手动填写，其余流程不受影响。
    · 修改 Excel 时请先用「打开 Excel」查看，不要在 Excel 中长时间占用该文件，
      否则保存会失败（软件会给出提示）。
"""


class MainWindow(QMainWindow):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1220, 820)
        self.setMinimumSize(1020, 680)
        self.setStyleSheet(QSS)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 14, 16, 12)
        body_lay.setSpacing(10)

        self.tabs = QTabWidget()
        self.archive_page = ArchivePage(store)
        self.records_page = RecordsPage(store)
        self.bearers_page = BearersPage(store)
        self.tabs.addTab(self.archive_page, "① 发票归档")
        self.tabs.addTab(self.records_page, "② 归档记录")
        self.tabs.addTab(self.bearers_page, "③ 费用承担人")
        body_lay.addWidget(self.tabs, 1)
        outer.addWidget(body, 1)

        # 信号互联
        self.archive_page.goto_bearers.connect(lambda: self.tabs.setCurrentIndex(2))
        self.archive_page.data_changed.connect(self.records_page.reload)
        self.bearers_page.data_changed.connect(self._on_bearers_changed)
        self.records_page.data_changed.connect(self._refresh_status)

        self.statusBar().showMessage(f"数据目录：{DATA_DIR}")
        self._refresh_status()

    # ------------------------------------------------------------ 顶栏
    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        header.setFixedHeight(64)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(20, 0, 16, 0)
        lay.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(0)
        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")
        sub = QLabel("本地离线 · 发票 PDF 自动识别 · 报销归档")
        sub.setObjectName("AppSubtitle")
        left.addWidget(title)
        left.addWidget(sub)
        lay.addLayout(left)
        lay.addStretch(1)

        btn_dir = QPushButton("打开数据文件夹")
        btn_dir.setObjectName("HeaderBtn")
        btn_dir.clicked.connect(lambda: open_in_explorer(DATA_DIR))
        btn_help = QPushButton("使用说明")
        btn_help.setObjectName("HeaderBtn")
        btn_help.clicked.connect(self._show_help)
        lay.addWidget(btn_dir)
        lay.addWidget(btn_help)
        return header

    # ------------------------------------------------------------ 槽
    def _on_bearers_changed(self) -> None:
        self.archive_page.reload_bearers()
        self._refresh_status()

    def _refresh_status(self) -> None:
        try:
            recs = self.store.list_records()
            summary = self.store.summarize(recs)
            bearers = self.store.list_bearers()
        except Exception:  # noqa: BLE001
            return
        self.statusBar().showMessage(
            f"数据目录：{DATA_DIR}    |    费用承担人 {len(bearers)} 位    |    "
            f"归档 {summary['count']} 条，价税合计 {summary['amount']:,.2f} 元"
        )

    def _show_help(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("使用说明")
        box.setIcon(QMessageBox.Information)
        box.setText("发票报销归档助手 · 使用说明")
        box.setInformativeText(HELP_TEXT)
        box.exec()

    def closeEvent(self, event) -> None:  # noqa: N802
        worker = getattr(self.archive_page, "_worker", None)
        if worker and worker.isRunning():
            worker.cancel()
            worker.wait(3000)
        super().closeEvent(event)
