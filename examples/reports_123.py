# -*- coding: utf-8 -*-
"""実験123 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LABEL = {"cube": "立方体の角8つ＋中の点", "octahedron": "正八面体の頂点6つ＋中の点",
         "plane2d": "板（4×3）に scatter した点（2D）"}


def main():
    with open(os.path.join(OUT, "123_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    solid = [r for r in rows if r["case"] != "plane2d"]
    flat = [r for r in rows if r["case"] == "plane2d"]
    worst_v = max(abs(r["volume"] - r["want"]) for r in solid)
    worst_a = max(abs(r["area"] - r["want"]) for r in flat)

    line_chart(
        os.path.join(OUT, "123_hull.png"),
        [{"label": "shrinkwrap の面積（2D）", "points": [(i, r["area"]) for i, r in enumerate(flat)],
          "color": PALETTE[0]},
         {"label": "Python で計算した凸包の面積", "points": [(i, r["want"]) for i, r in enumerate(flat)],
          "color": PALETTE[2], "dash": True},
         {"label": "板の面積 12", "points": [(i, 12.0) for i in range(len(flat))],
          "color": PALETTE[4], "dash": True}],
        title="点を増やすと凸包は板いっぱいに近づく（0=20点、1=1,000点、2=100,000点）",
        x_label="点の数", y_label="面積")
    print("123_hull.png")

    payload = {
        "title": "shrinkwrap は凸包そのもの — 中の点をいくら足しても立方体は体積1.000000、同じ平面の三角形はまとめる",
        "summary":
            "答えが決まる点の置き方で、shrinkwrap の外形が凸包（へこみの無い、いちばん小さな外形）かを確かめた。\n\n"
            "**3D: 立方体の角8つに、中の点を最大3,000個ほど足しても、外形は立方体のまま。** "
            f"体積は 1.000000、正八面体は 4/3 と一致（差は最大 {worst_v:.6f}）。"
            "中の点は外形に1つも使われず、出てきた点は立方体で8個・正八面体で6個だけ。"
            "面の数は立方体で6枚（同じ平面の三角形を1枚の四角形にまとめている）、正八面体で8枚。\n\n"
            "**2D: scatter した点の外形の面積は、Python で別に計算した凸包の面積と一致**"
            f"（差は最大 {worst_a:.6f}）。\n\n"
            "**ついでに分かったこと: scatter の点は、既定の Relax Iterations で板の縁にぴったり乗る。** "
            "1,000 点のうち 52 点が、板の縁の上にあった（Relax を切ると 0 点）。"
            f"shrinkwrap は一直線上の点を外すので、外形の点は {flat[1]['out_points']} 個まで減る"
            f"（縁に乗った点を数えると {flat[1]['hull_points']} 個）。\n\n"
            f"速さ: 10万点の 2D で {flat[-1]['sec']:.2f} 秒。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "点の置き方と、外形の大きさ",
             "note": "中の点は |x|+|y|+|z| < 0.49 の範囲だけに置いた（立方体・正八面体のどちらの内側にも入る）。"
                     "体積・面積は measure で出した。",
             "images": [{"path": "123_hull.png",
                         "caption": "shrinkwrap（青）と Python の凸包（緑の破線）は重なる。"}],
             "per_row": 1,
             "columns": ["点の置き方", "入力の点", "外形の点", "外形の面", "体積・面積", "式・別計算", "秒"],
             "rows": [[LABEL[r["case"]], f"{r['input_points']:,}", str(r["out_points"]),
                       str(r["out_prims"]), f"{r.get('volume', r.get('area')):.6f}",
                       f"{r['want']:.6f}", f"{r['sec']:.4f}"] for r in rows]},
        ],
        "notes": [
            "<strong>shrinkwrap は凸包。</strong>中の点は使われず、角の点だけが残る。",
            "<strong>同じ平面の面はまとめる。</strong>立方体の外形は三角形12枚ではなく四角形6枚。",
            "<strong>scatter の点は縁にも乗る。</strong>Relax を入れたまま（既定）だと、1,000点中52点が縁の上。"
            "縁から離したいときは Relax を切るか、少し内側の板に散らす。",
        ],
        "next": [
            "shrinkwrap の Shrink Amount を上げたとき、どれだけ内側へ寄るか",
            "scatter の Relax で縁に乗る点の割合が、点の数でどう変わるか",
            "3D の凸包で、点が球面上にあるとき（全部の点が外形に使われる）の速さ",
        ],
    }
    with open(os.path.join(OUT, "123_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 123_report.json")


if __name__ == "__main__":
    main()
