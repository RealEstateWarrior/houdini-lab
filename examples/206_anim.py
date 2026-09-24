# -*- coding: utf-8 -*-
"""実験206 の動き: 粗い布（44×56）と実践の細かさ（110×140）が机に落ちる様子を、横に並べた GIF にする。

    hython examples/206_anim.py          （連番を撮る）
    python examples/206_anim.py gif      （GIF にまとめる）
"""
import glob
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
TMP = os.path.join(OUT, "_206_frames")
LAST = 72
EVERY = 2
PAIR = [(44, 56), (110, 140)]


def shoot():
    import hou
    import hou_tools
    import sop_bench
    spec = importlib.util.spec_from_file_location("e206", os.path.join(HERE, "examples", "206_vellum_cloth_preview_res.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    hou.setFps(24)
    os.makedirs(TMP, exist_ok=True)
    geo = sop_bench.fresh()
    table = m.build_table(geo)
    box = hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.95, 0.8)
    for r, c in PAIR:
        vs, _ = m.build_cloth(geo, table, r, c)
        show = geo.createNode("merge", f"show_{r}")
        show.setInput(0, table)
        show.setInput(1, vs)
        for f in range(1, LAST + 1):
            hou.setFrame(f)
            vs.geometry()
            if f % EVERY == 0 or f == 1:
                hou_tools.render_preview(show.path(), os.path.join(TMP, f"r{r}_{f:03d}.png"), res=(480, 300),
                                         direction=(1.0, 0.7, 1.25), shading="smooth", frame_bbox=box)
        show.setDisplayFlag(False)
        print("撮った", r, flush=True)


def gif():
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(HERE, "examples"))
    from pil_chart import _font
    font = _font(16)
    frames = []
    names = sorted(glob.glob(os.path.join(TMP, f"r{PAIR[0][0]}_*.png")))
    for n in names:
        f = n.rsplit("_", 1)[1]
        # ビューポートの画は背景が透明なので、明るい灰色の上に重ねる
        def flat(path):
            im = Image.open(path).convert("RGBA")
            bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
            return Image.alpha_composite(bg, im).convert("RGB")
        a = flat(n)
        b = flat(os.path.join(TMP, f"r{PAIR[1][0]}_{f}"))
        w, h = a.size
        im = Image.new("RGB", (w * 2, h + 26), (236, 236, 238))
        im.paste(a, (0, 26))
        im.paste(b, (w, 26))
        d = ImageDraw.Draw(im)
        d.text((8, 4), f"粗い布 {PAIR[0][0]}×{PAIR[0][1]}", fill=(30, 30, 30), font=font)
        d.text((w + 8, 4), f"実践の細かさ {PAIR[1][0]}×{PAIR[1][1]}", fill=(30, 30, 30), font=font)
        d.text((w * 2 - 110, 4), f"フレーム {int(f[:3])}", fill=(110, 110, 110), font=font)
        frames.append(im.quantize(colors=128))
    path = os.path.join(OUT, "206_anim.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:] + [frames[-1]] * 12, duration=83, loop=0, optimize=True)
    print("GIF", len(frames), os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "gif":
        gif()
    else:
        shoot()
