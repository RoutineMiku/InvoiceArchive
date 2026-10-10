# 测试脚本

这些脚本用于开发期自测，**不属于软件本体**，运行它们是可选的。

| 脚本 | 作用 |
|------|------|
| `make_samples.py` | 用 reportlab 生成 3 张仿真发票 PDF（含「销售方在前」的异常版面），输出到 `tests/samples/` |
| `test_parser.py` | 校验发票识别正则，逐一比对期望值 |
| `test_smoke.py` | 端到端冒烟测试：数据层 CRUD + GUI 构建 + 模拟归档流程 + 撤销 |

## 运行

```bash
pip install reportlab          # 仅生成样本时需要

python tests/make_samples.py   # 先生成测试 PDF

python tests/test_parser.py    # 识别测试
python tests/test_smoke.py     # 端到端测试（使用临时目录，不污染 data/）
```

两个测试脚本均以退出码 0 表示全部通过，非 0 表示存在失败项。
