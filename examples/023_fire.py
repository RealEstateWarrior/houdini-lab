"""実験023 — 炎を出す。shredding は本当に炎のための設定なのか。

実験021で shredding を 1.0 でも 20.0 でも試したが、数値が小数点以下まで完全に一致した。
まったく効いていない。付属ヘルプにはこうある。

「温度の勾配にもとづいて速度場を押し引きし、炎に特有の筋・裂け目・舌のような形を作る」

021では「炎を伴わない煙だけの設定では出番がないのだろう」と書いたが、確かめていない。
今回それを確かめる。

仮説: 燃焼を入れて炎が出れば、shredding は効くようになる。
否定できる形: 燃焼を入れても数値が変わらなければ、仮説は誤り。
              その場合は shredding が効く条件を別に探す必要がある。

    hython examples/023_fire.py <条件>
    条件: smoke / smoke_shred / fire / fire_shred
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
    "smoke":       dict(fire=False, shredding=0.0),
    "smoke_shred": dict(fire=False, shredding=5.0),
    "fire":        dict(fire=True, shredding=0.0),
    "fire_shred":  dict(fire=True, shredding=5.0),
}


def build(fire, shredding):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "burn")

    emitter = geo.createNode("sphere", "emitter")
    emitter.parm("type").set(2)
    emitter.parmTuple("rad").set((0.22, 0.22, 0.22))
    emitter.parmTuple("t").set((0.0, -0.9, 0.0))
    emitter.parm("rows").set(24)
    emitter.parm("cols").set(24)

    src = geo.createNode("pyrosource", "src")
    src.setFirstInput(emitter)
    if fire:
        # 燃焼用の一式（密度・温度・燃料・燃え方）をまとめて作る presets
        src.parm("initialize").set("sourceburn")
        src.parm("initialize").pressButton()
    else:
        src.parm("attributes").set(2)
        src.parm("attribute1").set("density")
        src.parm("attribute2").set("temperature")

    made = [src.parm(f"attribute{i + 1}").evalAsString()
            for i in range(src.parm("attributes").eval())]
    print("  pyrosource が作る属性:", made)

    rast = geo.createNode("volumerasterizeattributes", "rasterize")
    rast.setFirstInput(src)
    rast.parm("attributes").set(" ".join(made))
    rast.parm("voxelsize").set(VOXEL)

    solver = geo.createNode("pyrosolver", "solve")
    solver.setFirstInput(rast)
    if fire:
        solver.parm("addflamefield").set(True)
        # 炎から煙（density）も出す。これが無いと見えるものが炎だけになる
        if solver.parm("doflamedensity") is not None:
            solver.parm("doflamedensity").set(True)
            # 既定は 0.0001 で、ほとんど煙が出ない
            solver.parm("flamedensity").set(1.0)
    if shredding > 0:
        solver.parm("enable_shredding").set(True)
        solver.parm("shredding").set(shredding)

    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    return geo, solver, made


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
    names = sorted({p.attribValue("name") for p in geo.prims()
                    if p.type() == hou.primType.Volume})
    # 炎の設定では density が作られない。どの条件にもある temperature を主指標にする。
    volume = field(geo, "temperature")
    if volume is None:
        return {"fields": names}

    res = volume.resolution()
    values = numpy.asarray(volume.allVoxels(), dtype=numpy.float64)
    filled = values[values > 1e-4]
    if filled.size == 0:
        return {"fields": names, "total": 0.0, "filled": 0, "cv": 0.0,
                "res": list(res)}
    mean = float(filled.mean())
    row = {"fields": names, "total": float(filled.sum()),
           "filled": int(filled.size), "cv": float(filled.std() / mean),
           "res": list(res)}

    for extra_name in ("flame", "burn", "density"):
        prim = field(geo, extra_name)
        if prim is None:
            continue
        vals = numpy.asarray(prim.allVoxels(), dtype=numpy.float64)
        hot = vals[vals > 1e-4]
        row[f"{extra_name}_total"] = float(hot.sum()) if hot.size else 0.0
        row[f"{extra_name}_filled"] = int(hot.size)
    return row


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if name not in CASES:
        raise SystemExit(f"条件は {list(CASES)} のどれか")

    print(f"条件: {name}  {CASES[name]}")
    geo, solver, made = build(**CASES[name])

    rows = []
    start = time.perf_counter()
    for frame in FRAMES:
        row = stats(solver, frame)
        if row is None or "total" not in row:
            print(f"  F{frame}: 密度が見つからない / 場: {row}")
            continue
        rows.append(dict(row, frame=frame))
        extra = "".join(
            f" / {tag} {row[f'{tag}_total']:8.1f}({row[f'{tag}_filled']})"
            for tag in ("flame", "burn", "density") if f"{tag}_total" in row)
        print(f"  F{frame:3d}: 合計 {row['total']:10.2f} / 中身 {row['filled']:7d} / "
              f"ばらつき {row['cv']:.4f} / 格子 {row['res']}{extra}")
    elapsed = time.perf_counter() - start

    hou.setFrame(LAST)
    bbox = hou_tools.bbox_over_frames(solver.path(), [LAST])
    hou_tools.render_preview(solver.path(), os.path.join(OUT, f"023_{name}.png"),
                             res=(400, 480), shading="smooth", frame_bbox=bbox)

    with open(os.path.join(OUT, f"023_{name}.json"), "w", encoding="utf-8") as fp:
        json.dump({"case": name, "params": CASES[name], "fields": made,
                   "rows": rows, "sec": elapsed}, fp, ensure_ascii=False, indent=2)
    if name == "fire_shred":
        hou_tools.write_graph(geo.path(), os.path.join(OUT, "023_graph.json"),
                              title="実験023 — 炎を出す")
        hou_tools.save_hip(os.path.join(OUT, "023_fire.hipnc"))
    print(f"  {elapsed:.1f}秒 / out/023_{name}.json, out/023_{name}.png")


if __name__ == "__main__":
    main()
