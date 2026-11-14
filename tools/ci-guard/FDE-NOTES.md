# FDE 视角：这个产物对上了什么，还差什么

## FDE 是什么

FDE（Forward Deployed Engineer，前沿部署工程师）是把大厂 AI 模型部署进客户真实生产环境、并对最终业务结果负责的工程师。Palantir 在 2000 年代中期发明这个岗位，OpenAI、Anthropic、Sierra 现在大量招。OpenAI 的 JD 把职责写成 "owning discovery, technical scoping, system design, build, and production rollout"，把成功标准写成 production adoption 与可量化的工作流影响——**不是 demo 成功，是被用起来**。Anthropic 的 Applied AI 岗还明确要求交付 MCP servers、sub-agents、agent skills 这类"会在生产工作流里跑的技术资产"。

能力模型可以拆成五条：扎实工程、在混乱不完备的现实约束里找到可行方案、直接进代码、把现场缺口反馈回平台、以及让东西离场后还能活着。

## 已经对上的五条

### 1. 在别人的环境里，先证明自己无害

FDE 进场第一件事不是改造，是理解。ci-guard 的做法是先在 open-code-review 这个范本仓上校准：第一版报了 4 条 FAIL，逐条读原文后确认全是误报（把 `pages: write` 当应下沉权限、把 jq 里的 `|` 当 shell 管道……），改判定才做到 0 FAIL。**一个会在客户仓上误报的工具，客户第二天就会把它关掉。**

### 2. 不逼客户先还完历史债

tea 有 34 条存量问题。直接开阻断等于立刻红一片，然后被人关掉——这是检查器最常见的死法。`--init-config` 把它们冻结成基线，CI 只报新增：这是棘轮，不是清零。客户的历史债不是你的 KPI。

### 3. 意见要落在人正在看的地方

`--format=github` 把告警变成 PR diff 行上的 annotations，而不是让人翻日志文件。Anthropic 的 FDE 职责里有"和客户工程团队做 code review"——工具得出现在他们已经在看的地方。

### 4. 交付物要能被下一个人接手

README 讲怎么跑，`docs/RULES.md` 每条规则一页（症状 / 为什么 / 怎么修 / 误报边界 / 实测），`COVERAGE.md` 说清与 actionlint、zizmor 的边界，`selftest.py` 让人改规则时知道自己没弄坏东西，SARIF 用官方 schema 校过。FDE 离场后东西得继续活着，否则就是"顾问走了，代码烂了"。

### 5. 能说清"不做什么"

明确不判（工具零命中是否算失败、覆盖率阈值、SHA 是否对应版本）与明确不做（`--fix`、`--collect=actions`）都写在文档里，每条带理由。在客户面前，**能说清边界的人比什么都能做的人可信**。

## 还差三条，而且第一条是硬缺口

1. **没有真的接进任何仓的 CI。** 工具能跑，但 adoption 是零。按 OpenAI 那句 "success is production systems and sustained adoption"，现在只能算 demo。tea 与 yg-gateway 你禁止改动，所以这一步停在"提供接入文件"。
2. **没有一页纸的价值说明。** FDE 要能对客户讲"修 R03 这一行，避免的是什么"。现在只有四仓体检报告，没有 ROI 口径：部署被取消一次，代价是站点停在半新半旧的状态多久、谁去收拾。
3. **没有应急路径。** 三条上线路径写了（冻结 → 观察 → 收紧），但没写"如果工具误报挡住了 merge，5 分钟内怎么关掉"：重冻结基线、或把 job 改成 `continue-on-error: true`、或直接删那一步。

## 一句话

这个产物在 FDE 方向能讲的不是"我写了个检查器"，而是"我把一套只能被读的规范，做成了在三个真实仓上零误报、有棘轮、有文档、有回归锁的门禁，并且我知道它离 production adoption 还差哪一步"。

知道差哪一步，大概就是 FDE 和普通工程师的区别。

---

来源：腾讯云开发者社区《今天我来谈谈 FDE 工程师是什么》（2026-08）、hk.ai《前线引擎：FDE 与 AI 原生组织的进化》（2026-10）、OpenAI Forward Deployed Engineer JD（2026-07）、Anthropic Applied AI FDE 岗位说明（经腾讯云 2026-06 文章转述）、AgenticCareers《What Is a Forward Deployed Engineer?》（2026-04）、北京日报《年薪百万，招聘需求涨 42 倍》（2026-06）。
