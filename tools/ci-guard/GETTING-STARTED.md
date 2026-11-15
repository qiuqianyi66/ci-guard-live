# 从零到第一个门禁：30 分钟

写给第一次接触 GitHub Actions 的人。每一步都有命令、预期输出和失败时怎么办。不需要你先懂 CI。

---

## 0. 你需要什么

- 一个 GitHub 账号
- 一个仓库（只有一个 README 也算）
- 电脑上装了 Python 3.8 以上（`python --version` 能看到版本号就行）

不需要：服务器、Docker、付费账号。

---

## 1. 先看懂一个 workflow（5 分钟）

GitHub Actions 的 workflow 就是一个 YAML 文件，放在 `.github/workflows/` 里。它回答三个问题：**什么时候跑、在哪台机器跑、按顺序做什么。**

```yaml
name: demo

on:                    # 什么时候跑
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest    # 在哪台机器跑
    steps:                    # 按顺序做什么
      - uses: actions/checkout@v4
      - run: echo "hello"
```

两个词必须记住：

- `uses:` 引用别人写好的动作（action），比如 checkout 就是把你的代码拉到机器上。
- `run:` 直接执行一条 shell 命令。

**新手第一个认知**：`uses: xxx@v4` 里的 `v4` 是一个标签，不是固定代码。上游可以随时把 `v4` 指向另一份代码。所以生产环境要写死 40 位 SHA，这就是本工具的第 1 条规则。

---

## 2. 在本地跑一次（3 分钟）

```bash
git clone https://github.com/qiuqianyi66/ci-guard-live
cd ci-guard-live
pip install pyyaml
python tools/ci-guard/ci_guard.py .
```

预期：屏幕上列出几条问题，每条形如

```
FAIL[H] R01  .github/workflows/demo.yml:12
    uses: actions/checkout@v4 — 第三方 action 必须 pin 到不可变 SHA
    why: tag 可被上游改写，同一 tag 今天与明天可能是两份代码
    fix: 改为 @<40 位 commit SHA>，并在同行留 # vX.Y.Z 注释
```

三个字母要认识：`H` = high（一定要改），`M` = medium（该改），`L` = low（看情况）。退出码 0 = 干净，14 = 有 FAIL。

**卡住时**：如果报 `ModuleNotFoundError: yaml`，说明 pip 装到了另一个 Python 里，用 `python -m pip install pyyaml`。

---

## 3. 接进自己的仓（5 分钟）

1. 把 `tools/ci-guard/` 整个目录复制到你自己的仓库（主程序 29 KB；只留运行必需四件约 152 KB，整个目录含文档与演示视频约 586 KB，纯 Python，无其他依赖）。
2. 新建 `.github/workflows/ci-guard.yml`：

```yaml
name: ci-guard
on: [push, pull_request]
permissions:
  contents: read
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - run: pip install pyyaml==6.0.3
      - run: python tools/ci-guard/ci_guard.py .
```

3. 推一次，去 Actions 页面看。

**这时候它多半是红的。这是正常的，也是必须看到的**——你要先知道自己的存量有多少。

---

## 4. 冻结存量（2 分钟）

红一片没人会修，团队第一件事就是把门禁删掉。所以第二步不是修，是**先冻结**：

```bash
python tools/ci-guard/ci_guard.py . --init-config
```

它会生成 `.ci-guard-baseline.json`，把当前所有问题记成一份"欠条"。然后把 workflow 最后一行改成：

```yaml
      - run: python tools/ci-guard/ci_guard.py . --baseline .ci-guard-baseline.json
```

再推一次，CI 变绿。

**理解棘轮**：baseline 不是"豁免名单"，是"存量清单"。你修好一条，那条指纹就再也匹配不上，等于自动消失；但新犯的同类问题会单独被抓住。所以这个门禁只会越来越严，不会越来越松。

---

## 5. 修一条，亲眼看见它收紧（10 分钟）

挑最简单的一条：打开被点名的 workflow，把

```yaml
cancel-in-progress: true
```

改成 `false`（假设它挂在一个部署 job 上）。重跑：

```bash
python tools/ci-guard/ci_guard.py . --baseline .ci-guard-baseline.json
```

输出里的"被忽略"数字会少 1。这就是你要的反馈——**修一条，门就紧一格**。

---

## 6. 新手最容易踩的六个坑

1. **`on:` 被当成布尔值**。YAML 1.1 会把裸写的 `on:` 解析成 `True`，程序里读 `wf["on"]` 会拿到空。本工具踩过这个坑，代码里对 `True` 做了回退。
2. **把 baseline 当豁免**。它不是"这些不用管"，是"这些先记账、不许再新增"。写成豁免，三个月后你会得到一份没人看的名单。
3. **pin 了 tag 就以为安全**。`@v4` 和 `@11bd719...` 是两件事，前者随时可变。
4. **误报直接改规则**。先读原文再改。我们第一版在成熟仓库报了 4 条，逐条读原文后发现全是误报——不改判定，规则就会被当成噪音关掉。
5. **一上来用 pedantic**。它会把 low 级别的也报出来（自托管 runner、cron 整点），新手容易被淹没。先用默认 regular。
6. **私有仓等 code scanning 面板**。那个要付费的 Advanced Security。本工具的交付方式是 PR 拦截 + SARIF 文件，不依赖面板。

---

## 7. 接下来读什么

- `docs/RULES.md`：17 条规则逐条，每条都有症状、为什么、怎么修、误报边界
- `COVERAGE.md`：和 actionlint、zizmor 的对照，搞清楚它判的不是同一件事
- 真实仓的四次运行记录：`ADOPT.md`

**一句话记住**：门禁的价值不在"能查出多少问题"，在"团队愿意一直留着它"。
