# -*- coding: utf-8 -*-
"""実験204 — 焚き火の Pyro をキャッシュに書くと何 MB になるか。何を削れば小さくなり、見た目の値はどれだけ変わるか。

制作の問い: Pyro を回したら、キャッシュがディスクを食う。速度の場（vel）を捨てる・VDB にする・16 bit で書く、
のどれがどれだけ効くのか。描画に使う値（density・flame・temperature）はどれだけずれるのか。

  実験202 と同じ焚き火（平たい球を Source Burn で燃やす。Voxel Size 0.04 と 0.02）を 48 フレーム回し、
  毎フレーム、次の 6 通りで .bgeo.sc に書いて大きさと書く時間を測る。VDB の 2 通りは .vdb にも書く。
    raw        … pyrosolver の出力そのまま（Houdini の Volume が 6 つ: density・temperature・flame・vel.x/y/z）
    novel      … vel.* を blast で消す
    vdb        … convertvdb で VDB にする
    vdb_novel  … VDB にしてから vel.* を消す
    vdb_half   … VDB を 16 bit（half）で書く（primitive wrangle で intrinsic の vdb_is_saved_as_half_float を 1 に）
    vdb_half_novel
    vdb_half_velmask … vel を残し、煙も炎も無い升（density・flame < 0.001）の vel を 0 にしてから VDB・16 bit
    vdb_half_prune … vel を残し、convertvdb の Prune Tolerance を 0.01 にして（小さい値を捨てて）16 bit で書く
  書いたファイルを file で読み戻し、volume wrangle で元の値との差（絶対値）を取って、最大と平均を記録する。

    hython examples/204_pyro_cache_size.py 0.04
    hython examples/204_pyro_cache_size.py 0.02
    python examples/204_pyro_cache_size.py combine
"""
import glob
import json
import os
import shutil
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
FRAMES = 48
CHECK = [24, 48]          # 読み戻して差を取るフレーム
FIELDS = ["density", "temperature", "flame"]
VARIANTS = ["raw", "novel", "vdb", "vdb_novel", "vdb_half", "vdb_half_novel", "vdb_half_prune", "vdb_half_velmask"]


def load202():
    import importlib.util
    spec = importlib.util.spec_from_file_location("e202", os.path.join(HERE, "examples", "202_pyro_campfire_cost.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build_variants(geo, solver):
    def blast_vel(src, name):
        b = geo.createNode("blast", name)
        b.setFirstInput(src)
        b.parm("group").set("@name=vel.*")
        b.parm("grouptype").set("prims")
        return b

    novel = blast_vel(solver, "drop_vel")
    vdb = geo.createNode("convertvdb", "to_vdb")
    vdb.setFirstInput(solver)
    vdb.parm("conversion").set(1)          # Convert To = VDB
    vdb_novel = blast_vel(vdb, "vdb_drop_vel")
    half = geo.createNode("attribwrangle", "save_half")
    half.setFirstInput(vdb)
    half.parm("class").set(1)              # Primitives
    half.parm("snippet").set('setprimintrinsic(0, "vdb_is_saved_as_half_float", @primnum, 1);')
    half_novel = blast_vel(half, "half_drop_vel")
    # vel を残したまま小さくする: 0.01 より小さい値を VDB の背景（0）に落とす
    pr = geo.createNode("convertvdb", "to_vdb_prune")
    pr.setFirstInput(solver)
    pr.parm("conversion").set(1)
    pr.parm("tolerance").set(0.01)
    half_pr = geo.createNode("attribwrangle", "save_half_prune")
    half_pr.setFirstInput(pr)
    half_pr.parm("class").set(1)
    half_pr.parm("snippet").set('setprimintrinsic(0, "vdb_is_saved_as_half_float", @primnum, 1);')
    # vel を残したまま小さくする（2）: 煙も炎も無い升の vel を 0 にしてから VDB にする（VEX の volume wrangle）
    mask = geo.createNode("volumewrangle", "vel_only_where_smoke")
    mask.setFirstInput(solver)
    mask.parm("snippet").set("if (@density < 0.001 && @flame < 0.001)\n    v@vel = {0, 0, 0};")
    mv = geo.createNode("convertvdb", "to_vdb_mask")
    mv.setFirstInput(mask)
    mv.parm("conversion").set(1)
    half_mv = geo.createNode("attribwrangle", "save_half_mask")
    half_mv.setFirstInput(mv)
    half_mv.parm("class").set(1)
    half_mv.parm("snippet").set('setprimintrinsic(0, "vdb_is_saved_as_half_float", @primnum, 1);')
    return {"vdb_half_velmask": half_mv, "vdb_half_prune": half_pr, "raw": solver, "novel": novel, "vdb": vdb, "vdb_novel": vdb_novel, "vdb_half": half, "vdb_half_novel": half_novel}


def compare_node(geo, solver):
    """元の Volume と、読み戻したファイルの値の差を Volume に書く（VEX の volume wrangle）。"""
    rd = geo.createNode("file", "read_back")
    diff = geo.createNode("volumewrangle", "diff")
    diff.setInput(0, solver)
    diff.setInput(1, rd)
    diff.parm("snippet").set("\n".join(f'@{f} = abs(@{f} - volumesample(1, "{f}", @P));' for f in FIELDS))
    return rd, diff


def arr(geo, name):
    import hou
    for p in geo.prims():
        if p.type() == hou.primType.Volume and p.attribValue("name") == name:
            return np.asarray(p.allVoxels(), dtype=np.float32)
    return None


def run(vox):
    import hou
    import hou_tools
    m = load202()
    tag = f"v{int(round(vox * 100)):03d}"
    geo, solver, _ = m.build(vox)
    nodes = build_variants(geo, solver)
    rd, diff = compare_node(geo, solver)
    tmp = tempfile.mkdtemp(prefix="c204_")
    rec = {"vox": vox, "sizes": {v: 0 for v in VARIANTS}, "vdbfile": {v: 0 for v in VARIANTS if v.startswith("vdb")},
           "write_sec": {v: 0.0 for v in VARIANTS}, "read_sec": {v: 0.0 for v in VARIANTS}, "diff": {}, "per_frame": []}
    t_sim = 0.0
    for f in range(1, FRAMES + 1):
        hou.setFrame(f)
        t0 = time.perf_counter()
        solver.geometry()
        t_sim += time.perf_counter() - t0
        row = {"f": f}
        for v, n in nodes.items():
            g = n.geometry()
            path = os.path.join(tmp, f"{v}.{f:04d}.bgeo.sc")
            t0 = time.perf_counter()
            g.saveToFile(path)
            rec["write_sec"][v] += time.perf_counter() - t0
            sz = os.path.getsize(path)
            rec["sizes"][v] += sz
            row[v] = sz
            if v.startswith("vdb"):
                vp = os.path.join(tmp, f"{v}.{f:04d}.vdb")
                g.saveToFile(vp)
                rec["vdbfile"][v] += os.path.getsize(vp)
            t0 = time.perf_counter()
            hou.Geometry().loadFromFile(path)
            rec["read_sec"][v] += time.perf_counter() - t0
            if f in CHECK:
                rd.parm("file").set(path.replace("\\", "/"))
                dg = diff.geometry()
                ref = solver.geometry()
                d = {}
                for fld in FIELDS:
                    a, r = arr(dg, fld), arr(ref, fld)
                    top = float(np.abs(r).max())
                    d[fld] = {"max": float(a.max()), "mean": float(a.mean()), "field_max": top}
                rec["diff"][f"{v}@{f}"] = d
        rec["per_frame"].append(row)
    # 升のうち、値が入っている割合（フレーム 48）
    g48 = solver.geometry()
    vel = np.sqrt(sum(arr(g48, c) ** 2 for c in ("vel.x", "vel.y", "vel.z")))
    rec["filled"] = {"density>0.001": float((arr(g48, "density") > 0.001).mean()), "flame>0.001": float((arr(g48, "flame") > 0.001).mean()),
                     "temperature>0.001": float((arr(g48, "temperature") > 0.001).mean()), "|vel|>0.01": float((vel > 0.01).mean()),
                     "|vel|>0.1": float((vel > 0.1).mean())}
    mg = nodes["vdb_half_velmask"].geometry()
    rec["vel_mask_check"] = [p.attribValue("name") for p in mg.prims()]
    rec["sim_sec"] = round(t_sim, 2)
    rec["res"] = list([p for p in solver.geometry().prims()][0].resolution())
    rec["prims"] = {v: [p.attribValue("name") + ":" + p.type().name() for p in n.geometry().prims()] for v, n in nodes.items()}
    with open(os.path.join(OUT, f"204_part_{tag}.json"), "w", encoding="utf-8") as fp:
        json.dump(rec, fp, ensure_ascii=False, indent=1)
    if vox == 0.04:
        # 読者が開くシーン: File Cache の代わりに、6 通りの出口と読み戻しの比べ方が並んだ形で残す
        hou.setFrame(24)
        rd.parm("file").set("")
        geo.layoutChildren()
        hou_tools.save_hip(os.path.join(OUT, "204_scene.hipnc"))
        hou_tools.write_graph(geo.path(), os.path.join(OUT, "204_graph.json"), title="実験204")
    shutil.rmtree(tmp, ignore_errors=True)
    print(tag, "sim", rec["sim_sec"], {k: round(v / 1e6, 2) for k, v in rec["sizes"].items()}, flush=True)


def combine():
    import sop_bench
    rows = []
    for p in sorted(glob.glob(os.path.join(OUT, "204_part_v*.json"))):
        with open(p, encoding="utf-8") as fp:
            rows.append(json.load(fp))
    sop_bench.save(204, rows, {"frames": FRAMES, "check": CHECK, "fields": FIELDS})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(float(sys.argv[1]))
