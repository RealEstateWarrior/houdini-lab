"""実験021 — 煙はなぜ動かなかったのか。そして形をどう出すか。

実験018で「いまの煙は一様な球で、レンダラーの差を見せる題材として弱い」と書いた。
形のある煙を作ろうとして測ったら、もっと手前に問題があった。

<strong>煙がまったく動いていなかった。</strong>

中身のあるボクセルの数が全フレームで 504 のまま、ばらつきも 1.4927 のまま。
合計だけが増えていく。これは「同じ形が濃くなっていくだけ」を意味する。
昇りも広がりもしていない。実験016の煙も、実は同じだった。

仮説: 浮力は温度で決まる。density だけを供給して temperature を供給していないので、
      昇る理由がない。

否定できる形にする。temperature を足して動かなければ、仮説は誤り。

測るもの
  中身のあるボクセル数 … 広がったか
  密度の重心の高さ    … 昇ったか
  変動係数           … 形があるか（倍率では変わらない量）
  合計               … かき乱しても保たれるか

    hython examples/021_smoke_structure.py <条件>
    条件: density / heat / heat_disturb / heat_shred
"""

import json
import os
import sys
import time

import hou
import numpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

FRAMES = [5, 15, 25, 40]
LAST = 40
VOXEL = 0.05

CASES = {
    "density":     dict(heat=False, disturbance=0.0, shredding=0.0),
    "heat":        dict(heat=True, disturbance=0.0, shredding=0.0),
    "heat_disturb": dict(heat=True, disturbance=2.0, shredding=0.0),
    "heat_shred":  dict(heat=True, disturbance=0.0, shredding=1.0),
    "heat_shred_big": dict(heat=True, disturbance=0.0, shredding=20.0),
}


def build(heat, disturbance, shredding):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "smoke")

    emitter = geo.createNode("sphere", "emitter")
    emitter.parm("type").set(2)
    emitter.parmTuple("rad").set((0.22, 0.22, 0.22))
    emitter.parmTuple("t").set((0.0, -0.9, 0.0))
    emitter.parm("rows").set(24)
    emitter.parm("cols").set(24)

    src = geo.createNode("pyrosource", "src")
    src.setFirstInput(emitter)
    # attributes は「作る属性の個数」。名前を書く欄ではない（実験016で踏んだ）
    src.parm("attributes").set(2 if heat else 1)
    src.parm("attribute1").set("density")
    if heat:
        src.parm("attribute2").set("temperature")

    rast = geo.createNode("volumerasterizeattributes", "rasterize")
    rast.setFirstInput(src)
    # こちらの attributes は空白区切りの文字列。同じ名前で意味が違う
    rast.parm("attributes").set("density temperature" if heat else "density")
    rast.parm("voxelsize").set(VOXEL)

    solver = geo.createNode("pyrosolver", "solve")
    solver.setFirstInput(rast)
    if disturbance > 0:
        solver.parm("enable_disturbance").set(True)
        solver.parm("disturbance").set(disturbance)
    if shredding > 0:
        solver.parm("enable_shredding").set(True)
        solver.parm("shredding").set(shredding)

    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    return geo, solver


def field(geo, name):
    for prim in geo.prims():
        if prim.type() == hou.primType.Volume and prim.attribValue("name") == name:
            return prim
    return None


def stats(solver, frame):
    hou.setFrame(frame)
    geo = solver.geometry()
    if geo is None:
        return None
    volume = field(geo, "density")
    if volume is None:
        return None

    res = volume.resolution()
    values = numpy.asarray(volume.allVoxels(), dtype=numpy.float64)
    grid = values.reshape((res[2], res[1], res[0]))   # z, y, x の順
    mask = grid > 1e-4
    filled = grid[mask]
    if filled.size == 0:
        return {"total": 0.0, "filled": 0, "cv": 0.0, "centre_y": 0.0,
                "res": list(res)}

    # 密度の重心が、上下方向でどこにあるか（0が下端、1が上端）
    weights = grid.sum(axis=(0, 2))            # y ごとの合計
    rows = numpy.arange(weights.size)
    centre = float((weights * rows).sum() / weights.sum() / max(weights.size - 1, 1))

    mean = float(filled.mean())
    return {"total": float(filled.sum()), "filled": int(filled.size),
            "cv": float(filled.std() / mean), "centre_y": centre,
            "peak": float(filled.max()), "res": list(res)}


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "density"
    if name not in CASES:
        raise SystemExit(f"条件は {list(CASES)} のどれか")

    geo, solver = build(**CASES[name])
    print(f"条件: {name}  {CASES[name]}")
    rows = []
    start = time.perf_counter()
    for frame in FRAMES:
        row = stats(solver, frame)
        if row is None:
            print(f"  フレーム{frame}: 密度が見つからない")
            continue
        rows.append(dict(row, frame=frame))
        print(f"  F{frame:3d}: 合計 {row['total']:10.2f} / 中身 {row['filled']:7d} / "
              f"重心の高さ {row['centre_y']:.4f} / ばらつき {row['cv']:.4f} / "
              f"格子 {row['res']}")
    elapsed = time.perf_counter() - start

    hou.setFrame(LAST)
    bbox = hou_tools.bbox_over_frames(solver.path(), [LAST])
    hou_tools.render_preview(solver.path(), os.path.join(OUT, f"021_{name}.png"),
                             res=(400, 480), shading="smooth", frame_bbox=bbox)

    with open(os.path.join(OUT, f"021_{name}.json"), "w", encoding="utf-8") as fp:
        json.dump({"case": name, "params": CASES[name], "rows": rows,
                   "sec": elapsed, "voxel": VOXEL}, fp, ensure_ascii=False, indent=2)
    if name == "heat_disturb":
        hou_tools.write_graph(geo.path(), os.path.join(OUT, "021_graph.json"),
                              title="実験021 — 構造のある煙")
        hou_tools.save_hip(os.path.join(OUT, "021_smoke.hipnc"))
    print(f"  {elapsed:.1f}秒 / out/021_{name}.json, out/021_{name}.png")


if __name__ == "__main__":
    main()
