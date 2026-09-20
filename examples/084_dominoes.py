"""実験084 — ドミノを倒す。間隔はどこまで空けられるか。倒れていく速さは。

高さ 0.6・厚み 0.08 の板を等間隔に並べ、最初の1枚に横向きの初速を与えて倒す。

  A. 間隔を 0.15 から 0.55 まで変えて、最後まで倒れるかどうかと、かかった時間を見る
  B. 倒れる境目の間隔を挟み撃ちで探す（板の高さ 0.6 との比で見る）
  C. 板の枚数を変えて、倒れていく速さ（1秒あたり何枚）が一定かを見る

倒れた判定は、板の「上向き」が まっすぐ上から 60度以上傾いたら倒れたとみなす。

    hython examples/084_dominoes.py a
    hython examples/084_dominoes.py b
    hython examples/084_dominoes.py c
    hython examples/084_dominoes.py shot
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

HEIGHT = 0.6
THICK = 0.08
WIDTH = 0.3
LAST = 160        # 24枚・間隔 0.55 は 96フレームでは終わらなかった
FPS = 24.0
PUSH = 1.6            # 最初の1枚に与える横向きの初速


def build(gap=0.3, count=12):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "dominoes")

    line = geo.createNode("line", "spots")
    line.parmTuple("origin").set((0.0, HEIGHT / 2, 0.0))
    line.parmTuple("dir").set((1.0, 0.0, 0.0))
    line.parm("dist").set(gap * (count - 1))
    line.parm("points").set(count)

    tile = geo.createNode("box", "tile")
    tile.parmTuple("size").set((THICK, HEIGHT, WIDTH))

    copies = geo.createNode("copytopoints::2.0", "tiles")
    copies.setInput(0, tile)
    copies.setInput(1, line)
    copies.parm("pack").set(1)             # 実験082。細かくなくても、まとめたほうが軽い

    push = geo.createNode("attribwrangle", "push_first")
    push.setFirstInput(copies)
    push.parm("class").set(1)              # Primitives（1枚＝1つの塊）
    # 初速は「点」に付ける。プリミティブに v を付けても、rbdbulletsolver は見ない
    push.parm("snippet").set(
        "int pts[] = primpoints(0, @primnum);\n"
        f"setpointattrib(0, \"v\", pts[0], (@primnum == 0) ? set({PUSH}, 0, 0) : set(0, 0, 0));")

    solver = geo.createNode("rbdbulletsolver", "solve")
    solver.setFirstInput(push)
    solver.parm("useground").set(True)
    solver.parm("startframe").set(1)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, solver


def tilts(node):
    """各板の「上向き」が、まっすぐ上から何度傾いたか。"""
    import hou
    out = []
    for prim in node.geometry().prims():
        m = prim.intrinsicValue("transform")
        up = hou.Vector3(m[3], m[4], m[5]).normalized()
        out.append(math.degrees(math.acos(max(-1.0, min(1.0, up.dot(hou.Vector3(0, 1, 0)))))))
    return out


def run(gap, count=12):
    import hou
    geo, solver = build(gap, count)
    fell = {}
    start = time.perf_counter()
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        for i, t in enumerate(tilts(solver)):
            if i not in fell and t > 60.0:
                fell[i] = frame
    seconds = time.perf_counter() - start
    last_tilts = tilts(solver)
    done = len(fell) == count
    span = (max(fell.values()) - min(fell.values())) / FPS if len(fell) > 1 else None
    return {"gap": gap, "count": count, "fell": len(fell), "all": done,
            "first_frame": min(fell.values()) if fell else None,
            "last_frame": max(fell.values()) if fell else None,
            "span_sec": span,
            "per_sec": (len(fell) - 1) / span if span else None,
            "tilt_min": min(last_tilts), "tilt_mean": sum(last_tilts) / len(last_tilts),
            "seconds": seconds}


def show(r):
    span = "—" if r["span_sec"] is None else f"{r['span_sec']:.3f}秒"
    rate = "—" if not r["per_sec"] else f"1秒に {r['per_sec']:.2f}枚"
    print(f"   間隔 {r['gap']:<6}（高さの {r['gap'] / HEIGHT:.2f}倍） 枚数 {r['count']:>3} | "
          f"倒れた {r['fell']}/{r['count']} {'すべて' if r['all'] else '途中で止まった'} | "
          f"F{r['first_frame']}〜F{r['last_frame']}（{span}・{rate}） | "
          f"最後の傾き 最小 {r['tilt_min']:.1f}度 平均 {r['tilt_mean']:.1f}度 | {r['seconds']:.2f}秒")


def part_a():
    print("A. 間隔を変える（12枚・高さ 0.6・厚み 0.08）")
    rows = []
    for gap in (0.15, 0.25, 0.35, 0.45, 0.55):
        r = run(gap)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "084_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/084_a.json")


def edge(lo, hi, want_all_at_lo=True, steps=5):
    """lo は「最後まで倒れる」側、hi は「途中で止まる」側。間を詰める。"""
    tried = []
    for _ in range(steps):
        mid = round(0.5 * (lo + hi), 4)
        r = run(mid)
        tried.append(r)
        show(r)
        if r["all"] == want_all_at_lo:
            lo = mid
        else:
            hi = mid
    return lo, hi, tried


def part_b():
    print("B. 最後まで倒れる間隔の境目（12枚）")
    print("  B1. 狭いほうの境目（0.15 は途中で止まる、0.25 は全部倒れる）")
    hi1, lo1, t1 = edge(0.25, 0.15, want_all_at_lo=True)
    print(f"   → 狭いほうの境目は {lo1}〜{hi1}（高さの {lo1 / HEIGHT:.2f}〜{hi1 / HEIGHT:.2f}倍）")
    print("  B2. 広いほうの境目（0.45 は全部倒れる、0.55 は途中で止まる）")
    lo2, hi2, t2 = edge(0.45, 0.55, want_all_at_lo=True)
    print(f"   → 広いほうの境目は {lo2}〜{hi2}（高さの {lo2 / HEIGHT:.2f}〜{hi2 / HEIGHT:.2f}倍）")
    with open(os.path.join(OUT, "084_b.json"), "w", encoding="utf-8") as fp:
        json.dump({"narrow": {"lo": lo1, "hi": hi1, "tried": t1},
                   "wide": {"lo": lo2, "hi": hi2, "tried": t2}}, fp, ensure_ascii=False, indent=2)
    print("保存: out/084_b.json")


def part_c():
    print("C. 枚数を変える（間隔 0.3）")
    rows = []
    for count in (6, 12, 24):
        r = run(0.3, count)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "084_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/084_c.json")


def shot(frame="40"):
    import hou
    import hou_tools
    geo, solver = build(0.3, 12)
    frame = int(frame)
    for f in range(1, frame + 1):
        hou.setFrame(f)
        solver.geometry()
    hou_tools.save_hip(os.path.join(OUT, "084_dominoes.hipnc"))
    bbox = hou.BoundingBox(-0.6, -0.05, -0.6, 3.9, 0.9, 0.6)
    png = os.path.join(OUT, f"084_dominoes_{frame}.png")
    hou_tools.render_preview(solver.path(), png, res=(760, 340), direction=(0.25, 0.45, 1.0),
                             shading="smoothwire", frame_bbox=bbox, margin=1.03)
    print(f"保存: {png}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "40")
    else:
        {"a": part_a, "b": part_b, "c": part_c}[arg]()
