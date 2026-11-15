# -*- coding: utf-8 -*-
"""论文格式检查器 —— 文科生也能看懂、能改的第一个"门禁"。

用法：
    python check_paper.py 我的论文.md

它只做六件小事，每件都能用眼睛核对：
    1. 有没有一级标题（# 开头）
    2. 有没有"摘要""关键词""参考文献"三个部分
    3. 正文字数够不够
    4. 正文里的引用 [1] 有没有在参考文献里出现
    5. 有没有超长段落（超过 400 字，读者会喘不过气）
    6. 有没有连续两个空行（排版松散）

不检查内容好坏。它判不了你写得好不好，只判"格式有没有按规矩来"。
"""
import re
import sys

# ---- 规矩写在这里，改这里就等于改规矩 ----
MIN_CHARS = 800          # 正文字数下限
MAX_PARA_CHARS = 400     # 单段字数上限
REQUIRED_SECTIONS = ["摘要", "关键词", "参考文献"]


def check(path):
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    problems = []

    # 1. 一级标题
    h1 = [l for l in lines if re.match(r"^#\s+\S", l)]
    if not h1:
        problems.append(("FAIL", "缺一级标题", "第一行写成 `# 论文题目`"))
    elif len(h1) > 1:
        problems.append(("WARN", "一级标题不止一个", "一篇论文只该有一个 `#`，其余用 `##`"))

    # 2. 必备部分
    for sec in REQUIRED_SECTIONS:
        if not re.search(r"^#+\s*" + sec, text, re.M):
            problems.append(("FAIL", "缺「%s」" % sec, "加一个 `## %s` 小节" % sec))

    # 3. 字数
    body = re.sub(r"^#+\s.*$", "", text, flags=re.M)
    body = re.sub(r"\s", "", body)
    n = len(body)
    if n < MIN_CHARS:
        problems.append(("FAIL", "正文只有 %d 字，下限 %d" % (n, MIN_CHARS), "补内容，别靠加空行凑"))

    # 4. 引用对应
    cited = set(re.findall(r"\[(\d+)\]", text))
    ref_block = text.split("参考文献", 1)[-1]
    listed = set(re.findall(r"^\[(\d+)\]", ref_block, re.M))
    missing = cited - listed
    if missing:
        problems.append(("FAIL", "正文引用了但参考文献里没有：%s" % "、".join(sorted(missing)),
                         "补进参考文献，或删掉正文里那个标注"))

    # 5. 超长段落
    for i, para in enumerate([p for p in text.split("\n\n") if p.strip()], 1):
        clean = re.sub(r"\s", "", re.sub(r"^#+\s.*$", "", para, flags=re.M))
        if len(clean) > MAX_PARA_CHARS:
            problems.append(("WARN", "第 %d 段有 %d 字，超过 %d" % (i, len(clean), MAX_PARA_CHARS),
                             "拆成两段，读者需要换气的地方"))

    # 6. 连续空行
    if "\n\n\n" in text:
        problems.append(("WARN", "出现连续空行", "删掉多余空行，排版要紧凑"))

    return n, problems


def main():
    if len(sys.argv) < 2:
        print("用法： python check_paper.py 你的论文.md")
        return 2
    path = sys.argv[1]
    try:
        n, problems = check(path)
    except FileNotFoundError:
        print("找不到文件：", path)
        return 2

    print("检查：", path)
    print("正文字数：", n)
    if not problems:
        print("全部通过。格式没毛病，可以交了。")
        return 0

    for level, what, fix in problems:
        print("[%s] %s" % (level, what))
        print("      怎么改：%s" % fix)

    fails = sum(1 for p in problems if p[0] == "FAIL")
    warns = len(problems) - fails
    print("\n合计 FAIL %d / WARN %d" % (fails, warns))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
