# 规则目录

每条规则一页。`ruleId` 与 finding、SARIF 里的 `ruleId` 完全一致，锚点就是 `#r01` 这样的形式。

可信度说明：`high` 的证据是闭合的，见到就修；`medium` 需要看一眼上下文再判；`low` 是 code smell，只在 `--pedantic` 里出现。级别 `FAIL` / `WARN` 只影响默认退出码，不影响判定本身（`--strict` 下 WARN 也算失败）。

---

## R01 action 未 pin 到 40 位 SHA

**级别** FAIL / high　**出处** AV.6

**症状**：`uses: actions/checkout@v4`、`uses: docker/build-push-action@v6` 这类 tag 引用。

**为什么是问题**：tag 是可被上游改写的可变引用。同一个 `@v4` 今天与明天可能是两份代码，而 CI 的结论会跟着一起变——你 pin 的其实是"信任上游永远不干这事"。2025 年 tj-actions 事件就是这么发生的：一个 tag 被改写，所有引用它的仓同时执行了陌生代码。

**怎么修**：`uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`。SHA 用 `git ls-remote https://github.com/<owner>/<repo> refs/tags/v4` 取，不要手敲。批量场景用 renovate 的 `pinDigests: true` 让机器人维护。

**误报边界**：本地 action（`uses: ./path`）不报——它本来就在仓内，不存在上游改写。`docker://` 镜像引用不报，镜像的不可变性靠 digest 保证，是另一套机制。

**实测**：tea 33 处、yg-gateway 21 处，open-code-review 0 处。

---

## R02 多行 shell 块有管道却没有 pipefail

**级别** WARN / low　**出处** AU.3、AV.13

**症状**：`run: |` 块里出现 `cmd | grep`、`cmd | head`，而块首没有 `set -euo pipefail`。

**为什么是问题**：`a | b` 的退出码默认是**最后一个**命令的。`go test ./... | tee log` 里测试失败会被 tee 的成功退出码盖掉，CI 一路绿到底。这个 bug 的恶劣之处是它只在失败路径上出现——平时看不见，出事时把红事变绿。

**怎么修**：块首加 `set -euo pipefail`。

**误报边界**（这条收窄过两轮，现在的判定是"真管道 + 无兜底"）：
- 管道下游有断言兜底的不报：`test -s`、`test -n`、`grep -q`、`-z "$..."`、结尾的 `|| exit`
- 管道在程序内部而非 shell 的不报：`jq '... | ...'`、`awk 'BEGIN {exit} ...'` —— 第一版把 jq 字符串里的 `|` 当成了 shell 管道，在 open-code-review 上一次报了 4 条假 FAIL
- 单行 `run:` 不报：单行命令失败即整步失败，语义本来就对

**实测**：open-code-review 24 条噪音压到 2 条真管道（`acp-ci.yml:106`、`ci.yml:87`，两处下游都有阈值断言）。

---

## R03 Pages 部署会被后续推送取消

**级别** FAIL / high　**出处** AV.5、AW.9

**症状**：
```yaml
concurrency:
  group: pages
  cancel-in-progress: true
```

**为什么是问题**：取消一个跑到一半的部署，代价不是"重跑一次"，而是站点可能停在一个谁也不认识的状态：环境已切、artifact 已传、但发布的指针没动。用户看到的是半新半旧的页面。白皮书把这条列为硬判据，不是风格偏好。

**怎么修**：删掉 `cancel-in-progress`（缺省即 false），或写 `${{ github.event_name == 'pull_request' }}` —— 只在 PR 侧取消，部署侧永不取消。

**误报边界**：只有部署面才判。构建/测试 job 的 `cancel-in-progress: true` 是正确实践（省 runner），不报。判定依据是"有 pages 权限或调用了 deploy-pages / upload-pages-artifact"。

**实测**：tea `deploy-pages.yml:15` 一处真缺陷；open-code-review 与 yg-gateway 的发布链都写的是 false 或只在 PR 取消。

---

## R04 顶层给内容类写权限，文件里却有多个 job

**级别** WARN / medium　**出处** AW.7

**症状**：`permissions: contents: write` 写在文件顶层，下面有 build、test、deploy 三个 job。

**为什么是问题**：顶层权限对整个文件的每个 job 生效。构建 job 只需要读代码，却也拿到了写权限——任何一步被注入（一条被投毒的依赖、一个拼错的 `curl | sh`）都能改仓库。权限应该按 job 给，能不给就不给。

**怎么修**：顶层只留 `contents: read`，把写权限挪到真正需要的那一个 job 上。

**误报边界**：单 job 的文件不报（没有下沉空间）。`pages: write`、`id-token: write` 不算"内容类写权限"——它们是 Pages 部署的必需品，曾被我第一版误判为应下沉，在 open-code-review 上制造了假 FAIL。

**实测**：四仓当前 0 命中（这条是预防性的）。

---

## R05 顶层与 job 级都没有 permissions

**级别** WARN / medium　**出处** AW.7

**症状**：workflow 里完全没有 `permissions:` 键。

**为什么是问题**：不写不等于没有。默认 token 权限由仓库设置决定，很多组织仍是"全部可写"。等于把权限交给一个你看不见的仓库开关，而不是写在代码里可评审的声明。

**怎么修**：顶层加 `permissions: contents: read`，需要的地方按 job 提升。

**误报边界**：只要顶层或任一 job 写了 permissions 就不报——说明作者想过这件事了，写多写少是判断力问题，不是遗漏。

**实测**：tea `ci.yml` 首版命中，后确认它有 job 级 permissions，判定已相应收紧。

---

## R06 Pages 部署没有 fork 守卫

**级别** WARN / medium　**出处** AW.8

**症状**：`on: push` 触发 Pages 部署，但 job 上没有 `if: github.repository == '<owner>/<repo>'`。

**为什么是问题**：fork 之后推自己的 main 会往自己的 Pages 发东西，通常无害。真正的问题是复制：一份没有守卫的部署 workflow 被复制到组织仓或模板仓后，任何人 fork 都能触发往生产环境发内容。守卫就是那道分界线。

**怎么修**：deploy job 加 `if: github.repository == '<owner>/<repo>'`。

**误报边界**：只在 Pages 部署面判。普通构建 job 不需要这条。

**实测**：tea 1 处（`deploy-pages.yml`）；open-code-review 的两个 job 都带守卫，是范本。

---

## R07 cron 落在整点

**级别** WARN / low　**出处** AW.9

**症状**：`- cron: '0 0 * * *'`、`- cron: '0 6 * * 1'`。

**为什么是问题**：GitHub 的定时任务是全平台共享队列的，整点是所有仓同时挤进来的时刻，延迟可能从几分钟到几十分钟。一个"每天 0 点跑"的任务，实际可能 0:40 才启动。对时效有要求的任务（对账、日报）会因此错位。

**怎么修**：错开到非整点，`39 6 * * 5` 比 `0 6 * * 5` 稳得多。

**误报边界**：只判分钟位为 0 且小时位是具体数字的表达式。`*/15` 这类间隔执行的、以及 `*` 通配的不报——它们本来就不追求某个精确时刻。

**实测**：四仓当前 0 命中。

---

## R08 名字含不变量语义的检查只在 PR 触发

**级别** WARN / medium　**出处** AW.5

**症状**：workflow 叫 `plugin-contract.yml` / `契约检查`，但只有 `pull_request` 触发。

**为什么是问题**：不变量（契约）的价值在于"任何时候都为真"。只在 PR 上验，等于 main 上的状态没人守——有人直接 push、或 rebase 合并绕过了 PR，不变量就破了，且没人知道。

**怎么修**：加 `push: branches: [main]` 触发，或把检查挂到 pre-commit / 定时任务上做兜底。

**误报边界**：按名字判，所以只认明确的语义词（contract、契约、invariant、不变量）。名字里带这些词的普通 workflow 会被误报，可以用 inline 忽略写清理由。

**实测**：四仓当前 0 命中。

---

## R09 依赖用 @latest 或 pip 未钉版本

**级别** WARN / medium　**出处** AU.9、AV.9

**症状**：`go install ...@latest`、`pip install requests`（无 `==`）。

**为什么是问题**：构建工具自己浮动，意味着"扫出什么"会随上游发版变化——同一天重跑两次可能结论不同。对漏洞扫描器尤其致命：你无法回答"上次那个 CVE 为什么这次没报"。

**怎么修**：`@v1.6.0`、`requests==2.32.3`。

**误报边界**：`pip install -e .`、`pip install -r requirements.txt` 不报（版本固定在文件里）；`npm i` 不在此规则范围。

**实测**：yg-gateway `release.yml:78` 一处。

---

## R10 secrets 直接插值进 run

**级别** FAIL / high　**出处** AU.10

**症状**：`run: echo ${{ secrets.TOKEN }}`，或把 secret 拼进命令行参数。

**为什么是问题**：`${{ }}` 是**在 shell 执行之前**做文本替换的。secret 一旦进了命令行，就会出现在进程列表、日志、以及任何 `set -x` 打开时的追踪里。GitHub 的掩码是尽力而为的（只匹配完整字符串），拼接、切片、base64 之后就掩不住了。

**怎么修**：改用环境变量——`env: TOKEN: ${{ secrets.TOKEN }}`，脚本里读 `"$TOKEN"`。环境变量不会被写进命令行。

**误报边界**：`env:` 里引用 secrets 不报，那正是推荐写法。`with:` 里传 secrets 给官方 action 不报（action 内部如何用是它的事）。

**实测**：四仓当前 0 命中。

---

## R11 发布 job 没有 needs

**级别** WARN / low　**出处** AU.6、AW.7

**症状**：`publish` / `deploy` / `release` 名字的 job，没有 `needs:`，与其他 job 平行跑。

**为什么是问题**：没有 needs 就是在赌——赌构建先完成、赌测试先通过。并行 job 的完成顺序不保证，发布可能拿着半成品上去，且发布成功后测试才红，回滚要人工做。

**怎么修**：`needs: [build, test]`，让顺序变成声明而不是运气。

**误报边界**：**第一个 job 不报**——第一版把 open-code-review release workflow 里的首个预演 job 判成缺陷，读过原文才确认它本来就该排在最前，无 needs 是正确的。只判非首 job，且名字要像发布。

**实测**：四仓当前 0 命中。

---

## R12 嵌套 go module 没有被任何 workflow 触及

**级别** FAIL / high　**出处** AW.3

**症状**：仓库根有 `go.mod`，某个子目录（如 `acp/`）也有独立 `go.mod`，但没有任何 workflow 提到那个目录。

**为什么是问题**：Go 的多模块布局里，根 module 的 `go test ./...` **不会**进入子 module。子模块的代码因此完全不在 CI 里——它坏了没人知道，直到有人单独构建它。这是"看起来有 CI，实际有一半没覆盖"的典型。

**怎么修**：加一个 `working-directory: acp` 的 job，或加 `go test ./acp/...` 到矩阵里。

**误报边界**：只看 workflow 文本里是否出现该目录的相对路径。用变量拼出来的路径（`matrix.module`）可能漏判——这是本规则已知的盲区。

**实测**：四仓当前 0 命中（open-code-review 有正确的 matrix 覆盖）。

---

## R13 仓库没有任何 workflow

**级别** WARN / medium　**出处** AV.2

**症状**：`.github/workflows/` 不存在，或里面是空的。

**为什么是问题**：没有 CI 意味着全部检查靠"人记得跑"。人的记忆是不可靠的，尤其是在赶时间的周五下午。

**怎么修**：最小起步不是把全部脚本搬上去，而是先有一条 `on: [push, pull_request]` 的 lint + test。

**误报边界**：不是每个仓都需要 CI——纯文档仓、模板仓可以忽略。

**实测**：career-os（work 目录）只有本地 `verify_harness.py` 与若干 `audit-*.cjs`，没有任何 workflow。

---

## R14 发布路径里的文件，PR 阶段没有检查覆盖

**级别** WARN / medium　**出处** AW.8

**症状**：`deploy-pages.yml` 的 `push.paths` 里有 `install.sh`，但所有 `pull_request.paths` 里都没有它。

**为什么是问题**：发布面比检查面宽。只改 `install.sh` 时，PR 阶段没有任何检查会跑——要等合并进 main、部署触发后才由下游断言兜住，那时已经晚了半步。这类缺口不会自己暴露，只能靠交叉比对 paths 发现。

**怎么修**：把该文件加进对应检查 workflow 的 `pull_request.paths`，或在 workflow 里写明为什么不加。

**误报边界**：只比对**具体文件**（不含 `*` / `?` / `[` 通配），glob 的覆盖语义（`site/**` 是否覆盖 `install.sh`）判不了。也只在 Pages 发布面判。这条规则的来源是白皮书 AW.8 的一处人工发现，机械化之后在 open-code-review 上精确复现出 `install.sh`、`install.ps1` 两条——**规则不是凭空设计的，是先有人读出了问题，再回头把它写成判据。**

**实测**：open-code-review 2 条（`install.sh`、`install.ps1`）。

---

## R15 pull_request_target 下 checkout 了 PR 的 head

**级别** FAIL / high　**出处** AW.10

**症状**：
```yaml
on: pull_request_target
steps:
  - uses: actions/checkout@<sha>
    with:
      ref: ${{ github.event.pull_request.head.sha }}
```

**为什么是问题**：`pull_request_target` 在 base 仓的上下文里运行，**拿得到 secrets 和写权限**；而 checkout PR head 等于把攻击者的代码放进来。两者一组合就是标准的提权链：攻击者提一个 PR，改一行代码，你的 CI 带着 token 跑他的代码。这是安全公告里出现频率最高的 GitHub Actions 配置。

**怎么修**：只 checkout base。确实需要分析 PR 代码时，用 `pull_request` 事件（无 secrets），或用 `pull_request_target` 只读 diff 文本、不执行。

**误报边界**：`pull_request_target` 本身不报——合法用法是打标签、评论、读 diff。只有同时 checkout 了 head 才报。引用 `github.event.pull_request.head.label` 这类元数据不算。

**实测**：四仓当前 0 命中。

---

## R16 permissions 写了 write-all

**级别** FAIL / high　**出处** AW.7

**症状**：`permissions: write-all`。

**为什么是问题**：把 token 的全部写权限一次发出去——内容、包、issue、PR、workflow 全在。任何一步被注入（一个被投毒的依赖、一条 `curl | sh`）都能改仓库、发版本、甚至改其他 workflow。这是"省事"换来的最贵的一种省事。

**怎么修**：改成显式列表，顶层 `contents: read`，需要的 job 单独提升。

**误报边界**：没有。`write-all` 没有任何正当使用场景。

**实测**：四仓当前 0 命中。

---

## R17 自托管 runner 上跑 PR 触发的代码

**级别** WARN / low　**出处** AV.10

**症状**：`runs-on: self-hosted` 且 workflow 有 `pull_request` 触发。

**为什么是问题**：自托管机器通常持有内网凭据、持久缓存、可信网络位置。PR 代码在那里跑，等于把边界的钥匙交给任何能提 PR 的人。更糟的是持久化：上一个 job 留下的文件、token、缓存，下一个 job 还在。

**怎么修**：PR 用 GitHub 托管 runner；自托管只跑 main / tag 上的可信代码。做不到就加审批（environment + required reviewers）。

**误报边界**：**这条低置信是有意的。** 很多团队（包括 open-code-review）是有意把 PR 放在自托管的，通常因为成本或特殊硬件。工具判不了"这台机器上有没有敏感凭据"，所以只标 low、只在 `--pedantic` 下出现，让人自己判断。

**实测**：open-code-review 11 条（该仓确实把 PR 跑在自托管上，是已知的设计选择）。
