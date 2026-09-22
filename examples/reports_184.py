# -*- coding: utf-8 -*-
"""実験184 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "184_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "184_count.png"),
               [{"label": "Jitter Scale 1（既定）", "points": [(r["sep"], r["n_s3"]) for r in rows if r["jitter"] == 1.0], "color": PALETTE[0]},
                {"label": "Jitter Scale 0", "points": [(r["sep"], r["n_s3"]) for r in rows if r["jitter"] == 0.0], "color": PALETTE[1]},
                {"label": "箱の体積 1", "points": [(0.025, 1.0), (0.1, 1.0)], "color": PALETTE[4], "dash": True}],
               title="mpmsource（1×1×1 の箱）: 粒の数 × Particle Separation³",
               x_label="Particle Separation", y_label="粒の数 × s³")
    j0 = [r for r in rows if r["jitter"] == 0.0]
    grid_ok = all(r["points"] == (round(1 / r["sep"]) + 1) ** 3 for r in j0)
    j1 = [r for r in rows if r["jitter"] == 1.0]
    payload = {
        "title": "mpmsource は箱に「体積 ÷ Particle Separation³」個の粒を詰める — pscale には Separation そのものが入る",
        "summary":
            "1 × 1 × 1 の箱を mpmsource（入力 2 に mpmcontainer）で粒にし、mpmcontainer の Particle Separation s と、mpmsource の Jitter Scale を変えた。\n\n"
            "**既定（Jitter Scale 1）では、粒の数 × s³ が箱の体積 1 にほぼ一致した**（"
            + "・".join(f"s = {r['sep']:g} で {r['n_s3']:.4f}" for r in j1) + "）。粒1つが s³ の体積を受け持つ。\n\n"
            f"**Jitter Scale 0 だと、粒は升目どおりに並び、箱の面の上にも乗る。**数は (1/s + 1)³ と{'3通りとも一致' if grid_ok else '合わないものがあった'}"
            f"（s = 0.1 で {j0[0]['points']:,} = 11³）。x の並びは −0.5 から 0.5 まで {j0[0]['x_layers']} 層。そのぶん、粒の数 × s³ は体積より多くなる"
            "（実験141 の pointsfromvolume の Grid と同じ）。揺らぎ（Jitter）を入れると、面の上に並ぶぶんが消えて数が合う。\n\n"
            "**粒には pscale と density が付き、mass は付かない。**pscale は Particle Separation と同じ値（s = 0.05 なら 0.05。半径なら半分のはずだが、そうではない）、"
            "density はどの粒も既定の 400。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Particle Separation・Jitter と粒",
            "images": [{"path": "184_count.png", "caption": "Jitter 1（青）は 1 に乗る。Jitter 0（橙）は面の上の分だけ多い。"}],
            "per_row": 1,
            "columns": ["Separation", "Jitter Scale", "粒の数", "粒の数 × s³", "(1/s+1)³", "pscale", "density", "x の層", "秒"],
            "rows": [[f"{r['sep']:g}", f"{r['jitter']:g}", f"{r['points']:,}", f"{r['n_s3']:.5f}", f"{(round(1 / r['sep']) + 1) ** 3:,}",
                      f"{r['pscale_min']:g}", f"{r['density_min']:g}", r["x_layers"] or "—", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>粒の数は 体積 ÷ Separation³。</strong>Separation を半分にすると粒は 8 倍（重さの見積もりに使える）。",
            "<strong>pscale は Separation と同じ値。</strong>粒を球で見せるとき、そのまま使うと隣と重なる。",
            "<strong>Jitter を 0 にすると、面の上にも粒が並ぶ。</strong>数が (1/s + 1)³ に増える。",
        ],
        "next": ["丸い形（球）を詰めたときの数", "mpmsolver で落としたときに粒の数と体積が保たれるか"],
    }
    with open(os.path.join(OUT, "184_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 184_report.json", grid_ok)


if __name__ == "__main__":
    main()
