# -*- coding: utf-8 -*-
"""実験128 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def rot(axis, deg):
    """行ベクトル用の回転行列（v' = v · R）。実験103 と同じ向き。"""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return [[1, 0, 0], [0, c, s], [0, -s, c]]
    if axis == "y":
        return [[c, 0, -s], [0, 1, 0], [s, 0, c]]
    return [[c, s, 0], [-s, c, 0], [0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def vm(v, m):
    return [sum(v[k] * m[k][j] for k in range(3)) for j in range(3)]


def main():
    with open(os.path.join(OUT, "128_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    for r in rows:
        R = mul(mul(rot("x", r["r"][0]), rot("y", r["r"][1])), rot("z", r["r"][2]))
        tr = R[0][0] + R[1][1] + R[2][2]
        r["want_angle"] = math.degrees(math.acos(max(-1, min(1, (tr - 1) / 2))))
        c = [v * s for v, s in zip(r["rest_center"], r["s"])]
        r["want_P"] = [a + b for a, b in zip(vm(c, R), r["t"])]
        r["P_err"] = math.dist(r["want_P"], r["P"])
    line_chart(
        os.path.join(OUT, "128_extract.png"),
        [{"label": "かけ直したときの最大のずれ", "points": [(i, r["max_err"]) for i, r in enumerate(rows)],
          "color": PALETTE[0]},
         {"label": "distortion", "points": [(i, r["distortion"]) for i, r in enumerate(rows)],
          "color": PALETTE[1], "dash": True}],
        title="移動と回転は取り出せる。拡大は取り出されず distortion に出る（0=移動 1=回転 2=全部 3=x だけ2倍）",
        x_label="かけた変形", y_label="長さ")
    print("128_extract.png")

    payload = {
        "title": "extracttransform は移動と回転だけを取り出す — 拡大は捨てて distortion に出す",
        "summary":
            "半径1の球に、分かっている移動・回転・拡大をかけ、元の形と変形後の形を extracttransform に渡した。"
            "取り出した変形を元の形にかけ直し、変形後の形とのずれを測った。\n\n"
            "**出てくるのは、点1つと4つの属性だけ:** P（変形後の中心）、pivot（元の中心）、"
            "orient（回転の四元数）、distortion。拡大の属性は無い。\n\n"
            "**移動と回転は、ぴったり取り出せた。** かけ直したずれは、移動だけ・回転だけのどちらも 0.000000。"
            f"回転 (10°, 20°, 30°) は、1つの軸のまわりの {rows[1]['angle_deg']:.4f}° として出た"
            f"（xyz の順に掛けた回転行列から計算すると {rows[1]['want_angle']:.4f}°）。"
            f"P は、元の中心を変形した位置と一致（差は最大 {max(r['P_err'] for r in rows):.6f}）。\n\n"
            "**拡大は取り出されない。** 1.5 倍にすると、かけ直しのずれは "
            f"{rows[2]['max_err']:g}（半径 1 → 1.5 の差）で、distortion も {rows[2]['distortion']:g}。"
            "x だけ2倍に伸ばすと、ずれ "
            f"{rows[3]['max_err']:g}・distortion {rows[3]['distortion']:.4f}。"
            "distortion は「かたい変形では説明できない分」の大きさの目安になる"
            "（伸ばしたときに最大のずれと一致しない理由は確かめていない）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "かけた変形と、取り出した結果",
             "note": "元の形は半径1の球（中心 (0.3, 0.1, −0.2)）。transform SOP（xform）で変形。"
                     "かけ直し = (元の点 − pivot) × orient の回転 + P。",
             "images": [{"path": "128_extract.png",
                         "caption": "拡大を含むと、かけ直してもずれが残り、distortion が0でなくなる。"}],
             "per_row": 1,
             "columns": ["変形", "移動", "回転", "拡大", "取り出した角度", "かけ直しのずれ", "distortion"],
             "rows": [[r["case"], str(tuple(r["t"])), str(tuple(r["r"])), str(tuple(r["s"])),
                       f"{r['angle_deg']:.4f}°", f"{r['max_err']:.6f}", f"{r['distortion']:.6f}"]
                      for r in rows]},
        ],
        "notes": [
            "<strong>移動と回転は正確に取り出せる。</strong>破片のシミュレーション結果を、軽い変形として持ち運ぶのに使える。",
            "<strong>拡大は取り出さない。</strong>大きさが変わる動きは、distortion が0でなくなることで気づける。",
            "<strong>回転は1本の軸のまわりの角度として出る。</strong>(10°, 20°, 30°) は 35.8° になる。",
        ],
        "next": [
            "Use Piece Attribute で、破片ごとに別の変形を取り出せるか",
            "点に少しノイズを足したとき、回転の取り出しがどれだけ乱れるか",
            "取り出した orient と P を、copy to points でかけ直す手順",
        ],
    }
    with open(os.path.join(OUT, "128_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 128_report.json")
    print([(r["case"], round(r["want_angle"], 4), round(r["P_err"], 6)) for r in rows])


if __name__ == "__main__":
    main()
