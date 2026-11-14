# 接入演练记录（2026-11-14）

在 open-code-review 的 14 份 workflow 副本上完整走了一遍"别人拿到这个工具，接进自己的仓"。

## 实测数据

| 步骤 | 动作 | 实测 |
|---|---|---|
| 1 | 复制 `tools/ci-guard` 到目标仓 | 44 ms，249 KB（含文档、schema、报告） |
| 2 | `--init-config` 生成配置与基线 | 353 ms，冻结 15 条存量 |
| 3 | 带基线跑一次 | 0 新增，exit 0 |
| 4 | 改一行引入新违规（`uses: actions/checkout@v4`） | 精确抓出那 1 条，其余 15 条继续被忽略，exit 14 |

全流程不到 1 秒（大头是 Python 启动）。**所谓"5 分钟接入"，实际是把 4 条命令写进 workflow 的时间。**

## 接入 checklist

```bash
# 1. 复制工具（249 KB，无子模块、无网络依赖）
cp -r tools/ci-guard <你的仓>/tools/

# 2. 冻结存量（只跑一次，产物要提交）
python tools/ci-guard/ci_guard.py . --init-config

# 3. 加进 CI
```

```yaml
# .github/workflows/ci-guard.yml
name: ci-guard
on: [pull_request]
permissions:
  contents: read
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - run: pip install pyyaml==6.0.3
      - run: python tools/ci-guard/ci_guard.py . --baseline .ci-guard-baseline.json
```

第 3 步也可用仓内自带的 `ci-guard.yml`（可复用 workflow，三个 action 已 pin 真实 SHA），它多支持 `strict` 与 `baseline` 两个输入。

## 应急路径：误报挡住 merge，5 分钟内关掉

按代价从小到大，三条：

1. **按文件或行忽略**（不动 CI，只动被误报的那一处）
   ```yaml
   - run: |  # ci-guard: ignore[R02] 下游有阈值断言
   ```
   或写进 `.ci-guard.yml` 的 `ignore:`，支持 `file` 与 `file:line`。

2. **把 job 改成不阻断**（保留告警，不挡合并）
   ```yaml
   continue-on-error: true
   ```
   或把 `strict` 关掉、退回 `--format=github` 观察模式。

3. **重冻结基线**（承认这批是存量，不再逐条争）
   ```bash
   python tools/ci-guard/ci_guard.py . --init-config
   ```

如果三步都救不回来，说明规则本身判错了——那要改的是规则，不是 CI。请把命中处的原文和一个反例发过来，`selftest.py` 里加一条坏样本就能锁住。

## 演练中踩到 / 已知的坑

- **pyyaml 缺失会降级**：只跑正则类规则，输出标 `DEGRADED`。CI 里请显式 `pip install pyyaml==6.0.3`。
- **YAML 1.1 把裸 `on:` 解析成布尔 `True`**：工具内部已兜底（`wf.get(True)`），但如果自己写脚本读取 workflow，这个坑一定会踩。
- **Windows 路径**：finding 的 `path` 统一替换成 `/`，SARIF 的 `uri` 也断言过不含反斜杠，跨平台可用。
- **基线要提交**：`.ci-guard-baseline.json` 与 `.ci-guard.yml` 是团队共识的一部分，不进版本库等于每次 CI 都从零开始。
