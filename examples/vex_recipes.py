# -*- coding: utf-8 -*-
"""VEX 解説ページ（vex.html）のお手本 6 つを組んで、結果の画と hip を作る。

1 つのお手本 = 1 つの geo。入力の形 → Attribute Wrangle（コード）→ 結果。
画は vex_<名前>_before.png と vex_<名前>.png（ビューポート）。hip は out/vex_recipes.hipnc。
ページに載せるコードは、ここに書いたものと同じ文字列を out/vex_recipes.json に書き出して使う（手で写さない）。

    hython examples/vex_recipes.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

RECIPES = [
    {"id": "height_color", "result": "いちばん下の点は青（t = 0）、いちばん上の点は赤（t = 1）になり、その間はなめらかに移り変わる。点の数（1,522 個）は変わらず、色の値だけが足された。", "why": "点の高さ（@P.y）を読み、その値で色（@Cd）を決めます。fit() で「−1〜1 の高さ」を「0〜1 の割合」に直してから、赤と青の混ざり具合に使っています。", "title": "高さで色を塗る", "run": "Points", "src": "sphere",
     "code": "// 下は青、上は赤。高さ（@P.y）を 0〜1 に直してから色に使う\n"
             "float t = fit(@P.y, -1, 1, 0, 1);\n"
             "@Cd = set(t, 0.25, 1 - t);"},
    {"id": "noise_wave", "result": "板の点が、低い所で −0.34、高い所で +0.39 まで動いた。ここから、この板の上で noise() が返した値は 0.22〜0.82 の間だったと分かる（0〜1 いっぱいには届かない。実験135 と同じ傾向）。", "why": "平らな板の点を、場所ごとに違う量だけ上下させます。noise() は近い場所どうしで似た値を返すので、でこぼこがなめらかにつながります。", "title": "ノイズで地面を波打たせる", "run": "Points", "src": "grid",
     "code": "// noise() は 0.06〜0.92 ほどの値を返す（実験135）。0.5 を引いて上下に振る\n"
             "float n = noise(@P * 1.5);\n"
             "@P.y += (n - 0.5) * 1.2;\n"
             "@Cd = set(n, n, 1);"},
    {"id": "random_scale", "result": "81 個の点に、それぞれ違う大きさと色の箱が乗った。rand() は番号から値を作るので、何度計算し直しても同じ並びになる。", "why": "点ごとに大きさ（@pscale）を決め、Copy to Points で箱を並べます。Copy to Points は @pscale を見て箱の大きさを変えます。", "title": "点ごとに大きさをばらつかせて並べる", "run": "Points", "src": "grid_pts",
     "code": "// rand() は点の番号から 0〜1 の決まった乱数を作る（毎回同じ）\n"
             "@pscale = fit01(rand(@ptnum), 0.2, 1.0);\n"
             "@Cd = set(rand(@ptnum + 7), 0.6, 0.3);"},
    {"id": "delete_prims", "result": "1,560 枚の面のうち 591 枚（38%）が消えて 969 枚になった。点も、どの面にも使われなくなった 37 個が消えた。", "why": "Run Over を Primitives にして、面ごとに走らせます。rand(@primnum) は面の番号から 0〜1 の値を作るので、0.4 より小さい面（約 4 割）だけ消えます。", "title": "条件に合う面を消す", "run": "Primitives", "src": "sphere",
     "code": "// 面ごとに走らせ、4 割ほどの面を消す。最後の 1 は、使われなくなった点も消す指定\n"
             "if (rand(@primnum) < 0.4)\n"
             "    removeprim(0, @primnum, 1);"},
    {"id": "make_spiral", "result": "何もない所から、点 300 個と、それをつなぐ線 299 本ができた。高さは 0〜2 で、下から上へ広がるらせんになった。", "why": "Run Over を Detail にすると、全体で 1 回だけ走ります。その中で for ループを 300 回まわし、点を 1 つずつ作って、前の点と線でつなぎます。", "title": "点と線を作る（らせん）", "run": "Detail", "src": "empty",
     "code": "// Detail は全体で 1 回だけ走る。ここで for ループを回して点を作り、前の点と線でつなぐ\n"
             "int prev = -1;\n"
             "for (int i = 0; i < 300; i++) {\n"
             "    float t = i / 299.0;\n"
             "    vector p = set(cos(t * 25) * t, t * 2, sin(t * 25) * t);\n"
             "    int pt = addpoint(0, p);\n"
             "    if (prev >= 0)\n"
             "        addprim(0, \"polyline\", prev, pt);\n"
             "    prev = pt;\n"
             "}"},
    {"id": "distance_color", "result": "ドーナツの真下とそのまわりが橙に、離れるほど紺になった。xyzdist() は面までのいちばん近い距離なので、ドーナツの穴の中も近いと判定されて橙になる。", "why": "入口 1 にドーナツをつなぎ、板の各点からドーナツの面までの距離を xyzdist() で測って、近いほど橙、遠いほど紺に塗ります。", "title": "別の形からの距離で色を変える", "run": "Points", "src": "grid_torus",
     "code": "// 2 つめの入力（番号 1）につないだドーナツの面までの距離\n"
             "float d = xyzdist(1, @P);\n"
             "@Cd = lerp({1, 0.45, 0.1}, {0.1, 0.2, 0.45}, fit(d, 0, 1.2, 0, 1));"},
]


def source(geo, kind):
    if kind == "sphere":
        s = geo.createNode("sphere", "input_sphere")
        s.parm("type").set(2)
        s.parm("rows").set(40)
        s.parm("cols").set(40)
        return s, None
    if kind == "grid":
        s = geo.createNode("grid", "input_grid")
        s.parmTuple("size").set((6, 6))
        s.parm("rows").set(120)
        s.parm("cols").set(120)
        return s, None
    if kind == "grid_pts":
        s = geo.createNode("grid", "input_grid")
        s.parmTuple("size").set((4, 4))
        s.parm("rows").set(9)
        s.parm("cols").set(9)
        return s, None
    if kind == "grid_torus":
        s = geo.createNode("grid", "input_grid")
        s.parmTuple("size").set((6, 6))
        s.parm("rows").set(120)
        s.parm("cols").set(120)
        t = geo.createNode("torus", "donut")
        t.parmTuple("rad").set((1.0, 0.3))
        t.parmTuple("t").set((0.6, 0.3, 0.0))
        return s, t
    return None, None


def build(r):
    import hou
    geo = hou.node("/obj").createNode("geo", "vex_" + r["id"])
    src, other = source(geo, r["src"])
    w = geo.createNode("attribwrangle", "wrangle")
    w.parm("class").set({"Detail": 0, "Primitives": 1, "Points": 2}[r["run"]])
    w.parm("snippet").set(r["code"])
    if src is not None:
        w.setInput(0, src)
    if other is not None:
        w.setInput(1, other)
    shown = w
    before = src
    if r["id"] == "random_scale":
        cube = geo.createNode("box", "small_box")
        cube.parmTuple("size").set((0.4, 0.4, 0.4))
        cp = geo.createNode("copytopoints::2.0", "copy_boxes")
        cp.setInput(0, cube)
        cp.setInput(1, w)
        cp.parm("targetattribs").set(1)
        cp.parm("applyattribs1").set("Cd")
        cp.parm("applyto1").set("points")
        shown = cp
        cp0 = geo.createNode("copytopoints::2.0", "copy_boxes_before")
        cp0.setInput(0, cube)
        cp0.setInput(1, src)
        before = cp0
    if r["id"] == "distance_color":
        m = geo.createNode("merge", "show_with_donut")
        m.setInput(0, w)
        m.setInput(1, other)
        shown = m
        m0 = geo.createNode("merge", "before_with_donut")
        m0.setInput(0, src)
        m0.setInput(1, other)
        before = m0
    geo.layoutChildren()
    return geo, before, shown


def main():
    import hou
    import hou_tools
    hou.hipFile.clear(suppress_save_prompt=True)
    built = [(r, *build(r)) for r in RECIPES]
    info = []
    for r, geo, before, shown in built:
        for g2, *_ in [(b[1],) for b in built]:
            g2.setDisplayFlag(g2 == geo)
        t0 = time.perf_counter()
        shown.geometry()
        cook_ms = (time.perf_counter() - t0) * 1000
        g = shown.geometry()
        direction = (1.0, 1.1, 1.3) if r["id"] in ("noise_wave",) else (1.0, 0.7, 1.15)
        shading = "wire" if r["id"] == "make_spiral" else "smooth"
        box = shown.geometry().boundingBox()
        if before is not None:
            hou_tools.render_preview(before.path(), os.path.join(OUT, f"vex_{r['id']}_before.png"), res=(640, 400),
                                     direction=direction, shading="smoothwire" if r["id"] != "random_scale" else "smooth",
                                     frame_bbox=box)
        hou_tools.render_preview(shown.path(), os.path.join(OUT, f"vex_{r['id']}.png"), res=(640, 400),
                                 direction=direction, shading=shading, frame_bbox=box)
        shown.setDisplayFlag(True)
        info.append({**r, "points": len(g.points()), "prims": len(g.prims()), "cook_ms": round(cook_ms, 2), "ymin": round(box.minvec()[1], 3), "ymax": round(box.maxvec()[1], 3),
                     "before": before is not None})
        print(r["id"], len(g.points()), len(g.prims()), flush=True)
    for _, geo, _, _ in built:
        geo.setDisplayFlag(geo.name() == "vex_height_color")
    hou_tools.save_hip(os.path.join(OUT, "vex_recipes.hipnc"))
    with open(os.path.join(OUT, "vex_recipes.json"), "w", encoding="utf-8") as fp:
        json.dump(info, fp, ensure_ascii=False, indent=1)
    print("書いた: vex_recipes.json")


if __name__ == "__main__":
    main()
