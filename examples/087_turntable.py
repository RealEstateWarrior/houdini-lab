"""実験087 — ターンテーブルで見せる。回すのは物か、カメラか。時間はどれだけか。

作ったものを見せるとき、ぐるりと1周見せる「ターンテーブル」がいちばん分かりやすい。
物を回す方法と、カメラを回す方法の2通りがある。同じ絵になるのか、時間は違うのかを測る。

  A. 物を回す（xform の ry に式）とカメラを回す（カメラの位置を毎フレーム置き直す）で、
     同じ絵になるか。画素を数えて比べる
  B. コマ数（12 / 24 / 48）と解像度（320 / 480 / 720）で、1枚あたりの時間を測る
  C. GIF にしたときの大きさ（バイト）

    hython examples/087_turntable.py a
    hython examples/087_turntable.py b
    python  examples/087_turntable.py gif
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
SHOTS = os.path.join(OUT, "087_frames")


def build(spin_object=True):
    """見せる物（文字の看板）を作る。spin_object が真なら、物のほうを回す。"""
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "turntable")

    text = geo.createNode("font", "letters")
    text.parm("text").set("SP")
    text.parm("fontsize").set(1.0)

    thick = geo.createNode("polyextrude::2.0", "thickness")
    thick.setFirstInput(text)
    thick.parm("dist").set(0.15)
    thick.parm("outputback").set(1)

    center = geo.createNode("xform", "center")
    center.setFirstInput(thick)
    mid = thick.geometry().boundingBox().center()       # 外接箱の真ん中を原点に
    center.parmTuple("t").set((-mid[0], -mid[1], -mid[2]))

    spin = geo.createNode("xform", "spin")
    spin.setFirstInput(center)
    if spin_object:
        spin.parm("ry").setExpression("($FF - 1) / 24.0 * 360.0")
    spin.setDisplayFlag(True)
    spin.setRenderFlag(True)
    geo.layoutChildren()
    return geo, spin


def orbit_camera(frame, radius=1.0, height=0.25):
    """カメラを回すほうのやり方。見る向きを、物を回した分だけ逆に回す。

    物を +θ 回すのと、カメラを −θ 回すのは同じ見え方になるはず。
    高さの比（height ÷ radius）も、物を回すときの向き (0, 0.25, 1) にそろえる。
    """
    angle = math.radians((frame - 1) / 24.0 * 360.0)
    return (-radius * math.sin(angle), height, radius * math.cos(angle))


def shoot(node, png, res, direction, bbox):
    import hou_tools
    hou_tools.render_preview(node.path(), png, res=res, direction=direction,
                             shading="smoothwire", frame_bbox=bbox, margin=1.15)


def build_both():
    """回す版と止める版を、1つのシーンに並べて作る。

    レンダしたあとにシーンを作り直すと hython が固まる（実験027）。
    だから作り直さずに、両方を先に作っておく。
    """
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    spins, stills = [], []
    for name, spinning in (("spun", True), ("still", False)):
        geo = hou.node("/obj").createNode("geo", name)
        text = geo.createNode("font", "letters")
        text.parm("text").set("SP")
        thick = geo.createNode("polyextrude::2.0", "thickness")
        thick.setFirstInput(text)
        thick.parm("dist").set(0.15)
        thick.parm("outputback").set(1)
        center = geo.createNode("xform", "center")
        center.setFirstInput(thick)
        # 中心は当て推量にしない。実際の外接箱の真ん中を測ってずらす
        mid = thick.geometry().boundingBox().center()
        center.parmTuple("t").set((-mid[0], -mid[1], -mid[2]))
        spin = geo.createNode("xform", "spin")
        spin.setFirstInput(center)
        if spinning:
            spin.parm("ry").setExpression("($FF - 1) / 24.0 * 360.0")
        spin.setDisplayFlag(True)
        spin.setRenderFlag(True)
        geo.layoutChildren()
        (spins if spinning else stills).append(spin)
    return spins[0], stills[0]


def part_a():
    """物を回す / カメラを回す の2通りで、同じフレームを撮って比べる。"""
    import hou
    import numpy
    from PIL import Image
    os.makedirs(SHOTS, exist_ok=True)
    spun, still = build_both()
    bbox = hou.BoundingBox(-0.8, -0.6, -0.8, 0.8, 0.6, 0.8)
    rows = []
    for frame in (1, 7, 13, 19):
        hou.setFrame(frame)
        a = os.path.join(SHOTS, f"obj_{frame:02d}.png")
        shoot(spun, a, (320, 320), (0.0, 0.25, 1.0), bbox)
        x, y, z = orbit_camera(frame)
        b = os.path.join(SHOTS, f"cam_{frame:02d}.png")
        shoot(still, b, (320, 320), (x, y, z), bbox)
        ia = numpy.asarray(Image.open(a).convert("L"), dtype=float)
        ib = numpy.asarray(Image.open(b).convert("L"), dtype=float)
        diff = float(numpy.abs(ia - ib).mean())
        ink_a = float((ia > 20).mean() * 100)
        ink_b = float((ib > 20).mean() * 100)
        # 形（シルエット）と明るさを分けて見る。5 より明るい画素を「物が写っている」とみなす
        sil_a, sil_b = ia > 5, ib > 5
        bright_a = float(ia[sil_a].mean()) if sil_a.any() else 0.0
        bright_b = float(ib[sil_b].mean()) if sil_b.any() else 0.0
        rows.append({"frame": frame, "diff": diff, "ink_object": ink_a, "ink_camera": ink_b,
                     "silhouette_object": float(sil_a.mean() * 100),
                     "silhouette_camera": float(sil_b.mean() * 100),
                     "bright_object": bright_a, "bright_camera": bright_b})
        print(f"   F{frame:>3} | 画素の平均の差 {diff:.3f} | シルエットの割合 "
              f"{sil_a.mean() * 100:.2f}% / {sil_b.mean() * 100:.2f}% | "
              f"明るさの平均 物 {bright_a:.1f} / カメラ {bright_b:.1f}")
    with open(os.path.join(OUT, "087_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/087_a.json")


def part_b():
    """コマ数と解像度で、1枚あたりの時間を測る。"""
    import hou
    os.makedirs(SHOTS, exist_ok=True)
    rows = []
    geo, spin = build(spin_object=True)
    bbox = hou.BoundingBox(-0.8, -0.6, -0.8, 0.8, 0.6, 0.8)
    for res in (320, 480, 720):
        for count in (12, 24):
            start = time.perf_counter()
            for k in range(count):
                hou.setFrame(1 + k * (24 // count))
                png = os.path.join(SHOTS, f"t_{res}_{count}_{k:02d}.png")
                shoot(spin, png, (res, res), (0.0, 0.25, 1.0), bbox)
            sec = time.perf_counter() - start
            size = os.path.getsize(png)
            rows.append({"res": res, "count": count, "seconds": sec,
                         "per_frame_ms": sec / count * 1000, "png_bytes": size})
            print(f"   {res}×{res} {count}コマ | 合計 {sec:.2f}秒 | 1コマ {sec / count * 1000:.0f}ms | "
                  f"1枚 {size:,}バイト")
    with open(os.path.join(OUT, "087_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/087_b.json")


def gif():
    """撮った連番から GIF を作り、大きさを測る（hython でなく普通の python でよい）。"""
    sys.path.insert(0, HERE)
    import sequence_report
    rows = []
    for res, count in ((320, 12), (320, 24), (480, 24)):
        paths = [os.path.join(SHOTS, f"t_{res}_{count}_{k:02d}.png") for k in range(count)]
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            continue
        out_gif = os.path.join(OUT, f"087_turntable_{res}_{count}.gif")
        sequence_report.make_gif(paths, out_gif, duration=90, scale=1.0)
        size = os.path.getsize(out_gif)
        rows.append({"res": res, "count": count, "gif_bytes": size,
                     "png_total": sum(os.path.getsize(p) for p in paths)})
        print(f"   {res}×{res} {count}コマ | GIF {size:,}バイト | 元の PNG 合計 "
              f"{sum(os.path.getsize(p) for p in paths):,}バイト")
    with open(os.path.join(OUT, "087_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/087_c.json")


def sheet():
    """12コマを1枚の図に並べる。"""
    sys.path.insert(0, HERE)
    import sequence_report
    paths = [os.path.join(SHOTS, f"t_320_12_{k:02d}.png") for k in range(12)]
    paths = [p for p in paths if os.path.exists(p)]
    out_png = os.path.join(OUT, "087_sheet.png")
    sequence_report.contact_sheet(paths, out_png, columns=6)
    print(f"保存: {out_png}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    {"a": part_a, "b": part_b, "gif": gif, "sheet": sheet}[arg]()
