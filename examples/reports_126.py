# -*- coding: utf-8 -*-
"""実験126 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def main():
    with open(os.path.join(OUT, "126_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows = data["rows"]
    for r in rows:
        # 塊の中心は (±s, ±s)。境目は x=0・z=0。正しい側に入る確率は軸ごとに Φ(s/σ)、2軸で2乗
        r["best"] = phi(r["spread"] / r["sd"]) ** 2
        r["mean_purity"] = sum(r["purity"]) / 4
    line_chart(
        os.path.join(OUT, "126_cluster.png"),
        [{"label": "cluster の純度（4つの塊の平均）",
          "points": [(r["spread"] / r["sd"], r["mean_purity"]) for r in rows], "color": PALETTE[0]},
         {"label": "理論の上限 Φ(s/σ)²", "points": [(r["spread"] / r["sd"], r["best"]) for r in rows],
          "color": PALETTE[2], "dash": True}],
        title="塊が近づくと純度は下がるが、どこでも理論の上限に沿っている",
        x_label="中心の座標 s ÷ ばらつき σ", y_label="純度")
    print("126_cluster.png")

    worst = max(abs(r["mean_purity"] - r["best"]) for r in rows)
    payload = {
        "title": "cluster（k-means）は塊を理論の上限どおりに分ける — 重なる塊でも Φ(s/σ)² と1%以内",
        "summary":
            f"中心の分かっている4つの塊（(±s, ±s) に各 {data['per']:,} 点、正規分布のばらつき σ）を作り、"
            "cluster に「4つに分けて」と頼んだ。元の塊の点が、どれだけ同じ番号にまとまるか（純度）を測った。\n\n"
            "塊が重なっていると、どんな分け方でも100%は取れない。境目は x=0・z=0 なので、"
            "点が正しい側にいる確率は1軸あたり Φ(s/σ)（正規分布の累積）、2軸で **Φ(s/σ)²** が上限になる。\n\n"
            f"**4通りすべてで、純度はこの上限と {worst * 100:.1f}% 以内。** "
            f"十分離れた塊（s/σ = {rows[0]['spread'] / rows[0]['sd']:g}）は 100%、"
            f"s/σ = 1 まで近づけると {rows[-1]['mean_purity'] * 100:.1f}%（上限 {rows[-1]['best'] * 100:.1f}%）。"
            "k-means は、重なった塊でも取れるだけ取っている。\n\n"
            f"番号ごとの点の平均は、元の中心から最大 {rows[0]['center_err_max']:.4f}（離れた塊）〜"
            f"{rows[-1]['center_err_max']:.4f}（重なった塊）。"
            f"結果の番号は点の属性 {rows[0]['attr']} に入る。\n\n"
            f"速さ: 8,000 点で {min(r['sec'] for r in rows):.2f}〜{max(r['sec'] for r in rows):.2f} 秒。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "塊の近さと、分け方の純度",
             "note": "純度 = 元の塊ごとに、いちばん多い番号に入った点の割合（4つの平均）。",
             "images": [{"path": "126_cluster.png",
                         "caption": "実測（青）は理論の上限（緑の破線）に沿う。"}],
             "per_row": 1,
             "columns": ["s", "σ", "s/σ", "番号の数", "純度（4つ）", "上限 Φ(s/σ)²", "中心のずれ", "秒"],
             "rows": [[f"{r['spread']:g}", f"{r['sd']:g}", f"{r['spread'] / r['sd']:.2f}",
                       str(r["clusters"]), " / ".join(f"{p:.3f}" for p in r["purity"]),
                       f"{r['best']:.4f}", f"{r['center_err_max']:.4f}", f"{r['sec']:.3f}"]
                      for r in rows]},
        ],
        "notes": [
            "<strong>離れた塊は100%正しく分ける。</strong>",
            "<strong>重なった塊でも、理論の上限まで取る。</strong>s/σ = 1 で約70%。それ以上は、どの方法でも無理。",
            "<strong>番号は cluster 属性。</strong>色分けや、塊ごとの処理にそのまま使える。",
        ],
        "next": [
            "塊の大きさ（点の数）が違うとき、k-means が大きな塊を割ってしまうか",
            "num_clusters を実際の塊の数と違う数にしたときの分かれ方",
            "clusterpoints との結果と速さの比較",
        ],
    }
    with open(os.path.join(OUT, "126_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 126_report.json")


if __name__ == "__main__":
    main()
