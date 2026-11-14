# ci-guard

把《企业级 AI Native 项目开发全流程白皮书》附录 AV–AW 的 CI 判据，变成一条命令能跑的门禁。

产品面按 actionlint 与 zizmor 的路数补齐（配置可选、可生成初始配置、persona 三档、inline 忽略、退出码分级、GitHub annotations）——逆向依据见 `PRODUCT-NOTES.md`，不是凭印象抄。

## 文档地图

- `ONEPAGER.md` —— 一页纸：是什么、值不值得接（给要拍板的人）
- `ADOPT.md` —— 5 分钟接入演练（实测耗时）、应急路径、已知坑
- `docs/RULES.md` —— 17 条规则逐页：症状 / 为什么 / 怎么修 / 误报边界 / 实测
- `COVERAGE.md` —— 与 actionlint（36 类）、zizmor（34 条）的逐条边界
- `FDE-NOTES.md` —— 从 Forward Deployed Engineer 视角看对上了什么、还差什么
- `PRODUCT-NOTES.md` —— actionlint / zizmor 的产品结构逆向笔记与差距表
- 四仓体检明细与 `reports/*.json` 不随仓发布（内含内部仓库路径），需要时单独索取

## 用法

```bash
python ci_guard.py .                                  # 默认 regular：只报高/中信噪比
python ci_guard.py . --pedantic                       # 连低置信（code smell）一起报
python ci_guard.py . --format=json|sarif|github
python ci_guard.py . --baseline .ci-guard-baseline.json   # 只报新增（存量仓上线用）
python ci_guard.py . --init-config                    # 生成 .ci-guard.yml + 基线
python ci_guard.py . --no-ignores                     # 临时无视所有忽略规则（审计用）
python ci_guard.py . --only R01,R03                   # 只跑某几条
```

依赖：Python 3.8+、pyyaml。未装 pyyaml 时降级运行（只跑正则类规则，输出会标 `DEGRADED`）。

## 三条上线路径

1. **新仓**：直接把 `--strict` 挂进 CI，一次红就修。
2. **存量仓（tea / yg-gateway 这种情况）**：`--init-config` 把现有 36 条冻结成基线，之后只报**新增**。这是棘轮：不逼你先还完历史债，但禁止再欠新的。
3. **只想先看**：`--format=github` 出 annotations 贴 PR，别挡合并；观察两周再收紧成阻断。

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 无问题（或 SARIF 模式，语义在 SARIF 里） |
| 1 | 内部错误 |
| 2 | 参数错误 / 基线文件不存在 |
| 3 | 没收集到任何 workflow |
| 11 / 12 / 13 / 14 | 最高级别为 low / medium / high（`--strict` 一律 14） |

## persona：低置信不是删掉，是降档

| persona | 报什么 | 适合 |
|---|---|---|
| `regular`（默认） | 排除 low 置信，只留证据闭合的项 | 日常与 CI |
| `pedantic`（`--pedantic`） | 含 low（R02 管道、R07 整点 cron、R11 发布 needs） | 定期体检 |
| `auditor` | 全部，且配合 `--no-ignores` 看全貌 | 接手别人的仓时先审一遍 |

## 17 条规则

| ID | 级别 | 置信 | 判什么 | 出处 |
|---|---|---|---|---|
| R01 | FAIL | high | action 必须 pin 到 40 位 SHA；已 pin 的要有 `# vX.Y.Z` | AV.6 |
| R02 | WARN | low | 多行块有 shell 管道却无 pipefail（有 `-z`/`grep -q`/`\|\|` 兜底的不报） | AU.3、AV.13 |
| R03 | FAIL | high | Pages 部署 `cancel-in-progress: true`，或部署无 concurrency 组 | AV.5、AW.9 |
| R04 | WARN | medium | 顶层给内容类写权限，而文件里有多个 job | AW.7 |
| R05 | WARN | medium | 顶层与 job 级都没写 permissions | AW.7 |
| R06 | WARN | medium | Pages 部署无 `github.repository ==` 守卫 | AW.8 |
| R07 | WARN | low | `cron` 落在整点 | AW.9 |
| R08 | WARN | medium | 名字含 contract/契约 的检查只在 PR 触发 | AW.5 |
| R09 | WARN | medium | `@latest`、`pip install` 未钉 `==` | AU.9、AV.9 |
| R10 | FAIL | high | `${{ secrets.* }}` 直接插进 `run` | AU.10 |
| R11 | WARN | low | 非首个 job、名字像发布，却没有 `needs` | AU.6、AW.7 |
| R12 | FAIL | high | 嵌套 go module 未被任何 workflow 触及 | AW.3 |
| R13 | WARN | medium | 仓库没有任何 workflow | AV.2 |
| R14 | WARN | medium | 发布 paths 里的具体文件，PR 检查的 paths 里完全没有 | AW.8 |
| R15 | FAIL | high | `pull_request_target` 下 checkout 了 PR 的 head | AW.10 |
| R16 | FAIL | high | `permissions: write-all` | AW.7 |
| R17 | WARN | low | `self-hosted` runner 上跑 PR 触发的代码 | AV.10 |

R14 是上一版里唯一一条「把人工读数机械化」的规则：它在 open-code-review 上精确复现了 AW.8 记录的缺口——`install.sh` 与 `install.ps1` 出现在 `deploy-pages.yml` 的推送 paths 里，却不在 `pages-ci.yml` 的 PR paths 里，于是只改安装脚本时 PR 阶段没有任何页面检查。这条以前只能靠人逐份读出来。

每条规则的完整说明（症状 / 为什么是问题 / 怎么修 / 误报边界 / 实测样本）在 **`docs/RULES.md`**。finding 的 `url` 与 SARIF 的 `helpUri` 都指向 `tools/ci-guard/docs/RULES.md#rNN`，而不是白皮书章节——文档要跟规则一一对应，改规则的人才知道该改哪一页。

与 actionlint（36 类检查）、zizmor（34 条 audit）的逐条覆盖对照在 **`COVERAGE.md`**：7 条重叠、6 条三边都没有、3 条部分重叠。结论是三者判的不是同一件事——actionlint 管对错、zizmor 管安全、ci-guard 管判据，可以叠着用。

从 Forward Deployed Engineer 的视角看，这个产物对上了「在现场先证明无害、不逼客户还债、意见落在 PR 上、交付能被接手、能说清边界」五条，硬缺口是 adoption 为零——见 **`FDE-NOTES.md`**。

## 配置与忽略

`--init-config` 会在仓根生成 `.ci-guard.yml`（默认全开）与 `.ci-guard-baseline.json`。

```yaml
version: 1
persona: regular
rules:
  R07: {enabled: false}
  R11: {severity: FAIL}
ignore:
  R02:
    - ".github/workflows/ci.yml"
    - ".github/workflows/ci.yml:51"
```

单点忽略用注释，比配置文件轻：

```yaml
- run: |  # ci-guard: ignore[R02] 这条管道下游有断言兜底
    go tool cover -func=coverage.out | grep total:
```

注释对**所在行与下一行**生效，正好覆盖 `run: |` 与块首的关系。

## 接入 CI

```yaml
jobs:
  guard:
    uses: ./.github/workflows/ci-guard.yml
    with:
      strict: false
```

或不依赖任何 action，直接跑（最省）：

```yaml
- run: pip install pyyaml==6.0.3
- run: python tools/ci-guard/ci_guard.py . --baseline .ci-guard-baseline.json
```

SARIF 接 code scanning：

```yaml
- run: python tools/ci-guard/ci_guard.py . --sarif ci-guard.sarif || true
- uses: github/codeql-action/upload-sarif@b7b84b636b4f90c9b31da1bc5f72bfadd5b31410 # v3
  with:
    sarif_file: ci-guard.sarif
```

pre-commit（本地先挡一道）：

```yaml
- repo: local
  hooks:
    - id: ci-guard
      name: ci-guard
      entry: python tools/ci-guard/ci_guard.py .
      language: system
      pass_filenames: false
```

reviewdog 用法同理：把 `--format=github` 的输出喂给 reviewdog 的 `-f=github-annotations`，让意见落在 diff 行上。

## SARIF 校验（上传前的最后一道）

```bash
python ci_guard.py . --sarif ci-guard.sarif
python verify_sarif.py ci-guard.sarif
```

`verify_sarif.py` 用 `schema/sarif-2.1.0.json`（schemastore 官方副本，112 KB，随工具离线带着）做完整校验，不联网。这一步过，说明结构与 GitHub 服务端要的格式一致；`selftest.py` 里也跑同一套校验，规则改坏了会当场红。

**平台侧那一步的实测边界（2026-11-14）**：本机 `gh` 已登录（`qiuqianyi66`），但 `qiuqianyi66/yg-gateway`、`dsh-purge`、`tea-ceremony` 的 `/code-scanning/alerts` 全部返回 404——仓库侧没有启用 code scanning。所以拦住的不是 token，而是"没有可落地的仓"：要真验证，得先在某个仓的 Settings 里启用 Code scanning（公开仓可用默认 CodeQL），再 `gh api /repos/<o>/<r>/code-scanning/sarifs` 提交。

## 四仓实测（2026-11-14，0.3.0，pedantic 口径）

| 仓 | workflow | FAIL | WARN | 分布 |
|---|---|---|---|---|
| open-code-review | 14 | 0 | 15 | R02=2、R14=2、R17=11 |
| tea | 2 | 34 | 2 | R01=33、R02=1、R03=1、R06=1 |
| yg-gateway | 3 | 21 | 1 | R01=21、R09=1 |
| career-os（work） | 0 | 0 | 1 | R13=1 |

regular 口径下 OCR 剩 2 条（R02 与 R17 是 low 被降档，R14 的 2 条 medium 留下，0 FAIL）；tea 35 条、yg 22 条。

规则不是拍脑袋写的：第一版在 ocr 上报出 4 条 FAIL，逐条核对原文后确认全是误报（把 `pages: write` 当应下沉权限、把 `pages-ci` 当部署面、把首个 job 无 needs 当缺陷、把 jq 程序里的 `|` 当 shell 管道），全部改写判定后才达到「范本仓 0 FAIL」。**能在一份严谨的仓上不误报，是这套规则可用的前提。**

## 自测

```bash
python selftest.py
```

七项：R01–R17 在坏样本里全部命中（R13 由空仓单独验）、合规样本零命中、regular 确实隐藏 low、SARIF 字段断言、官方 SARIF 2.1.0 schema 校验、baseline 冻结后零残留。规则改动必须跑它——没有回归锁，规则会在「以为还生效」的状态里悄悄失效。

自测本身抓到过四个真 bug：YAML 1.1 把裸 `on:` 解析成布尔 `True`（导致依赖触发的 R08 永不命中）；按 `rule|file|detail` 去重会让基线一次冻结吞掉未来所有同类违规（已改成按实例编号的指纹）；我手误删掉一个坏样本时它立刻报「16/17 未覆盖」；以及 SARIF 校验段的变量名覆盖了坏样本仓路径（`bad` 被复用），当场炸成 TypeError——三个都在产品化之前，不是在用户环境里。

## 明确不判（写在这里，免得当成漏检）

- 工具零命中是否被当成失败：要读 shell 脚本本体，YAML 看不出来
- 覆盖率阈值是否合理、测试是否真的覆盖
- `paths` 与发布面是否**逐条对齐**（glob 覆盖语义判不了，例如 `site/**` 是否真覆盖 `install.sh`）。具体文件级的缺口已经机械化成了 R14，在 open-code-review 上复现出 `install.sh`、`install.ps1` 两条。
- job 内部命令顺序、缓存配了却没命中
- pin 的 SHA 是否真对应注释里的版本（要联网核；本工具不联网，也不带 token）

## 明确不做

- **不做 `--fix`**：命中处多是结构性判断（部署取消、权限分层），自动改 workflow 会动到人没读懂的地方。给修法文本，不给自动改。
- **不做 `--collect=actions`**：13 条规则都是针对 workflow 结构的，套到 `action.yml` 上会大面积空转。等有对应规则再加。

## 版本

0.3.2 — 17 条规则 + 独立规则文档 + 官方 SARIF 2.1.0 schema 离线校验（`verify_sarif.py`）+ persona / baseline / 配置 / inline 忽略 / GitHub annotations / 退出码分级。
