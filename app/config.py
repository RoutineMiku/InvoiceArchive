# -*- coding: utf-8 -*-
"""全局配置：路径、表头列定义、常量。

所有数据（Excel 文件）默认保存在软件所在目录下的 data/ 文件夹中，
保证软件整体可拷贝、可离线、可归档。
"""
from __future__ import annotations

import sys
from pathlib import Path


def _app_root() -> Path:
    """返回软件所在目录。打包为 exe 后为 exe 同级目录，否则为项目根目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


APP_ROOT: Path = _app_root()
DATA_DIR: Path = APP_ROOT / "data"
BACKUP_DIR: Path = DATA_DIR / "backup"

BEARER_FILE: Path = DATA_DIR / "费用承担人.xlsx"
RECORD_FILE: Path = DATA_DIR / "发票报销归档.xlsx"
CONFIG_FILE: Path = DATA_DIR / "设置.json"

APP_NAME = "发票报销归档助手"
APP_VERSION = "1.0.0"
ORG_NAME = "LocalArchive"

# ---------------------------------------------------------------- 表结构定义

# 费用承担人表
BEARER_COLUMNS = ["姓名", "部门", "状态", "备注", "创建时间"]
BEARER_WIDTHS = [16, 18, 10, 28, 20]

# 归档表列顺序
COL_SEQ = "序号"
COL_BEARER = "费用承担人"
COL_INV_NO = "发票号码"
COL_INV_DATE = "开票日期"
COL_SELLER = "销售方公司名称"
COL_AMOUNT = "价税合计"
COL_EXPENSE = "费用类型"
COL_PAY_DATE = "支付时间"
COL_NOTE = "备注"
COL_RECOG_TIME = "识别时间"
COL_FILENAME = "源文件名"

RECORD_COLUMNS = [
    COL_SEQ,
    COL_BEARER,
    COL_INV_NO,
    COL_INV_DATE,
    COL_SELLER,
    COL_AMOUNT,
    COL_EXPENSE,
    COL_PAY_DATE,
    COL_NOTE,
    COL_RECOG_TIME,
    COL_FILENAME,
]

RECORD_WIDTHS = [6, 12, 24, 13, 36, 11, 12, 13, 22, 20, 30]

# 软件内允许人工修改的列（其余列由系统自动写入）
EDITABLE_COLUMNS = {COL_BEARER, COL_AMOUNT, COL_EXPENSE, COL_PAY_DATE, COL_NOTE}

# 自动生成、不允许人工改写的列
AUTO_COLUMNS = {COL_SEQ, COL_INV_NO, COL_INV_DATE, COL_SELLER, COL_RECOG_TIME, COL_FILENAME}

# 默认费用类型（可自由输入其它值，会累积记录到 设置.json）
DEFAULT_EXPENSE_TYPES = [
    "办公费", "差旅费", "交通费", "业务招待费", "会议费",
    "通讯费", "培训费", "福利费", "低值易耗品", "其他",
]

# 识别状态
STATUS_OK = "识别成功"
STATUS_PARTIAL = "部分识别"
STATUS_FAILED = "识别失败"

TIME_FMT = "%Y-%m-%d %H:%M:%S"
DATE_FMT = "%Y-%m-%d"
