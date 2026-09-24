# -*- coding: utf-8 -*-
"""実験205 — Karma で被写界深度（ピントのぼけ）とモーションブラー（動きのぶれ）を入れると、何倍重いか。
何サンプルあれば、ざらつきが気にならなくなるか。

制作の問い: 映像らしく見せるために、ぼけとぶれを入れたい。ぼけ・ぶれの入った所は、1 画素に入る光がばらつくので
ざらつきやすい。サンプル数をどこまで上げればよいのか、時間はどれだけ増えるのか。

  奥へ並んだ球 7 つ（手前から奥へ 0.6 m おき）と、画面を横切る箱（秒速 12 m、Transform の tx に $T の式）を、
  practice_kit と同じ撮り方（明るめの灰色の幕・キー・リム・ドーム）で 960×540 に撮る。フレーム 12。
    base   … ぼけ・ぶれ無し（Enable Motion Blur を切る）
    mblur  … モーションブラーだけ（カメラの Shutter Time 0.5 フレーム。Karma の既定）
    dof    … 被写界深度だけ（Enable Depth of Field を入れ、F-Stop 0.7、ピントは 4 番目の球）
    both   … 両方
  それぞれを Primary Samples 16・64・256 で撮る（Max Secondary Samples も同じ数。Noise Level は既定の 0.01）。
  ざらつきの目安は、画を 3×3 の中央値でならした画との差（画素の値 0〜255 の二乗平均の平方根）。
  （はじめは Noise Level 0.001 の画を答えにしようとしたが、1 枚 8 分を超えても終わらなかったのでやめた）
  最後に、両方入れた画で Noise Level を 0.005・0.0025 に下げて撮り、何がざらつきを決めているかを確かめる。

    hython examples/205_karma_dof_mblur_cost.py      （撮る）
    hython examples/205_karma_dof_mblur_cost.py strong   （F-Stop 0.2・Shutter Time 1 で、ぼけ・ぶれを強めて撮る）
    hython examples/205_karma_dof_mblur_cost.py tune     （16 サンプルで Noise Level を下げる・ノイズ除去を入れる）
    python examples/205_karma_dof_mblur_cost.py combine
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
RES = (960, 540)
SPPS = [16, 64, 256]
CASES = ["base", "mblur", "dof", "both"]
FRAME = 12
FSTOP = 0.7
# ざらつきを測る範囲（画の幅・高さに対する割合）。205_base_16.png を見て決める
REGIONS = {"box": (0.28, 0.4, 0.5, 0.6), "near": (0.1, 0.58, 0.3, 0.88)}


def build(g):
    balls = g.node("attribwrangle", "ball_spots", snippet=(
        "// 奥へ並べる 7 つの点。色を変えて、ぼけ具合を見分けやすくする\n"
        "for (int i = 0; i < 7; i++) {\n"
        "    int p = addpoint(0, set(-0.9 + i * 0.3, 0.25, 1.8 - i * 0.6));\n"
        "    setpointattrib(0, 'Cd', p, hsvtorgb(set(i / 7.0, 0.55, 0.85)));\n"
        "}"))
    balls.parm("class").set(0)
    ball = g.node("sphere", "ball", type=2, rad=(0.25, 0.25, 0.25), rows=48, cols=48)
    row = g.node("copytopoints::2.0", "row_of_balls", [ball, balls], targetattribs=1)
    # H21 の copytopoints は、ここに書かないと点の色を移さない
    row.parm("applyattribs1").set("Cd")
    row.parm("applyto1").set("points")
    box = g.node("box", "runner_box", size=(0.35, 0.35, 0.35))
    move = g.node("xform", "run_across", [box])
    move.parm("tx").setExpression("($T - 0.5) * 12")   # 秒速 12 m で右へ。フレーム 12 で x = −0.5
    move.parm("ty").set(0.6)
    move.parm("tz").set(0.6)
    m_balls = g.mat("ball_mat", basecolor=(1, 1, 1), rough=0.3)
    m_box = g.mat("box_mat", basecolor=(0.9, 0.9, 0.92), rough=0.4)
    for m in (m_balls,):
        # 点の色（Cd）を使う
        if m.parm("basecolor_usePointColor") is not None:
            m.parm("basecolor_usePointColor").set(1)
    a1 = g.assign(row, m_balls, "assign_balls")
    a2 = g.assign(move, m_box, "assign_box")
    final = g.node("merge", "scene", [a1, a2])
    return final, row


def shoot(strong=False, tune=False):
    import hou
    import practice_kit as kit
    g = kit.Guide("exp205", "実験205", "", tags=[])
    final, row = build(g)
    hou.setFrame(FRAME)
    bbox = hou.BoundingBox(-1.3, 0.0, -2.1, 1.3, 1.0, 2.1)
    g.hero(final, "", direction=(0.35, 0.3, 1.0), res=RES, spp=16, bbox=bbox, margin=1.0, frame=FRAME,
           backdrop=(0.3, 0.31, 0.33), key=4.0, dome=0.5)   # 温め（捨てる）
    karma = hou.node("/out/hero_karma")
    cam = hou.node("/obj/hero_cam")
    campos = cam.worldTransform().extractTranslates()
    focus_pt = hou.Vector3(-0.9 + 3 * 0.3, 0.25, 1.8 - 3 * 0.6)
    focus = (focus_pt - campos).length()
    cam.parm("focus").set(focus)
    fstop = 0.2 if strong else FSTOP
    cam.parm("fstop").set(fstop)
    if strong:
        cam.parm("shutter").set(1.0)   # 1 フレームのあいだ開けておく（既定 0.5 の倍ぶれる）
    pre = "s_" if strong else ""
    rows = []

    def render(case, spp, tag, noise=None, denoise=False):
        karma.parm("denoiser").set("oidn" if denoise else "off")
        karma.parm("enabledof").set(case in ("dof", "both"))
        karma.parm("enablemblur").set(case in ("mblur", "both"))
        karma.parm("samplesperpixel").set(spp)
        karma.parm("varianceaa_maxsamples").set(spp)
        karma.parm("varianceaa_thresh").set(noise or 0.01)
        karma.parm("oracle_variance").set(noise or 0.01)
        tag = pre + tag
        path = os.path.join(OUT, f"205_{tag}.png")
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
        rows.append({"case": case, "spp": spp, "noise": noise or 0.01, "denoise": denoise, "tag": tag, "sec": round(time.perf_counter() - t0, 2)})
        print(rows[-1], flush=True)

    if tune:
        # 仕上げの決め方を探す: 両方入れた画で、16 サンプルのまま Noise Level を下げる／ノイズ除去を入れる
        for nz in (0.005, 0.0025):
            render("both", 16, f"tune_both_16_n{nz}", noise=nz)
        render("both", 16, "tune_both_16_oidn", denoise=True)
        render("both", 64, "tune_both_64_oidn", denoise=True)
        with open(os.path.join(OUT, "205_times_tune.json"), "w", encoding="utf-8") as fp:
            json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
        print("書いた: 205_times_tune.json")
        return
    for case in (["base", "mblur", "dof", "both"] if not strong else ["mblur", "dof", "both"]):
        for spp in SPPS:
            render(case, spp, f"{case}_{spp}")
    if strong:
        with open(os.path.join(OUT, "205_times_strong.json"), "w", encoding="utf-8") as fp:
            json.dump({"fstop": fstop, "shutter": 1.0, "rows": rows}, fp, ensure_ascii=False, indent=1)
        print("書いた: 205_times_strong.json")
        return
    # ざらつきの決め手を確かめる: 両方入れた画で、Noise Level を下げる
    for nz in (0.005, 0.0025):
        render("both", 64, f"both_64_n{nz}", noise=nz)
    info = {"focus": focus, "fstop": fstop, "shutter": cam.parm("shutter").eval(), "res": RES, "frame": FRAME,
            "box_speed": 12, "rows": rows,
            "karma": {p: karma.parm(p).eval() for p in ("geosamples", "xformsamples", "varianceaa_minsamples")}}
    with open(os.path.join(OUT, "205_times.json"), "w", encoding="utf-8") as fp:
        json.dump(info, fp, ensure_ascii=False, indent=1)
    import hou_tools
    g.geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "205_scene.hipnc"))
    hou_tools.write_graph(g.geo.path(), os.path.join(OUT, "205_graph.json"), title="実験205")
    print("書いた: 205_times.json")


def combine():
    import numpy as np
    from PIL import Image
    sys.path.insert(0, os.path.join(HERE, "examples"))
    import sop_bench
    with open(os.path.join(OUT, "205_times.json"), encoding="utf-8") as fp:
        info = json.load(fp)
    from PIL import ImageFilter
    sp = os.path.join(OUT, "205_times_strong.json")
    if os.path.exists(sp):
        with open(sp, encoding="utf-8") as fp:
            strong = json.load(fp)
        for r in strong["rows"]:
            r["strong"] = True
        info["rows"] += strong["rows"]
        info["strong"] = {"fstop": strong["fstop"], "shutter": strong["shutter"]}
    tp = os.path.join(OUT, "205_times_tune.json")
    if os.path.exists(tp):
        with open(tp, encoding="utf-8") as fp:
            info["rows"] += json.load(fp)["rows"]
    for r in info["rows"]:
        im = Image.open(os.path.join(OUT, f"205_{r['tag']}.png")).convert("RGB")
        a = np.asarray(im, dtype=np.float64)
        med = np.asarray(im.filter(ImageFilter.MedianFilter(3)), dtype=np.float64)
        d = a - med
        r["grain"] = round(float(np.sqrt((d ** 2).mean())), 3)
        # 動く箱のまわり（ぶれる所）と、手前の球のまわり（ぼける所）だけでも測る
        h, w = d.shape[:2]
        for name, (x0, y0, x1, y1) in REGIONS.items():
            sub = d[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
            r["grain_" + name] = round(float(np.sqrt((sub ** 2).mean())), 3)
    sop_bench.save(205, info["rows"], {k: v for k, v in info.items() if k != "rows"})


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "combine":
        combine()
    else:
        shoot(strong=len(sys.argv) > 1 and sys.argv[1] == "strong", tune=len(sys.argv) > 1 and sys.argv[1] == "tune")
