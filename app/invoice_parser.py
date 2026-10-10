# -*- coding: utf-8 -*-
"""发票 PDF 识别。

从 PDF 中提取：发票号码、开票日期、销售方公司名称、价税合计（可选）。
识别策略（多路兜底，先精确后宽松）：
  1. PyMuPDF 抽取带版面顺序的正文文本；
  2. 兼容 pdfplumber（PyMuPDF 不可用时）；
  3. 对同一份文本生成三种视图（原始 / 按块 / 去空白），依次尝试多种正则；
  4. 销售方名称优先取「销售方」上下文，退化时取所有「名称：」中的最后一个
     （增值税发票版面中购买方在前、销售方在后）。

识别结果仅作自动填充，软件界面允许人工修正。
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

# ------------------------------------------------------------------ PDF 取文本


def _text_by_pymupdf(path: Path) -> str:
    import fitz  # PyMuPDF

    parts: list[str] = []
    with fitz.open(str(path)) as doc:
        for page in doc:
            parts.append(page.get_text("text") or "")
    return "\n".join(parts)


def _text_by_pdfplumber(path: Path) -> str:
    import pdfplumber

    parts: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def read_pdf_text(path: str | Path) -> tuple[str, str]:
    """返回 (文本, 使用的解析器名称)。

    依次尝试多个解析引擎，任一可用即返回；
    当全部失败时返回空文本与错误明细（供界面提示）。
    """
    path = Path(path)
    errors: list[str] = []
    for name, func in (("pdfplumber", _text_by_pdfplumber), ("pymupdf", _text_by_pymupdf)):
        try:
            text = func(path) or ""
            if text.strip():
                return text, name
            errors.append(f"{name}: 未提取到文本")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {exc}")
    return "", "; ".join(errors)


# ------------------------------------------------------------------ 文本归一化

_FULLWIDTH = {
    ord("０"): "0", ord("１"): "1", ord("２"): "2", ord("３"): "3", ord("４"): "4",
    ord("５"): "5", ord("６"): "6", ord("７"): "7", ord("８"): "8", ord("９"): "9",
    ord("Ａ"): "A", ord("Ｂ"): "B", ord("Ｃ"): "C", ord("Ｄ"): "D", ord("Ｅ"): "E",
    ord("："): ":", ord("（"): "(", ord("）"): ")", ord("　"): " ",
    ord("￥"): "¥", ord("－"): "-", ord("．"): ".",
}


def _normalize(text: str) -> str:
    return text.translate(_FULLWIDTH)


def _views(raw: str) -> list[str]:
    """生成三种文本视图，用于不同正则风格。"""
    raw = _normalize(raw)
    flat_no_space = re.sub(r"[ \t\u00a0]+", "", raw)          # 去行内空白，保留换行
    compact = re.sub(r"\s+", "", raw)                          # 去所有空白
    return [raw, flat_no_space, compact]


# ------------------------------------------------------------------ 提取规则

_INV_NO_PATTERNS = [
    r"发票号码\s*[:：]?\s*(\d[\d\s]{5,30}\d)",
    r"发\s*票\s*号\s*码\s*[:：]?\s*(\d[\d\s]{5,30}\d)",
    r"发票代码\s*[:：]?\s*(\d{10,14})\s*[,，]?\s*发票号码\s*[:：]?\s*(\d[\d\s]{5,30}\d)",
]

_INV_DATE_PATTERNS = [
    r"开票日期\s*[:：]?\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
    r"开票日期\s*[:：]?\s*(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})",
    r"开票时间\s*[:：]?\s*(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})",
]

_SELLER_PATTERNS = [
    # 明确带「销售方」上下文
    r"销售方[^\n]{0,30}?名\s*称\s*[:：]\s*([^\n]{2,80})",
    r"销\s*售\s*方[\s\S]{0,150}?名\s*称\s*[:：]\s*([^\n]{2,80})",
    r"销售方(?:信息)?名称\s*[:：]?\s*([\u4e00-\u9fa5A-Za-z0-9()（）·\-]{2,60})",
]

_NAME_LINE = re.compile(r"名\s*称\s*[:：]\s*([^\n]{2,80})")

_AMOUNT_PATTERNS = [
    r"价税合计[\s\S]{0,80}?([0-9][0-9,]*\.\d{1,2})",
    r"[（(]\s*小\s*写\s*[）)]\s*[¥￥]?\s*([0-9][0-9,]*\.\d{1,2})",
    r"价税合计\s*[:：]?\s*[¥￥]?\s*([0-9][0-9,]*\.\d{1,2})",
]

# 明显不是销售方名称的噪声
_BAD_NAME_KEYS = (
    "货物或应税", "项目名称", "商品名称", "开户行", "银行账号", "地址", "电话",
    "规格型号", "单位", "数量", "单价", "税率", "税额",
)


def _clean_company(value: str) -> str:
    s = (value or "").strip()
    s = re.sub(r"[\s\u3000]+", "", s)
    # 截断到下一个字段标签
    s = re.split(
        r"(统一社会信用代码|纳税人识别号|识别号|地\s*址|开户行|账\s*号|电\s*话)",
        s,
    )[0]
    s = s.strip(":：,，.。;；")
    # 去掉可能混入的前导标签
    s = re.sub(r"^(销售方|购买方|购方|销方|信息|名称)[:：]?", "", s)
    if not s or len(s) < 2:
        return ""
    if any(k in s for k in _BAD_NAME_KEYS):
        return ""
    if not re.search(r"[\u4e00-\u9fa5A-Za-z]", s):
        return ""
    return s[:60]


def _first_match(patterns: list[str], views: list[str], group: int = 1) -> str:
    for view in views:
        for pat in patterns:
            m = re.search(pat, view)
            if m:
                try:
                    val = m.group(group)
                except IndexError:
                    continue
                if val:
                    return val
    return ""


def _extract_invoice_no(views: list[str]) -> str:
    for view in views:
        for pat in _INV_NO_PATTERNS:
            m = re.search(pat, view)
            if not m:
                continue
            digits = re.sub(r"\D", "", m.group(m.lastindex or 1))
            if 8 <= len(digits) <= 25:
                return digits
    return ""


def _extract_invoice_date(views: list[str]) -> str:
    for view in views:
        for pat in _INV_DATE_PATTERNS:
            m = re.search(pat, view)
            if not m:
                continue
            y, mo, d = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            try:
                return datetime(y, mo, d).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return ""


def _extract_seller(views: list[str]) -> str:
    # 1) 带「销售方」上下文的精确匹配
    for view in views:
        for pat in _SELLER_PATTERNS:
            for m in re.finditer(pat, view):
                name = _clean_company(m.group(1))
                if name:
                    return name
    # 2) 退化：收集所有「名称：」，取最后一个（销售方通常在后）
    candidates: list[str] = []
    for view in views[:2]:
        for m in _NAME_LINE.finditer(view):
            name = _clean_company(m.group(1))
            if name and name not in candidates:
                candidates.append(name)
    if candidates:
        return candidates[-1]
    return ""


def _extract_amount(views: list[str]) -> str:
    for view in views:
        for pat in _AMOUNT_PATTERNS:
            m = re.search(pat, view)
            if not m:
                continue
            raw = m.group(m.lastindex or 1).replace(",", "")
            try:
                return f"{float(raw):.2f}"
            except ValueError:
                continue
    return ""


# ------------------------------------------------------------------ 对外接口

def parse_invoice(pdf_path: str | Path) -> dict[str, Any]:
    """识别单个发票 PDF。

    返回值包含：
      发票号码 / 开票日期 / 销售方公司名称 / 价税合计 / 识别状态 / 备注信息
    永不抛异常，失败时字段留空并在「识别状态」中说明原因。
    """
    pdf_path = Path(pdf_path)
    result: dict[str, Any] = {
        "发票号码": "",
        "开票日期": "",
        "销售方公司名称": "",
        "价税合计": "",
        "识别状态": "",
        "解析器": "",
    }

    if not pdf_path.exists():
        result["识别状态"] = "文件不存在"
        return result

    try:
        raw, parser = read_pdf_text(pdf_path)
    except Exception as exc:  # noqa: BLE001
        result["识别状态"] = f"无法读取 PDF（{exc}）"
        return result

    result["解析器"] = parser
    if not raw.strip():
        result["识别状态"] = "PDF 无文本层（可能为扫描件图片），无法自动识别"
        return result

    views = _views(raw)
    result["发票号码"] = _extract_invoice_no(views)
    result["开票日期"] = _extract_invoice_date(views)
    result["销售方公司名称"] = _extract_seller(views)
    result["价税合计"] = _extract_amount(views)

    found = [k for k in ("发票号码", "开票日期", "销售方公司名称") if result[k]]
    if len(found) == 3:
        result["识别状态"] = "识别成功"
    elif found:
        missing = [k for k in ("发票号码", "开票日期", "销售方公司名称") if not result[k]]
        result["识别状态"] = "部分识别，缺少：" + "、".join(missing)
    else:
        result["识别状态"] = "未识别到发票关键信息，请手动填写"
    return result
