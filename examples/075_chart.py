"""実験075の図。粒の間隔ごとの「実効の摩擦」。

    python examples/075_chart.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pil_chart import PALETTE, line_chart  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
rows = []
for name in ("075_a.json", "075_c.json"):
    with open(os.path.join(OUT, name), encoding="utf-8") as fp:
        rows += json.load(fp)
rows.sort(key=lambda r: r["sep"])
pts = [(r["sep"], r["mu_eff"]) for r in rows]
line_chart(os.path.join(OUT, "075_mu.png"),
           [{"label": "実効の摩擦（境目の ω² r ÷ g）", "points": pts, "color": PALETTE[0]},
            {"label": "入れた摩擦 1.0", "points": [(0.03 + i * 0.004, 1.0) for i in range(41)],
             "color": PALETTE[4], "dash": True}],
           x_label="粒の間隔 particlesep（左ほど細かい）", y_label="実効の摩擦",
           size=(900, 500), x_range=(0.03, 0.19), y_range=(0.0, 1.1),
           markers=[(r["sep"], r["mu_eff"], f"{r['mu_eff']:.2f}") for r in rows])
print("保存: out/075_mu.png")
