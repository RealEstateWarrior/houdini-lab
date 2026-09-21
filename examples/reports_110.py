# -*- coding: utf-8 -*-
"""実験110 の図とレポートを、測った値から組み立てる。

2つの読み方を式にして、実測とのずれを出す。
  A「値を i 倍して1回かける」: 移動 i·t、回転 i·r、拡大 s^i を、指定の順で1回
  B「1回分を i 回くり返す」:   1回分の変形 M を i 回かける（M^i）
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

P0 = (0.5, 0.0, 0.0)


def rot_y(p, deg):
    # 実験103 と同じ向き: (1,0,0) を +90° 回すと (0,0,-1)
    a = math.radians(deg)
    return (p[0] * math.cos(a) + p[2] * math.sin(a), p[1],
            -p[0] * math.sin(a) + p[2] * math.cos(a))


def add(p, q):
    return tuple(a + b for a, b in zip(p, q))


def mul(p, k):
    return tuple(a * k for a in p)


def step(p, setup):
    """1回分の変形（SRT なら 拡大→回転→移動、TRS なら 移動→回転→拡大）。"""
    t = setup.get("t", (0, 0, 0))
    ry = setup.get("r", (0, 0, 0))[1]
    s = setup.get("scale", 1.0)
    if setup.get("xOrd") == "trs":
        return mul(rot_y(add(p, t), ry), s)
    return add(rot_y(mul(p, s), ry), t)


def hypo_a(i, setup):
    t = mul(setup.get("t", (0, 0, 0)), i)
    ry = setup.get("r", (0, 0, 0))[1] * i
    s = setup.get("scale", 1.0) ** i
    return step(P0, {"t": t, "r": (0, ry, 0), "scale": s, "xOrd": setup.get("xOrd")})


def hypo_b(i, setup):
    p = P0
    for _ in range(i):
        p = step(p, setup)
    return p


def main():
    with open(os.path.join(OUT, "110_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    table, errs = [], {}
    for name, d in data.items():
        ea = eb = 0.0
        for i, c in enumerate(d["copies"]):
            a, b = hypo_a(i, d["setup"]), hypo_b(i, d["setup"])
            ea = max(ea, math.dist(c["center"], a))
            eb = max(eb, math.dist(c["center"], b))
        errs[name] = (ea, eb)
    label = {"move": "移動だけ（x+1）", "scale": "拡大だけ（0.8倍）",
             "turn": "回転72°＋移動2（SRT）", "turn_trs": "回転72°＋移動2（TRS）"}
    for name in data:
        ea, eb = errs[name]
        table.append([label[name], str(len(data[name]["copies"])), f"{ea:.6f}", f"{eb:.6f}"])

    turn = data["turn"]["copies"]
    loop = [hypo_b(i, data["turn"]["setup"]) for i in range(6)]
    line_chart(
        os.path.join(OUT, "110_turn.png"),
        [{"label": "実測（SRT）: 移動は i×2、回転は i×72°",
          "points": [(c["center"][0], -c["center"][2]) for c in turn],
          "color": PALETTE[0]},
         {"label": "もし「1回分を i 回くり返す」なら（正五角形で1周）",
          "points": [(p[0], -p[2]) for p in loop],
          "color": PALETTE[1], "dash": True}],
        title="回転と移動を組み合わせると、輪にならずに前へ進む（6個目が x=10.5）",
        x_label="x", y_label="−z（上から見た図）")
    print("110_turn.png")

    payload = {
        "title": "copyxform は「1回分をくり返す」ではなく「値を i 倍して1回かける」 — 回転＋移動は輪にならない",
        "summary":
            "copyxform（Copy and Transform）は、1つ置くたびに同じ変形を重ねていく箱だと思われがち。"
            "もしそうなら、i 個目は「1回分の変形 M を i 回かけたもの（M^i）」になる。"
            "ところが、もう1つの読み方がある。**移動を i 倍・回転を i 倍・拡大を i 乗した値で、"
            "1回だけ変形する**。移動だけ・拡大だけなら2つは同じ答えになるが、"
            "回転と移動を組み合わせると大きく分かれる。4通りで確かめた。\n\n"
            "結果は **4通りすべてで「値を i 倍して1回」の式と一致**"
            f"（ずれは最大 {max(e[0] for e in errs.values()):.6f}）。"
            "「i 回くり返す」の式とは、回転を含む2通りで "
            f"{errs['turn'][1]:.3f}・{errs['turn_trs'][1]:.3f} ずれた。\n\n"
            "たとえば回転 72°＋移動 2 を6個並べると、5回で1周するはずなのに、6個目は "
            f"x={turn[5]['center'][0]:g} にいる。移動 2×5=10 と、360° 回った元の位置 0.5 の和。"
            "輪（正五角形）にはならず、蛇行しながら x の方へ進む。\n\n"
            "拡大は i 乗だった（0.8 → 0.64 → 0.512…）。i 倍（0.8 → 0.6 → 0.4）ではない。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "2つの読み方と、実測とのずれ（各コピーの中心の最大距離）",
             "note": "元の形は x=0.5 に置いた一辺 0.2 の箱。中心は箱の8点の平均。",
             "images": [{"path": "110_turn.png",
                         "caption": "青が実測。輪になるのは「くり返す」読み方（橙の破線）のとき。"}],
             "per_row": 1,
             "columns": ["置き方", "個数", "値を i 倍して1回", "1回分を i 回くり返す"],
             "rows": table},
            {"label": "回転72°＋移動2（SRT）の各コピーの中心",
             "note": "i 個目 = 拡大 → 回転 i×72° → 移動 i×2。",
             "images": [],
             "per_row": 1,
             "columns": ["i", "x", "z"],
             "rows": [[str(i), f"{c['center'][0]:.6f}", f"{c['center'][2]:.6f}"]
                      for i, c in enumerate(turn)]},
        ],
        "notes": [
            "<strong>値を i 倍して1回かける。</strong>移動は i 倍、回転は i 倍、拡大は i 乗。"
            "それを Transform Order の順で1回かける。",
            "<strong>回転と移動を混ぜると輪にならない。</strong>72°×5 で1周しても、"
            "移動は 2×5=10 進んでいる。輪に並べたいときは、Pivot を輪の中心に置くか、"
            "copy to points で円周上の点に置く（どちらも今回は試していない）。",
            "<strong>回転の軸と同じ向きの移動なら、らせん階段になる。</strong>"
            "軸方向の移動は回転と入れ替えても同じなので、2つの読み方が一致する"
            "（式から言えること。今回は測っていない）。",
            "<strong>拡大は i 乗。</strong>0.8 なら 5個目で 0.8⁴≒0.41 倍。",
        ],
        "next": [
            "Pivot Translate を輪の中心に置いたとき、正五角形に並ぶか",
            "回転の軸（y）に沿った移動で、らせん階段が式どおりになるか",
            "copy to points との速さの差（10万個）",
        ],
    }
    with open(os.path.join(OUT, "110_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 110_report.json")
    print(errs)


if __name__ == "__main__":
    main()
