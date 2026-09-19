"""実験072の図。塊の一番下の高さを、時間に沿って描く。点線は板の真ん中の高さ。

    python examples/072_chart.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pil_chart import PALETTE, line_chart  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
START, LIFT = 0.5, 1.0

with open(os.path.join(OUT, "072_a.json"), encoding="utf-8") as fp:
    rows = json.load(fp)

series = []
for i, r in enumerate(rows):
    color = PALETTE[i]
    pts = [(f["time"], f["y_min"]) for f in r["frames"]]
    series.append({"label": f"v = {r['speed']:g}", "points": pts, "color": color})
    T = LIFT / r["speed"]
    plank = [(t / 100.0, min(max((t / 100.0 - START) / T, 0.0), 1.0) * LIFT)
             for t in range(0, 247)]
    series.append({"label": "", "points": plank, "color": color, "dash": True})
series[1]["label"] = "点線は同じ色の板の真ん中"
line_chart(os.path.join(OUT, "072_heights.png"),
           [s for s in series],
           x_label="時間（秒）", y_label="塊の一番下の高さ",
           size=(1000, 560), x_range=(0.0, 2.46), y_range=(-0.2, 3.8))
print("保存: out/072_heights.png")
