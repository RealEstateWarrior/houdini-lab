# -*- coding: utf-8 -*-
"""実験170 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "170_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "170_stretch.png"),
               [{"label": f"Substeps {s}", "points": [(r["exp"], (r["max_stretch"] - 1) * 100) for r in rows if r["substeps"] == s],
                 "color": PALETTE[i]} for i, s in enumerate((1, 5))],
               title="Vellum（上の辺を留めた 1×1 の布・2 秒後）: いちばん伸びた辺の伸び率と Stretch Stiffness（10 の何乗か）",
               x_label="Stretch Stiffness の指数 e（1 × 10^e）", y_label="いちばん伸びた辺の伸び %")
    by = {(r["exp"], r["substeps"]): r for r in rows}
    t1 = sum(r["sec_49f"] for r in rows if r["substeps"] == 1) / 4
    t5 = sum(r["sec_49f"] for r in rows if r["substeps"] == 5) / 4
    payload = {
        "title": "Vellum の布は既定の硬さでも Substeps 1 で 2% 伸びる — Substeps 1 では 10^4 と 10^10 の差が出ない",
        "summary":
            "1 × 1 の布（21 × 21 点）を縦に立て、上の辺を Pin Points で留めて、重力で 2 秒（49 フレーム）ぶら下げた。"
            "vellumconstraints（Cloth）の Stretch Stiffness を 1 × 10^e で変え、四角形の辺の長さが元の何倍になったかを測った。\n\n"
            f"**既定（10^10）でも、Substeps 1 ではいちばん伸びた辺が {(by[(10, 1)]['max_stretch'] - 1) * 100:.1f}% 伸びた**"
            f"（平均 {(by[(10, 1)]['mean_stretch'] - 1) * 100:.2f}%、下の辺は {by[(10, 1)]['sag']:.4f} 下がった）。"
            f"Substeps を 5 にすると {(by[(10, 5)]['max_stretch'] - 1) * 100:.2f}% まで縮んだ。\n\n"
            f"**10^4 と 10^10 は、Substeps 1 ではほぼ同じ伸び**（{(by[(4, 1)]['max_stretch'] - 1) * 100:.1f}% と {(by[(10, 1)]['max_stretch'] - 1) * 100:.1f}%）。"
            "硬さをいくら上げても、1 ステップで直しきれる量に上限があり、そこで止まっている。上限を上げるのは Substeps。\n\n"
            f"**10^3 から下では、硬さそのものが効く。**10^3 で {(by[(3, 1)]['max_stretch'] - 1) * 100:.0f}%、10^2 で {(by[(2, 1)]['max_stretch'] - 1) * 100:.0f}%"
            f"（布の下の辺が {by[(2, 1)]['sag']:.2f} 下がり、ゴムのように伸びる）。ここでは Substeps を上げても、伸びはあまり変わらない（10^3 で 29% → 25%、10^2 で 184% → 185%）。\n\n"
            f"**Substeps 5 の時間は約 {t5 / t1:.1f} 倍**（49 フレームで平均 {t1:.1f} 秒 → {t5:.1f} 秒）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Stretch Stiffness・Substeps と伸び",
            "images": [{"path": "170_stretch.png", "caption": "Substeps 1（青）は 10^4 より上で平ら。Substeps 5（橙）は 10^10 まで下がり続ける。"}],
            "per_row": 1,
            "columns": ["Stretch Stiffness", "Substeps", "いちばん伸びた辺", "辺の平均", "下の辺の下がり", "49 フレームの秒"],
            "rows": [[f"1e{r['exp']}", r["substeps"], f"{(r['max_stretch'] - 1) * 100:.2f}%", f"{(r['mean_stretch'] - 1) * 100:.2f}%",
                      f"{r['sag']:.4f}", f"{r['sec_49f']:.2f}"] for r in rows]}],
        "notes": [
            "<strong>布が伸びて見えるなら、まず Substeps を上げる。</strong>既定の硬さのままで、伸びは 2.3% → 0.1%。",
            "<strong>Substeps 1 なら、Stretch Stiffness は 10^4 より上ではほぼ同じ。</strong>Substeps 5 では 10^4 でも 2.3% 伸びるので、硬さも要る。",
            "<strong>Substeps 5 で時間は約 2.5 倍。</strong>",
        ],
        "next": ["Constraint Iterations を増やしたときの伸び", "布の細かさ（点の数）で伸びがどう変わるか"],
    }
    with open(os.path.join(OUT, "170_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 170_report.json", round(t5 / t1, 2))


if __name__ == "__main__":
    main()
