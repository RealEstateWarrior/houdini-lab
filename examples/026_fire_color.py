"""実験026 — 炎に色を付ける。温度から色を出す式は、思ったとおりに効いているか。

実験023で炎を出したが、白黒でしか描けていなかった。炎は温度で色が変わる。
低いと赤、高くなるにつれて橙・黄・白へ。これは<strong>黒体放射</strong>という物理の話で、
Houdini の VEX には <code>blackbody()</code> という関数がそのまま入っている。

ただ「色が付いた」で終わらせない。次の2つを測る。

  1. blackbody() が返す色は、温度とともに本当に赤→橙→白と変わるか。
     赤成分と青成分の比を温度ごとに出せば、数字で追える。
  2. 炎の温度の場を色に変えたとき、その対応が保たれているか。

否定できる形にする。温度を上げても赤と青の比が変わらなければ、式は効いていない。

    hython examples/026_fire_color.py
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

FRAME = 30
VOXEL = 0.05
TEMPS = [1000, 1500, 2000, 2500, 3000, 4000, 5000, 6500, 8000]


def measure_blackbody():
    """blackbody() が温度ごとに返す色を、数値で取り出す。

    点を並べて、1点ごとに温度を割り当てて色を計算させる。
    ノードに計算させた結果を読むので、こちらの思い込みは入らない。
    """
    geo = hou.node("/obj").createNode("geo", "bb")
    line = geo.createNode("line", "line")
    line.parm("points").set(len(TEMPS))

    wrangle = geo.createNode("attribwrangle", "colors")
    wrangle.setFirstInput(line)
    wrangle.parm("class").set(2)
    temps = ", ".join(str(t) for t in TEMPS)
    wrangle.parm("snippet").set(
        f"float temps[] = {{{temps}}};\n"
        "f@temp = temps[@ptnum];\n"
        "// 2つ目の引数は「白として扱う温度」。6500K を白にする\n"
        "// 返る値は 6500倍ほどの大きさなので、割って 0〜1 に収める\n"
        "@Cd = blackbody(f@temp, 6500) / 6500.0;")

    rows = []
    for point in wrangle.geometry().points():
        temp = point.attribValue("temp")
        r, g, b = point.attribValue("Cd")
        rows.append({"temp": temp, "r": r, "g": g, "b": b,
                     "rb": (r / b) if b > 1e-9 else float("inf")})
    return rows


def build_fire():
    geo = hou.node("/obj").createNode("geo", "fire")

    emitter = geo.createNode("sphere", "emitter")
    emitter.parm("type").set(2)
    emitter.parmTuple("rad").set((0.22, 0.22, 0.22))
    emitter.parmTuple("t").set((0.0, -0.9, 0.0))
    emitter.parm("rows").set(24)
    emitter.parm("cols").set(24)

    src = geo.createNode("pyrosource", "src")
    src.setFirstInput(emitter)
    src.parm("initialize").set("sourceburn")
    src.parm("initialize").pressButton()
    made = [src.parm(f"attribute{i + 1}").evalAsString()
            for i in range(src.parm("attributes").eval())]

    rast = geo.createNode("volumerasterizeattributes", "rasterize")
    rast.setFirstInput(src)
    rast.parm("attributes").set(" ".join(made))
    rast.parm("voxelsize").set(VOXEL)

    solver = geo.createNode("pyrosolver", "solve")
    solver.setFirstInput(rast)
    solver.parm("addflamefield").set(True)
    solver.parm("doflamedensity").set(True)
    solver.parm("flamedensity").set(1.0)

    # ボリュームの中に点をばらまいて、その点に色を付ける。
    # 点なら OpenGL でも色が出るので、確認用の描画で色が見える。
    points = geo.createNode("pointsfromvolume", "points")
    points.setFirstInput(solver)
    if points.parm("particlesep") is not None:
        points.parm("particlesep").set(VOXEL * 1.6)

    color = geo.createNode("attribwrangle", "color")
    color.setFirstInput(points)
    color.setInput(1, solver)
    color.parm("class").set(2)
    color.parm("snippet").set(
        "// 2本目の入力（ボリューム）から、この点の位置の温度を読む\n"
        "float t = volumesample(1, \"temperature\", @P);\n"
        "f@temp = t;\n"
        "// 温度の単位をケルビンに直してから色にする\n"
        "vector c = blackbody(t * 3000.0, 6500) / 6500.0;\n"
        "// 1で切ると赤が潰れて全部黄色になる。\n"
        "// 一番大きい成分で割れば、明るさだけ揃って色味は残る。\n"
        "@Cd = c / max(max(c.x, c.y), max(c.z, 1e-6));\n"
        "// 温度の低いところは薄くする\n"
        "@Alpha = clamp(t, 0.0, 1.0);")

    blast = geo.createNode("blast", "drop_cold")
    blast.setFirstInput(color)
    blast.parm("group").set("@temp<0.02")
    blast.parm("grouptype").set(3)       # 点
    blast.parm("negate").set(False)

    geo.layoutChildren()
    color.setDisplayFlag(True)
    return geo, solver, points, color, blast


def main():
    hou.hipFile.clear(suppress_save_prompt=True)

    print("1. blackbody() が返す色")
    rows = measure_blackbody()
    print(f"{'温度(K)':>9} {'赤':>9} {'緑':>9} {'青':>9} {'赤/青':>10}")
    for row in rows:
        rb = row["rb"]
        print(f"{row['temp']:9.0f} {row['r']:9.4f} {row['g']:9.4f} "
              f"{row['b']:9.4f} {rb:10.4f}" if rb != float("inf")
              else f"{row['temp']:9.0f} {row['r']:9.4f} {row['g']:9.4f} "
                   f"{row['b']:9.4f} {'∞':>10}")

    ratios = [r["rb"] for r in rows if r["rb"] != float("inf")]
    falling = all(a >= b for a, b in zip(ratios, ratios[1:]))
    print(f"\n  赤/青は温度とともに単調に下がるか: {'はい' if falling else 'いいえ'}")
    print(f"  {rows[0]['temp']:.0f}K で {ratios[0]:.2f}、"
          f"{rows[-1]['temp']:.0f}K で {ratios[-1]:.4f}"
          f"（{ratios[0] / ratios[-1]:.1f}分の1）")

    print("\n2. 炎の温度を色にする")
    geo, solver, points, color, blast = build_fire()
    hou.setFrame(FRAME)
    pts = points.geometry()
    print(f"  ばらまいた点: {len(pts.points())} 個")

    try:
        colored = color.geometry()
    except hou.Error as exc:
        colored = None
        print("  色付けでエラー:", exc)
    if colored is None:
        print("  ノードのエラー:", color.errors())
        return
    temps = [p.attribValue("temp") for p in colored.points()]
    if temps:
        print(f"  温度の範囲: {min(temps):.4f} 〜 {max(temps):.4f}")
    hot = blast.geometry()
    print(f"  温度の低い点を落としたあと: {len(hot.points())} 個")

    bbox = hou_tools.bbox_over_frames(blast.path(), [FRAME])
    hou_tools.render_preview(blast.path(), os.path.join(OUT, "026_fire_color.png"),
                             res=(420, 620), shading="smooth", frame_bbox=bbox,
                             margin=1.04)
    hou_tools.render_preview(solver.path(), os.path.join(OUT, "026_fire_grey.png"),
                             res=(420, 620), shading="smooth", frame_bbox=bbox,
                             margin=1.04)

    with open(os.path.join(OUT, "026_stats.json"), "w", encoding="utf-8") as fp:
        json.dump({"blackbody": rows, "frame": FRAME,
                   "points": len(pts.points()), "hot_points": len(hot.points()),
                   "temp_min": min(temps) if temps else None,
                   "temp_max": max(temps) if temps else None},
                  fp, ensure_ascii=False, indent=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "026_graph.json"),
                          title="実験026 — 炎に色を付ける")
    hou_tools.save_hip(os.path.join(OUT, "026_color.hipnc"))
    print("\n保存: out/026_stats.json, out/026_graph.json, out/026_color.hipnc")


if __name__ == "__main__":
    main()
