# -*- coding: utf-8 -*-
"""校验发票识别逻辑（仅测试用）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.invoice_parser import parse_invoice, read_pdf_text  # noqa: E402

SAMPLES = Path(__file__).resolve().parent / "samples"

EXPECT = {
    "01_全电发票_技术服务费.pdf": {
        "发票号码": "24312000000012345678",
        "开票日期": "2024-05-20",
        "销售方公司名称": "北京云图信息技术有限公司",
        "价税合计": "10600.00",
    },
    "02_增值税电子普通发票_运输费.pdf": {
        "发票号码": "12345678",
        "开票日期": "2020-01-15",
        "销售方公司名称": "广州顺达物流有限公司",
        "价税合计": "320.00",
    },
    "03_电子发票_餐饮费.pdf": {
        "发票号码": "24502000000098765432",
        "开票日期": "2025-11-03",
        "销售方公司名称": "成都锦江餐饮管理有限公司",
        "价税合计": "860.00",
    },
}

ok = True
for name, exp in EXPECT.items():
    path = SAMPLES / name
    if not path.exists():
        print(f"[跳过] 缺少样本 {name}")
        continue
    print("=" * 70)
    print("文件：", name)
    text, parser = read_pdf_text(path)
    print(f"--- 解析器 {parser}，文本长度 {len(text)} ---")
    print(text[:300].replace("\n", " / "))
    res = parse_invoice(path)
    for k, v in exp.items():
        got = res.get(k, "")
        flag = "✔" if got == v else "✘"
        if got != v:
            ok = False
        print(f"  {flag} {k}: 期望={v!r}  实际={got!r}")
    print("  状态：", res.get("识别状态"))

print("=" * 70)
print("全部通过" if ok else "存在不一致，需要调整正则")
sys.exit(0 if ok else 1)
