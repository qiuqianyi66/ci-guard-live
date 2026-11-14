# ci-guard-live

把《企业级 AI Native 项目开发全流程白皮书》附录 AV–AW 的 CI 判据，接进一条真实的 GitHub Actions 流水线。

这是一个演练仓，不是产品仓。

## 里面有什么

- `tools/ci-guard/` —— 检查器本体，17 条规则，249 KB，除 pyyaml 外零依赖
- `.github/workflows/demo.yml` —— **被检对象**，故意留了两处问题：`actions/checkout@v4` 未 pin、整个文件没有任何 `permissions`
- `.github/workflows/guard.yml` —— **检查器自己的 job**，跑 `--format=github`，把命中变成 PR/提交行上的 annotation
- `tools/ci-guard/docs/RULES.md` —— 17 条规则逐页说明
- `tools/ci-guard/COVERAGE.md` —— 与 actionlint、zizmor 的边界

## 预期结果

`guard` job 会报出 `demo.yml` 的两条 FAIL：

- **R01** action 未 pin 到 40 位 SHA（AV.6）
- **R05** 顶层与 job 级都没有 permissions（AW.7）

并以 `exit 14` 阻断。这是有意的：一个检查器如果在自己的演示里都不能让红，它就没有资格去判别人。

想让它变绿，改 `demo.yml` 的两处即可；或者用 `--baseline` 把现状冻结，只报新增。

## 本地跑

```bash
pip install pyyaml==6.0.3
python tools/ci-guard/ci_guard.py . --format=github
python tools/ci-guard/selftest.py          # 回归自测，7 项
python tools/ci-guard/verify_sarif.py out.sarif
```
