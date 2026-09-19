"""実験082 — 道に沿って物を並べる。間隔・向き・重さを測る。

S字の道（曲線）に沿って、両側に杭を並べる。手順ページに書くために、3つを確かめる。

  A. 間隔：resample の Length 1.0 で切ると、点の間隔は本当に 1.0 か。最後の区間はどうなるか
     （Maintain Last Vertex の入り・切りで比べる）
  B. 向き：杭の「前」（+Z）を道の向き（tangentu）に、「上」（+Y）を真上にそろえられるか
       N だけ入れる / N と up を入れる / 何も入れない の3通りで、ずれの角度を測る
  C. 重さ：細かい形（球 48 × 48）を 1,000 / 10,000 点に配る。Pack and Instance の入り・切りで、
     計算の時間と点の数を比べる

    hython examples/082_along_path.py a
    hython examples/082_along_path.py b
    hython examples/082_along_path.py c
    hython examples/082_along_path.py shot
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

ROAD = ("float t = @P.x;\n"
        "@P.z = 3.0 * sin(t * 0.35);\n"
        "@P.y = 0.0;")


def build_path(geo, length=1.0, last=False, tangent=True):
    line = geo.createNode("line", "road_line")
    line.parmTuple("origin").set((0.0, 0.0, 0.0))
    line.parmTuple("dir").set((1.0, 0.0, 0.0))
    line.parm("dist").set(20.0)
    line.parm("points").set(400)
    bend = geo.createNode("attribwrangle", "s_curve")
    bend.setFirstInput(line)
    bend.parm("snippet").set(ROAD)
    rs = geo.createNode("resample", "spacing")
    rs.setFirstInput(bend)
    rs.parm("length").set(length)
    rs.parm("last").set(1 if last else 0)
    rs.parm("dotangentattr").set(1 if tangent else 0)
    return bend, rs


def curve_length(node):
    g = node.geometry()
    pts = [p.position() for p in g.prims()[0].points()]
    return sum((b - a).length() for a, b in zip(pts, pts[1:]))


def part_a():
    import hou
    print("A. resample の Length 1.0 で切った間隔")
    rows = []
    for last in (False, True):
        hou.hipFile.clear(suppress_save_prompt=True)
        geo = hou.node("/obj").createNode("geo", "path")
        bend, rs = build_path(geo, 1.0, last)
        total = curve_length(bend)
        pts = [p.position() for p in rs.geometry().prims()[0].points()]
        gaps = [(b - a).length() for a, b in zip(pts, pts[1:])]
        # 元の曲線は 400点の折れ線。resample の間隔は直線距離で測る
        row = {"last": last, "curve_length": total, "points": len(pts),
               "gap_min": min(gaps[:-1]), "gap_max": max(gaps[:-1]), "last_gap": gaps[-1],
               "end_error": (pts[-1] - bend.geometry().prims()[0].points()[-1].position()).length()}
        rows.append(row)
        print(f"   Maintain Last Vertex {'入' if last else '切'} | 曲線の長さ {total:.4f} | 点 {len(pts)} | "
              f"間隔（最後以外） {row['gap_min']:.6f}〜{row['gap_max']:.6f} | 最後の間隔 {row['last_gap']:.6f} | "
              f"終点とのずれ {row['end_error']:.6f}")
    with open(os.path.join(OUT, "082_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/082_a.json")


HILLY = ("float t = @P.x;\n"
         "@P.z = 3.0 * sin(t * 0.35);\n"
         "@P.y = 1.2 * sin(t * 0.6);")


def build_posts(mode, pack=True, hilly=False):
    """mode: "n_up"（N と up）/ "n"（N だけ）/ "none"（何もしない）"""
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "road")
    bend, rs = build_path(geo, 1.0, True)
    if hilly:
        bend.parm("snippet").set(HILLY)
    aim = geo.createNode("attribwrangle", "aim")
    aim.setFirstInput(rs)
    code = {"n_up": "@N = normalize(v@tangentu);\nv@up = {0, 1, 0};",
            "n": "@N = normalize(v@tangentu);",
            "none": "// 向きは入れない"}[mode]
    aim.parm("snippet").set(code)
    post = geo.createNode("box", "post")
    post.parmTuple("size").set((0.15, 1.0, 0.5))      # 前後（z）に長い杭
    post.parm("ty").set(0.5)
    copy = geo.createNode("copytopoints::2.0", "posts")
    copy.setInput(0, post)
    copy.setInput(1, aim)
    copy.parm("pack").set(1 if pack else 0)
    copy.setDisplayFlag(True)
    geo.layoutChildren()
    return geo, aim, copy


def part_b():
    import hou
    print("B. 杭の向き。前（+Z）と道の向きのずれ、横（+X）の傾き（ロール）")
    rows = []
    for hilly in (False, True):
        for mode in ("n_up", "n", "none"):
            geo, aim, copy = build_posts(mode, hilly=hilly)
            tans = [hou.Vector3(p.attribValue("tangentu")).normalized() for p in aim.geometry().points()]
            fwd_err, roll = [], []
            for prim, t in zip(copy.geometry().prims(), tans):
                m = prim.intrinsicValue("transform")          # 3×3。行が各軸の行き先
                x = hou.Vector3(m[0], m[1], m[2]).normalized()
                z = hou.Vector3(m[6], m[7], m[8]).normalized()
                fwd_err.append(math.degrees(math.acos(max(-1.0, min(1.0, z.dot(t))))))
                # 横の軸が水平からどれだけ傾いたか。0 なら転がっていない
                roll.append(math.degrees(math.asin(max(-1.0, min(1.0, abs(x[1]))))))
            row = {"hilly": hilly, "mode": mode, "copies": len(fwd_err),
                   "fwd_max": max(fwd_err), "fwd_mean": sum(fwd_err) / len(fwd_err),
                   "roll_max": max(roll), "roll_mean": sum(roll) / len(roll)}
            rows.append(row)
            print(f"   {'起伏あり' if hilly else '平ら'} {mode:<5} | {row['copies']}本 | 前のずれ 最大 {row['fwd_max']:.4f}度 "
                  f"平均 {row['fwd_mean']:.4f}度 | 横の傾き 最大 {row['roll_max']:.4f}度 平均 {row['roll_mean']:.4f}度")
    with open(os.path.join(OUT, "082_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/082_b.json")


def part_c():
    import hou
    print("C. 細かい球（48 × 48）を配る。Pack and Instance の入り・切り")
    rows = []
    for count in (1000, 10000):
        for pack in (False, True):
            times = []
            for rep in range(3):
                seconds, g = fresh_copy(count, pack)
                times.append(seconds)
            times.sort()
            side = int(round(math.sqrt(count)))
            row = {"count": side * side, "pack": pack, "seconds": times[1], "all": times,
                   "points": g.intrinsicValue("pointcount"), "prims": g.intrinsicValue("primitivecount"),
                   "memory_mb": g.intrinsicValue("memoryusage") / 1024 / 1024}
            rows.append(row)
            print(f"   {row['count']:>6}個 Pack {'入' if pack else '切'} | 3回の中央値 {row['seconds'] * 1000:.1f}ms "
                  f"（{', '.join(f'{t * 1000:.1f}' for t in times)}） | 点 {row['points']:,} 面 {row['prims']:,} | "
                  f"メモリ {row['memory_mb']:.1f}MB")
    with open(os.path.join(OUT, "082_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/082_c.json")


def fresh_copy(count, pack):
    """毎回まっさらに組み、配る直前までを計算させてから、copytopoints の最初の計算を測る。

    上流の板をわずかに動かして測ると、22,100,000点のコピーが 9.5ms と出た。
    位置だけが変わったときは、全部を作り直していないらしい。だから毎回組み直す。
    """
    import hou
    if True:
            hou.hipFile.clear(suppress_save_prompt=True)
            geo = hou.node("/obj").createNode("geo", "many")
            grid = geo.createNode("grid", "targets")
            side = int(round(math.sqrt(count)))
            grid.parm("rows").set(side)
            grid.parm("cols").set(side)
            grid.parmTuple("size").set((side * 0.5, side * 0.5))
            ball = geo.createNode("sphere", "ball")
            ball.parm("type").set(2)
            ball.parm("rows").set(48)
            ball.parm("cols").set(48)
            ball.parmTuple("rad").set((0.2, 0.2, 0.2))
            copy = geo.createNode("copytopoints::2.0", "copies")
            copy.setInput(0, ball)
            copy.setInput(1, grid)
            copy.parm("pack").set(1 if pack else 0)
            ball.geometry()
            grid.geometry()
            start = time.perf_counter()
            g = copy.geometry()
            # 点の数は Houdini 側で数えさせる。len(g.points()) だと
            # 2,210万点を Python の一覧にする時間が乗ってしまう（実験077）
            n = g.intrinsicValue("pointcount")
            return time.perf_counter() - start, g


def shot():
    """道の両側に杭を立てる。道の真ん中の線から、横へ ±1.2 ずらした点に配る。"""
    import hou
    import hou_tools
    geo, aim, copy = build_posts("n_up")
    aim.parm("snippet").set(
        "@N = normalize(v@tangentu);\n"
        "v@up = {0, 1, 0};\n"
        "// 道の横向き＝向き × 上。左右に 1.2 ずつずらした点を作る\n"
        "vector side = normalize(cross(@N, v@up));\n"
        "int twin = addpoint(0, @P - side * 1.2);\n"
        "setpointattrib(0, 'N', twin, @N);\n"
        "setpointattrib(0, 'up', twin, v@up);\n"
        "@P += side * 1.2;")
    road = geo.createNode("sweep::2.0", "road")
    road.setFirstInput(geo.node("spacing"))
    road.parm("surfaceshape").set("ribbon")
    if road.parm("width"):
        road.parm("width").set(2.0)
    road.parm("upvectortype").set("y")
    both = geo.createNode("merge", "show")
    both.setInput(0, road)
    both.setInput(1, copy)
    both.setDisplayFlag(True)
    both.setRenderFlag(True)
    geo.layoutChildren()
    start = time.perf_counter()
    n = len(copy.geometry().prims())
    print(f"杭 {n}本・道の面 {len(road.geometry().prims())}枚 / {time.perf_counter() - start:.3f}秒")
    hou_tools.save_hip(os.path.join(OUT, "082_path.hipnc"))
    png = os.path.join(OUT, "082_posts.png")
    hou_tools.render_preview(both.path(), png, res=(760, 420), direction=(0.25, 0.9, 1.0),
                             shading="smoothwire", margin=1.04)
    print(f"保存: {png}")


def shot_roll(mode):
    """起伏のある道で、N だけ / N と up の杭の傾きを見比べる。"""
    import hou
    import hou_tools
    geo, aim, copy = build_posts(mode, hilly=True)
    line = geo.createNode("sweep::2.0", "road")
    line.setFirstInput(geo.node("spacing"))
    line.parm("surfaceshape").set("ribbon")
    line.parm("width").set(0.6)
    line.parm("upvectortype").set("y")
    both = geo.createNode("merge", "show")
    both.setInput(0, line)
    both.setInput(1, copy)
    both.setDisplayFlag(True)
    both.setRenderFlag(True)
    png = os.path.join(OUT, f"082_roll_{mode}.png")
    hou_tools.render_preview(both.path(), png, res=(760, 360), direction=(0.0, 0.35, 1.0),
                             shading="smoothwire", margin=1.04)
    print(f"保存: {png}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "roll":
        shot_roll(sys.argv[2])
        sys.exit(0)
    {"a": part_a, "b": part_b, "c": part_c, "shot": shot}[sys.argv[1] if len(sys.argv) > 1 else "a"]()
