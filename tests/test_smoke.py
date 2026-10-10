# -*- coding: utf-8 -*-
"""端到端冒烟测试：数据层 CRUD + 主窗口构建 + 模拟一次完整归档流程。"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SANDBOX = Path(tempfile.mkdtemp(prefix="inv_test_"))

import app.config as config  # noqa: E402
config.DATA_DIR = SANDBOX / "data"
config.BACKUP_DIR = config.DATA_DIR / "backup"
config.BEARER_FILE = config.DATA_DIR / "费用承担人.xlsx"
config.RECORD_FILE = config.DATA_DIR / "发票报销归档.xlsx"

from app.excel_store import ExcelStore  # noqa: E402
from app.invoice_parser import parse_invoice  # noqa: E402

failures = []


def check(cond, msg):
    print(("  ✔ " if cond else "  ✘ ") + msg)
    if not cond:
        failures.append(msg)


print("== 1. 数据层：费用承担人 CRUD ==")
store = ExcelStore(config.BEARER_FILE, config.RECORD_FILE)
check(config.BEARER_FILE.exists(), "费用承担人.xlsx 自动创建")
check(config.RECORD_FILE.exists(), "发票报销归档.xlsx 自动创建")

store.add_bearer("张三", "财务部", "启用", "测试")
store.add_bearer("李四", "研发部", "启用", "")
store.add_bearer("王五", "已离职", "停用", "历史")
names = store.bearer_names()
check(names == ["张三", "李四"], f"停用者不出现在下拉列表 -> {names}")

rows = store.list_bearers()
check(len(rows) == 3, "费用承担人共 3 条")
store.update_bearer(rows[1]["_row"], "李四", "市场部", "启用", "改过")
r2 = [b for b in store.list_bearers() if b["姓名"] == "李四"][0]
check(r2["部门"] == "市场部" and r2["备注"] == "改过", "编辑生效")
store.delete_bearer(rows[2]["_row"])
check(len(store.list_bearers()) == 2, "删除生效")

try:
    store.add_bearer("张三")
    check(False, "重名应被拒绝")
except Exception:
    check(True, "重名被拒绝")

print("== 2. 数据层：归档记录 ==")
samples = Path(__file__).resolve().parent / "samples"
pdfs = sorted(samples.glob("*.pdf"))
check(len(pdfs) == 3, f"找到 {len(pdfs)} 个测试 PDF")

from datetime import datetime  # noqa: E402
from app.config import TIME_FMT  # noqa: E402

for p in pdfs:
    info = parse_invoice(p)
    row = store.append_record({
        "费用承担人": "张三",
        "发票号码": info["发票号码"],
        "开票日期": info["开票日期"],
        "销售方公司名称": info["销售方公司名称"],
        "价税合计": info["价税合计"],
        "费用类型": "办公费",
        "支付时间": "",
        "备注": "",
        "识别时间": datetime.now().strftime(TIME_FMT),
        "源文件名": p.name,
    })
    check(row >= 2, f"追加 {p.name} -> Excel 第 {row} 行")

recs = store.list_records()
check(len(recs) == 3, "归档表共 3 条")
check(recs[0]["序号"] == "1" and recs[2]["序号"] == "3", "序号自动递增")
check(store.next_seq() == 4, "下一个序号 = 4")
s = store.summarize(recs)
check(abs(s["amount"] - (10600.00 + 320.00 + 860.00)) < 0.01,
      f"价税合计统计 = {s['amount']:.2f}")
check(store.has_invoice_no("24312000000012345678"), "发票号查重可用")

store.update_record(recs[0]["_row"], {"支付时间": "2026-10-10", "备注": "已报销"})
recs = store.list_records()
check(recs[0]["支付时间"] == "2026-10-10" and recs[0]["备注"] == "已报销",
      "修改支付时间/备注回写成功")

store.delete_records([recs[2]["_row"]])
check(len(store.list_records()) == 2, "删除单条记录成功")

print("== 3. 界面：主窗口构建 ==")
from PySide6.QtWidgets import QApplication  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402

qapp = QApplication.instance() or QApplication([])
win = MainWindow(store)
win.show()
qapp.processEvents()
check(win.tabs.count() == 3, "三个选项卡就绪")
check(win.archive_page.cmb_bearer.count() == 2, "归档页下拉读取到 2 位承担人")
check(win.records_page.table.rowCount() == 2, "归档记录页显示 2 条")
check(win.bearers_page.table.rowCount() == 2, "费用承担人页显示 2 位")

print("== 4. 界面：模拟一次识别归档 ==")
page = win.archive_page
page.add_files([str(p) for p in pdfs[:1]])
qapp.processEvents()
check(len(page.pending_files) == 1, "文件已加入待处理列表")
page.cmb_bearer.setCurrentText("张三")
page.cmb_expense.setCurrentText("差旅费")
before = len(store.list_records())
page.start_parse()
page._worker.wait(20000)
qapp.processEvents()
after = len(store.list_records())
check(after == before + 1, f"识别后 Excel 记录数 {before} -> {after}")
check(page.table.rowCount() == 1, "结果表新增 1 行")
check(len(page.pending_files) == 0, "待处理列表已清空")

# 模拟在结果表中修改备注
item = page.table.item(0, 7)   # 价税合计列
item.setText("9999.00")
qapp.processEvents()
last = store.list_records()[-1]
check(last["价税合计"] == "9999.00", "结果表内修改已同步到 Excel")

print("== 5. 界面：撤销本次归档 ==")
rows_before = len(store.list_records())
import app.ui.archive_page as ap  # noqa: E402
from PySide6.QtWidgets import QMessageBox  # noqa: E402
_orig = QMessageBox.question
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
page.undo_session()
QMessageBox.question = _orig
check(len(store.list_records()) == rows_before - 1, "撤销后记录已回退")

win.close()
print("=" * 70)
if failures:
    print(f"FAILED: {len(failures)} 项")
    for f in failures:
        print("  -", f)
else:
    print("ALL PASSED ✔")
shutil.rmtree(SANDBOX, ignore_errors=True)
sys.exit(1 if failures else 0)
