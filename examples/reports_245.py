# -*- coding: utf-8 -*-
"""実験245 の図とレポートを、測った値から組み立てる。陰影図は保存した高さ（out/245_h_*.npy）から描く。"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

CASES = [(4, 10), (2, 10), (1, 10), (1, 5), (1, 2.5)]


def shade(h, sp):
    gy, gx = np.gradient(h, sp)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a, e = np.radians(315), np.radians(45)
    return np.clip(np.sin(e) * np.cos(slope) + np.cos(e) * np.sin(slope) * np.cos(a - aspect), 0, 1)


def main():
    with open(os.path.join(OUT, "245_stats.json"), encoding="utf-8") as fp:
        t = {(r["spacing"], r["feature_size"]): r for r in json.load(fp)["rows"]}
    font = _font(15)
    size = 300
    sheet = Image.new("RGB", (size * 5, size + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (sp, fs) in enumerate(CASES):
        h = np.load(os.path.join(OUT, f"245_h_{sp:g}_{fs:g}.npy"))
        c, q = h.shape[0] // 2, int(125 / sp)
        s = shade(h, sp)[c - q:c + q, c - q:c + q]
        sheet.paste(Image.fromarray((s * 255).astype(np.uint8)).resize((size, size)).convert("RGB"), (i * size, 26))
        dr.text((i * size + 6, 4), f"升 {sp:g} m・Feature {fs:g} m  {t[(sp, float(fs))]['sec']:.1f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "245_grid.png"))
    table = [[f"{sp:g}", f"{fs:g}", "×".join(map(str, t[(sp, float(fs))]["cells"])), f"{t[(sp, float(fs))]['sec']:.2f}",
              f"{t[(sp, float(fs))]['slope_mean']:.1f}", f"{t[(sp, float(fs))]['gully_share'] * 100:.1f}"] for sp, fs in CASES]
    g = lambda sp, fs, f: t[(float(sp), float(fs))][f]  # noqa: E731
    payload = {
        "title": "地形を削る heightfield_erode は、升を細かくしても谷の細かさは変わらない（升 2 m と 1 m でほぼ同じ絵、時間もほぼ同じ）。"
                 f"谷の細かさを決めるのは Erosion Feature Size（既定 10 m）で、2.5 m にすると細かい谷が刻まれ、時間は {g(1, 10, 'sec'):.1f} → {g(1, 2.5, 'sec'):.1f} 秒",
        "summary":
            "**課題: 実験227 で、1000 m 四方の地形（升 2 m）を 20 フレーム削るのは 1 秒だった。升を細かくすれば谷筋も細かくなり、時間は増えるはず。"
            "升を倍に細かくすると、刻まれる谷の細かさも倍になるのか。**\n\n"
            "heightfield（1000 m 四方）の Grid Spacing を 4・2・1 m にし、heightfield_noise（Element Size 300）で山を作って、heightfield_erode（::3.0）で 20 フレーム削った。"
            "升を細かくしても時間が変わらなかったので、升 1 m で Erosion Feature Size（既定 10 m）を 5・2.5 m にしたものも回した。"
            "谷の多さは、高さの 2 階微分（くぼみの強さ）が大きい升の割合で数え、陰影図（真ん中の 250 m 四方）で見比べた。\n\n"
            f"**升を細かくしても、時間も谷の細かさもほとんど変わらない。**升 4・2・1 m（升の数 16 倍）で、削る時間は {g(4, 10, 'sec'):.2f}・{g(2, 10, 'sec'):.2f}・{g(1, 10, 'sec'):.2f} 秒、"
            f"谷の多さは {g(4, 10, 'gully_share') * 100:.0f}・{g(2, 10, 'gully_share') * 100:.0f}・{g(1, 10, 'gully_share') * 100:.0f}%。"
            "陰影図でも、升 2 m と 1 m はほぼ同じ絵だった（4 m は少しぼやける）。\n\n"
            f"**谷の細かさは Erosion Feature Size で決まる。**升 1 m のまま Feature Size を 10・5・2.5 m にすると、谷の多さは {g(1, 10, 'gully_share') * 100:.0f}・{g(1, 5, 'gully_share') * 100:.0f}・{g(1, 2.5, 'gully_share') * 100:.0f}%、"
            f"斜面の傾きの平均は {g(1, 10, 'slope_mean'):.1f}・{g(1, 5, 'slope_mean'):.1f}・{g(1, 2.5, 'slope_mean'):.1f}°。陰影図でも、細かい谷が尾根いっぱいに刻まれた。"
            f"時間は {g(1, 10, 'sec'):.2f}・{g(1, 5, 'sec'):.2f}・{g(1, 2.5, 'sec'):.2f} 秒。"
            "升の数によらず時間がほぼ同じなのは、削る計算を Feature Size に合わせた粗さで行っているためと考えられる（確かめてはいない）。\n\n"
            "**決め方: 谷を細かくしたいときは、升ではなく Erosion Feature Size を小さくする。**この実験では、Feature Size 10 m に升 2 m と 1 m で同じ絵、"
            "4 m では少しぼやけた。升は Feature Size の 1/5 くらいあれば足りる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "升の細かさ・Erosion Feature Size と地形（陰影図、真ん中の 250 m 四方）",
             "images": [{"path": "245_grid.png", "caption": "左 3 つ: 升 4・2・1 m（Feature 10 m）。右 2 つ: 升 1 m で Feature 5・2.5 m。谷の細かさは Feature Size で決まる。"}],
             "per_row": 1, "columns": ["升（m）", "Feature Size（m）", "升の数", "削る時間（秒）", "斜面の傾き（°）", "谷の多さ（%）"], "rows": table},
        ],
        "notes": [
            "<strong>升を細かくしても、削る時間も谷の細かさもほとんど変わらない。</strong>",
            "<strong>谷の細かさは Erosion Feature Size で決まる（既定 10 m → 2.5 m で細かい谷）。</strong>",
            f"<strong>Feature Size 2.5 m でも、1000 m 四方・20 フレームで {g(1, 2.5, 'sec'):.1f} 秒。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "245_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
