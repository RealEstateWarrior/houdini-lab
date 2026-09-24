# -*- coding: utf-8 -*-
"""実験224 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font, line_chart  # noqa: E402


def main():
    with open(os.path.join(OUT, "224_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    sub = [t[k] for k in ("sub1", "sub2", "sub5", "sub10")]
    it = [t[k] for k in ("it25", "it50", "sub5", "it200", "it400")]
    line_chart(os.path.join(OUT, "224_cost.png"),
               [{"label": "Substeps 1・2・5・10（Iterations 100）", "points": [(r["sec"], r["stretch_mean"]) for r in sub]},
                {"label": "Constraint Iterations 25・50・100・200・400（Substeps 5）", "points": [(r["sec"], r["stretch_mean"]) for r in it]}],
               "布の伸び（平均）と計算の時間（66×84・72 フレーム）", "計算の時間（秒）", "伸びの平均（%）")
    font = _font(15)
    w, h = 480, 300
    shots = [("sub1", "Substeps 1"), ("sub2", "Substeps 2"), ("sub5", "Substeps 5（実験206）"), ("sub10", "Substeps 10")]
    sheet = Image.new("RGB", (w * 4, h + 28), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, lab) in enumerate(shots):
        im = Image.open(os.path.join(OUT, f"224_{k}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB").crop((0, 0, w, h)), (i * w, 28))
        dr.text((i * w + 8, 5), f"{lab}  伸び {t[k]['stretch_mean']:.2f}%・角 {t[k]['lowest']:.2f} m", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "224_grid.png"))
    table = [[k, f"{r['grid'][0]}×{r['grid'][1]}", str(r["substeps"]), str(r["niter"]), f"{r['sec']:.1f}", f"{r['stretch_mean']:.3f}",
              f"{r['stretch_p99']:.2f}", f"{r['stretch_max']:.1f}", f"{r['lowest']:.3f}"] for k, r in t.items()]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": f"Vellum の布の伸びは Substeps で決まる（1→5 で平均 {g('sub1', 'stretch_mean'):.1f}%→{g('sub5', 'stretch_mean'):.2f}%）。"
                 f"Constraint Iterations を 4 倍にするより Substeps を倍にする方が、短い時間でよく効く。布の目を細かくすると 4 倍伸びる",
        "summary":
            "**課題: テーブルクロスやカーテンが、ゴムのように伸びて垂れて見えることがある。vellumsolver の Substeps と Constraint Iterations（既定 100）の、"
            "どちらをいくつにすれば伸びなくなるのか。時間はどれだけ延びるのか。**\n\n"
            "実験206 と同じ机とテーブルクロス（1.9 × 1.45 m、66×84、Cloth の既定の硬さ）を 72 フレーム落とし、72 フレーム目の布の四角形の辺の長さを、"
            "落とす前の grid の同じ辺と比べた（伸び）。1 通りずつ、ほかの処理は回さずに時間も測った。\n\n"
            f"**Substeps がいちばん効く。**Substeps 1・2・5・10 で、伸びの平均は {g('sub1', 'stretch_mean'):.2f}・{g('sub2', 'stretch_mean'):.2f}・"
            f"{g('sub5', 'stretch_mean'):.3f}・{g('sub10', 'stretch_mean'):.3f}%、いちばん伸びた 1% の辺は {g('sub1', 'stretch_p99'):.1f}・{g('sub2', 'stretch_p99'):.1f}・"
            f"{g('sub5', 'stretch_p99'):.2f}・{g('sub10', 'stretch_p99'):.2f}%。"
            f"角のいちばん低い点は {g('sub1', 'lowest'):.2f}・{g('sub2', 'lowest'):.2f}・{g('sub5', 'lowest'):.2f}・{g('sub10', 'lowest'):.2f} m で、Substeps 1 では角が {(g('sub5', 'lowest') - g('sub1', 'lowest')) * 100:.0f} cm 長く垂れた。"
            f"時間は {g('sub1', 'sec'):.1f}・{g('sub2', 'sec'):.1f}・{g('sub5', 'sec'):.1f}・{g('sub10', 'sec'):.1f} 秒で、Substeps にほぼ比例する。\n\n"
            f"**Constraint Iterations も効くが、時間の割に弱い。**Substeps 5 のまま 25・50・100・200・400 にすると、伸びの平均は "
            f"{g('it25', 'stretch_mean'):.3f}・{g('it50', 'stretch_mean'):.3f}・{g('sub5', 'stretch_mean'):.3f}・{g('it200', 'stretch_mean'):.3f}・{g('it400', 'stretch_mean'):.3f}%、"
            f"時間は {g('it25', 'sec'):.1f}・{g('it50', 'sec'):.1f}・{g('sub5', 'sec'):.1f}・{g('it200', 'sec'):.1f}・{g('it400', 'sec'):.1f} 秒。"
            f"Substeps 10（{g('sub10', 'sec'):.0f} 秒、{g('sub10', 'stretch_mean'):.3f}%）は、Iterations 400（{g('it400', 'sec'):.0f} 秒、{g('it400', 'stretch_mean'):.3f}%）より短い時間でよく効いた。\n\n"
            f"**布の目を細かくすると伸びやすい。**132×168（目の数 4 倍）は同じ Substeps 5・Iterations 100 で伸びの平均 {g('fine_it100', 'stretch_mean'):.2f}%"
            f"（66×84 の約 {g('fine_it100', 'stretch_mean') / g('sub5', 'stretch_mean'):.0f} 倍）、角が {g('sub5', 'lowest') - g('fine_it100', 'lowest'):.2f} m 長く垂れた。"
            f"Iterations 400 にしても {g('fine_it400', 'stretch_mean'):.2f}%。時間は {g('fine_it100', 'sec'):.0f}・{g('fine_it400', 'sec'):.0f} 秒。\n\n"
            "**決め方: 伸びて見えたら、まず Substeps を上げる（布の目を細かくしたら、なおさら）。**Substeps 5 で平均 0.1% になり、見た目の垂れはほぼ止まる。"
            "Iterations は、Substeps を上げても伸びが残るときに足す。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "布の伸びと時間",
             "images": [{"path": "224_cost.png", "caption": "同じ時間なら、Substeps を上げた方が伸びは小さい。"},
                        {"path": "224_grid.png", "caption": "72 フレーム目。Substeps 1 は角が長く垂れる。"}],
             "per_row": 1, "columns": ["条件", "布の目", "Substeps", "Iterations", "時間（秒）", "伸び 平均（%）", "伸び 上位 1%（%）", "伸び 最大（%）", "角の高さ（m）"],
             "rows": table},
        ],
        "notes": [
            f"<strong>布の伸びは Substeps で決まる。</strong>1→5 で平均 {g('sub1', 'stretch_mean'):.1f}%→{g('sub5', 'stretch_mean'):.2f}%、角の垂れは {(g('sub5', 'lowest') - g('sub1', 'lowest')) * 100:.0f} cm 短くなった。",
            f"<strong>Iterations を 4 倍（400）にするより、Substeps を倍（10）にする方が、短い時間でよく効く。</strong>",
            f"<strong>布の目を 4 倍にすると、同じ設定で約 {g('fine_it100', 'stretch_mean') / g('sub5', 'stretch_mean'):.0f} 倍伸びる。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "224_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
