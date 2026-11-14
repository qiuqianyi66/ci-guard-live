# 逆向笔记：CI 检查器这类产品是怎么长成的（2026-11-14）

结论先说：三个成熟项目（actionlint / zizmor / OpenSSF Scorecard 的路数）都不是「规则越多越好」，而是把**规则之外的产品面**做厚。规则只是内核，真正决定能不能被企业装上的，是下面六件事。

## 一、上游产品的结构（一手文档，非印象）

### actionlint（rhysd/actionlint，GitHub Actions 静态检查器）

- **内核**：语法 / 表达式类型 / action 输入输出 / reusable workflow / shellcheck & pyflakes 集成 / 注入与硬编码凭据 / glob 与 cron 校验。它自己说「尽量多地发现错误，同时把误报压到最小」——这是可用的前提，不是客套。
- **配置可选**：`actionlint.yaml` 放 `.github/`，三块——自托管 runner 标签、仓库变量白名单、**`paths: {glob: {ignore: [正则]}}`**（按文件路径用正则忽略错误消息）。
- **上手降门槛**：`actionlint -init-config` 直接生成初始配置，不让用户手写第一份。
- **输出**：`file:line:col: 消息 [rule-id]`，附源码片段与 `^~~~` 指示位置。
- **集成面**：reviewdog、Problem Matchers、super-linter、pre-commit、VS Code、playground（WASM）、Docker、Go API。

### zizmor（zizmorcore/zizmor，CI/CD 安全审计）

- **输入**：单文件 / 本地目录 / 远程仓 slug（`owner/repo@ref`）/ stdin；`--collect=` 控制收集范围（workflows / actions / dependabot / pre-commit）。
- **运行模式**：offline / online / online-sans-audits，由 `ZIZMOR_OFFLINE`、`GH_TOKEN` 等环境变量自动推断，也可用 `--offline` 强制。
- **三档 persona**：
  - `regular`（默认）：高信噪比、可直接行动；
  - `pedantic`（`--pedantic` 别名）：额外报 code smell，例如非攻击者可控的模板展开；
  - `auditor`：全量，含很可能误报的项。文件明确说明 `self-hosted-runner` 一类审计**只在 auditor 出现**，因为它需要运行时上下文、天然可能误报。
  这条最有价值：**低置信规则不是删掉，而是降档到只有审计员才会看到的层**。
- **忽略**：inline `# zizmor: ignore[rule]`（可逗号分隔多条、可带解释；必须是 finding span 内的 YAML 注释，块字面量内部的注释无效），以及 `zizmor.yml` 的 `rules.<id>.ignore: [file / file:line / file:line:col]`；`--config`、`ZIZMOR_CONFIG`、`--no-ignores` 反向开关。
- **输出**：plain（cargo 风格，含 `置信度 → High` 注记）、JSON（**格式版本化**，`json` 是当前版别名，并注明它与 plain/SARIF 的行号 0-based/1-based 差异）、SARIF、**`--format=github` annotations**。文件自己写明了硬限制：单个 step 最多渲染 10 条 annotation，超出的只进日志。
- **退出码分级**：0 无问题 / 1 审计出错 / 2 参数错误 / 3 没收集到输入 / 11–14 按最高严重度（informational→high）。SARIF 模式不返回 11+；`--fix` 全部修完也不返回 11+（因为「需要行动」已经不成立）。
- **修复**：`--fix=safe|unsafe|all|unsafe-only`，in-place 改文件、尽量保持格式；unsafe 必须人工复核；远程输入不支持修复；`unpinned-uses` 检测离线、**修复需要联网取 SHA**。
- **过滤**：`--min-severity`、`--min-confidence`，复杂过滤交给 `jq`。
- **每条 finding 的元数据**：`ident`、`desc`、**`url`（指向该审计的文档锚点）**、`determinations`（confidence / severity / persona）、`ignored`、`fixes`（含 `disposition`）。

## 二、映射到 ci-guard 的差距表

| 产品面 | ci-guard 现状 | 上游做法 | 本次决定 |
|---|---|---|---|
| 上手成本 | 只能直接跑，34 条一屏红 | `-init-config` 生成初始配置 | 加 `--init-config`，同时生成 `.ci-guard.yml` 与 `baseline.json` |
| 存量仓落地 | 无（老仓永远红） | 未见内置棘轮 | **加 `--baseline`：只报新增，历史项冻结** |
| 噪音分层 | 只有 FAIL/WARN | 三档 persona，低置信降档 | 加 `confidence` 字段 + `--persona=regular/pedantic/auditor` |
| 精确忽略 | 无 | inline 注释 + 文件级配置 | 同构实现：`# ci-guard: ignore[R01]` + `rules.<id>.ignore: file:line` |
| 贴 PR | 只有文本/JSON/SARIF | `--format=github` annotations | 加，并在输出里写明 10 条硬限制 |
| 退出码 | 0/1 | 分级（3=无输入，11–14 按最高级） | 采用分级 |
| finding 元数据 | rule/level/file/line | + url / confidence / persona / fixable | 全部补齐 |
| 自动修复 | 无 | `--fix=safe/unsafe` | **不做**，理由见下 |
| 生态集成 | reusable workflow | pre-commit、reviewdog、super-linter、VS Code、Docker | README 补 pre-commit 与 reviewdog 用法；不做插件 |
| 缓存 | 无 | HTTP cache | 不需要：本工具不联网 |

## 三、明确不采纳的三件事

1. **不做 `--fix`。** 上游敢做，是因为它的修复单元小且可回滚（改一行 `uses:` 的 ref）。ci-guard 的规则命中处往往是结构性的（部署取消策略、权限分层），自动改 workflow 会动到用户没读懂的地方。可自动修的子集（R01 补版本注释）价值也很低。结论：提供修法文本，不提供自动改。
2. **不做联网校验 SHA 是否对应声明的版本。** 上游 `unpinned-uses` 的修复要联网，是因为它只判「有没有 pin」。我们要判「pin 的是不是那个版本」就必须访问 GitHub API，而本环境无 token 会被限流（已实测 403）。保持离线，把这条写进「明确不判」。
3. **不做 `--collect=actions`。** actionlint / zizmor 都覆盖 `action.yml` 本体；我们的 13 条规则全部针对 workflow 文件的结构（触发、并发、权限、部署面），套到 `action.yml` 上会大面积空转。等有了针对 action 的规则再加，不先搭空架子。

## 四、一条产品判断

zizmor 的 persona 与 actionlint 的 minimize-false-positive 说的是同一件事：**检查器的第一资产是「用户相信它」。** 一次误报的代价远大于漏报一条 WARN。所以规则进默认档的门槛应该是「证据闭合」，而不是「听起来有风险」——这也是本次把 R02/R07/R11 降到 `pedantic` 的原因。
