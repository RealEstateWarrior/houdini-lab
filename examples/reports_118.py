# -*- coding: utf-8 -*-
"""実験118 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "118_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    with open(os.path.join(OUT, "118_sign.json"), encoding="utf-8") as fp:
        sign = json.load(fp)
    fr = [r for r in data["rows"] if r["case"] == "frustum"]
    sq = [r for r in data["rows"] if r["case"] == "square_ring"]
    worst_a = max(abs(r["area"] - r["want_poly"]) for r in fr)
    worst_v = max(abs(abs(r["volume"]) - r["want_poly"]) for r in sq)
    all_neg = all(r["volume"] < 0 for r in sq)

    line_chart(
        os.path.join(OUT, "118_revolve.png"),
        [{"label": "円錐台の側面積 ÷ なめらかな式",
          "points": [(math.log2(r["k"]), r["area"] / r["want_smooth"]) for r in fr],
          "color": PALETTE[0]},
         {"label": "ドーナツの体積（絶対値）÷ パップスの式",
          "points": [(math.log2(r["k"]), abs(r["volume"]) / r["want_smooth"]) for r in sq],
          "color": PALETTE[1]}],
        title="一周の分割を増やすと、面積も体積もなめらかな式に近づく",
        x_label="一周の分割数（log2。2=4、8=256）", y_label="式との比")
    print("118_revolve.png")

    k64 = next(r for r in sq if r["k"] == 64)
    payload = {
        "title": "revolve の面積・体積は k 角の式に6桁一致 — ただし閉じた断面を回すと体積がマイナス（裏返し）",
        "summary":
            f"線分 ({data['r1']:g}, 0)→({data['r2']:g}, {data['h']:g}) を y 軸のまわりに一周させ、"
            "できた円錐台の側面積を式と比べた。一周を k 分割すると、1枚の面は等脚台形になるので、"
            "面積は k 角の角錐台の式で出せる。\n\n"
            f"**側面積は、5通りすべて k 角の式と一致**（差は最大 {worst_a:.6f}）。"
            f"なめらかな円錐台の式との比は、k=16 で {fr[2]['area'] / fr[2]['want_smooth']:.4f}、"
            f"k=256 で {fr[-1]['area'] / fr[-1]['want_smooth']:.6f}。\n\n"
            "次に、正方形（0.5×0.5、軸から 1.0〜1.5）を回して、四角い断面のドーナツを作った。"
            "体積はパップス・ギュルダンの定理（断面積 × 重心の回る長さ）で出る。"
            f"**大きさは k 角の式と一致**（差は最大 {worst_v:.6f}）。"
            f"**ところが符号が{'すべて' if all_neg else 'いくつか'}マイナスだった。** "
            f"k=64 で {k64['volume']:.6f}。面の表が内側を向いている（裏返し）ということ。\n\n"
            "直し方は3つとも効いた: revolve の Reverse Cross Sections を入れる "
            f"({sign['reversecross_True']:+.6f})、後ろに reverse を置く ({sign['reverse_sop']:+.6f})、"
            f"回す前の断面を reverse で裏返す ({sign['profile_reversed']:+.6f})。\n\n"
            "断面は xy 平面で反時計回り（手前から見て）に点を並べた。"
            "時計回りに並べていれば、最初から表向きになるはず（確かめていない）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "円錐台の側面積（下の半径1・上の半径0.4・高さ1.5）",
             "note": "k 角の式 = k × (上下の辺の和 / 2) × 斜めの高さ。"
                     "上下の辺 = 2r·sin(π/k)、斜めの高さ = √(h² + ((r2−r1)·cos(π/k))²)。",
             "images": [{"path": "118_revolve.png",
                         "caption": "どちらも分割を増やすと比が1に近づく。体積は符号を外して比べた。"}],
             "per_row": 1,
             "columns": ["一周の分割", "面の数", "面積", "k 角の式", "なめらかな式"],
             "rows": [[str(r["k"]), str(r["prims"]), f"{r['area']:.6f}",
                       f"{r['want_poly']:.6f}", f"{r['want_smooth']:.6f}"] for r in fr]},
            {"label": "四角い断面のドーナツの体積",
             "note": "k 角の式 = (k/2)·sin(2π/k)·(1.5² − 1.0²)·0.5。なめらかな式 = 0.25 × 2π × 1.25。",
             "images": [],
             "per_row": 1,
             "columns": ["一周の分割", "面の数", "体積（measure）", "k 角の式", "なめらかな式"],
             "rows": [[str(r["k"]), str(r["prims"]), f"{r['volume']:+.6f}",
                       f"{r['want_poly']:.6f}", f"{r['want_smooth']:.6f}"] for r in sq]},
        ],
        "notes": [
            "<strong>回した面の面積は k 角の式どおり。</strong>既定の分割のまま面積を出すなら、"
            "k 角の式で補正できる。",
            "<strong>閉じた断面を回すと、裏返しになることがある。</strong>体積がマイナスになったら、"
            "Reverse Cross Sections を入れる。",
            "<strong>裏返しは見た目では気づきにくい。</strong>measure の体積の符号で見つかる"
            "（実験098 の「答えが計算で出る形で試す」がここでも効いた）。",
        ],
        "next": [
            "断面を時計回りに並べたときに、最初から表向きになるか",
            "角度の範囲だけ回したとき（End Caps あり）の体積",
            "NURBS で回したときの面積が、なめらかな式に一致するか",
        ],
    }
    with open(os.path.join(OUT, "118_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 118_report.json")


if __name__ == "__main__":
    main()
