"""実験079の図。一度に生んだ 4,000粒のうち、生きている数の移り変わり。

    python examples/079_chart.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pil_chart import PALETTE, line_chart  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
with open(os.path.join(OUT, "079_a.json"), encoding="utf-8") as fp:
    rows = json.load(fp)
series = []
for i, r in enumerate(rows):
    pts = [(k / 24.0, c) for k, c in enumerate(r["counts"])]
    series.append({"label": f"Life 1.0・Life Variance {r['lifevar']:g}", "points": pts,
                   "color": PALETTE[i]})
line_chart(os.path.join(OUT, "079_alive.png"), series,
           x_label="生まれてからの秒", y_label="生きている粒の数",
           size=(1000, 520), x_range=(0, 2.4), y_range=(0, 4200))
print("保存: out/079_alive.png")
