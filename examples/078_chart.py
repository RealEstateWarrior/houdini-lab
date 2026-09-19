"""実験078の図。摩擦 1.0 で、いちばん高い粒の高さを粒の間隔ごとに描く（10フレームおき）。

    python examples/078_chart.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pil_chart import PALETTE, line_chart  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
with open(os.path.join(OUT, "078_stats.json"), encoding="utf-8") as fp:
    rows = json.load(fp)
series = []
for i, r in enumerate(x for x in rows if x["friction"] == 1.0):
    pts = [(t["frame"], t["top"]) for t in r["trace"]]
    series.append({"label": f"間隔 {r['sep']:g}（{r['count']}粒）", "points": pts, "color": PALETTE[i]})
line_chart(os.path.join(OUT, "078_top.png"), series,
           x_label="フレーム", y_label="いちばん高い粒の高さ（摩擦 1.0）",
           size=(1000, 540), x_range=(0, 120), y_range=(-1, 50))
print("保存: out/078_top.png")
