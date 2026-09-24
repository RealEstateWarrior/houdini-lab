# -*- coding: utf-8 -*-
"""実験233 の図とレポートを、測った値から組み立てる。

炎の細かさは、炎のまわり（640×360 の画の x 150〜490・y 40〜300）を切り出し、となりの画素との明るさの差の平均（くっきり具合）で測る。
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

BOX = (150, 40, 490, 300)


def png(v):
    return os.path.join(OUT, f"233_v{v:g}.png".replace("0.", "0p"))


def main():
    with open(os.path.join(OUT, "233_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    t = {r["voxel"]: r for r in rows}
    for v, r in t.items():
        im = np.asarray(Image.open(png(v)).convert("L").crop(BOX), dtype=float)
        r["sharp"] = round(float(np.abs(np.diff(im, axis=1)).mean() + np.abs(np.diff(im, axis=0)).mean()), 3)
    font = _font(15)
    w, h = BOX[2] - BOX[0], BOX[3] - BOX[1]
    order = sorted(t, reverse=True)
    sheet = Image.new("RGB", (w * len(order), h + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, v in enumerate(order):
        im = Image.open(png(v)).convert("RGBA").crop(BOX)
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (i * w, 26))
        dr.text((i * w + 6, 4), f"Voxel Size {v:g}{'（実践）' if v == 0.04 else ''}", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "233_grid.png"))
    table = [[f"{v:g}", "×".join(map(str, t[v]["res"])), f"{t[v]['voxels']:,}", f"{t[v]['sim_sec']:.2f}", f"{t[v]['render_sec']:.2f}", f"{t[v]['sharp']:.2f}",
              f"{t[v]['diff_to_002']:.2f}"] for v in order]
    g = lambda v, f: t[v][f]  # noqa: E731
    payload = {
        "title": f"焚き火の Pyro は、Voxel Size を 0.08 → 0.02 に細かくして升目が 28 倍になっても、撮る時間は {g(0.08, 'render_sec'):.1f} → {g(0.02, 'render_sec'):.1f} 秒（{(g(0.02, 'render_sec') / g(0.08, 'render_sec') - 1) * 100:.0f}% 増）。"
                 f"増えるのは計算（{g(0.08, 'sim_sec'):.1f} → {g(0.02, 'sim_sec'):.1f} 秒）で、画は細かいほど炎の縁が裂ける",
        "summary":
            "**課題: 実験202 で、焚き火の Pyro は Voxel Size 0.04 で計算が速くなり、炎の高さはほぼ変わらなかった。では、Karma で撮る時間と、画の見た目はどう変わるのか。どこまで粗くしてよいのか。**\n\n"
            "実践「焚き火」の場面（フレーム 60）で、pyrosolver の Voxel Size を 0.08・0.06・0.04（実践の値）・0.03・0.02 にした。"
            "640×360・16 サンプル＋ノイズ除去で撮り、条件ごとに別の hython で、はじめに小さく 1 枚撮って捨てた。"
            "炎の細かさは、炎のまわりを切り出して、となりの画素との明るさの差の平均（くっきり具合）で測った。\n\n"
            f"**撮る時間は、升目の数ほどは増えない。**升目は 0.08・0.06・0.04・0.03・0.02 で {g(0.08, 'voxels'):,}・{g(0.06, 'voxels'):,}・{g(0.04, 'voxels'):,}・{g(0.03, 'voxels'):,}・{g(0.02, 'voxels'):,} 個"
            f"（28 倍）なのに、撮る時間は {g(0.08, 'render_sec'):.1f}・{g(0.06, 'render_sec'):.1f}・{g(0.04, 'render_sec'):.1f}・{g(0.03, 'render_sec'):.1f}・{g(0.02, 'render_sec'):.1f} 秒。\n\n"
            f"**計算の時間は、升目に応じて増える。**60 フレームで {g(0.08, 'sim_sec'):.1f}・{g(0.06, 'sim_sec'):.1f}・{g(0.04, 'sim_sec'):.1f}・{g(0.03, 'sim_sec'):.1f}・{g(0.02, 'sim_sec'):.1f} 秒。\n\n"
            f"**細かいほど、炎の縁が裂けて舌が出る。**くっきり具合（大きいほど細かい）は {g(0.08, 'sharp'):.2f}・{g(0.06, 'sharp'):.2f}・{g(0.04, 'sharp'):.2f}・{g(0.03, 'sharp'):.2f}・{g(0.02, 'sharp'):.2f}。"
            "0.08・0.06 はぼんやりした塊、0.04 で炎の舌が見え、0.02 で縁が細かく裂けた。"
            f"画全体の 0.02 との差（0〜255）は {g(0.08, 'diff_to_002'):.1f}・{g(0.06, 'diff_to_002'):.1f}・{g(0.04, 'diff_to_002'):.1f}・{g(0.03, 'diff_to_002'):.1f} と小さい"
            "（画の大半が暗い背景のため。炎の形は升目ごとに違う揺れ方になる）。\n\n"
            "**決め方: 撮る時間は気にせず、計算の時間が許す限り細かくする。**この焚き火なら 0.02 でも計算は数秒。遠景で炎が小さく写るなら 0.04 で足りる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Voxel Size と炎（フレーム 60、炎のまわりを切り出し）",
             "images": [{"path": "233_grid.png", "caption": "左から 0.08・0.06・0.04（実践）・0.03・0.02。細かいほど炎の縁が裂ける。"}],
             "per_row": 1, "columns": ["Voxel Size", "炎の升目", "升目の数", "計算 60 フレーム（秒）", "撮る時間（秒）", "くっきり具合", "0.02 との差"],
             "rows": table},
        ],
        "notes": [
            f"<strong>Voxel Size を細かくして升目が 28 倍になっても、撮る時間は {(g(0.02, 'render_sec') / g(0.08, 'render_sec') - 1) * 100:.0f}% 増（{g(0.08, 'render_sec'):.1f} → {g(0.02, 'render_sec'):.1f} 秒）。</strong>",
            f"<strong>増えるのは計算の時間（{g(0.08, 'sim_sec'):.1f} → {g(0.02, 'sim_sec'):.1f} 秒）。</strong>",
            "<strong>細かいほど炎の縁が裂けて、炎らしくなる。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "233_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])
    print({v: t[v]["sharp"] for v in order})


if __name__ == "__main__":
    main()
