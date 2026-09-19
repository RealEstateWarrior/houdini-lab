"""実験081の図。風速ごとの旗の角度（最後の2秒の平均）。0度＝水平、90度＝真下。

    python examples/081_chart.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pil_chart import PALETTE, line_chart  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
with open(os.path.join(OUT, "081_a.json"), encoding="utf-8") as fp:
    rows = json.load(fp)
pts = [(r["wind"], r["angle"]) for r in rows]
lo = [(r["wind"], r["angle_min"]) for r in rows]
hi = [(r["wind"], r["angle_max"]) for r in rows]
line_chart(os.path.join(OUT, "081_angle.png"),
           [{"label": "角度の平均（最後の2秒）", "points": pts, "color": PALETTE[0]},
            {"label": "揺れの最小・最大", "points": lo, "color": PALETTE[4], "dash": True},
            {"label": "", "points": hi, "color": PALETTE[4], "dash": True}],
           x_label="風速（Built-in Wind Speed）", y_label="旗の角度（度）",
           size=(900, 500), x_range=(0, 16.5), y_range=(-10, 100),
           markers=[(r["wind"], r["angle"], f"{r['angle']:.0f}") for r in rows])
print("保存: out/081_angle.png")
