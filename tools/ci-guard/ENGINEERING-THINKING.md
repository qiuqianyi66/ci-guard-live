# 工程化思维：让规矩不靠人也能成立

**写给不写代码的人。** 论文、活动策划、社团管理、实习周报，都能用。

---

## 一句话把我问住了

我花一个月写了一份 288 页的项目规范，15 章、47 个附录、244 张表。自我感觉良好。

有人翻了两页，抬头问我：

> **"这些东西只能被读，不能被安装吗？"**

我当场没答上来。因为我心里清楚：这份文档里每一条"必须""禁止""应当"，最终都靠**人记得住**。人一忙就忘，一累就通融，一换人就没了。

那一刻我意识到，我做的不是制度，是一份**愿望清单**。

后来我把里面 17 条能判对错的条款，写成了一个会在别人提交时自动说"不"的程序。接进自己的三个仓，扫出 55 条 FAIL，其中一处是"部署会被新提交打断"——而这条恰好违反我自己写的规范。

这篇文章讲的就是那中间的一步：**怎么把"要求"变成"不靠人也成立"的机制。**

不需要你会写代码。会用 Word、会交作业就行。

---

## 一、先分清两个词：规范 和 门禁

这两个词天天被混用，但它们差着一整个执行力。

**规范**：贴在墙上的东西。"请保持安静""请勿吸烟""实验数据必须真实"。
**门禁**：刷不过就进不去的那台机器。地铁闸机、门禁卡、考试安检。

区别在哪？

规范依靠**自觉**。门禁依靠**机制**。
规范写在纸上，谁都能说自己遵守了。门禁不认说法，只认刷卡那一下。

绝大多数组织只有前者，然后困惑为什么大家不遵守。

**关键认知：规范是写给愿意遵守的人看的，门禁是给所有人用的。** 你不可能靠说服让一百个人都自觉，但你可以装一台机器。

---

## 二、工程化思维的四个零件

"工程化"听起来很技术，其实它只做四件事。我用交论文的场景讲。

### 零件一 判据：把"要怎样"写成能判对错的一句话

这是最难的一步，也是绝大多数规范失败的地方。

看看这些常见的规范怎么写：

> "论文要有学术性。"
> "活动策划要有执行力。"
> "周报要写清楚进展。"

**这三句话，一句都判不了对错。** 什么叫学术性？谁来定义执行力？"写清楚"是多清楚？

能判对错的写法长这样：

- 有 `#` 一级标题，且只有一个
- 有「摘要」「关键词」「参考文献」三个部分
- 正文不少于 800 字
- 正文里出现的每个 `[1]`，参考文献里都能找到对应条目
- 单段不超过 400 字

差别在这里：前一类是**形容词**，后一类是**可以当场核对的事实**。

**一句话原则：凡是不能判对错的规范，最后都会变成人情。**

"老师您看我这篇还行吧"，就是规范失败之后的必然产物。

### 零件二 检查：判的人不能是"应该负责的人"

规范里最爱写"由 XX 负责审核"。问题是，负责的人也要下班，也会心软。

工程化的做法是把判断**交给一个不会心软的东西**，可以是一段脚本、一张清单、一个表格公式。

不是不信任人，是不让人把精力耗在机械核对上。人该干的是"这篇论文有没有价值"，不是"数它有没有 800 字"。

### 零件三 证据：不认"我做了"，只认"这是输出"

职场上最常见的对话：

> "改好了吗？" "改好了。"

然后打开一看，没改。

工程化只认三样东西：**文件、日志、截图**。不是不信任，是因为"改好了"这三个字无法核对，而一个 diff 可以。

这条在论文里也一样：不要写"已按要求修改"，要留一份带修订标记的版本。

### 零件四 边界：明确说出"我不判什么"

这一条最容易被忽略，却决定了别人会不会信任你。

一个好的检查器必须敢说：我只查格式，不查你的观点对不对；我只查引用有没有对上，不查你引的文献质量高不高。

**不划边界的工具，最后会被当成万能的，然后在第一次判错时被彻底抛弃。**

---

## 三、一个反常识：规范写不完，是因为写的时候没想过"谁来判"

很多人写规范的习惯是：想到什么写什么，越全越好。

结果写了两百条，一条都执行不了。因为写的时候只想着"应该怎样"，没想着"这条谁来判、怎么判、判错了怎么办"。

我自己的白皮书就是这样：288 页，最后能变成机器判据的，只有 17 条。

**这不是失败，这是正常的比例。** 大部分规范是给人看的（原则、价值观、判断方法），少部分是能给机器判的（格式、流程、硬性条件）。

工程化的第一步不是写更多规范，是**把现有规范里能判的那部分挑出来**。

挑的标准就一条：**换成另一个人来看，他能不能得出同一个结论？**

能，就是判据。不能，就还是形容词。

---

## 四、为什么"只拦新增"是关键（这条最反直觉）

假设你给一个团队装了门禁，第一天跑出来 200 个问题。

会发生什么？

不是大家排队去修。是有人在群里说"这玩意儿太吵了"，然后第二天它被关掉。

**新规矩一上来就全面否定过去，等于逼人拆掉它。**

正确做法只有一条：**先冻结存量，只拦新增。**

- 第一次接上：把现有的 200 个问题记成一份"欠条"，不再报
- 之后：只报**新出现**的问题
- 每修好一条，欠条上就少一条，门自动紧一格

这叫棘轮：只进不退。

我在自己的项目上验证过：一个仓有 36 条存量，冻结后 CI 变绿；我改了一行代码修好一条，忽略数从 36 变成 35；再故意加一条新问题，它精确报出那一条，位置和行号都对。

**这个机制的意义不是技术，是政治。** 它让"上规矩"这件事从"清算过去"变成"约束未来"，团队才不会抵抗。

---

## 五、动手：30 分钟做一个你自己的门禁

下面这个脚本，检查一份 Markdown 格式的论文。你不需要懂编程，只要会复制粘贴、会改数字。

### 第一步：装 Python

去 python.org 下载，安装时勾选"Add Python to PATH"。装完打开命令行（Windows 搜 cmd，Mac 打开终端），输入 `python --version`，能看到版本号就成了。

### 第二步：把论文存成 .md 文件

用任何文本编辑器（记事本也行），把你的论文存成 `我的论文.md`。格式大概是这样：

```markdown
# 论文题目

## 摘要

这里是摘要……

## 关键词

公共空间；城市；行为

## 正文

正文内容，引用写成 [1] 这样……

## 参考文献

[1] 作者. 书名. 出版社, 2020.
```

### 第三步：把这个脚本存成 `check_paper.py`

```python
import re
import sys

MIN_CHARS = 800          # 正文字数下限，你可以改
MAX_PARA_CHARS = 400     # 单段字数上限
REQUIRED_SECTIONS = ["摘要", "关键词", "参考文献"]

def check(path):
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    problems = []

    h1 = [l for l in lines if re.match(r"^#\s+\S", l)]
    if not h1:
        problems.append(("FAIL", "缺一级标题", "第一行写成 `# 论文题目`"))

    for sec in REQUIRED_SECTIONS:
        if not re.search(r"^#+\s*" + sec, text, re.M):
            problems.append(("FAIL", "缺「%s」" % sec, "加一个 `## %s` 小节" % sec))

    body = re.sub(r"^#+\s.*$", "", text, flags=re.M)
    body = re.sub(r"\s", "", body)
    n = len(body)
    if n < MIN_CHARS:
        problems.append(("FAIL", "正文只有 %d 字，下限 %d" % (n, MIN_CHARS), "补内容，别靠加空行凑"))

    cited = set(re.findall(r"\[(\d+)\]", text))
    ref_block = text.split("参考文献", 1)[-1]
    listed = set(re.findall(r"^\[(\d+)\]", ref_block, re.M))
    missing = cited - listed
    if missing:
        problems.append(("FAIL", "正文引用了但参考文献里没有：%s" % "、".join(sorted(missing)),
                         "补进参考文献，或删掉正文里那个标注"))

    for i, para in enumerate([p for p in text.split("\n\n") if p.strip()], 1):
        clean = re.sub(r"\s", "", re.sub(r"^#+\s.*$", "", para, flags=re.M))
        if len(clean) > MAX_PARA_CHARS:
            problems.append(("WARN", "第 %d 段有 %d 字，超过 %d" % (i, len(clean), MAX_PARA_CHARS),
                             "拆成两段，读者需要换气的地方"))

    return n, problems

def main():
    if len(sys.argv) < 2:
        print("用法： python check_paper.py 你的论文.md")
        return 2
    path = sys.argv[1]
    n, problems = check(path)
    print("检查：", path)
    print("正文字数：", n)
    if not problems:
        print("全部通过。格式没毛病，可以交了。")
        return 0
    for level, what, fix in problems:
        print("[%s] %s" % (level, what))
        print("      怎么改：%s" % fix)
    fails = sum(1 for p in problems if p[0] == "FAIL")
    print("\n合计 FAIL %d / WARN %d" % (fails, len(problems) - fails))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
```

### 第四步：跑

```bash
python check_paper.py 我的论文.md
```

它大概会告诉你：

```
检查： 我的论文.md
正文字数： 30
[FAIL] 缺「关键词」
      怎么改：加一个 `## 关键词` 小节
[FAIL] 正文只有 30 字，下限 800
      怎么改：补内容，别靠加空行凑
[FAIL] 正文引用了但参考文献里没有：1
      怎么改：补进参考文献，或删掉正文里那个标注

合计 FAIL 3 / WARN 0
```

**到这里，你已经完成了一次工程化。** 你做的事是：把"老师的要求"变成了一段会自己判的代码。

### 第五步：改规矩

想改判定？改文件顶部那三行就行：

```python
MIN_CHARS = 800          # 改成 1200
MAX_PARA_CHARS = 400     # 改成 300
REQUIRED_SECTIONS = ["摘要", "关键词", "参考文献"]   # 加一个"致谢"
```

**这就是工程化最爽的地方：规矩变了，改一处就够，不用重新教一百个人。**

---

## 六、五个坑，我全踩过

**坑一：误报比漏报更致命。**
我的第一版检查器在一个成熟项目上报了 4 条问题，我逐条读原文，发现**全是误报**，把必须的权限当成越权、把正常的构建当成缺陷。如果我当时没去核对，这 4 条会让整个工具被当成噪音关掉。
**规则：报错之前，先读原文。宁可少报一条，不要错报一条。**

**坑二：拿"我觉得"当判据。**
"这段写得不好"不是判据，"这段 640 字超过上限"才是。

**坑三：一上来就全覆盖。**
想做十件事，结果一件都没落地。先做三条，跑通，再加。

**坑四：把门禁当惩罚。**
门禁该做的第一件事是让人变绿，不是让人变红。所以先冻结存量。

**坑五：承诺零误报。**
没有人能做到。承诺该是"每条误报都会被记录、并且会被改掉"。

---

## 七、这套东西能用到哪

凡是有要求、但靠人记的事，都能用：

- **论文/作业**：格式、字数、引用、结构
- **活动策划**：预算项齐不齐、物料清单有没有漏、时间节点有没有倒挂
- **社团管理**：报销单据要素、活动归档清单
- **实习周报**：本周做了什么、遇到什么问题、下周计划
- **团队协作**：代码规范、提交信息格式、发布流程

判断标准始终是那一条：**内容能不能换成另一个人来看，还能得出同一个结论。**

---

## 八、会过时的是判据，不是方法

这一节最重要。

2025 年 8 月 15 日，GitHub 官方的 Actions 策略开始支持**强制 SHA 钉扎**，管理员打开一个开关，任何没钉到完整 commit 的 action 直接失败。2026 年 10 月 14 日，官方又上线了 workflow lockfiles 公测，直接锁定所有依赖的 commit。

换句话说：我那些判据里最硬的一条（R01：action 必须钉到 40 位 SHA），在一年多之后被平台自己做掉了。

**这不是坏事，是必然规律。**

任何具体判据都活在两种力量之间：一边是"没人管的空档"，一边是"平台补上的能力"。空档被填上，判据就失去意义。今天稀缺的检查，明天会变成默认行为。

所以真正能留下的不是那 17 条规则。是这两样：

- **那四步方法**：找出能判对错的那句话 → 交给不会心软的东西 → 只认输出 → 划清边界
- **那一次练习**：你真的把一个要求变成了不靠人的机制，这个过程你走通了

规则会死，方法不会。这也是为什么我不建议任何人把这套东西当产品做——把它当一次练习做。练完你就有了那个能力，能力不会被版本号淘汰。

---

## 最后一段

我不想把工程化讲成"提高效率的工具"，那样太轻了。

它真正改变的是**责任的位置**。

以前，规矩靠人守，守不住就怪人。现在，规矩靠机器守，人只需要在机器拦下来的时候做决定——改还是不改。

这不是让人轻松，是让人把力气用在真正需要判断的地方。

一句话收尾：

> **好的制度，不是让人不敢犯错，是让错误在被发现之前就留下痕迹。**

如果你现在就有一份总也执行不下去的规矩，别去改它的措辞。先去挑一条能判对错的，让它自己跑起来。

---

# 附录：来源与依据

这一节是给"想核对"的人准备的。文中每个数字和判断都留了出处，你可以自己去查。这也算这篇文章的执行边界：**凡是查不到出处的，不算数。**

## 一、外部标准与官方事实

| 文中说法 | 出处 | 怎么核对 |
|---|---|---|
| SHA 钉扎是官方建议，且已能强制 | GitHub Changelog，2025-08-15《Actions policy now supports blocking and SHA pinning》 | 打开链接找 "Enforce SHA pinning" 段，原文写着 "The policy will check for a full commit SHA, and any workflow that attempts to use an action that isn't pinned will fail." |
| 官方在做依赖锁定 | GitHub Blog，2026 安全路线图《What's coming to our GitHub Actions 2026 security roadmap》 | 找 "workflow-level dependency locking" 段，提到用 commit SHA 锁住直接与传递依赖 |
| 锁定已进入公测 | GitHub Changelog，2026-10-14《GitHub Actions workflow lockfiles in public preview》 | 开头即写 "Tags and branches can move"，lockfiles 让引用保持但执行锁定 commit |
| SARIF 2.1.0 是国际标准 | OASIS 标准页（2019-07-23 批准）与规范正文 PDF | 标准页给出批准日期与定义：静态分析工具输出的标准格式 |
| actionlint 有 36 条规则 | arXiv 论文《Unpacking Security Scanners for GitHub Actions Workflows》 | 正文写明 "Most of the rules of actionlint (28 out of 36) aim at the GitHub Runner Compatibility Weakness"，据此确认总数 36 |
| zizmor 约 30 多种检查 | zizmor 官方仓（zizmorcore/zizmor） | 仓说明写明是 GitHub Actions 静态分析，覆盖脚本注入、权限过大、未钉扎依赖、危险触发器等 |
| 两者定位不同，建议一起用 | secure-pipelines.com 的对比实验文章 | 表格逐项列出 actionlint 与 zizmor 各自覆盖什么，结论是 use both |
| 私有仓的安全面板要付费 | Microsoft GHAS 产品页 + GitHub Blog 新手安全文章 | 两处都写明：多数安全功能对公开仓免费，私有仓需要 GHAS 许可 |

原文链接：

1. https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/
2. https://github.blog/news-insights/product-news/whats-coming-to-our-github-actions-2026-security-roadmap/
3. https://github.blog/changelog/2026-10-14-github-actions-workflow-lockfiles-in-public-preview/
4. https://www.oasis-open.org/standard/sarif-v2-1-0/
5. https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.pdf
6. https://arxiv.org/pdf/2601.14455v1
7. https://github.com/rhysd/actionlint
8. https://github.com/zizmorcore/zizmor
9. https://secure-pipelines.com/ci-cd-security/lab-detecting-malicious-github-actions-static-analysis/
10. https://www.microsoft.com/en-us/securityengineering/sdl/ghas
11. https://github.blog/developer-skills/github/github-for-beginners-getting-started-with-github-security/

## 二、文中关于自己的数字（可当场核对）

| 文中说法 | 出处 | 怎么核对 |
|---|---|---|
| 288 页、244 张表、62 个一级标题 | 《企业级 AI Native 项目开发全流程白皮书》PDF 与 Word 原件 | 成品 292 页（含 4 页目录），目录页逐条列出 62 个一级标题；表格数可用 Word 字数统计或脚本计数 |
| 17 条判据 | `ci_guard.py`（249 KB）与 `docs/RULES.md` | 每条在 RULES.md 里有独立小节，标注对应的白皮书条款（AV.5 / AV.6 / AW.7 / AW.8 / AW.10 等） |
| 三仓合计 55 条 FAIL | 各仓 `--format=json` 输出（2026-11-15 重跑） | tea 34 + yg-gateway 21 + career-os 0 = 55；另有一个范本仓 0 FAIL、2 WARN |
| 四次运行 8s / 9s / 10s / 18s | GitHub Actions run 记录 | 公开仓 `qiuqianyi66/ci-guard-live` 的 Actions 页面，按时间顺序可查四次 |
| 第一版 4 条全是误报 | 校准记录与改动前后两次输出 | 同一范本仓改判定前后各跑一次，对比命中项 |
| 36 → 35 | 基线文件前后 diff | 改一行 `cancel-in-progress` 后重跑，基线忽略数少一条 |
| SARIF 通过官方 schema | `verify_sarif.py` + 官方 2.1.0 schema（112 KB） | 本地跑校验器，19 条 results 全部合 schema |

## 三、你自己怎么复现

```bash
# 1. 拿到工具
git clone https://github.com/qiuqianyi66/ci-guard-live

# 2. 跑一次，看它到底报什么
cd ci-guard-live
python tools/ci-guard/ci_guard.py .

# 3. 只看结构化结果
python tools/ci-guard/ci_guard.py . --format=json

# 4. 跑自带回归测试（7 项）
python tools/ci-guard/selftest.py
```

跑出来的数字如果和本文说的不一致，以你跑出来的为准。**这篇文章里的所有数字都是 2026 年 11 月 15 日的快照，不是永恒真理。**

