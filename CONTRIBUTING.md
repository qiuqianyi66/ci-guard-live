# 贡献指南

## 先跑起来

```bash
pip install pyyaml
python tools/ci-guard/selftest.py        # 7 项回归，应该全 PASS
python tools/ci-guard/ci_guard.py .      # 扫本仓，演示用的 demo.yml 会命中 3 条
```

## 改一条规则

1. 在 `tools/ci-guard/ci_guard.py` 的 RULES 表里改判定。
2. 在 `tools/ci-guard/docs/RULES.md` 补这一条：症状、为什么是问题、怎么修、误报边界。
3. 在 `selftest.py` 里加**必须命中**的坏样本和**必须不命中**的好样本，两项都要。
4. 跑 `selftest.py`，全绿才提交。

## 提交前必须过

- `python tools/ci-guard/selftest.py` 全 PASS
- 新增规则同时有坏样本与好样本（只加坏样本会制造误报）
- 涉及数字（体积、判据数、扫描数）的改动，全仓检索同步，包括 README、文档与视频画面

## 不接受的改动

- 引入 pyyaml 之外的运行时依赖
- 把可判定的判据改成"看情况""通常""建议"
- 降低既有规则的严格度而不在 PR 里说明理由与影响范围
- 删掉断言或跳过测试来让 CI 变绿

## 报误报

带上：仓库地址、`--format=json` 的输出、你判断它是误报的理由。开 issue 时选 `diagnose` 模板。