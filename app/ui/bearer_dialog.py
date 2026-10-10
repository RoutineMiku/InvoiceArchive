# -*- coding: utf-8 -*-
"""费用承担人 新增 / 编辑 对话框。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


class BearerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, title: str = "新增费用承担人",
                 data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        data = data or {}

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 14)
        root.setSpacing(12)

        tip = QLabel("姓名必填；「停用」后不再出现在归档页的下拉列表中，历史记录不受影响。")
        tip.setObjectName("Muted")
        tip.setWordWrap(True)
        root.addWidget(tip)

        form = QFormLayout()
        form.setSpacing(10)

        self.ed_name = QLineEdit(data.get("姓名", ""))
        self.ed_name.setPlaceholderText("如：张三")
        self.ed_dept = QLineEdit(data.get("部门", ""))
        self.ed_dept.setPlaceholderText("如：财务部 / 项目组 A（可空）")

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["启用", "停用"])
        self.cmb_status.setCurrentText(data.get("状态") or "启用")

        self.ed_note = QLineEdit(data.get("备注", ""))
        self.ed_note.setPlaceholderText("可空")

        form.addRow("姓名 *", self.ed_name)
        form.addRow("部门", self.ed_dept)
        form.addRow("状态", self.cmb_status)
        form.addRow("备注", self.ed_note)
        root.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("保存")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.button(QDialogButtonBox.Ok).setObjectName("Primary")
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _on_accept(self) -> None:
        if not self.ed_name.text().strip():
            QMessageBox.warning(self, "提示", "姓名不能为空。")
            self.ed_name.setFocus()
            return
        self.accept()

    def values(self) -> dict:
        return {
            "姓名": self.ed_name.text().strip(),
            "部门": self.ed_dept.text().strip(),
            "状态": self.cmb_status.currentText(),
            "备注": self.ed_note.text().strip(),
        }
