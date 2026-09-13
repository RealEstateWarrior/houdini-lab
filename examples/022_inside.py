"""019の係数と突き合わせる。

019では、水位を変えたときの傾きから「増えた粒1つが担う体積」を 0.000293 と出した。
ただしあのときの粒の間隔は 0.08 で、今回は 0.07。
粒1つの体積は間隔の3乗に比例するはずなので、換算すると

    0.000293 × (0.07 / 0.08)³ = 0.000196

一方、今回の「本当の体積 ÷ 全部の粒の数」は 13.5 ÷ 81,106 = 0.000166 だった。
合わないが、これは<strong>比べているものが違う</strong>可能性が高い。

019の 0.000293 は傾きから出した値なので、体積に比例しない分
（境界の外側に作られる粒）を除いてある。
今回の 0.000166 は境界の粒まで含めた全部で割っている。

器の中にある粒だけを数え直せば、両者は近づくはず。
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

KNOWN = os.path.join(HERE, "examples", "022_known.py")
namespace = {"__name__": "notmain", "__file__": KNOWN}
exec(compile(open(KNOWN, encoding="utf-8").read(), KNOWN, "exec"), namespace)
build = namespace["build"]

SEP = namespace["SEP"]
BOX = namespace["BOX"]
TRUE_VOLUME = namespace["TRUE_VOLUME"]
SEP_019 = 0.08
PER_019 = 0.000293


def main():
    geo, solver, surface, convert = build()
    hou.setFrame(1)
    points = solver.geometry(0).points()
    total = len(points)

    half = BOX / 2.0
    inside = 0
    for point in points:
        x, y, z = point.position()
        if abs(x) <= half and abs(z) <= half and -half <= y <= 0.0:
            inside += 1

    scaled = PER_019 * (SEP / SEP_019) ** 3
    print(f"粒の総数 {total}")
    print(f"器の中（水のある範囲）にある粒 {inside}"
          f"（全体の {100.0 * inside / total:.1f}%）")
    print(f"外側にある粒 {total - inside}")
    print()
    print(f"本当の体積 {TRUE_VOLUME}")
    print(f"  全部の粒で割る : {TRUE_VOLUME / total:.6f}")
    print(f"  中の粒だけで割る: {TRUE_VOLUME / inside:.6f}")
    print(f"  019の値を間隔で換算: {scaled:.6f}")
    print(f"  中の粒との差: "
          f"{100.0 * (TRUE_VOLUME / inside - scaled) / scaled:+.1f}%")

    with open(os.path.join(OUT, "022_inside.json"), "w", encoding="utf-8") as fp:
        json.dump({"total": total, "inside": inside,
                   "true_volume": TRUE_VOLUME, "sep": SEP,
                   "per_all": TRUE_VOLUME / total,
                   "per_inside": TRUE_VOLUME / inside,
                   "per_019_scaled": scaled}, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/022_inside.json")


if __name__ == "__main__":
    main()
