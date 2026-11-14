# -*- coding: utf-8 -*-
"""用官方 SARIF 2.1.0 schema 校验 ci-guard 的输出。

我自己在 selftest 里写的字段断言，只能覆盖我想到的字段；官方 schema 覆盖整份规范。
GitHub 的 upload-sarif 在服务端做的也是同类结构校验，所以这一步通过之后，
剩下未验证的只是平台侧行为（需要 token + 一个启用了 code scanning 的仓库）。

用法：python verify_sarif.py <file.sarif>
依赖：jsonschema（schema 已随工具离线缓存，不联网）
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "schema", "sarif-2.1.0.json")


def main():
    if len(sys.argv) < 2:
        print("usage: python verify_sarif.py <file.sarif>")
        return 2
    target = sys.argv[1]
    if not os.path.isfile(target):
        print("找不到 %s" % target)
        return 2
    if not os.path.isfile(SCHEMA):
        print("缺少 schema：%s" % SCHEMA)
        return 2
    try:
        from jsonschema.validators import validator_for
    except ImportError:
        print("未安装 jsonschema（pip install jsonschema）")
        return 1

    with open(SCHEMA, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    with open(target, "r", encoding="utf-8") as fh:
        doc = json.load(fh)

    V = validator_for(schema)(schema)
    errs = sorted(V.iter_errors(doc), key=lambda e: list(e.path))
    if not errs:
        n_res = sum(len(r.get("results") or []) for r in doc.get("runs") or [])
        print("OK：通过官方 SARIF 2.1.0 schema 校验（%d run / %d results）"
              % (len(doc.get("runs") or []), n_res))
        return 0
    print("不通过：%d 处" % len(errs))
    for e in errs[:15]:
        where = "/".join(str(p) for p in e.path) or "<root>"
        print("  %s -> %s" % (where, e.message[:220]))
    if len(errs) > 15:
        print("  ... 其余 %d 处略" % (len(errs) - 15))
    return 1


if __name__ == "__main__":
    sys.exit(main())
