# -*- coding: utf-8 -*-
"""ci-guard 自测：13 条规则每条都要能命中，且合规样本必须零命中。

规则改动后必须跑这个。没有它，规则会在「以为还生效」的状态下悄悄失效
（zizmor / actionlint 都把 test-data 视为产品的一部分，不是附属品）。

用法：python selftest.py
"""
import json
import os, shutil, sys, tempfile, textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ci_guard as g

SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"  # actions/checkout v4.2.2

BAD = {
    # R01 未 pin；R09 @latest；R10 secrets 进 run；R02 管道无 pipefail
    "bad-misc.yml": textwrap.dedent("""\
        name: bad-misc
        on: push
        permissions:
          contents: read
        jobs:
          a:
            runs-on: ubuntu-latest
            steps:
              - uses: some/action@v1
              - run: |
                  go install golang.org/x/vuln/cmd/govulncheck@latest
                  govulncheck ./...
              - run: |
                  cat report.txt | grep TOTAL
              - run: |
                  echo ${{ secrets.TOKEN }}
        """),
    # R03 部署可取消；R06 无 fork 守卫
    "bad-deploy.yml": textwrap.dedent("""\
        name: Deploy Pages
        on:
          push:
            branches: [main]
        permissions:
          contents: read
          pages: write
          id-token: write
        concurrency:
          group: pages
          cancel-in-progress: true
        jobs:
          deploy:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/deploy-pages@v4
        """),
    # R04 顶层 contents: write + 多 job
    "bad-perm.yml": textwrap.dedent("""\
        name: bad-perm
        on: push
        permissions:
          contents: write
        jobs:
          a:
            runs-on: ubuntu-latest
            steps:
              - run: echo a
          b:
            runs-on: ubuntu-latest
            steps:
              - run: echo b
        """),
    # R05 完全没有 permissions；R07 整点 cron；R08 不变量只 PR；R11 发布 job 无 needs
    "bad-invariant.yml": textwrap.dedent("""\
        name: plugin contract
        on:
          pull_request:
            branches: [main]
          schedule:
            - cron: '0 0 * * *'
        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - run: echo build
          publish:
            runs-on: ubuntu-latest
            steps:
              - run: echo publish
        """),
    # R15 pull_request_target 下 checkout PR head
    "bad-target.yml": textwrap.dedent("""\
        name: review
        on:
          pull_request_target:
            types: [opened]
        permissions:
          contents: read
          pull-requests: write
        jobs:
          review:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@%s # v4.2.2
                with:
                  ref: ${{ github.event.pull_request.head.sha }}
        """ % SHA),
    # R16 write-all；R17 自托管 + PR
    "bad-wideper.yml": textwrap.dedent("""\
        name: wide
        on:
          pull_request:
          push:
            branches: [main]
        permissions: write-all
        jobs:
          a:
            runs-on: self-hosted
            steps:
              - run: echo a
        """),
    # R14 发布面比检查面宽：install.sh 只在 push 发布时被验
    "deploy-site.yml": textwrap.dedent("""\
        name: deploy site
        on:
          push:
            branches: [main]
            paths:
              - 'install.sh'
              - 'site/**'
        permissions:
          contents: read
          pages: write
        concurrency:
          group: pages
          cancel-in-progress: false
        jobs:
          deploy:
            if: github.repository == 'o/r'
            runs-on: ubuntu-latest
            steps:
              - uses: actions/deploy-pages@%s # v4.0.0
        """),
    "check-site.yml": textwrap.dedent("""\
        name: site ci
        on:
          pull_request:
            branches: [main]
            paths:
              - 'site/**'
        permissions:
          contents: read
        concurrency:
          group: ${{ github.workflow }}-${{ github.ref }}
          cancel-in-progress: true
        jobs:
          check:
            runs-on: ubuntu-latest
            steps:
              - run: echo check
        """),
}

GOOD = "good.yml", textwrap.dedent("""\
    name: good
    on:
      push:
        branches: [main]
      pull_request:
        branches: [main]
    permissions:
      contents: read
    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: true
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@%s # v4.2.2
          - run: |
              set -euo pipefail
              go test ./...
    """ % SHA)


def build(root, files, nested=False, empty=False):
    wf = os.path.join(root, ".github", "workflows")
    os.makedirs(wf, exist_ok=True)
    if empty:
        return
    for name, body in files.items():
        with open(os.path.join(wf, name), "w", encoding="utf-8") as f:
            f.write(body)
    if nested:
        with open(os.path.join(root, "go.mod"), "w", encoding="utf-8") as f:
            f.write("module example/root\n")
        sub = os.path.join(root, "acp")
        os.makedirs(sub, exist_ok=True)
        with open(os.path.join(sub, "go.mod"), "w", encoding="utf-8") as f:
            f.write("module example/root/acp\n")


def main():
    base = tempfile.mkdtemp(prefix="ci-guard-selftest-")
    ok = True
    try:
        # 1. 坏样本：R01–R12 必须全部命中（R13「无 workflow」由第 3 步单独验证）
        bad = os.path.join(base, "bad")
        build(bad, BAD, nested=True)
        fs = g.scan(bad)
        hit = {f.rule for f in fs}
        expect = set(g.RULES) - {"R13"}
        missing = sorted(expect - hit)
        print("坏样本命中规则：%d/%d  %s" % (len(hit), len(g.RULES), ",".join(sorted(hit))))
        if missing:
            ok = False
            print("  FAIL 未命中：%s" % ",".join(missing))

        # 2. 合规样本：零命中
        good = os.path.join(base, "good")
        build(good, {GOOD[0]: GOOD[1]})
        fs2 = g.scan(good)
        print("合规样本命中：%d（应为 0）" % len(fs2))
        if fs2:
            ok = False
            for f in fs2:
                print("  FAIL 误报 %s %s:%d %s" % (f.rule, f.path, f.line, f.detail))

        # 3. 空仓：只报 R13
        empty = os.path.join(base, "empty")
        build(empty, {}, empty=True)
        fs3 = g.scan(empty)
        rules3 = {f.rule for f in fs3}
        print("空仓命中：%s（应为 R13）" % ",".join(sorted(rules3)) or "无")
        if rules3 != {"R13"}:
            ok = False
            print("  FAIL 空仓应只报 R13")

        # 4. persona：regular 必须过滤 low 置信规则
        fs4 = g.apply_filters(g.scan(bad), bad, {}, "regular", True, None)
        lows_hidden = all(f.ignored for f in fs4 if f.confidence == "low")
        print("persona=regular 隐藏 low：%s" % ("是" if lows_hidden else "否"))
        if not lows_hidden:
            ok = False
            print("  FAIL regular 未过滤 low 置信规则")

        # 5. SARIF：结构能被 code scanning 接受（接入路径的硬前提）
        sarif = os.path.join(base, "out.sarif")
        g.emit_sarif(sarif, fs)
        with open(sarif, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        run = doc["runs"][0]
        ids = {r["id"] for r in run["tool"]["driver"]["rules"]}
        problems = []
        if doc.get("version") != "2.1.0" or "$schema" not in doc:
            problems.append("顶层 version/$schema")
        if run["tool"]["driver"]["name"] != "ci-guard" or not run["tool"]["driver"]["version"]:
            problems.append("driver name/version")
        if len(ids) != len(g.RULES):
            problems.append("rules 条数 %d != %d" % (len(ids), len(g.RULES)))
        for res in run["results"]:
            if res["ruleId"] not in ids:
                problems.append("ruleId 不在 rules 里：%s" % res["ruleId"])
            if res["level"] not in ("error", "warning", "note", "none"):
                problems.append("level 非法：%s" % res["level"])
            loc = res["locations"][0]["physicalLocation"]
            uri = loc["artifactLocation"]["uri"]
            if uri.startswith("/") or "\\" in uri:
                problems.append("uri 不是仓内相对路径：%s" % uri)
            if loc["region"]["startLine"] < 1:
                problems.append("startLine < 1")
            if not res["message"].get("text"):
                problems.append("message 为空")
        print("SARIF 校验：%s（%d rules / %d results）" %
              ("通过" if not problems else "不通过", len(ids), len(run["results"])))
        if problems:
            ok = False
            for b in problems[:5]:
                print("  FAIL " + b)

        # 5b. 官方 SARIF schema 校验（比上面的字段断言严格；schema 随工具离线缓存）
        try:
            from jsonschema.validators import validator_for
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "schema", "sarif-2.1.0.json")
            if os.path.isfile(schema_path):
                with open(schema_path, "r", encoding="utf-8") as fh:
                    schema = json.load(fh)
                errs = list(validator_for(schema)(schema).iter_errors(doc))
                print("官方 schema 校验：%s" % ("通过" if not errs else "不通过 %d 处" % len(errs)))
                if errs:
                    ok = False
                    for e in errs[:3]:
                        print("  FAIL %s -> %s" % ("/".join(str(p) for p in e.path), e.message[:160]))
            else:
                print("官方 schema 校验：跳过（缺 schema/sarif-2.1.0.json）")
        except ImportError:
            print("官方 schema 校验：跳过（未装 jsonschema）")

        # 6. baseline：冻结后零新增
        fps = {"fingerprints": sorted({f.fingerprint() for f in fs})}
        fs5 = g.apply_filters(g.scan(bad), bad, {}, "auditor", True, fps)
        rest = [f for f in fs5 if not f.ignored]
        print("baseline 冻结后剩余：%d（应为 0）" % len(rest))
        if rest:
            ok = False
            print("  FAIL baseline 未覆盖全部指纹")
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("结果：%s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
