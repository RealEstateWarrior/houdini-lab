# -*- coding: utf-8 -*-
"""実験134 — 最初から式が入っているつまみは、どれだけあるか。

実験133 で、ray の Direction には最初から @N.x などの式が入っていて、
Python の set では値が変わらないと分かった。同じ落とし穴がほかにどれだけあるかを、
SOP の全ノード（隠し・古いものを除く）を1つずつ作って数える。

あわせて、式の入ったつまみに set したとき何が起きるかを確かめる:
  - 値（eval）は変わるか
  - 式は残るか

    hython examples/134_default_expr.py
"""
import json
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    import hou
    geo = sop_bench.fresh()
    cat = hou.sopNodeTypeCategory()
    t0 = time.perf_counter()
    found, made, failed = [], 0, 0
    for name, ntype in sorted(cat.nodeTypes().items()):
        if ntype.hidden() or ntype.deprecated():
            continue
        try:
            node = geo.createNode(name)
        except hou.Error:
            failed += 1
            continue
        made += 1
        for p in node.parms():
            if p.keyframes():
                try:
                    expr = p.expression()
                except hou.Error:
                    expr = "(keyframe)"
                found.append({"node": name, "parm": p.name(), "label": p.description(),
                              "expr": expr[:80]})
        node.destroy()
    sec = time.perf_counter() - t0
    per_node = Counter(f["node"] for f in found)
    exprs = Counter(f["expr"] for f in found)

    # set したら何が起きるか（ray の dir で）
    ray = geo.createNode("ray", "probe")
    p = ray.parm("diry")
    before = (p.expression(), p.eval())
    p.set(-1.0)
    after_set = (p.expression() if p.keyframes() else None, p.eval())
    p.deleteAllKeyframes()
    p.set(-1.0)
    after_delete = (p.expression() if p.keyframes() else None, p.eval())

    out = {"nodes_made": made, "failed": failed, "sec": round(sec, 1),
           "parms_with_expr": len(found), "nodes_with_expr": len(per_node),
           "top_nodes": per_node.most_common(15), "top_exprs": exprs.most_common(15),
           "found": found,
           "set_probe": {"before": before, "after_set": after_set, "after_delete": after_delete}}
    path = os.path.join(sop_bench.OUT, "134_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)
    print({k: v for k, v in out.items() if k != "found"})
    print("書いた:", path)


if __name__ == "__main__":
    main()
