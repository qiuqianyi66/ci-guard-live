#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ci-guard — 把《企业级 AI Native 项目开发全流程白皮书》的 CI 判据变成可执行门禁。

产品面参考 actionlint（可选配置 + init-config）与 zizmor（persona 三档、inline ignore、
退出码分级、github annotations、每个 finding 带文档锚点）。设计依据见 PRODUCT-NOTES.md。

用法：
    python ci_guard.py <repo>                     # 默认 regular：只报高/中信噪比
    python ci_guard.py <repo> --pedantic          # 连低置信（code smell）一起报
    python ci_guard.py <repo> --format=json|sarif|github
    python ci_guard.py <repo> --baseline .ci-guard-baseline.json   # 只报新增（存量仓上线用）
    python ci_guard.py <repo> --init-config       # 生成 .ci-guard.yml + 基线
    python ci_guard.py <repo> --no-ignores        # 临时忽略所有 ignore（审计用）

退出码：0 无问题；1 内部错误；2 参数错误；3 未收集到 workflow；
        11/12/13/14 = 最高级别 informational/low/medium/high（SARIF 模式不返回 11+）。
"""
import argparse, fnmatch, hashlib, json, os, re, sys, glob

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

VERSION = "0.3.3"
DOC_BASE = "tools/ci-guard/docs/RULES.md"

RULES = {
    "R01": {"level": "FAIL", "confidence": "high",
            "title": "action 未 pin 到 40 位 SHA",
            "anchor": "AV.6",
            "why": "第三方 action 必须 pin 到不可变 SHA；tag 可被上游改写，同一 tag 今天与明天可能是两份代码",
            "fix": "改为 @<40 位 commit SHA>，并在同行留 # vX.Y.Z 注释"},
    "R02": {"level": "WARN", "confidence": "low",
            "title": "多行块用了管道却没有 pipefail",
            "anchor": "AU.3 / AV.13",
            "why": "缺 pipefail 时前段命令失败会被后段吞掉，退出码仍是后段的",
            "fix": "块首加 set -euo pipefail"},
    "R03": {"level": "FAIL", "confidence": "high",
            "title": "Pages 部署会被后续推送取消",
            "anchor": "AV.5 / AW.9",
            "why": "取消部署的代价不是重跑，而是上一个版本可能停在半截",
            "fix": "cancel-in-progress 改 false，或写 ${{ github.event_name == 'pull_request' }}"},
    "R04": {"level": "WARN", "confidence": "medium",
            "title": "顶层给了仓库内容类写权限",
            "anchor": "AW.7",
            "why": "写权限应按 job 授予；顶层一大包会让每个 job 都拿到不需要的权限",
            "fix": "下沉到真正需要它的 job"},
    "R05": {"level": "WARN", "confidence": "medium",
            "title": "没有声明 permissions",
            "anchor": "AW.7",
            "why": "未声明时 token 默认权限偏宽，显式 read 才是最小",
            "fix": "顶层写 permissions: contents: read"},
    "R06": {"level": "WARN", "confidence": "medium",
            "title": "Pages 部署没有 fork 守卫",
            "anchor": "AW.8",
            "why": "fork 之后推 main 会往自己的 Pages 发东西；一旦被复制到组织仓就是事故",
            "fix": "加 if: github.repository == '<owner>/<repo>'"},
    "R07": {"level": "WARN", "confidence": "low",
            "title": "定时任务落在整点",
            "anchor": "AW.9",
            "why": "整点是全球拥塞点，排队会拉长启动延迟",
            "fix": "改成非整点，例如 39 6 * * 5"},
    "R08": {"level": "WARN", "confidence": "medium",
            "title": "不变量检查只在 PR 触发",
            "anchor": "AW.5",
            "why": "只在 PR 上跑看不见「合并后」状态：两个 PR 各自绿，合并可能坏",
            "fix": "加 push: branches: [main]"},
    "R09": {"level": "WARN", "confidence": "medium",
            "title": "安装动作未钉版本",
            "anchor": "AU.9 / AV.9",
            "why": "@latest 意味着同一天重跑两次，扫出来的东西可能不同",
            "fix": "钉到具体版本，例如 govulncheck@v1.6.0"},
    "R10": {"level": "FAIL", "confidence": "high",
            "title": "secrets 直接插进 run 脚本",
            "anchor": "AU.10",
            "why": "表达式进 shell 会被当代码；改走 env 才能避免注入与泄漏",
            "fix": "env: X: ${{ secrets.X }}，脚本里读环境变量"},
    "R11": {"level": "WARN", "confidence": "low",
            "title": "发布类 job 没有 needs",
            "anchor": "AU.6 / AW.7",
            "why": "发布顺序是依赖图，缺 needs 会让产物在未验证时就被发出去",
            "fix": "加 needs 指向构建/校验 job"},
    "R12": {"level": "FAIL", "confidence": "high",
            "title": "嵌套 module 没有任何 workflow 覆盖",
            "anchor": "AW.3",
            "why": "嵌套 go module 不被根 CI 的 ./... 覆盖，等于盲区：不是测了通过，是压根没测",
            "fix": "为它单独建 workflow，paths 含该目录"},
    "R13": {"level": "WARN", "confidence": "medium",
            "title": "仓库没有任何 workflow",
            "anchor": "AV.2",
            "why": "没有 CI 等于全部检查靠自觉；最小 CI 面也要 lint + test + 构建",
            "fix": "至少建 ci.yml"},
    "R14": {"level": "WARN", "confidence": "medium",
            "title": "发布路径里的文件，PR 阶段没有检查覆盖",
            "anchor": "AW.8",
            "why": "发布面比检查面宽：某文件只在 push 时才被验，改动合进 main 后才发现问题",
            "fix": "把该文件加进对应检查 workflow 的 pull_request paths，或写明为什么不用"},
    "R15": {"level": "FAIL", "confidence": "high",
            "title": "pull_request_target 下 checkout 了 PR 的 head",
            "anchor": "AW.10 / AU.10",
            "why": "pull_request_target 拿得到 secrets，又 checkout 攻击者的 head，等于让不可信代码带着写权限跑",
            "fix": "只 checkout base；需要 PR 代码时用 pull_request 事件且不给 secrets"},
    "R16": {"level": "FAIL", "confidence": "high",
            "title": "permissions 写了 write-all",
            "anchor": "AW.7",
            "why": "write-all 把 token 的全部写权限一次发出，任何一步被注入都能改仓库",
            "fix": "按 job 逐项授予，顶层只留 contents: read"},
    "R17": {"level": "WARN", "confidence": "low",
            "title": "自托管 runner 上跑 PR 代码",
            "anchor": "AV.10",
            "why": "自托管机器通常持有内网凭据与持久缓存，PR 代码在那里跑等于把边界交给外部贡献者",
            "fix": "PR 用 GitHub 托管 runner；自托管只跑 main/tag 的可信代码"},
}

USES_RE = re.compile(r"^(?P<indent>\s*)(?:-?\s*)uses:\s*(?P<val>[^\s#]+)")
PIN_RE = re.compile(r"@[0-9a-f]{40}$")
VER_COMMENT_RE = re.compile(r"#\s*v?\d+(?:\.\d+)*")
CRON_RE = re.compile(r"cron:\s*['\"]?([^'\"\n]+)['\"]?")
DEPLOY_HINT = re.compile(r"deploy|publish|release|ghcr|pages|npm-publish", re.I)
INVARIANT_HINT = re.compile(r"contract|invariant|契约|不变量|consistency", re.I)
INLINE_IGNORE_RE = re.compile(r"#\s*ci-guard:\s*ignore\[([^\]]+)\]")


class Finding(object):
    def __init__(self, rule, path, line, detail, fix=None):
        self.rule, self.path, self.line, self.detail = rule, path, line, detail
        self.fix = fix or RULES[rule]["fix"]
        self.idx = 1
        self.ignored = False
        self.ignore_reason = ""

    @property
    def level(self):
        return RULES[self.rule]["level"]

    @property
    def confidence(self):
        return RULES[self.rule]["confidence"]

    def fingerprint(self):
        # 行号不进指纹（会随上方插入漂移），但要区分「同一文件里的第 N 个同类实例」：
        # 只用 rule|path|detail 会让基线一次冻结就吞掉未来新增的同类违规，等于棘轮失效。
        return "%s|%s|%s|%d" % (self.rule, self.path, self.detail, self.idx)

    def as_dict(self):
        r = RULES[self.rule]
        return {"rule": self.rule, "level": r["level"], "confidence": r["confidence"],
                "file": self.path, "line": self.line, "detail": self.detail,
                "title": r["title"], "why": r["why"], "fix": self.fix,
                "anchor": r["anchor"], "url": "%s#%s" % (DOC_BASE, self.rule.lower()),
                "ignored": self.ignored, "ignore_reason": self.ignore_reason,
                "fingerprint": self.fingerprint()}


def read(p):
    with open(p, "rb") as f:
        b = f.read()
    for enc in ("utf-8-sig", "utf-8", "cp936"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", "replace")


def line_of(text, needle, start=0):
    idx = text.find(needle, start)
    return 0 if idx < 0 else text.count("\n", 0, idx) + 1


def strip_quoted(s):
    s = re.sub(r"'[^']*'", "''", s, flags=re.S)
    s = re.sub(r'"[^"]*"', '""', s, flags=re.S)
    return s


def run_blocks(text):
    """返回 (起始行号, 块内容, 是否 pwsh)。只取 run: | 与 run: > 的多行块。"""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"^(\s*)(?:-\s*)?run:\s*([|>])\s*$", ln)
        if not m:
            continue
        ind = len(m.group(1))
        body = []
        for j in range(i + 1, len(lines)):
            l2 = lines[j]
            if l2.strip() == "":
                body.append("")
                continue
            if len(l2) - len(l2.lstrip()) <= ind:
                break
            body.append(l2)
        joined = "\n".join(body)
        ctx = "\n".join(lines[max(0, i - 4):i])
        yield i + 1, joined, ("pwsh" in ctx or "pwsh" in joined or "$ErrorActionPreference" in joined)


def load_wf(text):
    if HAS_YAML:
        try:
            return yaml.safe_load(text) or {}, None
        except Exception as e:
            return {}, str(e).splitlines()[0]
    return {"__degraded__": True}, None


def wf_files(repo):
    out = []
    for pat in ("*.yml", "*.yaml", "**/*.yml", "**/*.yaml"):
        out += glob.glob(os.path.join(repo, ".github", "workflows", pat))
    return sorted(set(out))


def on_events(wf):
    if not isinstance(wf, dict):
        return set()
    on = wf.get("on")
    if on is None:
        # YAML 1.1（pyyaml 的 safe_load）会把裸 `on:` 解析成布尔 True，
        # 这是 GitHub Actions workflow 解析里最经典的坑；不兜这一下，依赖触发的规则会永远不命中。
        on = wf.get(True)
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return set(str(x) for x in on)
    if isinstance(on, dict):
        return set(str(k) for k in on.keys())
    return set()


def trigger_paths(wf, event):
    if not isinstance(wf, dict):
        return []
    on = wf.get("on")
    if on is None:
        on = wf.get(True)
    if isinstance(on, dict):
        node = on.get(event)
        if isinstance(node, dict):
            return list(node.get("paths") or [])
    return []


def scan(repo):
    fs = []
    files = wf_files(repo)
    if not files:
        fs.append(Finding("R13", ".github/workflows", 0, "未发现任何 workflow 文件"))
    for path in files:
        rel = os.path.relpath(path, repo).replace("\\", "/")
        text = read(path)
        wf, perr = load_wf(text)
        if perr:
            f = Finding("R04", rel, 0, "YAML 解析失败：" + perr, "先修语法，坏 YAML 在 GitHub 侧同样会红")
            f.level = "FAIL"
            fs.append(f)
            continue

        for i, ln in enumerate(text.splitlines(), 1):
            m = USES_RE.match(ln)
            if m:
                val = m.group("val")
                if val.startswith("./") or val.startswith("docker://"):
                    pass
                elif not PIN_RE.search(val):
                    fs.append(Finding("R01", rel, i, "uses: %s" % val))
                elif not VER_COMMENT_RE.search(ln):
                    fs.append(Finding("R01", rel, i, "uses: %s 已 pin 但无版本注释" % val,
                                      "补 # vX.Y.Z：pin 是防改写，注释是让人知道升的是什么"))
            if "@latest" in ln.strip():
                fs.append(Finding("R09", rel, i, ln.strip()[:90]))
            if re.search(r"permissions:\s*write-all", ln):
                fs.append(Finding("R16", rel, i, "permissions: write-all"))

        for ln_no, body, is_pwsh in run_blocks(text):
            guard = re.search(r'-z "\s*\$|BEGIN \{exit|grep -q|test -s|test -n|\|\| ', body)
            if (not is_pwsh) and not guard and re.search(r"(?<!\|)\|(?!\|)", strip_quoted(body)) and "pipefail" not in body:
                fs.append(Finding("R02", rel, ln_no, "块内有管道但未 set -o pipefail"))
            if "${{ secrets." in body:
                fs.append(Finding("R10", rel, ln_no, "run 块内直接插值 secrets"))

        for i, ln in enumerate(text.splitlines(), 1):
            s = ln.split("#")[0].strip()
            mm = re.match(r"^(?:-\s*)?(?:run:\s*)?pip install\s+(.+)$", s)
            if mm and "-r " not in mm.group(1) and "==" not in mm.group(1) and "-e " not in mm.group(1):
                fs.append(Finding("R09", rel, i, s[:90]))

        if not HAS_YAML:
            continue
        jobs = wf.get("jobs") or {}
        name = str(wf.get("name") or os.path.basename(path))
        ev = on_events(wf)
        top_perm = wf.get("permissions")
        conc = wf.get("concurrency") or {}
        cancel = conc.get("cancel-in-progress") if isinstance(conc, dict) else None

        content_writes = ("contents", "packages", "actions", "security-events")
        any_job_perm = any(isinstance(j, dict) and j.get("permissions") for j in jobs.values())
        if top_perm is None and not any_job_perm:
            fs.append(Finding("R05", rel, 0, "顶层与 job 级都没有 permissions"))
        elif isinstance(top_perm, dict):
            writes = [k for k, v in top_perm.items()
                      if isinstance(v, str) and v.endswith("write") and k in content_writes]
            if writes and len(jobs) > 1:
                fs.append(Finding("R04", rel, line_of(text, "permissions:"),
                                  "顶层授予 %s，而本文件有 %d 个 job" % (",".join(writes), len(jobs))))

        perm_union = dict(top_perm) if isinstance(top_perm, dict) else {}
        for j in jobs.values():
            if isinstance(j, dict) and isinstance(j.get("permissions"), dict):
                perm_union.update(j["permissions"])
        uses_all = "\n".join(str(s.get("uses", "")) for j in jobs.values() if isinstance(j, dict)
                             for s in (j.get("steps") or []) if isinstance(s, dict))
        is_deploy = ("pages" in perm_union or "deploy-pages" in uses_all
                     or "upload-pages-artifact" in uses_all)
        if is_deploy:
            if cancel is True:
                fs.append(Finding("R03", rel, line_of(text, "cancel-in-progress"),
                                  "Pages 部署 workflow 的 cancel-in-progress 为 true"))
            elif conc == {}:
                fs.append(Finding("R03", rel, 0, "Pages 部署 workflow 没有 concurrency 组",
                                  "并发部署会互相覆盖，至少写 group 且 cancel-in-progress: false"))

        if "pages" in perm_union and "github.repository ==" not in text:
            fs.append(Finding("R06", rel, 0, "Pages 部署未限定 repository"))

        for cm in CRON_RE.finditer(text):
            parts = cm.group(1).split()
            if len(parts) >= 5 and parts[0] in ("0", "00") and parts[1] in ("0", "00"):
                fs.append(Finding("R07", rel, line_of(text, cm.group(0)), "cron: %s" % cm.group(1)))

        if INVARIANT_HINT.search(name) and "pull_request" in ev and "push" not in ev:
            fs.append(Finding("R08", rel, 0, "workflow 名含不变量语义但无 push 触发"))

        for idx, (jname, job) in enumerate(jobs.items()):
            if not isinstance(job, dict) or idx == 0:
                continue
            label = str(job.get("name") or "") + " " + str(jname)
            if DEPLOY_HINT.search(label) and not job.get("needs"):
                fs.append(Finding("R11", rel, line_of(text, jname + ":"),
                                  "job %s 疑似发布/部署但无 needs" % jname))

        # R15：pull_request_target 下把 PR 的 head 交给 checkout
        if "pull_request_target" in ev:
            for i, ln in enumerate(text.splitlines(), 1):
                if "github.event.pull_request.head" in ln and ("ref:" in ln or "sha" in ln):
                    fs.append(Finding("R15", rel, i, "pull_request_target 下 checkout 了 PR head"))

        # R15 补充：checkout v5 起自带 allow-unsafe-pr-checkout（默认 false），显式设 true 等于把这道防护关掉
        if re.search(r"allow-unsafe-pr-checkout:\s*true", text, re.I):
            fs.append(Finding("R15", rel, line_of(text, "allow-unsafe-pr-checkout"),
                              "显式打开了 allow-unsafe-pr-checkout"))

        # R17：自托管 runner 上跑 PR 代码（低置信：很多团队是有意的）
        if ("pull_request" in ev or "pull_request_target" in ev) and re.search(r"runs-on:\s*[^\n]*self-hosted", text):
            fs.append(Finding("R17", rel, line_of(text, "self-hosted"), "PR 触发且跑在 self-hosted runner"))

    for gomod in glob.glob(os.path.join(repo, "**", "go.mod"), recursive=True):
        if os.sep + "vendor" + os.sep in gomod or ".git" in gomod:
            continue
        parent = os.path.dirname(gomod)
        if not os.path.isfile(os.path.join(os.path.dirname(parent), "go.mod")):
            continue
        relmod = os.path.relpath(parent, repo).replace("\\", "/")
        if not any(relmod in read(p) or relmod.split("/")[0] in read(p) for p in wf_files(repo)):
            fs.append(Finding("R12", relmod, 0, "嵌套 module %s 未被任何 workflow 触及" % relmod))
    # R14：页面发布的 paths 里有、但 PR 检查的 paths 里没有的具体文件
    pub_paths, pr_files = {}, set()
    for path in files:
        rel = os.path.relpath(path, repo).replace("\\", "/")
        text = read(path)
        wf, perr = load_wf(text)
        if perr:
            continue
        ev = on_events(wf)
        perm = {}
        if isinstance(wf.get("permissions"), dict):
            perm.update(wf["permissions"])
        for j in (wf.get("jobs") or {}).values():
            if isinstance(j, dict) and isinstance(j.get("permissions"), dict):
                perm.update(j["permissions"])
        is_pages = ("pages" in perm or "deploy-pages" in text or "upload-pages-artifact" in text)
        literal = [p for p in trigger_paths(wf, "push") if not any(ch in p for ch in "*?[")]
        if is_pages:
            if literal:
                pub_paths[rel] = literal
        elif "pull_request" in ev:
            for p in trigger_paths(wf, "pull_request"):
                if not any(ch in p for ch in "*?["):
                    pr_files.add(p)
    for rel, items in pub_paths.items():
        for p in items:
            if p not in pr_files and not p.startswith(".github/workflows/"):
                fs.append(Finding("R14", rel, 0, "%s 只在发布时被验，PR 阶段没有任何检查覆盖它" % p))

    assign_ids(fs)
    return fs


def assign_ids(fs):
    """给同类同文件的实例编号：第 N 个出现即第 N 个指纹，可比、可棘轮。"""
    seen = {}
    for f in fs:
        key = (f.rule, f.path, f.detail)
        seen[key] = seen.get(key, 0) + 1
        f.idx = seen[key]


# ---------------- 过滤层：inline ignore → 配置 → persona → baseline ----------------

def collect_inline_ignores(repo):
    """返回 {rel_path: {line_no: [rule, ...]}}，注释行与其下一行算作同一 span。"""
    out = {}
    for path in wf_files(repo):
        rel = os.path.relpath(path, repo).replace("\\", "/")
        for i, ln in enumerate(read(path).splitlines(), 1):
            m = INLINE_IGNORE_RE.search(ln)
            if not m:
                continue
            rules = [x.strip().upper() for x in m.group(1).split(",") if x.strip()]
            for target in (i, i + 1):
                out.setdefault(rel, {}).setdefault(target, []).extend(rules)
    return out


def load_config(repo, explicit):
    p = explicit or os.path.join(repo, ".ci-guard.yml")
    if not os.path.isfile(p):
        return {}
    try:
        return (yaml.safe_load(read(p)) or {}) if HAS_YAML else {}
    except Exception:
        return {}


def apply_filters(fs, repo, cfg, persona, no_ignores, baseline):
    inline = {} if no_ignores else collect_inline_ignores(repo)

    # 1. inline ignore
    for f in fs:
        if f.rule in inline.get(f.path, {}).get(f.line, []):
            f.ignored = True
            f.ignore_reason = "inline"

    # 2. 配置 ignore 与 severity/enabled 覆盖
    for f in fs:
        rule_cfg = (cfg.get("rules") or {}).get(f.rule) or {}
        if rule_cfg.get("enabled") is False:
            f.ignored = True
            f.ignore_reason = "config:enabled=false"
        if rule_cfg.get("severity"):
            sev = str(rule_cfg["severity"]).upper()
            if sev in ("FAIL", "WARN", "OFF"):
                if sev == "OFF":
                    f.ignored = True
                    f.ignore_reason = "config:severity=off"
                else:
                    RULES[f.rule] = dict(RULES[f.rule], level=sev)
    if not no_ignores:
        for rid, patterns in (cfg.get("ignore") or {}).items():
            for f in fs:
                if f.rule != rid.upper():
                    continue
                for pat in (patterns or []):
                    if fnmatch.fnmatch(f.path, pat) or fnmatch.fnmatch("%s:%d" % (f.path, f.line), pat):
                        f.ignored = True
                        f.ignore_reason = "config:ignore"

    # 3. persona：regular 排除低置信
    if persona == "regular":
        for f in fs:
            if f.confidence == "low" and not f.ignored:
                f.ignored = True
                f.ignore_reason = "persona:regular"

    # 4. baseline：不在基线里的才算新增
    if baseline:
        known = set(baseline.get("fingerprints") or [])
        for f in fs:
            if f.fingerprint() in known and not f.ignored:
                f.ignored = True
                f.ignore_reason = "baseline"
    return fs


# ---------------- 输出 ----------------

def active(fs):
    return [f for f in fs if not f.ignored]


def summary(fs):
    a = active(fs)
    return {"total": len(fs), "active": len(a), "ignored": len(fs) - len(a),
            "fail": sum(1 for f in a if f.level == "FAIL"),
            "warn": sum(1 for f in a if f.level == "WARN")}


def emit_text(repo, fs, persona, degraded):
    s = summary(fs)
    print("ci-guard %s  repo=%s  persona=%s%s" % (
        VERSION, os.path.basename(os.path.abspath(repo)), persona,
        "  [DEGRADED：未装 pyyaml]" if degraded else ""))
    if not s["active"]:
        print("  全部通过（%d 条规则，%d 条被忽略）" % (len(RULES), s["ignored"]))
        return
    for f in active(fs):
        loc = "%s:%d" % (f.path, f.line) if f.line else f.path
        print("%s[%s] %s  %s" % (f.level, f.confidence[:1].upper(), f.rule, loc))
        print("    %s" % f.detail)
        print("    why: %s" % RULES[f.rule]["why"])
        print("    fix: %s   (%s)" % (f.fix, RULES[f.rule]["anchor"]))
    print("共 %d 项：FAIL %d / WARN %d（忽略 %d）" % (s["active"], s["fail"], s["warn"], s["ignored"]))


def emit_github(fs):
    """GitHub annotations：单个 step 最多渲染 10 条，超出的只进日志（zizmor 文档同一限制）。"""
    a = active(fs)
    for i, f in enumerate(a, 1):
        cmd = "error" if f.level == "FAIL" else "warning"
        msg = "%s — %s | fix: %s" % (f.detail, RULES[f.rule]["why"], f.fix)
        msg = msg.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        if i <= 10:
            title = (f.rule + " " + RULES[f.rule]["title"])[:40]
            print("::%s file=%s,line=%d,title=%s::%s" % (cmd, f.path, max(1, f.line), title, msg))
        else:
            print("（第 %d 条起不渲染为 annotation，仅日志）%s %s %s" % (i, f.rule, f.path, f.detail))


def emit_sarif(path, fs):
    rules = [{"id": k, "name": v["title"], "shortDescription": {"text": v["title"]},
              "fullDescription": {"text": v["why"]},
              "defaultConfiguration": {"level": "error" if v["level"] == "FAIL" else "warning"},
              "properties": {"confidence": v["confidence"], "anchor": v["anchor"]},
              "helpUri": "%s#%s" % (DOC_BASE, k.lower())} for k, v in RULES.items()]
    results = [{"ruleId": f.rule, "level": "error" if f.level == "FAIL" else "warning",
                "message": {"text": f.detail + " | fix: " + f.fix},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": f.path},
                                                    "region": {"startLine": max(1, f.line)}}}]}
               for f in active(fs)]
    doc = {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
           "runs": [{"tool": {"driver": {"name": "ci-guard", "version": VERSION, "rules": rules}},
                     "results": results}]}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)


def init_config(repo, fs):
    cfg_path = os.path.join(repo, ".ci-guard.yml")
    bl_path = os.path.join(repo, ".ci-guard-baseline.json")
    cfg = ("# ci-guard 配置（由 --init-config 生成）\n"
           "version: 1\n"
           "persona: regular          # regular | pedantic | auditor\n"
           "# rules:                  # 单条规则开关与级别覆盖\n"
           "#   R07: {enabled: false}\n"
           "#   R11: {severity: FAIL}\n"
           "# ignore:                  # 文件级忽略，支持 glob 与 file:line\n"
           "#   R02:\n"
           '#     - ".github/workflows/ci.yml"\n'
           '#     - ".github/workflows/ci.yml:51"\n')
    with open(cfg_path, "w", encoding="utf-8") as fh:
        fh.write(cfg)
    baseline = {"version": 1, "generated_by": "ci-guard " + VERSION,
                "repo": os.path.basename(os.path.abspath(repo)),
                "fingerprints": sorted({f.fingerprint() for f in active(fs)})}
    with open(bl_path, "w", encoding="utf-8") as fh:
        json.dump(baseline, fh, ensure_ascii=False, indent=1)
    print("已生成：")
    print("  %s（配置模板，全部规则默认开启）" % cfg_path)
    print("  %s（%d 条现有问题已冻结，之后只报新增）" % (bl_path, len(baseline["fingerprints"])))
    print("把这行加进 CI：python ci_guard.py . --baseline .ci-guard-baseline.json")


def load_baseline(path):
    if not path or not os.path.isfile(path):
        return None
    try:
        return json.loads(read(path))
    except Exception:
        return None


def exit_code(fs, sarif_mode, strict):
    a = active(fs)
    if not a:
        return 0
    if strict:
        return 14
    rank = {"low": 12, "medium": 13, "high": 14}
    if sarif_mode:
        return 0  # SARIF 消费者要求退出码 0，语义在 SARIF 里
    return max(rank.get(f.confidence, 13) for f in a)


def main():
    ap = argparse.ArgumentParser(prog="ci-guard")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--format", default=None, choices=["text", "json", "sarif", "github"])
    ap.add_argument("--json", action="store_true", help="等价于 --format=json")
    ap.add_argument("--sarif", help="写 SARIF 文件的路径")
    ap.add_argument("--persona", default=None, choices=["regular", "pedantic", "auditor"])
    ap.add_argument("--pedantic", action="store_true", help="等价于 --persona=pedantic")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--only", help="逗号分隔的规则 ID")
    ap.add_argument("--config", help="显式配置文件路径")
    ap.add_argument("--baseline", help="基线文件；不存在则先扫描并报错提示用 --init-config")
    ap.add_argument("--init-config", action="store_true")
    ap.add_argument("--no-ignores", action="store_true")
    a = ap.parse_args()

    if not os.path.isdir(a.repo):
        print("不是目录：%s" % a.repo, file=sys.stderr)
        return 2
    cfg = load_config(a.repo, a.config)
    persona = a.persona or ("pedantic" if a.pedantic else str(cfg.get("persona") or "regular"))
    fmt = "json" if a.json else (a.format or "text")

    fs = scan(a.repo)
    if a.only:
        keep = {x.strip().upper() for x in a.only.split(",")}
        fs = [f for f in fs if f.rule in keep]

    if a.init_config:
        init_config(a.repo, fs)
        return 0

    baseline = load_baseline(a.baseline) if a.baseline else None
    if a.baseline and baseline is None:
        print("基线文件不存在：%s（先跑 --init-config 生成）" % a.baseline, file=sys.stderr)
        return 2

    fs = apply_filters(fs, a.repo, cfg, persona, a.no_ignores, baseline)

    if fmt == "json":
        s = summary(fs)
        print(json.dumps({"version": VERSION, "repo": os.path.abspath(a.repo),
                          "persona": persona, "summary": s,
                          "findings": [f.as_dict() for f in fs]}, ensure_ascii=False, indent=1))
    elif fmt == "github":
        emit_github(fs)
    else:
        emit_text(a.repo, fs, persona, not HAS_YAML)
    if a.sarif:
        emit_sarif(a.sarif, fs)

    if not wf_files(a.repo):
        return 3
    return exit_code(fs, bool(a.sarif), a.strict)


if __name__ == "__main__":
    sys.exit(main())
