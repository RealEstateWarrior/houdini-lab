# -*- coding: utf-8 -*-
"""実験202 — 焚き火の炎を短時間で回すには、どの設定から下げればよいか。

制作の問い: Pyro の焚き火を速く回したい。Voxel Size を粗くするか、速度の升だけ粗くするか、Substeps を触るか。
何を下げると見た目（炎の高さ・揺らぎ・煙の量）が崩れ、どれだけ速くなるか。

  地面に置いた平たい球（半径 0.3、高さ方向 0.3 倍）を pyrosource の Initialize = Source Burn で燃やす（炎と煙を出す）。
  pyrosolver（SOP）を 48 フレーム（24 fps で 2 秒）回し、次の条件を1プロセスずつ測る。
    vox020（基準）・vox030・vox040・vox060  … Voxel Size（divsize）。発生源を升にする大きさも同じにする
    veldiv2                                  … Voxel Size 0.02 のまま Velocity Voxel Scale を 2（速度の升だけ倍）
    sub2                                     … Voxel Size 0.02 のまま Max Substeps を 2（既定は 1）
  毎フレーム、炎（flame > 0.1）の高さ（上から 1% の点の y）と量（升の数 × 升の体積）、煙（density > 0.02）の量を記録し、
  フレーム 24・36・48 で炎と煙を正面（z 方向）に投影した画を、どの条件も同じ枠（x −1〜1、y 0〜3）で書き出す。

    hython examples/202_pyro_campfire_cost.py vox020      （条件を1つずつ）
    hython examples/202_pyro_campfire_cost.py combine
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

CASES = {
    "vox020": {"vox": 0.02},
    "vox030": {"vox": 0.03},
    "vox040": {"vox": 0.04},
    "vox060": {"vox": 0.06},
    "veldiv2": {"vox": 0.02, "veldiv": 2.0},
    "sub2": {"vox": 0.02, "substeps": 2},
}
FRAMES = 48
SHOTS = [24, 36, 48]
CANVAS = (-1.0, 1.0, 0.0, 3.0)   # x0, x1, y0, y1
PIX = 0.01


def build(vox, veldiv=1.0, substeps=None):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "fire")
    emitter = geo.createNode("sphere", "log")
    emitter.parm("type").set(2)
    emitter.parmTuple("rad").set((0.3, 0.09, 0.3))
    emitter.parmTuple("t").set((0.0, 0.09, 0.0))
    emitter.parm("rows").set(24)
    emitter.parm("cols").set(24)
    src = geo.createNode("pyrosource", "src")
    src.setFirstInput(emitter)
    src.parm("initialize").set("sourceburn")
    src.parm("initialize").pressButton()
    made = [src.parm(f"attribute{i + 1}").evalAsString() for i in range(src.parm("attributes").eval())]
    rast = geo.createNode("volumerasterizeattributes", "rasterize")
    rast.setFirstInput(src)
    rast.parm("attributes").set(" ".join(made))
    rast.parm("voxelsize").set(vox)
    solver = geo.createNode("pyrosolver", "solve")
    solver.setFirstInput(rast)
    solver.parm("divsize").set(vox)
    solver.parm("addflamefield").set(True)
    solver.parm("doflamedensity").set(True)
    solver.parm("flamedensity").set(1.0)    # 既定 0.0001 では煙がほとんど出ない（実験023）
    solver.parm("veldivscale").set(veldiv)
    if substeps:
        solver.parm("substeps").set(substeps)
    solver.setDisplayFlag(True)
    return geo, solver, made


def field(geo, name):
    import hou
    for prim in geo.prims():
        if prim.type() == hou.primType.Volume and prim.attribValue("name") == name:
            return prim
    return None


def grid(prim):
    """升の値を (z, y, x) の配列と、各軸の位置で返す。"""
    rx, ry, rz = prim.resolution()
    a = np.asarray(prim.allVoxels(), dtype=np.float32).reshape(rz, ry, rx)
    p0 = prim.indexToPos((0, 0, 0))
    p1 = prim.indexToPos((rx - 1, ry - 1, rz - 1))
    xs = np.linspace(p0[0], p1[0], rx)
    ys = np.linspace(p0[1], p1[1], ry)
    return a, xs, ys, prim.voxelSize()[0]


def project(prim):
    """正面から見た最大値を、決まった枠の画素に置く（升の大きさが違っても同じ枠で比べるため）。"""
    x0, x1, y0, y1 = CANVAS
    w, h = int(round((x1 - x0) / PIX)), int(round((y1 - y0) / PIX))
    img = np.zeros((h, w), dtype=np.float32)
    if prim is None:
        return img
    a, xs, ys, _ = grid(prim)
    m = a.max(axis=0)                      # (y, x)
    ix = np.clip(np.searchsorted(xs, x0 + (np.arange(w) + 0.5) * PIX) , 0, len(xs) - 1)
    iy = np.clip(np.searchsorted(ys, y0 + (np.arange(h) + 0.5) * PIX), 0, len(ys) - 1)
    inside_x = (x0 + (np.arange(w) + 0.5) * PIX >= xs[0]) & (x0 + (np.arange(w) + 0.5) * PIX <= xs[-1])
    inside_y = (y0 + (np.arange(h) + 0.5) * PIX >= ys[0]) & (y0 + (np.arange(h) + 0.5) * PIX <= ys[-1])
    img = m[iy][:, ix]
    img[~inside_y, :] = 0
    img[:, ~inside_x] = 0
    return img[::-1]                       # 上を上に


def measure(prim, thresh):
    if prim is None:
        return {"height": 0.0, "amount": 0.0}
    a, xs, ys, vs = grid(prim)
    hot = a > thresh
    if not hot.any():
        return {"height": 0.0, "amount": 0.0}
    yy = np.broadcast_to(ys[None, :, None], a.shape)[hot]
    return {"height": round(float(np.percentile(yy, 99)), 4), "amount": round(float(hot.sum() * vs ** 3), 5)}


def run_one(name):
    import hou
    cfg = CASES[name]
    # 1 回目の cook は起動の分だけ遅いので、小さく回して温めておく
    _, s0, _ = build(0.1)
    hou.setFrame(3)
    s0.geometry()
    geo, solver, made = build(cfg["vox"], cfg.get("veldiv", 1.0), cfg.get("substeps"))
    rec = {"case": name, **cfg, "attributes": made, "per_frame": [], "shots": {}}
    t0 = time.perf_counter()
    for f in range(1, FRAMES + 1):
        hou.setFrame(f)
        g = solver.geometry()
        fl, de = field(g, "flame"), field(g, "density")
        row = {"f": f, "flame": measure(fl, 0.1), "smoke": measure(de, 0.02)}
        if fl is not None:
            row["res"] = list(fl.resolution())
        rec["per_frame"].append(row)
        if f in SHOTS:
            np.save(os.path.join(OUT, f"202_{name}_flame_{f}.npy"), project(fl))
            np.save(os.path.join(OUT, f"202_{name}_smoke_{f}.npy"), project(de))
    rec["sec"] = round(time.perf_counter() - t0, 2)
    with open(os.path.join(OUT, f"202_part_{name}.json"), "w", encoding="utf-8") as fp:
        json.dump(rec, fp)
    if name == "vox020":
        import hou_tools
        hou_tools.save_hip(os.path.join(OUT, "202_fire.hipnc"))
    last = rec["per_frame"][-1]
    print(name, rec["sec"], last["flame"], last["smoke"], last.get("res"), flush=True)


def combine():
    import sop_bench
    rows = []
    for name in CASES:
        with open(os.path.join(OUT, f"202_part_{name}.json"), encoding="utf-8") as fp:
            rows.append(json.load(fp))
    ref = {f: (np.load(os.path.join(OUT, f"202_vox020_flame_{f}.npy")), np.load(os.path.join(OUT, f"202_vox020_smoke_{f}.npy"))) for f in SHOTS}
    for r in rows:
        r["image_diff"] = {}
        for f in SHOTS:
            fl = np.load(os.path.join(OUT, f"202_{r['case']}_flame_{f}.npy"))
            sm = np.load(os.path.join(OUT, f"202_{r['case']}_smoke_{f}.npy"))
            # 基準との違い: 炎が出ている範囲（> 0.1）の重なり（IoU）
            a, b = fl > 0.1, ref[f][0] > 0.1
            c, d = sm > 0.02, ref[f][1] > 0.02
            r["image_diff"][str(f)] = {"flame_iou": round(float((a & b).sum() / max((a | b).sum(), 1)), 3),
                                       "smoke_iou": round(float((c & d).sum() / max((c | d).sum(), 1)), 3)}
        hs = [x["flame"]["height"] for x in r["per_frame"] if x["f"] >= 24]
        r["flame_height_mean"] = round(float(np.mean(hs)), 4)
        r["flame_height_std"] = round(float(np.std(hs)), 4)
        r["flame_amount_mean"] = round(float(np.mean([x["flame"]["amount"] for x in r["per_frame"] if x["f"] >= 24])), 5)
        r["smoke_amount_48"] = r["per_frame"][-1]["smoke"]["amount"]
    sop_bench.save(202, rows, {"frames": FRAMES, "shots": SHOTS, "canvas": CANVAS})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        import hou  # noqa: F401
        run_one(sys.argv[1])
