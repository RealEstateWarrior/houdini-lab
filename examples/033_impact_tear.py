"""実験033 — 布を物にぶつけて破る。当たった場所から裂けるか。

実験032では、布の重さだけで貼り目を外した。線は自分で決めた波の形で、
どこが破れるかは最初から決まっていた。

今回は<strong>ぶつける</strong>。格子状に切れ目を入れた布を吊るし、球を投げ込む。
当たったところの貼り目に力が集中するはずなので、

  <strong>ぶつけた場所の近くから裂け、遠くは残る</strong>

はずである。これを数字で確かめる。

  A. 球を通したときと通さないときで、外れた貼り目の数が変わるか
  B. 外れた貼り目は、球が通った場所の近くに偏っているか
  C. しきい値を上げていくと、外れる数はどう減るか

否定できる形にする。外れた貼り目が球の位置と無関係にばらけていれば、
「当たったところから裂ける」は言えない。

    hython examples/033_impact_tear.py
    hython examples/033_impact_tear.py shot hit
    hython examples/033_impact_tear.py shot miss
"""

import json
import math
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

LAST = 36
SHOT_FRAME = 26
SHOT_RES = (560, 560)
BBOX_PATH = os.path.join(OUT, "033_bbox.json")

# 布を割る格子の間隔。この線に沿って切れ目が入る。
CELLS = 4
BALL_R = 0.42
BALL_START_Z = -2.6
BALL_SPEED = 0.16          # 1フレームあたり z 方向へ進む距離


def build(with_ball=True, threshold=200.0, ball_x=0.0, ball_y=2.2,
          speed=BALL_SPEED, last=LAST):
    """格子状に切り分けて貼り直した布。球が奥から手前へ飛んでくる。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "impact")

    grid = geo.createNode("grid", "cloth")
    grid.parm("orient").set(0)          # XY 平面。縦に立てる
    grid.parm("sizex").set(3.0)
    grid.parm("sizey").set(3.0)
    grid.parm("rows").set(45)
    grid.parm("cols").set(45)
    grid.parmTuple("t").set((0, 2.2, 0))

    # 面を格子のマス目に振り分ける。隣り合うマスは別の番号になる。
    mark = geo.createNode("attribwrangle", "mark_cells")
    mark.setFirstInput(grid)
    mark.parm("class").set(1)           # プリミティブ
    mark.parm("snippet").set(
        f"int cx = int(floor((@P.x + 1.5) / 3.0 * {CELLS}));\n"
        f"int cy = int(floor((@P.y - 0.7) / 3.0 * {CELLS}));\n"
        f"i@cell = clamp(cx, 0, {CELLS - 1}) * {CELLS} "
        f"+ clamp(cy, 0, {CELLS - 1});")

    # マスごとに切り出して合流させる。切り口の点が二重になり、
    # そこを glue が拾う（実験032と同じ手）。
    pieces = []
    for index in range(CELLS * CELLS):
        piece = geo.createNode("blast", f"cell_{index}")
        piece.setFirstInput(mark)
        piece.parm("group").set(f"@cell!={index}")
        piece.parm("grouptype").set(4)  # 4=面。1 はブレークポイントなので効かない
        pieces.append(piece)

    both = geo.createNode("merge", "cells")
    for slot, piece in enumerate(pieces):
        both.setInput(slot, piece)

    pins = geo.createNode("attribwrangle", "make_pins")
    pins.setFirstInput(both)
    pins.parm("snippet").set("if (@P.y > 3.63) { @group_pins = 1; }")

    cloth = geo.createNode("vellumconstraints", "cloth")
    cloth.setFirstInput(pins)
    cloth.parm("constrainttype").set("cloth")
    cloth.parm("stretchstiffness").set(1.0)

    glue = geo.createNode("vellumconstraints", "glue")
    glue.setInput(0, cloth, 0)
    glue.setInput(1, cloth, 1)
    glue.parm("constrainttype").set("glue")
    glue.parm("dobreaking").set(True)
    glue.parm("breakthreshold").set(threshold)

    pin = geo.createNode("vellumconstraints", "pin")
    pin.setInput(0, glue, 0)
    pin.setInput(1, glue, 1)
    pin.parm("constrainttype").set("pin")
    pin.parm("grouptype").set("points")
    pin.parm("group").set("pins")

    solver = geo.createNode("vellumsolver", "solve")
    solver.setInput(0, pin, 0)
    solver.setInput(1, pin, 1)
    solver.parm("startframe").set(1)

    ball = None
    if with_ball:
        ball = geo.createNode("sphere", "ball")
        ball.parm("type").set(2)        # Polygon Mesh。rows/cols が効く型
        ball.parm("rows").set(24)
        ball.parm("cols").set(24)
        ball.parmTuple("rad").set((BALL_R, BALL_R, BALL_R))
        ball.parm("tx").setExpression(str(ball_x))
        ball.parm("ty").setExpression(str(ball_y))
        ball.parm("tz").setExpression(
            f"{BALL_START_Z} + ($FF - 1) * {speed}")
        solver.setInput(2, ball)

    geo.layoutChildren()
    return geo, grid, pin, solver, ball


def stitch_rows(constraint_geo):
    """stitch 拘束の位置（重心）を集める。"""
    rows = []
    for prim in constraint_geo.prims():
        if prim.attribValue("type") != "stitch":
            continue
        points = [v.point().position() for v in prim.vertices()]
        if not points:
            continue
        rows.append((sum(p[0] for p in points) / len(points),
                     sum(p[1] for p in points) / len(points)))
    return rows


def stitch_ids(constraint_geo):
    """stitch 拘束を「つないでいる点の番号」で見分ける。

    位置で見分けようとすると失敗する。布は動くので、
    最初の位置と最後の位置が一致しないため。点の番号なら動かない。
    """
    ids = set()
    for prim in constraint_geo.prims():
        if prim.attribValue("type") != "stitch":
            continue
        ids.add(frozenset(v.point().number() for v in prim.vertices()))
    return ids


def rest_place(ids, mesh_geo):
    """点の番号から、シミュレーション前の位置（重心）を出す。"""
    places = []
    for key in ids:
        points = [mesh_geo.point(number).position() for number in key]
        places.append((sum(p[0] for p in points) / len(points),
                       sum(p[1] for p in points) / len(points)))
    return places


def near_far(rows, cx, cy, radius):
    """球の通り道からの距離で、近い／遠いに分ける。"""
    near = sum(1 for x, y in rows if math.hypot(x - cx, y - cy) <= radius)
    return near, len(rows) - near


def broken_count(before_rows, with_ball, threshold, speed=BALL_SPEED):
    """最後のフレームで、貼り目が何本外れたか。"""
    geo, grid, pin, solver, ball = build(with_ball=with_ball,
                                         threshold=threshold, speed=speed)
    hou.setFrame(LAST)
    left = stitch_rows(solver.geometry(1))
    mesh = solver.geometry()
    return (len(before_rows) - len(left),
            min(p.position()[1] for p in mesh.points()))


def main():
    stats = {"cells": CELLS, "ball_r": BALL_R, "last": LAST}

    print("下ごしらえ: 格子に切って貼り直す")
    geo, grid, pin, solver, ball = build(with_ball=True)
    rest = grid.geometry()
    cons = pin.geometry(1)
    before_rows = stitch_rows(cons)
    cut_points = len(pin.geometry(0).points())
    kinds = {}
    for prim in cons.prims():
        key = prim.attribValue("type")
        kinds[key] = kinds.get(key, 0) + 1
    print(f"   元の布: {len(rest.points())}点 / {len(rest.prims())}面")
    print(f"   {CELLS}×{CELLS}に切ったあと: {cut_points}点"
          f"（{cut_points - len(rest.points()):+d}）")
    print(f"   作られた拘束: {kinds}")
    stats["setup"] = {"points": len(rest.points()), "cut_points": cut_points,
                      "constraints": kinds, "stitches": len(before_rows)}

    print("\nA. 球を通すと、外れる貼り目は増えるか")
    print("   最初は しきい値 1.0 で試して失敗した。重さだけで全部外れてしまい、")
    print("   球のあり／なしで差が出なかった。「重さでは外れない」しきい値まで上げる。")
    table = []
    print(f"   {'しきい値':>10} {'球なし':>8} {'球あり':>8} {'差':>7} {'最下点':>10}")
    for threshold in (1.0, 100.0, 200.0, 300.0, 500.0, 800.0, 1600.0):
        alone, _ = broken_count(before_rows, with_ball=False,
                                threshold=threshold)
        hit, lowest = broken_count(before_rows, with_ball=True,
                                   threshold=threshold)
        row = {"threshold": threshold, "alone": alone, "hit": hit,
               "gap": hit - alone, "lowest": lowest}
        table.append(row)
        print(f"   {threshold:>10} {alone:>8} {hit:>8} {hit - alone:>7} "
              f"{lowest:>10.3f}")
    stats["ball_vs_none"] = table
    window = [r for r in table if r["alone"] == 0 and r["hit"] > 0]
    print(f"   重さでは外れず、球でだけ外れるしきい値: "
          f"{', '.join(str(r['threshold']) for r in window) or 'なし'}")
    stats["impact_only_window"] = [r["threshold"] for r in window]

    print("\nB. 外れた貼り目は、球の通り道の近くに偏っているか（しきい値 200）")
    geo, grid, pin, solver, ball = build(with_ball=True, threshold=200.0)
    rest_mesh = pin.geometry(0)
    start_ids = stitch_ids(pin.geometry(1))
    all_places = rest_place(start_ids, rest_mesh)
    radius = 0.9
    near_all, far_all = near_far(all_places, 0.0, 2.2, radius)

    print(f"   球の通り道（x=0, y=2.2）から半径 {radius} の内と外で分ける")
    print(f"   貼り目は 内 {near_all}本 / 外 {far_all}本")
    print(f"   球が布を通るのは F17 あたり")
    print(f"   {'フレーム':>8} {'外れた計':>9} {'内で外れた':>11} {'外で外れた':>11} "
          f"{'内の率':>8} {'外の率':>8}")
    local = []
    for frame in (14, 18, 22, 28, LAST):
        hou.setFrame(frame)
        left_ids = stitch_ids(solver.geometry(1))
        gone_ids = start_ids - left_ids
        gone = rest_place(gone_ids, rest_mesh)
        near_gone, far_gone = near_far(gone, 0.0, 2.2, radius)
        rate_near = near_gone / near_all * 100 if near_all else 0.0
        rate_far = far_gone / far_all * 100 if far_all else 0.0
        local.append({"frame": frame, "gone": len(gone_ids),
                      "near_gone": near_gone, "far_gone": far_gone,
                      "rate_near": rate_near, "rate_far": rate_far})
        print(f"   {frame:>8} {len(gone_ids):>9} {near_gone:>11} "
              f"{far_gone:>11} {rate_near:>7.1f}% {rate_far:>7.1f}%")
    stats["locality"] = {"radius": radius, "near_all": near_all,
                         "far_all": far_all, "frames": local}
    first = next((r for r in local if r["gone"] > 0), None)
    if first and first["rate_far"] > 0:
        print(f"   最初に外れ始めた F{first['frame']} の時点で、"
              f"内側は外側の {first['rate_near'] / first['rate_far']:.1f}倍")

    print("\nC. 球の速さを変えると、外れる数は増えるか（しきい値 500）")
    speeds = []
    for speed in (0.08, 0.16, 0.32, 0.64):
        count, lowest = broken_count(before_rows, with_ball=True,
                                     threshold=500.0, speed=speed)
        row = {"speed": speed, "broken": count, "lowest": lowest}
        speeds.append(row)
        print(f"   1フレームあたり {speed:>5}: {count:>4}本 外れた / "
              f"最下点 {lowest:.3f}")
    stats["speed_sweep"] = speeds

    with open(os.path.join(OUT, "033_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, grid, pin, solver, ball = build(with_ball=True, threshold=200.0)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "033_graph.json"),
                          title="実験033 — 布を物にぶつけて破る")
    hou_tools.save_hip(os.path.join(OUT, "033_impact.hipnc"))
    print("\n保存: out/033_stats.json, out/033_graph.json, out/033_impact.hipnc")


def shot(case):
    """レンダはプロセスの最後に1枚だけ（実験027で学んだ癖）。"""
    geo, grid, pin, solver, ball = build(with_ball=(case == "hit"),
                                         threshold=200.0)
    hou.setFrame(SHOT_FRAME)

    merged = geo.createNode("merge", "shot")
    merged.setInput(0, solver)
    if ball is not None:
        merged.setInput(1, ball)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)

    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = merged.geometry().boundingBox()
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"033_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=SHOT_RES,
                             direction=(0.22, 0.16, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.06)
    print(f"保存: out/033_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
