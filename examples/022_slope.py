"""019の傾きが何を測っていたのかを確かめる。

019では、水位を変えたときの「粒の数 対 体積」の傾きから
「増えた粒1つが担う体積」を出した。切片は体積に比例しない分（境界の粒）として
別に扱ったつもりだった。

ところが今回、器の中の粒だけを数えたら、粒1つあたりの体積は 0.000330 で、
019から換算した 0.000196 と 68% も違った。

疑い: <strong>境界の粒も、水位が上がると一緒に増えている</strong>のではないか。
      器の側面に沿って作られるなら、水が深くなるほど側面の濡れる面積が増え、
      粒も増える。だとすれば傾きには境界の分も混ざっていて、
      「増えた粒1つが担う体積」は実際より小さく出る。

否定できる形: 水位を2つ試して、
  全部の粒の傾き と 中の粒だけの傾き を比べる。
  同じなら疑いは外れ。全部のほうが大きければ、境界の粒も増えている。
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

SEP = 0.07
BOX = 3.0


def build(waterline):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "slope")
    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((BOX, BOX, BOX))
    container.parm("particlesep").set(SEP)
    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)
    solver.parm("donarrowband").set(False)
    solver.parm("dowaterline").set(True)
    solver.parm("waterline").set(waterline)
    for channel in range(3):
        solver.setInput(channel, container, channel)
    return geo, solver


def counts(solver, waterline):
    hou.setFrame(1)
    points = solver.geometry(0).points()
    half = BOX / 2.0
    inside = 0
    for point in points:
        x, y, z = point.position()
        if abs(x) <= half and abs(z) <= half and -half <= y <= waterline:
            inside += 1
    return len(points), inside


def main():
    rows = []
    print(f"{'水位':>7} {'水の体積':>10} {'全部の粒':>10} {'中の粒':>10} "
          f"{'外の粒':>10}")
    for waterline in (-0.5, 0.5):
        geo, solver = build(waterline)
        total, inside = counts(solver, waterline)
        volume = BOX * BOX * (waterline + BOX / 2.0)
        rows.append({"waterline": waterline, "volume": volume,
                     "total": total, "inside": inside})
        print(f"{waterline:7.2f} {volume:10.4f} {total:10d} {inside:10d} "
              f"{total - inside:10d}")

    a, b = rows
    d_volume = b["volume"] - a["volume"]
    slope_total = (b["total"] - a["total"]) / d_volume
    slope_inside = (b["inside"] - a["inside"]) / d_volume
    slope_outside = ((b["total"] - b["inside"]) - (a["total"] - a["inside"])) / d_volume

    print(f"\n体積が {d_volume:.1f} 増えたときの傾き（粒 / 体積1あたり）")
    print(f"  全部の粒   : {slope_total:9.1f}  → 粒1つ {1 / slope_total:.6f}")
    print(f"  中の粒だけ : {slope_inside:9.1f}  → 粒1つ {1 / slope_inside:.6f}")
    print(f"  外の粒     : {slope_outside:9.1f}"
          f"（全体の {100.0 * slope_outside / slope_total:.1f}%）")
    print(f"\n粒の間隔の3乗 = {SEP ** 3:.6f}")
    print(f"中の粒から出した1つぶん / 間隔の3乗 = "
          f"{(1 / slope_inside) / SEP ** 3:.4f}")

    with open(os.path.join(OUT, "022_slope.json"), "w", encoding="utf-8") as fp:
        json.dump({"sep": SEP, "rows": rows,
                   "slope_total": slope_total, "slope_inside": slope_inside,
                   "slope_outside": slope_outside}, fp,
                  ensure_ascii=False, indent=2)
    print("\n保存: out/022_slope.json")


if __name__ == "__main__":
    main()
