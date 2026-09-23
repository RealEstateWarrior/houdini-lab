# -*- coding: utf-8 -*-
"""実験200 — 水の柱が崩れて流れる場面（ダムブレイク）で、Particle Separation をどこまで粗くしても見た目が保てるか。

制作の問い: プレビューや本番で FLIP の粒の間隔をいくつにすればよいか。粗くするとどれだけ速くなり、何が崩れるか。

  幅 3 × 高さ 1.5 × 奥行き 1 の水槽の左端に、
  幅 0.6 × 高さ 0.9 × 奥行き 1 の水（flipsource、Volume Name = source、最初のフレームだけ湧かせる。Narrow Band は切）を置いて崩す。
  容器は壁の無い開いた箱なので、床と4枚の壁を flipcollide で足す（水槽の内側は x −1.5〜1.5、y −0.75〜、z −0.5〜0.5）。
  Particle Separation 0.02（基準）・0.03・0.04・0.06・0.08 で 60 フレーム（24 fps で 2.5 秒）回し、
    - 波の先端の位置（粒の x の 99.5 パーセンタイル）
    - 右の壁を駆け上がる高さ（x > 1.35 の粒の y の 99.5 パーセンタイル）
    - 液面の形（x を 30 区間に分け、各区間の粒の y の 99 パーセンタイル）を基準と比べた差
    - particlefluidsurface で面にしたときの体積（最初の水 0.54 と比べる）
    - 計算時間（60 フレーム通し）と面にする時間
  を測り、フレーム 18・36・60 を同じカメラで撮る。
  粒が減る原因を切り分けるため、壁の上端 0.85（short）と 1.45（既定）の2つの水槽で回す。
  さらに 0.02・0.06 で Reseeding を切ったとき（noreseed）も回す。

    hython examples/200_flip_dambreak_res.py 0.02 [short]   （0.03・0.04・0.06・0.08 も1つずつ）
    hython examples/200_flip_dambreak_res.py combine
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

import hou  # noqa: E402
import hou_tools  # noqa: E402
import sop_bench  # noqa: E402

SEPS = [0.02, 0.03, 0.04, 0.06, 0.08]
FRAMES = 60
CHECK = [1, 6, 12, 18, 24, 36, 48, 60]
SHOTS = [18, 36, 60]
BINS = np.linspace(-1.5, 1.5, 31)
WATER = (0.6, 0.9, 1.0)
WATER_VOL = WATER[0] * WATER[1] * WATER[2]
TALL = True
NORESEED = False
RESEED_DEFAULT = []


def build(sep, tall=True, wall=0.2, gap=0.0):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "flip")
    container = geo.createNode("flipcontainer", "container")
    # 壁が中に収まるよう、水槽（3 × 1.5 × 1）より一回り大きくする
    # 壁が中に収まるよう、水槽より一回り大きくする。tall は壁の上端を 0.85 → 1.45 に上げ、容器も上へ伸ばす
    top = 1.45 if tall else 0.85
    container.parm("sizex").set(3.0 + 2 * wall)
    container.parm("sizey").set(top + 0.95 + 0.1)
    container.parm("ty").set((top + 0.1 - 0.95) / 2)
    container.parm("sizez").set(1.4)
    container.parm("particlesep").set(sep)
    box = geo.createNode("box", "water")
    # 最初のフレームだけ水を湧かせ、あとは箱を点ほどに縮めて止める
    for axis, v in zip("xyz", WATER):
        box.parm("size" + axis).setExpression(f"if($F<=1,{v},0.0001)")
    box.parmTuple("t").set((-1.5 + gap + WATER[0] / 2, -0.75 + WATER[1] / 2, 0.0))
    src = geo.createNode("flipsource", "src")
    src.setInput(0, box)
    src.parm("particlesep").set(sep)
    src.parm("volumename").set("source")   # 既定の surface ではソルバーに入らなかった
    src.parm("addpscale").set(True)         # 無いと「Required attribute pscale is missing」で止まる
    merge = geo.createNode("merge", "sources")
    merge.setInput(0, container, 0)
    merge.setInput(1, src)
    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(sep)
    solver.parm("donarrowband").set(False)  # 入のままだと source で入れた水の内側の粒が消えていく
    RESEED_DEFAULT.append(solver.parm("doreseeding").eval())
    if NORESEED:
        solver.parm("doreseeding").set(False)
    # 容器の外に出た粒は消える（ヘルプ: 容器は壁の無い開いた箱）。床と4枚の壁（厚み 0.2）を FLIP Collide の4番目の入力につなぐ
    walls = geo.createNode("merge", "walls")
    for i, (size, t) in enumerate((
            ((3.4, 0.2, 1.4), (0, -0.85, 0)),
            ((wall, top + 0.95, 1.4), (-1.5 - wall / 2, (top - 0.95) / 2, 0)),
            ((wall, top + 0.95, 1.4), (1.5 + wall / 2, (top - 0.95) / 2, 0)),
            ((3.4, top + 0.95, 0.2), (0, (top - 0.95) / 2, -0.6)), ((3.4, top + 0.95, 0.2), (0, (top - 0.95) / 2, 0.6)))):
        wall = geo.createNode("box", f"wall{i}")
        wall.parmTuple("size").set(size)
        wall.parmTuple("t").set(t)
        walls.setInput(i, wall)
    collide = geo.createNode("flipcollide", "tank")
    collide.setInput(0, merge)
    collide.setInput(1, container, 1)
    collide.setInput(2, container, 2)
    collide.setInput(3, walls)
    for k in range(3):
        solver.setInput(k, collide, k)
    surf = geo.createNode("particlefluidsurface::3.0", "surface")
    surf.setInput(0, solver)
    surf.parm("particlesep").set(sep)
    surf.parm("conversion").set("poly")   # 既定の Polygon Soup では体積を測れないので多角形にする
    return geo, solver, surf


def pts(solver):
    g = solver.geometry(0)
    return np.array(g.pointFloatAttribValues("P"), dtype=np.float64).reshape(-1, 3)


def profile(p):
    idx = np.digitize(p[:, 0], BINS) - 1
    out = []
    for i in range(len(BINS) - 1):
        ys = p[idx == i, 1]
        out.append(float(np.percentile(ys, 99)) if len(ys) >= 3 else -0.75)
    return out


def run_one(sep):
    """1 つの間隔だけ回して out/200_part_NNN.json に書く（続けて作り直すと hython が黙って落ちるため、1 プロセス 1 条件）。"""
    # 1 回目の cook は起動の分だけ遅いので、小さく回して温めておく
    _, s0, _ = build(0.1)
    hou.setFrame(3)
    s0.geometry(0)

    geo, solver, surf = build(sep, tall=TALL)
    solver.setDisplayFlag(True)
    rec = {"sep": sep, "tall": TALL, "noreseed": NORESEED, "reseed_default": RESEED_DEFAULT[-1], "frames": {}, "per_frame": []}
    t0 = time.perf_counter()
    for f in range(1, FRAMES + 1):
        hou.setFrame(f)
        p = pts(solver)
        right = p[p[:, 0] > 1.35, 1]
        rec["per_frame"].append({
            "f": f, "count": int(len(p)),
            "front": round(float(np.percentile(p[:, 0], 99.5)), 4),
            "runup": round(float(np.percentile(right, 99.5)), 4) if len(right) >= 5 else None,
            "above_085": int(np.sum(p[:, 1] > 0.85)),
        })
        if f in CHECK:
            right = p[p[:, 0] > 1.35, 1]
            rec["frames"][f] = {
                "count": int(len(p)),
                "front": round(float(np.percentile(p[:, 0], 99.5)), 4),
                "runup": round(float(np.percentile(right, 99.5)), 4) if len(right) >= 5 else None,
                "profile": [round(v, 4) for v in profile(p)],
            }
    rec["sim_sec"] = round(time.perf_counter() - t0, 2)
    # 面にする（最後のフレーム）
    hou.setFrame(FRAMES)
    t1 = time.perf_counter()
    sg = surf.geometry()
    rec["surface_sec"] = round(time.perf_counter() - t1, 2)
    rec["surface_volume"] = round(sop_bench.volume(sg), 5)
    rec["surface_polys"] = len(sg.prims())
    hou.setFrame(1)
    rec["surface_volume_f1"] = round(sop_bench.volume(surf.geometry()), 5)
    for f in (24, 36, 48):
        hou.setFrame(f)
        rec[f"surface_volume_f{f}"] = round(sop_bench.volume(surf.geometry()), 5)
    # 撮る（同じ枠・同じ向き）
    surf.setDisplayFlag(True)
    surf.setRenderFlag(True)
    bbox = hou.BoundingBox(-1.5, -0.75, -0.5, 1.5, 0.75, 0.5)
    hou_tools.render_sequence(surf.path(), OUT, f"200_{'t' if TALL else 's'}{'n' if NORESEED else ''}{int(round(sep * 1000)):03d}", SHOTS,
                              res=(480, 270), shading="smooth", frame_bbox=bbox,
                              direction=(0.35, 0.45, 1.0))
    if sep == SEPS[0] and TALL and not NORESEED:
        hou_tools.save_hip(os.path.join(OUT, "200_flip.hipnc"))
    with open(os.path.join(OUT, f"200_{'' if TALL else 'short_'}{'noreseed_' if NORESEED else ''}part_{int(round(sep * 1000)):03d}.json"), "w", encoding="utf-8") as fp:
        json.dump(rec, fp)
    print(sep, rec["sim_sec"], rec["frames"][60]["count"], rec["surface_volume"], flush=True)


def combine():
    out = {}
    for tag in ("", "short_"):
        results = []
        for sep in SEPS:
            with open(os.path.join(OUT, f"200_{tag}part_{int(round(sep * 1000)):03d}.json"), encoding="utf-8") as fp:
                results.append(json.load(fp))
        ref = results[0]
        for rec in results:
            for f in map(str, CHECK):
                a = np.array(rec["frames"][f]["profile"])
                b = np.array(ref["frames"][f]["profile"])
                rec["frames"][f]["profile_rms"] = round(float(np.sqrt(np.mean((a - b) ** 2))), 4)
        out[tag or "tall"] = results
    noreseed = []
    for sep in (0.02, 0.06):
        with open(os.path.join(OUT, f"200_noreseed_part_{int(round(sep * 1000)):03d}.json"), encoding="utf-8") as fp:
            noreseed.append(json.load(fp))
    sop_bench.save(200, out["tall"], {"short": out["short_"], "noreseed": noreseed, "water_volume": WATER_VOL, "check": CHECK,
                                      "shots": SHOTS, "bins": [round(b, 3) for b in BINS.tolist()]})


if __name__ == "__main__":
    TALL = "short" not in sys.argv
    NORESEED = "noreseed" in sys.argv
    if "combine" in sys.argv:
        combine()
    else:
        run_one(float(sys.argv[1]))
