"""実験083 — 看板の文字を立体にする。細かさ・厚み・角の丸めは、何で決まるか。

<code>font</code> で文字の形を作り、<code>polyextrude</code> で厚みを付け、角を丸める。
手順ページに書くために、つまみの意味を数字で確かめる。

  A. 細かさ：font の Level of Detail を変えると、点の数と時間はどう変わるか
  B. 厚み：polyextrude の Distance は、そのまま奥行きになるか。
     Output Back を切ると何が起きるか（裏が空いた形になるのか）
  C. 角の丸め：polybevel の Offset をどこまで上げられるか。上げすぎると何が起きるか

    hython examples/083_text_sign.py a
    hython examples/083_text_sign.py b
    hython examples/083_text_sign.py c
    hython examples/083_text_sign.py shot
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

TEXT = "SP"
BEVEL_TYPE = None          # 最初に調べて決める（polybevel の名前）


def bevel_type(geo):
    global BEVEL_TYPE
    if BEVEL_TYPE is None:
        import hou
        for name in ("polybevel::3.0", "polybevel::2.0", "polybevel"):
            try:
                node = geo.createNode(name, "probe")
                node.destroy()
                BEVEL_TYPE = name
                break
            except hou.OperationFailed:
                continue
    return BEVEL_TYPE


def build(lod=1.0, dist=0.15, back=True, offset=None):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "sign")

    text = geo.createNode("font", "letters")
    text.parm("text").set(TEXT)
    text.parm("fontsize").set(1.0)
    text.parm("lod").set(lod)

    thick = geo.createNode("polyextrude::2.0", "thickness")
    thick.setFirstInput(text)
    thick.parm("dist").set(dist)
    thick.parm("outputback").set(1 if back else 0)
    last = thick

    if offset is not None:
        name = bevel_type(geo)
        bev = geo.createNode(name, "round")
        bev.setFirstInput(thick)
        for parm in ("offset", "offsetscale", "beveloffset"):
            if bev.parm(parm):
                bev.parm(parm).set(offset)
                break
        last = bev
    last.setDisplayFlag(True)
    last.setRenderFlag(True)
    geo.layoutChildren()
    return geo, text, thick, last


def stats(node):
    g = node.geometry()
    b = g.boundingBox()
    names = g.intrinsicNames()
    out = {"points": g.intrinsicValue("pointcount"),
           "prims": g.intrinsicValue("primitivecount"),
           "width": b.sizevec()[0], "height": b.sizevec()[1], "depth": b.sizevec()[2]}
    return out


def total_area(node):
    """角の丸めは点や面の数を変えないので、面積で見る（measure SOP で面ごとに出して合計）。"""
    import numpy
    geo = node.parent()
    m = geo.node("area_probe") or geo.createNode("measure::2.0", "area_probe")
    m.setFirstInput(node)
    if m.parm("type"):
        m.parm("type").set("area")
    values = m.geometry().primFloatAttribValues("area")
    return float(numpy.asarray(values, dtype=numpy.float64).sum())


def timed(node):
    start = time.perf_counter()
    node.cook(force=True)
    s = stats(node)
    s["seconds"] = time.perf_counter() - start
    return s


def part_a():
    print("A. font の Level of Detail（文字 \"%s\"・Font Size 1）" % TEXT)
    rows = []
    for lod in (0.2, 0.5, 1.0, 2.0, 4.0):
        geo, text, thick, last = build(lod=lod)
        s = timed(text)
        s["lod"] = lod
        rows.append(s)
        print(f"   LOD {lod:<4} | 点 {s['points']:>6} 面 {s['prims']:>4} | "
              f"幅 {s['width']:.4f} 高さ {s['height']:.4f} | {s['seconds'] * 1000:.1f}ms")
    with open(os.path.join(OUT, "083_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/083_a.json")


def part_b():
    print("B. polyextrude の Distance と Output Back")
    rows = []
    for dist in (0.05, 0.15, 0.4):
        for back in (True, False):
            geo, text, thick, last = build(dist=dist, back=back)
            s = timed(thick)
            s.update({"dist": dist, "back": back})
            rows.append(s)
            print(f"   Distance {dist:<5} Output Back {'入' if back else '切'} | 点 {s['points']:>6} 面 {s['prims']:>5} | "
                  f"奥行き {s['depth']:.6f} | {s['seconds'] * 1000:.1f}ms")
    with open(os.path.join(OUT, "083_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/083_b.json")


def part_c():
    import hou
    print("C. 角の丸め（%s）" % (bevel_type(hou.node("/obj").createNode("geo", "probe_geo")) or "polybevel が無い"))
    rows = []
    for offset in (0.0, 0.005, 0.01, 0.02, 0.04, 0.08, 0.15, 0.3):
        geo, text, thick, last = build(offset=offset)
        try:
            s = timed(last)
            s["area"] = total_area(last)
            errs = list(last.errors())
            warns = list(last.warnings())
        except hou.OperationFailed as exc:
            s = {"points": None, "prims": None, "depth": None, "seconds": None, "area": None}
            errs, warns = [str(exc)], []
        s.update({"offset": offset, "errors": errs, "warnings": warns})
        rows.append(s)
        print(f"   Offset {offset:<6} | 点 {s['points']} 面 {s['prims']} | "
              f"面積 {None if s.get('area') is None else round(s['area'], 6)} "
              f"体積 {None if s.get('volume') is None else round(s['volume'], 6)} | "
              f"{'' if s['seconds'] is None else round(s['seconds'] * 1000, 1)}ms"
              f"{' | エラー ' + str(errs) if errs else ''}{' | 警告 ' + str(warns) if warns else ''}")
    with open(os.path.join(OUT, "083_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/083_c.json")


SHOTS = {"flat": dict(dist=0.0), "thick": dict(dist=0.15),
         "round": dict(dist=0.15, offset=0.02)}


def shot(which="flat"):
    """1プロセスにつき1枚だけ撮る。続けて撮ると OpenGL の初期化に失敗することがある。"""
    import hou
    import hou_tools
    for name, kw in [(which, SHOTS[which])]:
        geo, text, thick, last = build(**kw)
        bbox = hou.BoundingBox(-0.1, -0.25, -0.35, 1.3, 0.85, 0.35)
        png = os.path.join(OUT, f"083_{name}.png")
        hou_tools.render_preview(last.path(), png, res=(520, 360), direction=(0.45, 0.35, 1.0),
                                 shading="smoothwire", frame_bbox=bbox, margin=1.05)
        print(f"保存: {png}")
        if name == "round":
            hou_tools.save_hip(os.path.join(OUT, "083_sign.hipnc"))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "flat")
    else:
        {"a": part_a, "b": part_b, "c": part_c}[arg]()
