# -*- coding: utf-8 -*-
"""生成几张仿真发票 PDF，用于验证识别逻辑（仅测试用，不属于软件本体）。"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent / "samples"
OUT.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(TTFont("CN", "C:/Windows/Fonts/simsun.ttc"))
pdfmetrics.registerFont(TTFont("CNB", "C:/Windows/Fonts/simhei.ttf"))


def new_canvas(path: Path):
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle(path.stem)
    return c


def line(c, x, y, text, size=10, font="CN"):
    c.setFont(font, size)
    c.drawString(x, y, text)


# ---------------------------------------------------------------- 示例 1：全电发票
def sample_quandian(path: Path):
    c = new_canvas(path)
    line(c, 200, 780, "电子发票（增值税专用发票）", 15, "CNB")
    line(c, 380, 750, "发票号码：24312000000012345678")
    line(c, 380, 735, "开票日期：2024年05月20日")
    line(c, 60, 700, "购买方信息")
    line(c, 120, 700, "名称：深圳市前海智联科技有限公司")
    line(c, 120, 685, "统一社会信用代码/纳税人识别号：91440300MA5FL2Q31A")
    line(c, 60, 655, "销售方信息")
    line(c, 120, 655, "名称：北京云图信息技术有限公司")
    line(c, 120, 640, "统一社会信用代码/纳税人识别号：91110108MA01AB23CD")
    line(c, 60, 600, "项目名称")
    line(c, 160, 600, "规格型号")
    line(c, 250, 600, "单位")
    line(c, 300, 600, "数量")
    line(c, 350, 600, "单价")
    line(c, 410, 600, "金额")
    line(c, 470, 600, "税率")
    line(c, 510, 600, "税额")
    line(c, 60, 580, "*信息技术服务*技术服务费")
    line(c, 250, 580, "项")
    line(c, 300, 580, "1")
    line(c, 350, 580, "10000.00")
    line(c, 410, 580, "10000.00")
    line(c, 470, 580, "6%")
    line(c, 510, 580, "600.00")
    line(c, 60, 540, "合计")
    line(c, 410, 540, "¥10000.00")
    line(c, 510, 540, "¥600.00")
    line(c, 60, 515, "价税合计（大写）壹万零陆佰元整")
    line(c, 380, 515, "（小写）¥10600.00")
    line(c, 60, 470, "开票人：李四")
    c.showPage()
    c.save()
    return path


# ---------------------------------------------------------------- 示例 2：增值税电子普通发票（老版）
def sample_putong(path: Path):
    c = new_canvas(path)
    line(c, 190, 780, "增值税电子普通发票", 15, "CNB")
    line(c, 60, 750, "发票代码：031002000311")
    line(c, 60, 735, "发票号码：12345678")
    line(c, 60, 720, "开票日期：2020年01月15日")
    line(c, 380, 735, "校验码：12345 67890 12345 67890")
    line(c, 60, 690, "购买方  名称：上海某某贸易有限公司")
    line(c, 60, 675, "        纳税人识别号：91310115ABCDEF1234")
    line(c, 60, 640, "销售方  名称：广州顺达物流有限公司")
    line(c, 60, 625, "        纳税人识别号：91440101XYZ7890123")
    line(c, 60, 590, "货物或应税劳务、服务名称")
    line(c, 300, 590, "金额")
    line(c, 400, 590, "税率")
    line(c, 460, 590, "税额")
    line(c, 60, 570, "*运输服务*货物运输费")
    line(c, 300, 570, "301.89")
    line(c, 400, 570, "6%")
    line(c, 460, 570, "18.11")
    line(c, 60, 530, "价税合计（大写）叁佰贰拾元整")
    line(c, 380, 530, "（小写）¥320.00")
    c.showPage()
    c.save()
    return path


# ---------------------------------------------------------------- 示例 3：销售方在前（异常版面）
def sample_reverse(path: Path):
    c = new_canvas(path)
    line(c, 200, 780, "电子发票（普通发票）", 15, "CNB")
    line(c, 380, 750, "发票号码：24502000000098765432")
    line(c, 380, 735, "开票日期：2025年11月03日")
    line(c, 60, 700, "销售方信息")
    line(c, 120, 700, "名称：成都锦江餐饮管理有限公司")
    line(c, 120, 685, "统一社会信用代码：91510104MA6C123XYZ")
    line(c, 60, 650, "购买方信息")
    line(c, 120, 650, "名称：重庆山城电子有限公司")
    line(c, 60, 600, "价税合计（大写）捌佰陆拾元整")
    line(c, 380, 600, "（小写）¥860.00")
    c.showPage()
    c.save()
    return path


if __name__ == "__main__":
    files = [
        sample_quandian(OUT / "01_全电发票_技术服务费.pdf"),
        sample_putong(OUT / "02_增值税电子普通发票_运输费.pdf"),
        sample_reverse(OUT / "03_电子发票_餐饮费.pdf"),
    ]
    for f in files:
        print("生成：", f)
