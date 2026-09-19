"""実験076の図。粒の間隔ごとの「実測 ÷ 式」。1 に近いほど式どおり。

    python examples/076_chart.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pil_chart import PALETTE, line_chart  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
with open(os.path.join(OUT, "076_a.json"), encoding="utf-8") as fp:
    a = json.load(fp)
with open(os.path.join(OUT, "076_b.json"), encoding="utf-8") as fp:
    b = json.load(fp)

series = []
for i, mu in enumerate((0.25, 0.5, 1.0, 2.0)):
    pts = sorted((r["sep"], r["ratio"]) for r in a if r["friction"] == mu)
    series.append({"label": f"滑る塊・摩擦 {mu:g}", "points": pts, "color": PALETTE[i]})
series.append({"label": "動く板・摩擦 1", "points": sorted((r["sep"], r["ratio"]) for r in b),
               "color": PALETTE[4], "dash": False})
series.append({"label": "", "points": [(0.035 + k * 0.0025, 1.0) for k in range(37)],
               "color": (160, 160, 168), "dash": True})
line_chart(os.path.join(OUT, "076_ratio.png"), series,
           x_label="粒の間隔 particlesep（左ほど細かい）", y_label="実測 ÷ 式（1 なら式どおり）",
           size=(1000, 540), x_range=(0.035, 0.125), y_range=(0.5, 3.6))
print("保存: out/076_ratio.png")
