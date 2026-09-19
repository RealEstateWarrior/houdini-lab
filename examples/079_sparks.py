"""実験079 — 火花を散らす。「ばらつき」の数字は、実際にどうばらつくか。

火花は、1点から一斉に飛び出し、重力で落ちながら、少しずつ消えていく粒。
POP の popsource には、そのための「ばらつき」が2つある。

  Life Variance … 寿命のばらつき。Life Expectancy 1.0・Life Variance 0.5 なら、
                  寿命は 0.5〜1.5 に一様に散るのか、1.0 を中心に正規分布で散るのか
  Variance      … 初速のばらつき。Velocity (0, 6, 0)・Variance (3, 3, 3) なら、
                  各成分が ±3 の箱の中に一様に散るのか、それとも別の形か

名前だけではどちらとも取れる。手順ページに「こう入れればこうなる」と書くために、測って決める。

  A. 寿命：一度に 4,000粒を生み、生きている粒の数を毎フレーム数える
  B. 初速：生まれた直後の速さの成分を集めて、最小・最大・標準偏差・分布の形を見る
  C. 空気抵抗（popdrag）：重力なしで横に飛ばし、速さの減り方を式と比べる

    hython examples/079_sparks.py a
    hython examples/079_sparks.py b
    hython examples/079_sparks.py c
    hython examples/079_sparks.py shot
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

FPS = 24.0
BURST = 4000


def build(life=1.0, lifevar=0.5, vel=(0.0, 6.0, 0.0), var=(3.0, 3.0, 3.0),
          gravity=True, drag=None, burst=BURST, streak=False):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 72)
    geo = hou.node("/obj").createNode("geo", "sparks")

    origin = geo.createNode("add", "origin")
    origin.parm("points").set(1)
    origin.parm("usept0").set(1)
    origin.parmTuple("pt0").set((0.0, 0.0, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "particles")
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")
    source.parm("soppath").set(origin.path())
    source.parm("emittype").set("point")      # All Points だと点1つにつき毎フレーム1粒になる
    source.parm("constantactivate").set(False)
    source.parm("impulseactiveate").set(True)
    # 最初のフレームにだけ、まとめて生む
    source.parm("impulserate").setExpression(f"if($FF == 1, {burst}, 0)")
    source.parm("life").set(life)
    source.parm("lifevar").set(lifevar)
    source.parm("initvel").set("set")
    for axis, v, s in zip("xyz", vel, var):
        source.parm(f"vel{axis}").set(v)
        source.parm(f"var{axis}").set(s)

    last = None
    if gravity:
        grav = dop.createNode("popforce", "gravity")
        grav.parmTuple("force").set((0.0, -9.81, 0.0))
        last = grav
    if drag is not None:
        d = dop.createNode("popdrag", "drag")
        d.parm("airresist").set(drag)
        if last is not None:
            d.setFirstInput(last)
        last = d
    solver.setInput(0, obj)
    if last is not None:
        solver.setInput(1, last)
    solver.setInput(2, source)
    # DOP の中は、表示フラグの立ったノードまでしか計算されない。
    # これを忘れると、エラーも出ずに粒が1つも生まれない（dopimport に警告が出るだけ）
    solver.setDisplayFlag(True)
    dop.layoutChildren()

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")
    out = imp
    if streak:
        # 1粒を「今の位置から、少し前の位置まで」の線にする。速いほど長い筋になる
        lines = geo.createNode("attribwrangle", "streaks")
        lines.setFirstInput(imp)
        lines.parm("class").set(0)       # Detail（1回だけ）
        lines.parm("snippet").set(
            "for (int i = 0; i < npoints(0); i++) {\n"
            "    vector p = point(0, 'P', i);\n"
            "    vector v = point(0, 'v', i);\n"
            "    float nage = point(0, 'age', i) / max(point(0, 'life', i), 1e-6);\n"
            "    vector c = lerp({1.0, 0.85, 0.4}, {0.8, 0.15, 0.02}, clamp(nage, 0, 1));\n"
            "    int a = addpoint(0, p);\n"
            "    int b = addpoint(0, p - v * 0.04);\n"
            "    setpointattrib(0, 'Cd', a, c);\n"
            "    setpointattrib(0, 'Cd', b, c * 0.4);\n"
            "    int prim = addprim(0, 'polyline');\n"
            "    addvertex(0, prim, a);\n"
            "    addvertex(0, prim, b);\n"
            "    removepoint(0, i);\n"
            "}")
        out = lines
    out.setDisplayFlag(True)
    out.setRenderFlag(True)
    geo.layoutChildren()
    return geo, imp, out


def part_a():
    """寿命のばらつき。生きている粒の数を毎フレーム数える。"""
    import hou
    import hou_tools
    rows = []
    for life, var in ((1.0, 0.0), (1.0, 0.5), (1.0, 1.0)):
        geo, imp, out = build(life=life, lifevar=var, gravity=False)
        counts = []
        lives = None
        start = time.perf_counter()
        for frame in range(1, 61):
            hou.setFrame(frame)
            g = imp.geometry()
            n = len(g.points()) if g else 0
            counts.append(n)
            if frame == 2 and n:
                lives = hou_tools.point_array(g, "life")
        sec = time.perf_counter() - start
        import numpy
        row = {"life": life, "lifevar": var, "born": max(counts), "counts": counts,
               "life_min": float(lives.min()), "life_max": float(lives.max()),
               "life_mean": float(lives.mean()), "life_sd": float(lives.std()),
               "seconds": sec}
        # 分布の形：寿命を10区間に分けた数
        hist, edges = numpy.histogram(lives, bins=10)
        row["hist"] = hist.tolist()
        row["edges"] = [float(e) for e in edges]
        rows.append(row)
        print(f"   life {life} var {var} | 生まれた {row['born']} | 寿命 最小 {row['life_min']:.4f} "
              f"最大 {row['life_max']:.4f} 平均 {row['life_mean']:.4f} 標準偏差 {row['life_sd']:.4f} | "
              f"10区間 {row['hist']} | {sec:.2f}秒")
        alive = " ".join(f"{t / FPS:.2f}s:{c}" for t, c in enumerate(counts) if t % 6 == 0)
        print(f"      生きている数 {alive}")
    with open(os.path.join(OUT, "079_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/079_a.json")


def part_b():
    """初速のばらつき。生まれた直後の速さの成分を見る。"""
    import hou
    import hou_tools
    import numpy
    geo, imp, out = build(life=5.0, lifevar=0.0, gravity=False)
    hou.setFrame(2)
    v = hou_tools.point_array(imp.geometry(), "v")
    rows = {}
    for k, name in enumerate("xyz"):
        c = v[:, k]
        hist, edges = numpy.histogram(c, bins=12)
        rows[name] = {"min": float(c.min()), "max": float(c.max()), "mean": float(c.mean()),
                      "sd": float(c.std()), "hist": hist.tolist(),
                      "edges": [float(e) for e in edges]}
        print(f"   v{name} | 最小 {c.min():+.4f} 最大 {c.max():+.4f} 平均 {c.mean():+.4f} "
              f"標準偏差 {c.std():.4f} | 12区間 {hist.tolist()}")
    speed = numpy.linalg.norm(v - numpy.array([0.0, 6.0, 0.0]), axis=1)
    rows["offset_len"] = {"max": float(speed.max()), "mean": float(speed.mean()),
                          "corner_share": float((speed > 3.0).mean())}
    print(f"   (0,6,0) からのずれの長さ | 最大 {speed.max():.4f} 平均 {speed.mean():.4f} "
          f"3 を超える割合 {(speed > 3.0).mean() * 100:.1f}%（箱なら角があるので超える、球なら 0%）")
    rows["count"] = int(len(v))
    with open(os.path.join(OUT, "079_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/079_b.json")


def part_c():
    """空気抵抗。重力なし・横に 8 で飛ばし、平均の速さの減り方を見る。"""
    import hou
    import hou_tools
    import numpy
    rows = []
    for drag in (0.5, 1.0, 2.0):
        geo, imp, out = build(life=10.0, lifevar=0.0, vel=(8.0, 0.0, 0.0), var=(0.0, 0.0, 0.0),
                              gravity=False, drag=drag, burst=200)
        track = []
        for frame in range(2, 50):
            hou.setFrame(frame)
            v = hou_tools.point_array(imp.geometry(), "v")
            age = float(hou_tools.point_array(imp.geometry(), "age").mean())
            track.append({"frame": frame, "age": age, "vx": float(v[:, 0].mean())})
        v0 = track[0]["vx"]
        a0 = track[0]["age"]
        # 一次の抵抗なら v = v0·exp(−k t)、二次なら v = v0 / (1 + k v0 t)
        lin = [r["vx"] / v0 for r in track]
        for r in track:
            t = r["age"] - a0
            r["exp"] = v0 * math.exp(-drag * t)
            r["quad"] = v0 / (1 + drag * v0 * t)
        err_exp = max(abs(r["vx"] - r["exp"]) for r in track)
        err_quad = max(abs(r["vx"] - r["quad"]) for r in track)
        half = next((r["age"] - a0 for r in track if r["vx"] < v0 / 2), None)
        rows.append({"drag": drag, "v0": v0, "track": track, "err_exp": err_exp,
                     "err_quad": err_quad, "half": half})
        print(f"   airresist {drag} | 最初 {v0:.4f} → 1秒後 {track[24]['vx']:.4f} → 2秒後 {track[47]['vx']:.4f} | "
              f"半分になる秒 {half} | 一次の式との最大ずれ {err_exp:.4f} / 二次 {err_quad:.4f}")
    with open(os.path.join(OUT, "079_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/079_c.json")


def shot():
    """火花の完成形。寿命 1.2 ± 0.6、初速 (0, 3, 0) ± 半径 7 の球、重力、空気抵抗 0.15。

    B で分かったとおり、Variance は「その半径の球の中」に散らす数字なので、
    上向きの速さより大きくすると、全方向へ飛び散る。
    """
    import hou
    import hou_tools
    geo, imp, out = build(life=1.2, lifevar=0.6, vel=(0.0, 3.0, 0.0), var=(7.0, 7.0, 7.0),
                          drag=0.15, burst=3000, streak=True)
    start = time.perf_counter()
    for frame in range(1, 19):
        hou.setFrame(frame)
        out.geometry()
    print(f"18フレームの計算と筋の作成: {time.perf_counter() - start:.2f}秒 / "
          f"{len(imp.geometry().points())}粒 → {len(out.geometry().prims())}本の筋")
    hou_tools.save_hip(os.path.join(OUT, "079_sparks.hipnc"))
    bbox = hou.BoundingBox(-5.5, -4.0, -5.5, 5.5, 5.0, 5.5)
    for frame in (6, 18):
        hou.setFrame(frame)
        png = os.path.join(OUT, f"079_sparks_{frame}.png")
        hou_tools.render_preview(out.path(), png, res=(560, 460),
                                 direction=(0.0, 0.2, 1.0), shading="smooth",
                                 frame_bbox=bbox, margin=1.02)
        print(f"保存: {png}")


if __name__ == "__main__":
    {"a": part_a, "b": part_b, "c": part_c, "shot": shot}[sys.argv[1] if len(sys.argv) > 1 else "a"]()
