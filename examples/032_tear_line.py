"""実験032 — 狙った線で破れる布。切ってから貼り直す。

実験031で分かったこと。Vellum の breaking は <code>glue</code> が作る stitch 拘束にだけ効き、
<code>cloth</code> が作る distance 拘束には効かない。
つまり<strong>布の伸びを破ることはできないが、貼り合わせを外すことはできる</strong>。

ならば順序を逆にすればよい。<strong>先に切っておいて、あとから貼る。</strong>

  1. 布を1枚作る
  2. 破れてほしい線で2つに切り分ける（今回は波打つ線）
  3. <code>glue</code> で貼り直す。しきい値を決める
  4. 吊るす。重さが貼り目にかかり、しきい値を超えたところから外れる

確かめること。

  A. 貼り目は本当に切った線の上にあるか（拘束の位置を測る）
  B. しきい値で「外れる／外れない」を決められるか
  C. 切らずに breaking だけ入れた布は、やはり破れないままか（031の再確認）

    hython examples/032_tear_line.py
    hython examples/032_tear_line.py shot intact
    hython examples/032_tear_line.py shot torn
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

LAST = 40
SHOT_FRAME = 30
SHOT_RES = (520, 620)
BBOX_PATH = os.path.join(OUT, "032_bbox.json")

# 切る線: y = SEAM_Y + SEAM_AMP * sin(x * SEAM_FREQ)
SEAM_Y = 2.6
SEAM_AMP = 0.45
SEAM_FREQ = 2.2


def build(cut=True, threshold=1.0, last=LAST):
    """上端で吊るした布。cut が真なら、波打つ線で切ってから glue で貼る。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "tear_line")

    grid = geo.createNode("grid", "cloth")
    grid.parm("orient").set(0)          # XY 平面。縦に立てる
    grid.parm("sizex").set(4.0)
    grid.parm("sizey").set(4.0)
    grid.parm("rows").set(40)
    grid.parm("cols").set(40)
    grid.parmTuple("t").set((0, 2.2, 0))

    upstream = grid
    if cut:
        # 面の重心が線より下かどうかで印を付ける。
        # 点ではなく面に付けるのが肝心で、面を丸ごと振り分けたいため。
        mark = geo.createNode("attribwrangle", "mark_cut")
        mark.setFirstInput(grid)
        mark.parm("class").set(1)       # プリミティブ
        mark.parm("snippet").set(
            f"float line = {SEAM_Y} + {SEAM_AMP} * sin(@P.x * {SEAM_FREQ});\n"
            "i@lower = (@P.y < line) ? 1 : 0;")

        upper = geo.createNode("blast", "upper")
        upper.setFirstInput(mark)
        upper.parm("group").set("@lower==1")
        # blast の grouptype は 0=推測 1=ブレークポイント 2=辺 3=点 4=面。
        # 4 を選ばないと面のグループとして扱われず、何も消えない。
        upper.parm("grouptype").set(4)

        lower = geo.createNode("blast", "lower")
        lower.setFirstInput(mark)
        lower.parm("group").set("@lower==0")
        lower.parm("grouptype").set(4)

        # 2つに分けてから合流させると、切り口の点が二重になる。
        # この「重なった点どうし」を glue が拾う。
        both = geo.createNode("merge", "two_pieces")
        both.setInput(0, upper)
        both.setInput(1, lower)
        upstream = both

    pins = geo.createNode("attribwrangle", "make_pins")
    pins.setFirstInput(upstream)
    pins.parm("snippet").set("if (@P.y > 4.1) { @group_pins = 1; }")

    cloth = geo.createNode("vellumconstraints", "cloth")
    cloth.setFirstInput(pins)
    cloth.parm("constrainttype").set("cloth")
    cloth.parm("stretchstiffness").set(1.0)
    if not cut:
        # 切らない場合は、布そのものに breaking を入れて比べる（031の再確認）
        cloth.parm("dobreaking").set(True)
        cloth.parm("breakthreshold").set(threshold)

    upstream_con = cloth
    if cut:
        glue = geo.createNode("vellumconstraints", "glue")
        glue.setInput(0, cloth, 0)
        glue.setInput(1, cloth, 1)
        glue.parm("constrainttype").set("glue")
        glue.parm("dobreaking").set(True)
        glue.parm("breakthreshold").set(threshold)
        upstream_con = glue

    pin = geo.createNode("vellumconstraints", "pin")
    pin.setInput(0, upstream_con, 0)
    pin.setInput(1, upstream_con, 1)
    pin.parm("constrainttype").set("pin")
    pin.parm("grouptype").set("points")
    pin.parm("group").set("pins")

    solver = geo.createNode("vellumsolver", "solve")
    solver.setInput(0, pin, 0)
    solver.setInput(1, pin, 1)
    solver.parm("startframe").set(1)

    # どの点がどの塊に属するかを振る。
    # connecttype は 0=点でつながっているか / 1=面でつながっているか。
    conn = geo.createNode("connectivity", "conn")
    conn.setFirstInput(solver)
    conn.parm("connecttype").set(0)

    geo.layoutChildren()
    return geo, grid, pin, solver, conn


def stitch_positions(constraint_geo):
    """stitch 拘束が、どの高さに並んでいるか。

    拘束はプリミティブなので、その重心を「その拘束のある場所」とみなす。
    """
    rows = []
    for prim in constraint_geo.prims():
        if prim.attribValue("type") != "stitch":
            continue
        points = [v.point().position() for v in prim.vertices()]
        if not points:
            continue
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        rows.append((x, y))
    return rows


def seam_gap(rows):
    """拘束の位置が、狙った線からどれだけ離れているか。"""
    worst = 0.0
    total = 0.0
    for x, y in rows:
        line = SEAM_Y + SEAM_AMP * math.sin(x * SEAM_FREQ)
        gap = abs(y - line)
        worst = max(worst, gap)
        total += gap
    return worst, (total / len(rows) if rows else 0.0)


def counts_by_type(geometry):
    counts = {}
    for prim in geometry.prims():
        key = prim.attribValue("type")
        counts[key] = counts.get(key, 0) + 1
    return counts


def pieces_of(conn_node):
    """塊ごとに、点の数と高さの範囲を返す。

    吊るされているほうは上に残り、外れたほうは落ちる。
    2つを分けて測れば、「どちらが落ちたか」が数字で分かる。
    """
    geometry = conn_node.geometry()
    if geometry.findPointAttrib("class") is None:
        return []
    groups = {}
    for point in geometry.points():
        key = point.attribValue("class")
        y = point.position()[1]
        row = groups.setdefault(key, {"count": 0, "low": y, "high": y})
        row["count"] += 1
        row["low"] = min(row["low"], y)
        row["high"] = max(row["high"], y)
    # 高いほうを先に並べる（吊るされている側が先頭になる）
    return sorted(groups.values(), key=lambda r: -r["high"])


def main():
    stats = {"seam": {"y": SEAM_Y, "amp": SEAM_AMP, "freq": SEAM_FREQ},
             "last": LAST}

    print("A. 貼り目は、切った線の上にあるか")
    geo, grid, pin, solver, conn = build(cut=True, threshold=1.0)
    rest = grid.geometry()
    cons = pin.geometry(1)
    rows = stitch_positions(cons)
    worst, mean = seam_gap(rows)
    ys = [y for _, y in rows]
    stats["seam_check"] = {
        "grid_points": len(rest.points()), "grid_prims": len(rest.prims()),
        "constraints": counts_by_type(cons),
        "stitches": len(rows),
        "y_min": min(ys), "y_max": max(ys),
        "gap_worst": worst, "gap_mean": mean,
    }
    # 切ると、切り口の点が二重になる。その増えた数と stitch の数は
    # 一致するはず（重なった1組につき1本）。合っていれば筋が通っている。
    cut_points = len(pin.geometry(0).points())
    added = cut_points - len(rest.points())
    stats["seam_check"]["points_after_cut"] = cut_points
    stats["seam_check"]["points_added"] = added
    stats["seam_check"]["added_matches_stitches"] = (added == len(rows))

    print(f"   元の布: {len(rest.points())}点 / {len(rest.prims())}面")
    print(f"   切ったあと: {cut_points}点（{added:+d}）")
    print(f"   作られた拘束: {counts_by_type(cons)}")
    print(f"   stitch は {len(rows)}本、高さ {min(ys):.4f} 〜 {max(ys):.4f}")
    print(f"   狙った線からのずれ: 平均 {mean:.5f} / 最大 {worst:.5f}")
    print(f"   （線は y = {SEAM_Y} + {SEAM_AMP}·sin({SEAM_FREQ}x)。"
          f"波の高さは {SEAM_AMP * 2:.2f} ある）")
    print(f"   増えた点 {added} と stitch {len(rows)} は"
          f"{'一致する' if added == len(rows) else '一致しない'}")

    print("\nB. しきい値で、外れる／外れないを決められるか")
    sweep = []
    print(f"   {'しきい値':>10} {'拘束 F5':>9} {'F15':>7} {'F40':>7} "
          f"{'吊るした側':>22} {'外れた側':>22}")
    for threshold in (0.01, 1.0, 10.0, 100.0, 1000.0):
        geo, grid, pin, solver, conn = build(cut=True, threshold=threshold)
        before = len(pin.geometry(1).prims())
        counts = {}
        for frame in (5, 15, LAST):
            hou.setFrame(frame)
            counts[frame] = len(solver.geometry(1).prims())
        parts = pieces_of(conn)
        row = {"threshold": threshold, "before": before, "counts": counts,
               "pieces": parts}
        sweep.append(row)

        def describe(part):
            if not part:
                return " " * 22
            return (f"{part['count']:5d}点 "
                    f"{part['low']:7.3f}〜{part['high']:6.3f}")

        upper = parts[0] if parts else None
        lower = parts[1] if len(parts) > 1 else None
        print(f"   {threshold:>10} {counts[5]:>9} {counts[15]:>7} "
              f"{counts[LAST]:>7} {describe(upper):>22} {describe(lower):>22}")
    stats["threshold_sweep"] = sweep

    print("\nC. 切らずに breaking だけ入れた布は、やはり破れないか（031の再確認）")
    plain = []
    for threshold in (0.000001, 1.0):
        geo, grid, pin, solver, conn = build(cut=False, threshold=threshold)
        before = len(pin.geometry(1).prims())
        hou.setFrame(LAST)
        after = len(solver.geometry(1).prims())
        mesh = solver.geometry()
        row = {"threshold": threshold, "before": before, "after": after,
               "lowest": min(p.position()[1] for p in mesh.points())}
        plain.append(row)
        print(f"   しきい値 {threshold:<10}: {before} → {after}"
              f"（{after - before:+d}） 最下点 {row['lowest']:.4f}")
    stats["uncut"] = plain

    with open(os.path.join(OUT, "032_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, grid, pin, solver, conn = build(cut=True, threshold=1.0)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "032_graph.json"),
                          title="実験032 — 狙った線で破れる布")
    hou_tools.save_hip(os.path.join(OUT, "032_tear_line.hipnc"))
    print("\n保存: out/032_stats.json, out/032_graph.json, "
          "out/032_tear_line.hipnc")


def shot(case):
    """レンダはプロセスの最後に1枚だけ（実験027で学んだ癖）。"""
    threshold = 1000.0 if case == "intact" else 1.0
    geo, grid, pin, solver, conn = build(cut=True, threshold=threshold)
    hou.setFrame(SHOT_FRAME)

    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = solver.geometry().boundingBox()
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"032_{case}.png")
    hou_tools.render_preview(solver.path(), png, res=SHOT_RES,
                             direction=(0.18, 0.2, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.06)
    print(f"保存: out/032_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
