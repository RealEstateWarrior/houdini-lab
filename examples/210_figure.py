# -*- coding: utf-8 -*-
"""実験210 の図: 181〜209 の点検結果を、1 本 1 マスで色分けする。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
from pil_chart import _font  # noqa: E402
import importlib  # noqa: E402

rep = importlib.import_module("reports_210")
_, detail = rep.main()
COL = {"ok": (46, 139, 87), "soft": (214, 170, 40), "bad": (200, 60, 50)}
f, fs = _font(22), _font(15)
cell, cols = 120, 8
nos = sorted(detail)
rows = (len(nos) + cols - 1) // cols
im = Image.new("RGB", (cell * cols + 40, cell * rows + 150), (255, 255, 255))
d = ImageDraw.Draw(im)
d.text((20, 16), "181〜209 の点検（1 マス 1 本）", fill=(20, 20, 20), font=f)
for i, no in enumerate(nos):
    v = detail[no]
    c = v["counts"]
    k = "ok" if v["n"] == 0 else ("bad" if c["value"] else "soft")
    x, y = 20 + (i % cols) * cell, 60 + (i // cols) * cell
    d.rounded_rectangle((x, y, x + cell - 10, y + cell - 10), 12, fill=COL[k])
    d.text((x + 12, y + 10), no, fill=(255, 255, 255), font=f)
    d.text((x + 12, y + 48), f"{v['values']:,} 値", fill=(255, 255, 255), font=fs)
    d.text((x + 12, y + 72), "一致" if v["n"] == 0 else f"ずれ {v['n']}", fill=(255, 255, 255), font=fs)
y0 = 60 + rows * cell + 10
for j, (k, lab) in enumerate((("ok", "完全に一致"), ("soft", "時間・ファイルの大きさ・足した項目だけ"), ("bad", "値が違う"))):
    d.rectangle((20 + j * 330, y0 + 20, 40 + j * 330, y0 + 40), fill=COL[k])
    d.text((48 + j * 330, y0 + 18), lab, fill=(30, 30, 30), font=fs)
im.save(os.path.join(HERE, "out", "210_summary.png"))
print("ok")
