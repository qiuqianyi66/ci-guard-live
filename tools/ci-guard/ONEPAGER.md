# 一页纸：ci-guard 是什么，值不值得接

## 一句话

把《企业级 AI Native 项目开发全流程白皮书》附录 AV–AW 的 CI 判据，变成一条命令能跑、能接进流水线、能被下一个人接手的门禁。17 条规则，29 KB 单文件，零网络依赖，扫描不到 1 秒。

## 它防的是什么（三个真实命中）

**部署被后续推送取消。** tea 的 `deploy-pages.yml` 写的是 `cancel-in-progress: true`。取消一次跑到一半的 Pages 部署，代价不是"重跑一次"，是站点停在一个谁也不认识的状态：环境已切、artifact 已传、发布指针没动。用户看到半新半旧的页面，谁去收拾说不清。

**安装脚本改完没有任何检查。** open-code-review 的 `install.sh`、`install.ps1` 只出现在发布 workflow 的 push paths 里，PR 检查的 paths 里没有。也就是说，只改安装脚本时，PR 阶段零检查，问题要等合并进 main、部署触发后才暴露。这条以前只能靠人逐份读 14 个文件、交叉比对 paths 才发现。

**权限一次给满。** `permissions: write-all` 或顶层 `contents: write` 配多个 job：构建 job 只需要读代码，却也拿到了写权限。任何一步被注入就能改仓库。

## 成本

| | |
|---|---|
| 体积 | 主程序 29 KB；运行必需四件（含 110 KB 的 SARIF schema）约 152 KB；含文档与演示视频约 586 KB |
| 依赖 | Python 3.8+，pyyaml 可选（缺了降级为 DEGRADED，正则类规则照跑） |
| 接入 | 复制目录 → `--init-config` 冻结存量 → 加 4 行 workflow，实测 5 分钟内 |
| 运行 | 14 份 workflow 的仓，不到 1 秒 |
| 误报 | 先在 open-code-review 上校准到 0 FAIL 才拿出去用（第一版 4 条全是假报，逐条读原文改判定） |

## 代价与边界

**它不解决问题，只指出问题。** 明确不做 `--fix`：命中处多是结构性判断（部署取消、权限分层），自动改 workflow 会动到人没读懂的地方。给修法文本，不给自动改。

**它判不了的事写清楚了**：工具零命中是否被当成失败、覆盖率阈值是否合理、glob 覆盖语义、pin 的 SHA 是否对应注释版本。这些要读 shell 或联网，YAML 里看不出来。

**它不是 actionlint 的替代品。** actionlint 管语法与类型对不对，zizmor 管配置会不会被打，ci-guard 管工程判据有没有被破坏。三者判的不是同一件事，可以叠着用——逐条对照在 `COVERAGE.md`。

## 谁该用

多仓、有多模块、有 Pages 部署或发布链、CI 已经有但不是自己写的（接手别人的仓）——这四类场景收益最直接。单文件小仓只需要 actionlint。

## 现在到哪一步

已经接进一个真实仓：`qiuqianyi66/ci-guard-live`（private）。`guard` job 抓到 `demo.yml` 的两处问题，annotations 落在该文件第 1 行（warning）与第 12 行（failure），`exit 14` 让 job 在 8 秒内失败。**adoption 从 0 变成 1，闭环成立。**

下一步是把同样的接入复制到有存量债的仓（tea 34 条、yg-gateway 21 条），用 `--baseline` 先冻结再收紧。
