# -*- coding: utf-8 -*-
"""実験194 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "194_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    for r in rows:
        r["model"] = r["life"] * 24 - 1 / r["substeps"]
    worst = max(abs(r["frames_alive"] - r["model"]) for r in rows)
    line_chart(os.path.join(OUT, "194_life.png"),
               [{"label": f"Life {l:g} 秒（測った値）", "points": [(r["substeps"], r["frames_alive"]) for r in rows if r["life"] == l], "color": PALETTE[i]}
                for i, l in enumerate((0.5, 0.52, 0.54))]
               + [{"label": f"Life×24 − 1/Substeps（{l:g} 秒）", "points": [(r["substeps"], r["model"]) for r in rows if r["life"] == l],
                   "color": PALETTE[4], "dash": True} for l in (0.5, 0.52, 0.54)],
               title="popsource（1 フレーム 100 粒）: 粒が平均で何フレームぶん数えられるか",
               x_label="DOP Network の Substeps", y_label="止まった数 ÷ 100")
    payload = {
        "title": "POP の粒が数えられるフレームは Life × fps − 1/Substeps — 0.5 秒の粒は Substeps 1 で 11 フレーム、4 で 11.75",
        "summary":
            "実験193 の続き。Constant Birth Rate 2400（24 fps で 1 フレーム 100 粒）で粒を生み続け、Life Expectancy（ばらつき 0）と DOP Network の Substeps を変えて、"
            "数が止まったときの粒の数を読んだ。止まった数 ÷ 100 が、1 粒が平均で何フレーム数えられるかになる。\n\n"
            f"**平均のフレーム数は Life × 24 − 1/Substeps に合った**（9 通りで差は最大 {worst:.2f} フレーム）。"
            "Life 0.5 秒（12 フレーム）なら、Substeps 1 で 11、2 で 11.5、4 で 11.75。\n\n"
            "**Substeps を上げると、粒はフレームの途中（サブステップごと）に生まれる。**生まれた時刻がばらけるぶん、1 フレームの半端が小さくなり、"
            "寿命が Life × fps に近づく。Substeps 1 では、生まれた瞬間から 1 ステップぶん先に進む（実験165）ことと合わせて、ちょうど 1 フレーム短くなる。\n\n"
            "**Life を 1/fps の端数だけ延ばせば、Substeps 1 でも 12 フレームになる。**Life 0.54 秒で 11.99 フレーム。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Life・Substeps と、止まった粒の数",
            "images": [{"path": "194_life.png", "caption": "測った値は点線の式に重なる。"}],
            "per_row": 1,
            "columns": ["Life（秒）", "Substeps", "止まった数", "平均のフレーム数", "Life × 24 − 1/Substeps", "49 フレームの秒"],
            "rows": [[f"{r['life']:g}", r["substeps"], f"{r['settled']:,}", f"{r['frames_alive']:.2f}", f"{r['model']:.2f}", f"{r['sec_49f']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>粒の寿命は Life × fps − 1/Substeps フレーム。</strong>Substeps 1 では 1 フレーム短い。",
            "<strong>ぴったり n フレーム生かしたいなら、Life を (n + 1)/fps より少し短く（Substeps 1）。</strong>12 フレームなら 0.54 秒。",
            "<strong>Substeps を上げると、生まれる時刻がフレームの途中に散らばる。</strong>粒の数がフレームごとに揃わなくなる。",
        ],
        "next": ["Life Variance を入れたときの数の減り方", "Impulse で一度に生んだ粒が消えるフレーム"],
    }
    with open(os.path.join(OUT, "194_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 194_report.json", worst)


if __name__ == "__main__":
    main()
