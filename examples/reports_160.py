# -*- coding: utf-8 -*-
"""実験160 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "160_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows = d["rows"]
    by = {(r["rotstep"], r["padding"], r["resolution"]): r for r in rows}
    series = []
    for i, res in enumerate(("res1", "res2", "res3")):
        series.append({"label": f"Search Resolution {res}（回転なし）", "points": [(p, by[("none", p, res)]["fill"]) for p in (0, 1, 4, 16)], "color": PALETTE[i]})
    series.append({"label": "res3・90° 回転あり", "points": [(p, by[("PI2", p, "res3")]["fill"]) for p in (0, 1, 4, 16)], "color": PALETTE[3], "dash": True})
    line_chart(os.path.join(OUT, "160_fill.png"), series,
               title="uvlayout: 長方形 12 枚で 0〜1 の升を埋めた割合と Island Padding",
               x_label="Island Padding", y_label="埋まった割合")
    spread = max(r["scale_spread"] for r in rows)
    best = max(rows, key=lambda r: r["fill"])
    payload = {
        "title": "uvlayout は長方形 12 枚で升の 48〜84% を埋める — Padding は Search Resolution が粗いほど大きく効く",
        "summary":
            "大きさの違う長方形 12 枚（辺 0.4〜2.0）に形そのままの UV を付けて uvlayout にかけ、並べたあとの UV の面積の合計"
            "（0〜1 の升が埋まった割合）を測った。Island Padding・Island Rotation Step・Search Resolution を変えた。\n\n"
            f"**島どうしの大きさの比は保たれた。**全24通りで、元の面積に対する UV の面積の比は、島の間で最大 {spread:.6f} 倍しか違わない。"
            "どの島も同じ倍率で縮めて並べている。\n\n"
            f"**埋まった割合は 48〜84%。**いちばん良かったのは 90° 回転あり・Padding 0・{best['resolution']} の {best['fill'] * 100:.1f}%。"
            "回転なしでも同じ条件で 81.1%。長方形でも、回していい向きがあると少し詰まる。\n\n"
            "**Padding は Search Resolution が粗いほど大きく効く。**Padding 16 で、res1 は 47.8%、res3 は 71.5%。"
            "Padding が「探す升目の何個分」で決まっているように見えるが、確かめていない。\n\n"
            f"**速い。**どれも {max(r['sec'] for r in rows):.3f} 秒以下（12 枚）。細かい res3 でも数ミリ秒。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Rotation Step・Padding・Search Resolution と埋まった割合",
            "images": [{"path": "160_fill.png", "caption": "res1（青）は Padding を上げると急に落ちる。"}],
            "per_row": 1,
            "columns": ["Rotation Step", "Padding", "Search Resolution", "埋まった割合", "島の倍率の最大比", "U の範囲", "V の範囲", "秒"],
            "rows": [[r["rotstep"], r["padding"], r["resolution"], f"{r['fill'] * 100:.1f}%", f"{r['scale_spread']:.6f}",
                      f"{r['u_range'][0]:g}〜{r['u_range'][1]:g}", f"{r['v_range'][0]:g}〜{r['v_range'][1]:g}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>島の大きさの比は変えない。</strong>1 枚だけ大きくしたいなら、先に UV を拡大しておく（島ごとの倍率の属性もある）。",
            "<strong>Padding を大きくするなら Search Resolution も上げる。</strong>粗いままだと升の半分しか使わない。",
            "<strong>長方形の島でも 90° 回転を許すと数 % 詰まる。</strong>",
        ],
        "next": ["Island Padding と、書き出す画像のピクセルの関係", "形の複雑な島（L 字など）での埋まり方"],
    }
    with open(os.path.join(OUT, "160_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 160_report.json", spread, best["fill"])


if __name__ == "__main__":
    main()
