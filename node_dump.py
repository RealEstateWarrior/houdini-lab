# -*- coding: utf-8 -*-
"""ノードの素性を Houdini 本体から吐き出す。

    "…/hython.exe" node_dump.py 出力先.json sop/box sop/sphere …
    "…/hython.exe" node_dump.py 出力先.json --file 一覧.txt

つまみのラベルを手で書くと間違える。Houdini に聞いて、返ってきたものだけを書く。

型（nodeType）に聞くと、フォルダの中や親から受け継いだつまみが漏れる。
たとえばカメラの focal は型の一覧には出てこない。そこで実物を1つ作り、
その node.parms() を読む。作れなかったものは、その旨を残す。
"""
import json
import sys

import hou

HOLDERS = {}


def holder(category):
    """そのノードを作れる場所を用意する（無ければ作る）。"""
    if category in HOLDERS:
        return HOLDERS[category]
    if category == "sop":
        node = hou.node("/obj").createNode("geo", "dump_geo")
    elif category == "dop":
        node = hou.node("/obj").createNode("dopnet", "dump_dop")
    elif category == "obj":
        node = hou.node("/obj")
    elif category == "rop":
        node = hou.node("/out")
    elif category == "vop":
        node = hou.node("/mat") or hou.node("/shop")
    elif category == "lop":
        node = hou.node("/stage")
    else:
        node = None
    HOLDERS[category] = node
    return node


def parm_rows(node):
    """つまみを (内部名, 画面のラベル, 既定値, 種類) で返す。"""
    rows = []
    seen = set()
    for parm in node.parms():
        template = parm.parmTemplate()
        name = template.name()
        if name in seen:
            continue
        seen.add(name)
        kind = type(template).__name__.replace("ParmTemplate", "")
        try:
            default = template.defaultValue()
        except AttributeError:
            default = None
        if isinstance(default, tuple):
            default = list(default)
        menu = []
        try:
            if template.menuItems():
                menu = [[a, b] for a, b in
                        zip(template.menuItems(), template.menuLabels())]
        except AttributeError:
            pass
        rows.append({
            "name": name,
            "label": template.label(),
            "default": default,
            "kind": kind,
            "menu": menu[:12],
        })
    return rows


def dump(spec):
    """spec は "sop/box" のような category/name。"""
    category, _, name = spec.partition("/")
    place = holder(category)
    if place is None:
        return {"spec": spec, "ok": False, "why": "作る場所が分からない"}
    try:
        node = place.createNode(name, "dump_tmp")
    except hou.OperationFailed:
        return {"spec": spec, "ok": False, "why": "この版には無い"}
    except Exception as err:          # noqa: BLE001 - 何が来ても記録する
        return {"spec": spec, "ok": False, "why": "作れない: %s" % err}
    node_type = node.type()
    result = {
        "spec": spec,
        "ok": True,
        "category": category.upper(),
        "name": node_type.name(),
        "label": node_type.description(),
        "parms": parm_rows(node),
        "min_inputs": node_type.minNumInputs(),
        "max_inputs": node_type.maxNumInputs(),
    }
    node.destroy()
    return result


def main():
    out_path = sys.argv[1]
    specs = sys.argv[2:]
    if specs[:1] == ["--file"]:
        with open(specs[1], encoding="utf-8") as fp:
            specs = [line.strip() for line in fp
                     if line.strip() and not line.startswith("#")]
    result = [dump(spec) for spec in specs]
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=1)
    ok = sum(1 for item in result if item["ok"])
    print("%d / %d 件を取得。版 %s"
          % (ok, len(result), hou.applicationVersionString()))
    for item in result:
        if not item["ok"]:
            print("  取れず:", item["spec"], item["why"])


main()
