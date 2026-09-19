"""手順ページ用の画像と .hipnc（R8 で増やした分）。1つずつ別プロセスで動かす。

  wind … 粒に風を当てる（実験029）
  tear … 狙った線で布を破る（実験031・032）
  fire … 炎を出して色を付ける（実験023・026）
  hair … 毛を風で揺らす（実験048・049）
  grass … 流れの向きに草を寝かせる（実験036）
  carry … 動く板で塊を運ぶ（実験069・070）
  karma … Karma で見せる絵を撮る（実験018・038）
  export … 形を外へ書き出す（実験058・059）
  foreach … 面ごとの繰り返しを VEX に置き換える（実験010）

手順に載せる数字は、ここで組んだシーンでその場で測る（元の実験と条件が違う場合があるため）。
かかった時間も測って出す。レンダは最後にまとめて撮る。

    hython examples/guide_more.py wind
"""

import os
import sys
import time

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (560, 440)


def shoot(sop, name, bbox, frame, shading="smooth", direction=(1.0, 0.62, 1.15)):
    hou.setFrame(frame)
    path = os.path.join(OUT, f"{name}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading=shading,
                             frame_bbox=bbox, direction=direction, margin=1.2)
    geo = sop.geometry()
    print(f"  {name}: F{frame} {len(geo.points())}点")


def timed_sweep(node, first, last):
    start = time.perf_counter()
    for f in range(first, last + 1):
        hou.setFrame(f)
        node.geometry()
    return time.perf_counter() - start


def wind():
    """粒に風を当てる。板 → DOP（popsource → 重力 → popwind）→ 取り出す → 球を被せる。

    実験029は力の効き方だけを見るため重力なし・1回だけ生んだ。手順では
    普段使う形（生み続ける＋重力）にして、その場で測った値を載せる。
    """
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "wind")

    emitter = geo.createNode("grid", "emitter")
    emitter.parmTuple("size").set((1.0, 1.0))
    emitter.parm("rows").set(12)
    emitter.parm("cols").set(12)
    emitter.parmTuple("t").set((0.0, 3.0, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "particles")
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")
    source.parm("soppath").set(emitter.path())
    source.parm("constantactivate").set(True)
    source.parm("constantrate").set(200)
    source.parm("impulseactiveate").set(False)

    gravity = dop.createNode("popforce", "gravity")
    gravity.parmTuple("force").set((0.0, -9.80665, 0.0))

    blow = dop.createNode("popwind", "wind")
    blow.parmTuple("wind").set((3.0, 0.0, 0.0))
    blow.parm("windspeed").set(1.0)
    blow.parm("airresist").set(1.0)

    blow.setFirstInput(gravity)                 # 力は数珠つなぎにできる
    solver.setInput(0, obj)
    solver.setInput(1, blow)                    # Pre-Solve … 力
    solver.setInput(2, source)                  # Sources (post-solve) … 生む
    print("popsolver の入力:", solver.inputLabels())
    solver.setDisplayFlag(True)
    dop.layoutChildren()

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")

    dot = geo.createNode("sphere", "dot")
    dot.parm("type").set(2)
    dot.parmTuple("rad").set((0.06, 0.06, 0.06))
    dot.parm("rows").set(6)
    dot.parm("cols").set(8)

    dots = geo.createNode("copytopoints::2.0", "dots")
    dots.setInput(0, dot)
    dots.setInput(1, imp)
    dots.setDisplayFlag(True)
    dots.setRenderFlag(True)
    geo.layoutChildren()

    sec = timed_sweep(imp, 1, 72)
    print(f"72フレーム（3秒）の計算: {sec:.2f}秒")
    for frame in (24, 48, 72):
        hou.setFrame(frame)
        pts = imp.geometry().points()
        old = max(pts, key=lambda p: p.attribValue("age"))
        v = old.attribValue("v")
        print(f"  F{frame}: {len(pts)}点 / いちばん古い粒 age {old.attribValue('age'):.3f}秒 "
              f"v=({v[0]:.4f}, {v[1]:.4f}) 位置 x {old.position()[0]:.3f} y {old.position()[1]:.3f}")

    hou_tools.save_hip(os.path.join(OUT, "guide_wind.hipnc"))

    hou.setFrame(72)
    bbox = dots.geometry().boundingBox()
    view = (0.0, 0.25, 1.0)                     # ほぼ真横から。流される向きが見える
    shoot(emitter, "guide_wind_1_emitter", hou.BoundingBox(-1.2, 2.4, -1.2, 1.2, 3.6, 1.2), 1,
          shading="smoothwire")
    shoot(dots, "guide_wind_2_start", bbox, 24, direction=view)
    shoot(dots, "guide_wind_3_blown", bbox, 72, direction=view)


def tear():
    """狙った線で布を破る。組み方は実験032の build をそのまま使う。

    先に波打つ線で2枚に切り、glue で貼り直してから吊るす。
    破れた画は実験032で同じシーン・同じしきい値で撮ったものを使う。
    ここでは切り分けの図と、数・時間の確認だけ撮る。
    """
    import importlib
    sys.path.insert(0, os.path.join(HERE, "examples"))
    exp = importlib.import_module("032_tear_line")
    geo, grid, pin, solver, conn = exp.build(cut=True, threshold=1.0)

    rest = len(grid.geometry().points())
    cut = len(pin.geometry(0).points())
    cons = pin.geometry(1)
    kinds = {}
    for prim in cons.prims():
        kinds[prim.attribValue("type")] = kinds.get(prim.attribValue("type"), 0) + 1
    print(f"元の布 {rest}点 → 切ったあと {cut}点（{cut - rest:+d}） 拘束 {kinds}")

    sec = timed_sweep(solver, 1, exp.LAST)
    print(f"{exp.LAST}フレームの計算: {sec:.2f}秒")
    for frame in (5, 15, exp.LAST):
        hou.setFrame(frame)
        stitches = sum(1 for p in solver.geometry(1).prims()
                       if p.attribValue("type") == "stitch")
        print(f"  F{frame}: stitch 残り {stitches}本")
    hou.setFrame(exp.LAST)
    classes = {}
    attr = conn.geometry().findPointAttrib("class")
    for point in conn.geometry().points():
        classes[point.attribValue(attr)] = classes.get(point.attribValue(attr), 0) + 1
    print(f"  F{exp.LAST}: 塊 {len(classes)}個 {sorted(classes.values())}")
    hou_tools.save_hip(os.path.join(OUT, "guide_tear.hipnc"))

    # 切り分けの図。上と下で色を分けて、どこで切れたかを見せる（撮るだけの枝）
    two = geo.node("two_pieces")
    show = geo.createNode("attribwrangle", "show_cut")
    show.setFirstInput(two)
    show.parm("class").set(1)
    show.parm("snippet").set("@Cd = i@lower ? {0.95, 0.55, 0.25} : {0.45, 0.62, 0.9};")
    hou.setFrame(1)
    global RES
    RES = (520, 440)
    shoot(show, "guide_tear_1_cut", show.geometry().boundingBox(), 1,
          shading="smoothwire", direction=(0.18, 0.2, 1.0))


def fire():
    """炎を出して色を付ける。組み方は実験026の build_fire をそのまま使う。

    画は実験026で同じシーンを撮ったもの（F30）を使う。ここでは .hipnc と
    時間・数・パラメータの表示名だけを取る。
    """
    import importlib
    sys.path.insert(0, os.path.join(HERE, "examples"))
    exp = importlib.import_module("026_fire_color")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo, solver, points, color, blast = exp.build_fire()
    src = geo.node("src")
    made = [src.parm(f"attribute{i + 1}").evalAsString()
            for i in range(src.parm("attributes").eval())]
    print("pyrosource が作る属性:", made)
    t = src.parm("initialize").parmTemplate()
    print("initialize:", t.label(), [(a, b) for a, b in zip(t.menuItems(), t.menuLabels())])
    for name in ("addflamefield", "doflamedensity", "flamedensity",
                 "enable_shredding", "shredding"):
        parm = solver.parm(name)
        print(f"  solver {name}: {parm.parmTemplate().label()} = {parm.eval()}")
    print(f"  pointsfromvolume particlesep: {points.parm('particlesep').parmTemplate().label()}"
          f" = {points.parm('particlesep').eval()}")

    sec = timed_sweep(solver, 1, exp.FRAME)
    print(f"{exp.FRAME}フレームの計算: {sec:.2f}秒")
    hou.setFrame(exp.FRAME)
    start = time.perf_counter()
    n_all = len(points.geometry().points())
    n_hot = len(blast.geometry().points())
    print(f"点をばらまいて色を付ける: {time.perf_counter() - start:.2f}秒 "
          f"{n_all}点 → 冷たい点を落として {n_hot}点")
    blast.setDisplayFlag(True)
    hou_tools.save_hip(os.path.join(OUT, "guide_fire.hipnc"))


def hair():
    """毛を風で揺らす。組み方は実験049の build をそのまま使う（風速 40）。

    画は実験049で同じ組み方を撮ったもの（風速 0 と 40、F48）を使う。
    """
    import importlib
    sys.path.insert(0, os.path.join(HERE, "examples"))
    exp = importlib.import_module("049_hair_wind")
    geo, skin, hair_con, solver = exp.build(40.0)
    for node, names in ((geo.node("hairgen"), ("density", "influenceradius", "thickness")),
                        (hair_con, ("constrainttype", "bendstiffness", "domass")),
                        (solver, ("dowind", "windx", "windspeed"))):
        for name in names:
            parm = node.parm(name)
            print(f"  {node.name()} {name}: {parm.parmTemplate().label()} = {parm.evalAsString()}")
    hou.setFrame(1)
    rest = hair_con.geometry()
    print(f"毛: {len(rest.prims())}本 / {len(rest.points())}点")
    sec = timed_sweep(solver, 1, exp.LAST)
    print(f"{exp.LAST}フレームの計算: {sec:.2f}秒")
    hou_tools.save_hip(os.path.join(OUT, "guide_hair.hipnc"))


def grass():
    """流れの向きに草を寝かせる。組み方は実験036の build をそのまま使う。"""
    import importlib
    sys.path.insert(0, os.path.join(HERE, "examples"))
    exp = importlib.import_module("036_flow_grass")
    start = time.perf_counter()
    geo, erode, sample, scatter, aim, copies, both = exp.build(use_flow=True)
    both.geometry()
    print(f"組んで草まで出す: {time.perf_counter() - start:.2f}秒")
    for node in (erode, sample, copies):
        start = time.perf_counter()
        node.cook(force=True)
        print(f"  {node.name()} だけ計算し直す: {time.perf_counter() - start:.2f}秒")
    mesh = geo.node("mesh").geometry()
    print(f"地形 {len(mesh.points())}点 / 草 {len(scatter.geometry().points())}本 / "
          f"合流後 {len(both.geometry().points())}点")
    print("erode の iterations:", erode.parm("iterations").parmTemplate().label())
    both.setDisplayFlag(True)
    hou_tools.save_hip(os.path.join(OUT, "guide_grass.hipnc"))


def carry():
    """動く板で塊を運ぶ。組み方は実験070の build をそのまま使う（板の速さ 4、摩擦 1）。"""
    import importlib
    sys.path.insert(0, os.path.join(HERE, "examples"))
    exp = importlib.import_module("070_mpm_moving")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo, solver = exp.build(4.0)
    collider = geo.node("collider")
    t = collider.parm("type").parmTemplate()
    print("collider type:", t.label(), list(zip(t.menuItems(), t.menuLabels())),
          "→", collider.parm("type").evalAsString())
    for name in ("friction", "computevelocity"):
        print(f"  collider {name}: {collider.parm(name).parmTemplate().label()}"
              f" = {collider.parm(name).evalAsString()}")
    print("  solver groundactive:", solver.parm("groundactive").parmTemplate().label())
    print("  floor tx:", geo.node("floor").parm("tx").expression())
    sec = timed_sweep(solver, 1, exp.LAST)
    pts = solver.geometry().points()
    x = sum(p.position()[0] for p in pts) / len(pts)
    print(f"{exp.LAST}フレームの計算: {sec:.2f}秒 / {len(pts)}粒 / 平均 x {x:.4f}")
    hou_tools.save_hip(os.path.join(OUT, "guide_carry.hipnc"))


def karma():
    """Karma で見せる絵を撮る。実験038の render_karma（材質あり・キー 2.4）をそのまま使う。"""
    import importlib
    import shutil
    sys.path.insert(0, os.path.join(HERE, "examples"))
    exp = importlib.import_module("038_karma_terrain")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo, paint, info = exp.render_karma("guide", True, exp.KEY)
    print(f"Karma {exp.RES[0]}×{exp.RES[1]}・サンプル {exp.SAMPLES}: {info['seconds']:.2f}秒")
    print("  ", {k: v for k, v in info.items() if k not in ("file",)})
    rop = hou.node("/out/exp038_guide")
    for name in ("camera", "samplesperpixel", "varianceaa_maxsamples", "denoiser", "picture"):
        parm = rop.parm(name)
        print(f"  karma {name}: {parm.parmTemplate().label()} = {parm.evalAsString()}")
    shader = hou.node("/mat/terrain_mat")
    for name in ("basecolor_usePointColor", "rough"):
        print(f"  shader {name}: {shader.parm(name).parmTemplate().label()}")
    print("  material:", geo.node("assign").parm("shop_materialpath1").parmTemplate().label())
    shutil.move(os.path.join(OUT, "038_guide.png"), os.path.join(OUT, "guide_karma_render.png"))
    rop.parm("picture").set("$HIP/guide_karma_render.png")
    hou_tools.save_hip(os.path.join(OUT, "guide_karma.hipnc"))


def export():
    """形を外へ書き出す。実験058は Python の saveToFile で確かめた。
    手順では画面から使うやり方（File SOP の Write、ROP Geometry Output）で
    Apprentice でも書けるかを、その場で確かめる。
    """
    folder = os.path.join(OUT, "guide_export")
    os.makedirs(folder, exist_ok=True)
    for name in os.listdir(folder):
        os.remove(os.path.join(folder, name))

    hou.hipFile.clear(suppress_save_prompt=True)
    hou_tools.save_hip(os.path.join(OUT, "guide_export.hipnc"))
    geo = hou.node("/obj").createNode("geo", "export")
    shape = geo.createNode("sphere", "shape")
    shape.parm("type").set(2)
    shape.parm("rows").set(16)
    shape.parm("cols").set(24)
    uv = geo.createNode("uvunwrap", "uv")
    uv.setFirstInput(shape)
    color = geo.createNode("color", "color")
    color.setFirstInput(uv)
    color.parmTuple("color").set((0.9, 0.45, 0.2))
    t = color.parm("colortype").parmTemplate() if color.parm("colortype") else None
    src = color.geometry()
    print(f"書き出す形: {len(src.points())}点 / {len(src.prims())}面 "
          f"点 {[a.name() for a in src.pointAttribs()]} バーテックス {[a.name() for a in src.vertexAttribs()]}")

    results = []
    # 1. File SOP を Write にする
    writer = geo.createNode("file", "write_obj")
    writer.setFirstInput(color)
    t = writer.parm("filemode").parmTemplate()
    print("file filemode:", list(zip(t.menuItems(), t.menuLabels())))
    writer.parm("filemode").set("write")
    writer.parm("file").set("$HIP/guide_export/shape_file.obj")
    start = time.perf_counter()
    try:
        writer.cook(force=True)
        err = writer.errors()
    except hou.OperationFailed as exc:
        err = [str(exc)]
    results.append(("File SOP (Write)", "shape_file.obj", time.perf_counter() - start, err))

    # 2. ROP Geometry Output（SOP の中に置く）
    rop = geo.createNode("rop_geometry", "rop_obj")
    rop.setFirstInput(color)
    rop.parm("sopoutput").set("$HIP/guide_export/shape_rop.obj")
    rop.parm("trange").set(0)
    start = time.perf_counter()
    try:
        rop.render(verbose=False)
        err = rop.errors()
    except hou.OperationFailed as exc:
        err = [str(exc)]
    results.append(("ROP Geometry Output", "shape_rop.obj", time.perf_counter() - start, err))

    for label, name, sec, err in results:
        path = os.path.join(folder, name)
        ok = os.path.exists(path)
        size = os.path.getsize(path) if ok else 0
        back = ""
        if ok:
            g = hou.Geometry()
            g.loadFromFile(path)
            back = (f"読み直し {len(g.points())}点 / {len(g.prims())}面 "
                    f"点 {[a.name() for a in g.pointAttribs()]} "
                    f"バーテックス {[a.name() for a in g.vertexAttribs()]}")
        print(f"{label}: {'書けた' if ok else '書けない'} {size:,}バイト {sec:.3f}秒 {err} {back}")

    for p in ("filemode", "file"):
        print(f"  file {p}: {writer.parm(p).parmTemplate().label()}")
    for p in ("sopoutput", "trange", "execute"):
        print(f"  rop {p}: {rop.parm(p).parmTemplate().label()}")
    writer.setDisplayFlag(True)
    hou_tools.save_hip(os.path.join(OUT, "guide_export.hipnc"))


def foreach():
    """面ごとに高さを変える処理を、for-each と VEX の両方で組み、結果と時間を比べる。"""
    import statistics
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "tiles")
    grid = geo.createNode("grid", "floor")
    grid.parm("sizex").set(10.0)
    grid.parm("sizey").set(10.0)
    unique = geo.createNode("facet", "unique")
    unique.setFirstInput(grid)
    unique.parm("unique").set(True)

    begin = geo.createNode("block_begin", "each_begin")
    begin.parm("method").set("piece")
    meta = geo.createNode("block_begin", "each_meta")
    meta.parm("method").set("metadata")
    inner = geo.createNode("attribwrangle", "lift_one")
    inner.setFirstInput(begin)
    inner.parm("class").set("point")
    inner.parm("snippet").set(
        'int i = detail("op:../each_meta", "iteration", 0);\n'
        "@P.y += rand(i) * 0.5;")
    end = geo.createNode("block_end", "each_end")
    end.setFirstInput(inner)
    end.parm("itermethod").set("pieces")
    end.parm("class").set("primitive")
    end.parm("method").set("merge")
    end.parm("blockpath").set("../each_begin")
    end.parm("templatepath").set("../each_begin")
    begin.parm("blockpath").set("../each_end")
    meta.parm("blockpath").set("../each_end")
    begin.setFirstInput(unique)

    vex = geo.createNode("attribwrangle", "lift_all")
    vex.setFirstInput(unique)
    vex.parm("class").set("primitive")
    vex.parm("snippet").set(
        "float h = rand(@primnum) * 0.5;\n"
        "foreach (int pt; primpoints(0, @primnum)) {\n"
        "    vector p = point(0, \"P\", pt);\n"
        "    setpointattrib(0, \"P\", pt, p + set(0, h, 0));\n"
        "}")
    geo.layoutChildren()
    for node, names in ((begin, ("method", "blockpath")), (end, ("itermethod", "class", "method", "templatepath")),
                        (unique, ("unique",))):
        for name in names:
            parm = node.parm(name)
            print(f"  {node.name()} {name}: {parm.parmTemplate().label()} = {parm.evalAsString()}")

    def heights(node):
        out = {}
        for prim in node.geometry().prims():
            ps = [v.point().position() for v in prim.vertices()]
            c = sum(ps, hou.Vector3()) / len(ps)
            out[(round(c[0], 4), round(c[2], 4))] = round(c[1], 6)
        return out

    # cook(force=True) では wrangle が計算し直されないことがあった（0.02ms と出た）。
    # 上流の grid をわずかに動かして両方を本当に計算し直させ、上流だけの時間を引く。
    flip = [0.0]

    def dirty():
        flip[0] = 1e-6 if flip[0] == 0.0 else 0.0
        grid.parm("ty").set(flip[0])

    def ms(node, runs=7):
        samples = []
        for _ in range(runs):
            dirty()
            start = time.perf_counter()
            node.geometry()
            samples.append((time.perf_counter() - start) * 1000)
        return statistics.median(samples)

    for div in (8, 22, 64):
        grid.parm("rows").set(div)
        grid.parm("cols").set(div)
        faces = len(unique.geometry().prims())
        a, b = heights(end), heights(vex)
        same = a == b
        up, fe, vx = ms(unique), ms(end), ms(vex)
        fe, vx = fe - up, vx - up
        print(f"{faces:5d}面 / {len(unique.geometry().points())}点: 上流 {up:6.2f}ms  "
              f"for-each {fe:8.2f}ms  VEX {vx:6.2f}ms  {fe / vx:5.1f}倍  結果が同じ: {same}")

    grid.parm("rows").set(22)
    grid.parm("cols").set(22)
    vex.setDisplayFlag(True)
    vex.setRenderFlag(True)
    hou_tools.save_hip(os.path.join(OUT, "guide_foreach.hipnc"))
    shoot(vex, "guide_foreach_tiles", vex.geometry().boundingBox(), 1, shading="smoothwire")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    {"wind": wind, "tear": tear, "fire": fire, "hair": hair, "grass": grass, "carry": carry, "karma": karma, "export": export, "foreach": foreach}[which]()
    print("完了:", which)
