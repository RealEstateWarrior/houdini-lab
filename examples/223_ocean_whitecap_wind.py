# -*- coding: utf-8 -*-
"""実験223 — 海の白波は、風の強さに合わせてどれだけ出せばよいか。cusp のしきい値を風速ごとに決める。

制作の問い: oceanevaluate の Cusp Attribute（波の頭のとがり）で白波の色を付けるとき、しきい値をいくつにすればよいのか。
実践「夕暮れの海」（風 7 m/秒）では 0.55 で白波が 0% だった。風が強い海では、どれだけ白くなるのが本物らしいのか。

  答えの出る形と突き合わせる:
    本物の白波が覆う割合 W（0〜1）= 3.84 × 10⁻⁶ × U^3.41（Monahan と O'Muircheartaigh, 1980。U は海面 10 m の風速 m/秒）
    本物の波の高さ（有義波高）Hs = 0.21 × U² / g（Pierson と Moskowitz の十分に発達した海）。高さの標準偏差は Hs / 4
  手順（風 U = 5・7・10・12・15 m/秒）:
    1. 200 m 四方の板（512 × 512）を、oceanspectrum（Grid Size 200・Resolution Exponent 9・Speed U・Chop 0.9）で動かす
    2. Amplitude の Scale を、高さの標準偏差が Hs / 4 になるように決める（既定 3 で測って比で直す）
    3. cusp の分布を測り、「cusp がしきい値を超える点の割合」が W になるしきい値を求める
  あわせて、しきい値を 0.55（夕暮れの海の値）に固定したときの割合も出す。

    hython examples/223_ocean_whitecap_wind.py
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
WINDS = (5, 7, 10, 12, 15)
G = 9.8
TIMES = (1.0, 3.0, 5.0)   # 3 つの時刻で測って平均する


def main():
    import hou
    import hou_tools
    import sop_bench
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "whitecaps")
    grid = geo.createNode("grid", "sea")
    grid.parmTuple("size").set((200, 200))
    grid.parm("rows").set(512)
    grid.parm("cols").set(512)
    spec = geo.createNode("oceanspectrum", "wind_waves")
    for k, v in dict(gridsize=200, res=9, chopscale=0.9).items():
        spec.parm(k).set(v)
    ev = geo.createNode("oceanevaluate::2.0", "move_points")
    ev.setInput(0, grid)
    ev.setInput(1, spec)
    ev.parm("cusp").set(1)
    rows = []
    for u in WINDS:
        spec.parm("windspeed").set(u)
        spec.parm("ampscale").set(3.0)
        target_std = 0.21 * u * u / G / 4
        ev.parm("time").set(TIMES[0])
        std3 = statistics.pstdev(ev.geometry().pointFloatAttribValues("P")[1::3])
        amp = 3.0 * target_std / std3
        spec.parm("ampscale").set(amp)
        cusp, stds = [], []
        for t in TIMES:
            ev.parm("time").set(t)
            g = ev.geometry()
            stds.append(statistics.pstdev(g.pointFloatAttribValues("P")[1::3]))
            cusp.extend(g.pointFloatAttribValues("cusp"))
        cusp.sort()
        w_frac = 3.84e-6 * u ** 3.41          # 割合（0〜1）。% にするなら 100 倍
        w_pct = w_frac * 100
        k = int(len(cusp) * (1 - w_frac))
        thr = cusp[min(k, len(cusp) - 1)]
        at055 = sum(1 for c in cusp if c > 0.55) / len(cusp) * 100
        info = {"wind": u, "hs_pm": round(0.21 * u * u / G, 3), "target_std": round(target_std, 4), "ampscale": round(amp, 4),
                "std": round(statistics.fmean(stds), 4), "whitecap_pct": round(w_pct, 4), "cusp_threshold": round(thr, 4),
                "pct_at_055": round(at055, 3), "cusp_p50": round(cusp[len(cusp) // 2], 4), "cusp_p99": round(cusp[int(len(cusp) * 0.99)], 4),
                "cusp_max": round(cusp[-1], 4)}
        rows.append(info)
        print(info, flush=True)
    # しきい値は、設計図の細かさ（Resolution Exponent）と Chop でどれだけ変わるか（風 10 m/秒で）
    base = next(r for r in rows if r["wind"] == 10)
    sens = []
    for label, parms in (("Resolution Exponent 8", {"res": 8}), ("Resolution Exponent 10", {"res": 10}),
                         ("Chop 0.6", {"chopscale": 0.6}), ("Chop 1.3", {"chopscale": 1.3})):
        spec.parm("windspeed").set(10)
        spec.parm("ampscale").set(base["ampscale"])
        keep = {k: spec.parm(k).eval() for k in parms}
        for k, v in parms.items():
            spec.parm(k).set(v)
        cusp = []
        for t in TIMES:
            ev.parm("time").set(t)
            cusp.extend(ev.geometry().pointFloatAttribValues("cusp"))
        cusp.sort()
        thr = cusp[int(len(cusp) * (1 - base["whitecap_pct"] / 100))]
        sens.append({"case": label, "cusp_threshold": round(thr, 4)})
        print(sens[-1], flush=True)
        for k, v in keep.items():
            spec.parm(k).set(v)
    # 画: 風 5・10・15 m/秒で、求めたしきい値を超えた所を白く塗って上から見る（手前 60 m 四方）
    paint = geo.createNode("attribwrangle", "paint_whitecaps")
    paint.setFirstInput(ev)
    paint.parm("snippet").set('v@Cd = f@cusp > ch("threshold") ? {0.95, 0.95, 0.95} : {0.02, 0.06, 0.09};')
    paint.addSpareParmTuple(hou.FloatParmTemplate("threshold", "Threshold", 1, default_value=(0.15,)))
    ev.parm("time").set(TIMES[0])
    for r in rows:
        if r["wind"] in (5, 10, 15):
            spec.parm("windspeed").set(r["wind"])
            spec.parm("ampscale").set(r["ampscale"])
            paint.parm("threshold").set(r["cusp_threshold"])
            hou_tools.render_preview(paint.path(), os.path.join(OUT, f"223_top_{r['wind']}.png"), res=(480, 480),
                                     direction=(0.0, 1.0, 0.001), shading="smooth",
                                     frame_bbox=hou.BoundingBox(-30, -2, -30, 30, 2, 30))
    spec.parm("windspeed").set(10)
    spec.parm("ampscale").set(base["ampscale"])
    paint.parm("threshold").set(base["cusp_threshold"])
    paint.setDisplayFlag(True)
    geo.layoutChildren()
    with open(os.path.join(OUT, "223_sens.json"), "w", encoding="utf-8") as fp:
        json.dump(sens, fp, ensure_ascii=False, indent=1)
    hou_tools.save_hip(os.path.join(OUT, "223_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "223_graph.json"), title="実験223")
    sop_bench.save(223, rows, {"times": TIMES, "grid": [200, 512]})


if __name__ == "__main__":
    main()
