# 与 actionlint、zizmor 的覆盖对照

数据来源：`actionlint` 的 `docs/checks.md` 目录（36 类检查）、`zizmor` 的 `docs.zizmor.sh/audits` 目录（34 条 audit），2026-11-14 抓取。zizmor 侧只精读了前四条正文（adhoc-packages、anonymous-definition、archived-uses、artipacked），其余按名称归类——凡是没读过正文的判断，下面都标了"按名称"。

## 三者不是同一类工具

| | 判什么 | 一句话 |
|---|---|---|
| actionlint | workflow **本身对不对** | 语法、类型、表达式、job 依赖合法性；有 shellcheck / pyflakes 集成，把静态分析嵌进 `run:` |
| zizmor | 配置**有没有被攻击面利用** | 供应链、提权、注入、凭据泄漏；面向安全审计，多数规则带 auto-fix |
| ci-guard | 工程**判据有没有被破坏** | 部署语义、权限分层、发布顺序、路径覆盖；判据来自白皮书 AV–AW，不是安全公告 |

这个定位差不是文字游戏：**R03（部署可取消）在 actionlint 和 zizmor 里都不存在**——它不是安全漏洞，也不会让 YAML 报错，它只是让站点停在一个半新半旧的状态。同类还有 R08、R11、R12、R13、R14。

## 我们 17 条 → 它们的对应

下表里 zizmor 侧只有 `adhoc-packages`、`unpinned-uses` 等前四条读过正文，其余对应关系均为**按名称归类**的判断，可能与实际判据有偏差；actionlint 侧的依据是 checks.md 的目录与已读到的正文片段。

| ci-guard | actionlint | zizmor | 关系 |
|---|---|---|---|
| R01 未 pin SHA | 无（outdated popular actions 是版本提醒，不是 pin） | `unpinned-uses` | **重叠**，zizmor 更细（按 policy 分级） |
| R02 管道无 pipefail | `shellcheck integration`（全量嵌入，覆盖更广） | 无 | **被覆盖**，actionlint 更强 |
| R03 部署可取消 | 无 | 无（`concurrency-limits` 是限并发数，不是取消语义） | **独有** |
| R04 顶层写权限 | `permissions`（只查语法与未知权限名） | `excessive-permissions` | **重叠** |
| R05 无 permissions | `permissions` | `undocumented-permissions` | **重叠** |
| R06 Pages fork 守卫 | 无 | `dangerous-triggers` 部分（按名称） | 部分重叠 |
| R07 整点 cron | `CRON syntax`（只查语法） | 无 | **独有** |
| R08 不变量只 PR | 无 | 无 | **独有** |
| R09 @latest | 无 | `unpinned-tools`、`adhoc-packages`（npm/gem） | **重叠** |
| R10 secrets 进 run | 无 | `template-injection` 部分 | 部分重叠 |
| R11 发布 job 无 needs | `job dependencies`（只查指向不存在的 job） | 无 | **独有** |
| R12 嵌套 module 无覆盖 | 无 | 无 | **独有** |
| R13 无 workflow | 无 | 无 | **独有** |
| R14 发布路径缺口 | `glob filter pattern`（只查 glob 语法） | 无 | **独有** |
| R15 pr_target + PR head | 无 | `dangerous-triggers` | **重叠** |
| R16 write-all | `permissions` | `excessive-permissions` | **重叠** |
| R17 自托管跑 PR | `runner labels`（只查标签合法性） | `self-hosted-runner` | **重叠**，zizmor 按名称看更宽 |

净结果：**7 条与它们重叠（其中 R02 被 actionlint 更强地覆盖），6 条是三边都没有的工程判据，3 条部分重叠。**

## 它们有、我们没有：四类，各自的理由

**A. 语法与类型（actionlint 主体，约 20 类）**
未知键、缺必填键、空 mapping、mapping 值类型、`${{ }}` 语法与类型、上下文与内置函数、steps/matrix/needs 上下文类型、比较运算类型、事件名校验、matrix 值、runner 标签、`uses` 格式、本地/流行 action 的 inputs、shell 名、job/step id 唯一性、环境变量名、可复用 workflow、id 命名规范、上下文可用性、已弃用命令、恒真 `if`、action metadata 语法。

**不做的理由**：这类检查的正确性依赖 GitHub 侧的类型定义，需要持续跟进平台变化。自己重写等于造一个更差的 actionlint。**正确做法是两个都装**，分工明确。

**B. 需要联网或漏洞库（5 条）**
`impostor-commit`、`stale-action-refs`、`known-vulnerable-actions`、`archived-uses`、`typosquat-uses`。

**不做的理由**：本环境 `api.github.com` 无 token 时 403，且漏洞库需要持续同步。zizmor 在做，重复造没有边际价值。

**C. 需要跨步骤数据流分析（5 条）**
`template-injection`、`github-env`、`obfuscation`、`insecure-commands`、`artipacked`。

**不做的理由**：这些要追踪"哪个不可信值在哪个步骤被拼进哪条命令"，本质是污点分析。用单文件正则硬做，误报会高到没法用——这正是我第一版 R02 在 open-code-review 上误报 4 条的原因。**边界清楚地说不做，比含糊地做一半好。**

**D. 组织策略类（4 条）**
`dependabot-cooldown`、`dependabot-execution`、`github-app`、`secrets-inherit`、`forbidden-uses`。

**不做的理由**：这些面向"组织允许用什么"，不是白皮书附录 AV–AW 的工程判据。属于平台治理，不属于这个工具的职责。

## 该装几个

- 只关心"workflow 写错了没有" → actionlint 一个够了。
- 只关心"配置会不会被打" → zizmor 一个够了。
- 关心"白皮书那套工程判据有没有被破坏"（部署可取消、发布顺序、路径覆盖、嵌套模块没测试）→ 只有 ci-guard 会报。

三者可以叠着用：actionlint 管对错，zizmor 管安全，ci-guard 管判据。三者都不报重叠告警，因为判的是不同的东西。
