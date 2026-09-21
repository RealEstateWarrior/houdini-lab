# -*- coding: utf-8 -*-
"""nodes_add_*.py の解説を nodes.json に混ぜ、つまみの名前を実測データと突き合わせる。

    python nodes_merge.py

out/_nodes_dump.json（Houdini 本体から取ったもの）に無いつまみ名を書いていたら
止める。手で書いた名前が間違っていないことを、毎回機械に確かめさせる。
"""
import io
import json
import os

import nodes_add_1
import nodes_add_2
import nodes_add_3
import nodes_add_4
import nodes_add_5
import nodes_notes

HERE = os.path.dirname(os.path.abspath(__file__))

# ページに出す順
ORDER = ["make", "shape", "deform", "measure", "vdb", "scatter", "attrib", "group", "flow", "pack",
         "uv", "program", "sim", "pop", "force", "terrain", "rig", "groom",
         "mpm", "obj", "rop", "vop"]

LABELS = {
    "make": "形を作る",
    "shape": "形を変える",
    "scatter": "ばらまく・複製する",
    "program": "プログラムで処理",
    "sim": "シミュレーション",
    "terrain": "地形を作る",
    "rig": "骨組みを作る",
    "groom": "毛を生やす",
    "mpm": "MPM（砂・雪・泥）",
}


def load_dump():
    """spec からつまみ名の集合を引く表と、名前だけで引く表を作る。"""
    path = os.path.join(HERE, "out", "_nodes_dump.json")
    with io.open(path, encoding="utf-8") as fp:
        rows = json.load(fp)
    by_name = {}
    for row in rows:
        if not row["ok"]:
            continue
        names = {p["name"] for p in row["parms"]}
        by_name.setdefault(row["name"], set()).update(names)
        # createNode("remesh") は remesh::2.0 になる。版を外した名前でも引けるように
        base = row["name"].split("::")[0]
        by_name.setdefault(base, set()).update(names)
    return by_name


def main():
    with io.open(os.path.join(HERE, "nodes.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    dump = load_dump()

    groups = {g["id"]: g for g in data["groups"]}
    added = 0
    unknown = []

    for module in (nodes_add_1, nodes_add_2, nodes_add_3, nodes_add_4,
                   nodes_add_5):
        for gid, label, note in getattr(module, "GROUPS_NEW", []):
            if gid not in groups:
                groups[gid] = {"id": gid, "label": label, "note": note,
                               "nodes": []}
                LABELS[gid] = label
        for gid, entries in module.ADD.items():
            if gid not in groups:
                groups[gid] = {"id": gid, "label": LABELS.get(gid, gid),
                               "nodes": []}
            have = {n["name"] for n in groups[gid]["nodes"]}
            for entry in entries:
                if entry["name"] in have:
                    continue
                # つまみの名前を実測データと突き合わせる
                known = dump.get(entry["name"])
                if known is not None:
                    for pname, _ in entry.get("params", []):
                        if pname not in known:
                            unknown.append((entry["name"], pname))
                groups[gid]["nodes"].append(entry)
                added += 1

    if unknown:
        print("Houdini に無いつまみ名を書いている:")
        for name, pname in unknown:
            print(f"  {name} の {pname}")
        raise SystemExit("直してから通す")

    data["groups"] = [groups[gid] for gid in ORDER if gid in groups]
    missing = nodes_notes.apply(data["groups"])
    if missing:
        print("書き足す先のノードが無い:", missing)
    total = sum(len(g["nodes"]) for g in data["groups"])
    with io.open(os.path.join(HERE, "nodes.json"), "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)
    print(f"{added} 件を足して、合計 {total} 件")
    for group in data["groups"]:
        print(f"  {group['id']}: {len(group['nodes'])}")


if __name__ == "__main__":
    main()
