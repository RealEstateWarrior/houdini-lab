"""実験059 — obj で渡せる範囲。何が残って、何が落ちるか。

実験058で、Apprentice から外へ出せるのは
<code>bgeo.sc</code> / <code>geo</code> / <code>obj</code> / <code>ply</code> /
<code>stl</code> の5つだけだと分かった。

このうち他のソフトが読めるのは <strong>obj</strong> と <strong>stl</strong>。
では obj で何が渡せて、何が落ちるのか。<strong>1つずつ持たせて往復させる。</strong>

  A. 形の種類（ポリゴン・線・点・NURBS）は残るか
  B. アトリビュート（色・UV・法線・名前・自作）は残るか
  C. グループは残るか
  D. 数はどう変わるか

    hython examples/059_obj_limits.py
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "059_stats.json")
EXP_DIR = os.path.join(OUT, "059_obj")

ATTRIB_VEX = """
@Cd = set(rand(@ptnum), rand(@ptnum + 7), rand(@ptnum + 13));
v@myvec = set(1.0, 2.0, 3.0);
f@myfloat = float(@ptnum) * 0.5;
i@myint = @ptnum;
s@mystring = sprintf("pt%d", @ptnum);
@pscale = 0.5;
if (@ptnum < 10) { @group_firstten = 1; }
"""


def build_case(kind):
    """1つの種類だけを持つジオメトリを作る。"""
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "case")

    if kind == "polygon":
        src = geo.createNode("sphere", "src")
        src.parm("type").set(2)
        src.parm("rows").set(12)
        src.parm("cols").set(12)
    elif kind == "line":
        src = geo.createNode("line", "src")
        src.parm("points").set(9)
        src.parm("dist").set(2.0)
    elif kind == "points":
        base = geo.createNode("sphere", "base")
        base.parm("type").set(2)
        src = geo.createNode("scatter::2.0", "src")
        src.setFirstInput(base)
        src.parm("npts").set(50)
    elif kind == "nurbs":
        src = geo.createNode("sphere", "src")
        src.parm("type").set(4)          # NURBS
    elif kind == "opencurve":
        base = geo.createNode("line", "base")
        base.parm("points").set(9)
        src = geo.createNode("resample", "src")
        src.setFirstInput(base)
    else:
        raise ValueError(kind)

    uv = geo.createNode("uvunwrap", "uv")
    uv.setFirstInput(src)
    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(uv)
    attribs = geo.createNode("attribwrangle", "attribs")
    attribs.setFirstInput(normal)
    attribs.parm("class").set(2)
    attribs.parm("snippet").set(ATTRIB_VEX)
    attribs.setDisplayFlag(True)
    attribs.setRenderFlag(True)
    geo.layoutChildren()
    return geo, attribs


def describe(geometry):
    if geometry is None:
        return None
    prim_types = {}
    for prim in geometry.prims():
        name = str(prim.type()).split(".")[-1]
        prim_types[name] = prim_types.get(name, 0) + 1
    return {
        "points": len(geometry.points()),
        "prims": len(geometry.prims()),
        "prim_types": prim_types,
        "point_attribs": sorted(a.name() for a in geometry.pointAttribs()),
        "vertex_attribs": sorted(a.name() for a in geometry.vertexAttribs()),
        "prim_attribs": sorted(a.name() for a in geometry.primAttribs()),
        "point_groups": sorted(g.name() for g in geometry.pointGroups()),
        "prim_groups": sorted(g.name() for g in geometry.primGroups()),
    }


def main():
    import hou
    os.makedirs(EXP_DIR, exist_ok=True)
    stats = {}

    kinds = ("polygon", "line", "points", "nurbs", "opencurve")
    labels = {"polygon": "面（ポリゴン）", "line": "線（1本）",
              "points": "点だけ", "nurbs": "NURBS の球",
              "opencurve": "開いたカーブ"}

    print("A・D. 形の種類は残るか")
    print(f"   {'種類':>14} {'点 元':>7} {'点 後':>7} {'面 元':>7} "
          f"{'面 後':>7} {'位置のずれ':>12} {'中身の変化'}")
    rows = []
    for kind in kinds:
        path = os.path.join(EXP_DIR, f"{kind}.obj")
        if os.path.exists(path):
            os.remove(path)
        geo, node = build_case(kind)
        before = describe(node.geometry())
        before_pos = [(float(p.position()[0]), float(p.position()[1]),
                       float(p.position()[2]))
                      for p in node.geometry().points()]
        node.geometry().saveToFile(path)

        g2 = hou.Geometry()
        g2.loadFromFile(path)
        after = describe(g2)
        after_pos = [(float(p.position()[0]), float(p.position()[1]),
                      float(p.position()[2])) for p in g2.points()]
        worst = None
        if len(before_pos) == len(after_pos):
            worst = max(math.dist(a, b)
                        for a, b in zip(before_pos, after_pos))
        change = (f"{before['prim_types']} → {after['prim_types']}")
        rows.append({"kind": kind, "label": labels[kind],
                     "before": before, "after": after, "worst": worst,
                     "bytes": os.path.getsize(path)})
        shown = "—" if worst is None else f"{worst:.9f}"
        print(f"   {labels[kind]:>14} {before['points']:>7} "
              f"{after['points']:>7} {before['prims']:>7} "
              f"{after['prims']:>7} {shown:>12} {change}")
    stats["kinds"] = rows

    print("\nB. アトリビュートは残るか（面のポリゴンで見る）")
    poly = [r for r in rows if r["kind"] == "polygon"][0]
    before, after = poly["before"], poly["after"]
    print(f"   {'置き場所':>10} {'書き出す前':>44} {'読み直した後'}")
    for where, key in (("点", "point_attribs"), ("バーテックス",
                                                 "vertex_attribs"),
                       ("プリミティブ", "prim_attribs")):
        print(f"   {where:>10} {str(before[key]):>44} {after[key]}")
    kept = [a for a in before["point_attribs"]
            if a in after["point_attribs"]]
    lost = [a for a in before["point_attribs"]
            if a not in after["point_attribs"]]
    print(f"   残った点のアトリビュート: {kept}")
    print(f"   落ちた点のアトリビュート: {lost}")
    stats["attribs"] = {"kept": kept, "lost": lost}

    print("\nC. グループは残るか")
    print(f"   点のグループ: {before['point_groups']} → "
          f"{after['point_groups']}")
    print(f"   面のグループ: {before['prim_groups']} → "
          f"{after['prim_groups']}")
    stats["groups"] = {"point_before": before["point_groups"],
                       "point_after": after["point_groups"],
                       "prim_before": before["prim_groups"],
                       "prim_after": after["prim_groups"]}

    print("\n   ファイルの大きさ")
    print(f"   {'種類':>14} {'バイト':>10} {'点あたり':>12}")
    for r in rows:
        pts = max(r["before"]["points"], 1)
        print(f"   {r['label']:>14} {r['bytes']:>10,} "
              f"{r['bytes'] / pts:>11.1f}B")

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/059_stats.json")


if __name__ == "__main__":
    main()
