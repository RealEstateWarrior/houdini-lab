# -*- coding: utf-8 -*-
"""実験211 の断面: 保存したシーンから、机の真ん中（z = 0 付近）の布の点を取り出す。

    hython examples/211_section.py
"""
import json
import os

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
hou.hipFile.load(os.path.join(OUT, "211_scene.hipnc").replace("\\", "/"), suppress_save_prompt=True, ignore_load_warnings=True)
geo = hou.node("/obj/bench")
sec = {}
for name in ("t020", "t010", "t005", "t0025", "calc"):
    g = geo.node(f"final_{name}").geometry()
    pts = sorted((round(p.position()[0], 4), round(p.position()[1], 4)) for p in g.points() if abs(p.position()[2]) < 0.012)
    sec[name] = pts
with open(os.path.join(OUT, "211_section.json"), "w", encoding="utf-8") as fp:
    json.dump(sec, fp)
print({k: len(v) for k, v in sec.items()})
