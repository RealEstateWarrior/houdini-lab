"""実験073の図。いちばん高い粒の高さを、フレームに沿って描く。

    python examples/073_chart.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pil_chart import PALETTE, line_chart  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
with open(os.path.join(OUT, "073_b.json"), encoding="utf-8") as fp:
    b = {r["friction"]: r for r in json.load(fp)}
with open(os.path.join(OUT, "073_d.json"), encoding="utf-8") as fp:
    d = {r["substeps"]: r for r in json.load(fp)}

series = []
for i, mu in enumerate((0.25, 0.5, 1.0, 1.5)):
    pts = [(f["frame"], f["y_top"]) for f in b[mu]["frames"]]
    series.append({"label": f"摩擦 {mu:g}", "points": pts, "color": PALETTE[i]})
pts = [(f["frame"], f["y_top"]) for f in d[8]["frames"]]
series.append({"label": "摩擦 0.25・substep 8", "points": pts, "color": PALETTE[4], "dash": True})
line_chart(os.path.join(OUT, "073_top.png"), series,
           x_label="フレーム", y_label="いちばん高い粒の高さ",
           size=(1000, 540), x_range=(0, 120), y_range=(-0.5, 20.0))
print("保存: out/073_top.png")
