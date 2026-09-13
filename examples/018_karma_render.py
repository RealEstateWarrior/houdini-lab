"""実験018 — Karma でボリュームを描き、ノイズがサンプル数でどう減るかを式で確かめる。

実験016で、ハードウェアレンダラー（OpenGL ROP）では煙が塊にしか描けないと分かった。
そこで本式のレンダラーである Karma を使う。ただ「きれいに描けた」では終わらせない。

Karma は1ピクセルの色を、乱数で飛ばした何本もの光線の平均で決める。
平均のばらつきは本数の平方根に反比例するので、

    ノイズ ∝ 1 / √(サンプル数)

サンプル数を4倍にすればノイズは半分になるはず。これを実測で確かめる。

ここに至るまでに3つ踏んだので、対策込みで残す。

1. 背景が真っ黒、煙の芯が真っ白。255に張り付いた画素は元の値が分からないので、
   明るさを下げたうえで、中間調（40〜200）の画素だけを測る対象にする。
2. 最初のマスクは「白から離れた画素」で作ったが、背景が黒だったため
   画面の88%を拾ってしまい、ほぼ何も測っていなかった。
3. 時間がサンプル数に比例しない。調べると、時間の大半は準備にかかる固定費だった。
   実験009のVEXと同じく「固定費 + 比例する分」に分けて測る。

    hython examples/018_karma_render.py
"""

import json
import math
import os
import sys
import time

import hou
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SCENE = os.path.join(OUT, "016_pyro.hipnc")
FRAME = 30
RES = (640, 360)
SHOWCASE_RES = (1280, 720)
SAMPLES = [2, 4, 8, 16, 32, 64, 128, 256]
REFERENCE = 2048
DOME, KEY = 0.10, 0.25          # 白飛びを避ける明るさ（露出を振って決めた）
MID_LO, MID_HI = 40, 200        # この範囲の画素だけで測る


def setup():
    hou.hipFile.load(SCENE, suppress_save_prompt=True, ignore_load_warnings=True)
    hou.setFrame(FRAME)
    sop = hou.node("/obj/pyro_test/solve_d0_1")
    if sop is None:
        raise SystemExit("煙のSOPが見つからない")
    sop.setDisplayFlag(True)
    sop.setRenderFlag(True)
    hou.node("/obj/report_dome").parm("light_intensity").set(DOME)
    hou.node("/obj/report_key").parm("light_intensity").set(KEY)
    return sop


def place_camera(sop, res):
    cam = hou.node("/obj/report_cam") or hou.node("/obj").createNode("cam", "report_cam")
    cam.parm("resx").set(res[0])
    cam.parm("resy").set(res[1])
    hou_tools._frame_camera(cam, sop.geometry().boundingBox(), res, margin=0.5)
    return cam


def make_karma(cam, res):
    out = hou.node("/out")
    karma = out.node("exp018_karma") or out.createNode("karma", "exp018_karma")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")     # ノイズを測るので消す機能は切る
    karma.parm("resolutionx").set(res[0])
    karma.parm("resolutiony").set(res[1])
    return karma


def shoot(karma, spp, path):
    karma.parm("samplesperpixel").set(spp)
    karma.parm("varianceaa_maxsamples").set(spp)   # 適応サンプリングで頭打ちにしない
    karma.parm("picture").set(path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
    return time.perf_counter() - start


def gray(path):
    img = Image.open(path).convert("L")
    return img.size, list(img.getdata())


def rms(a, b, mask):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in mask) / len(mask))


def fit_line(xs, ys):
    """最小二乗で y = a + b*x に当てはめる。a が固定費、b が1サンプルあたり。"""
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    b = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    return (sy - b * sx) / n, b


def main():
    sop = setup()
    geo = sop.geometry()
    print(f"煙: {len(geo.points())}点 / {len(geo.prims())}プリミティブ "
          f"({sorted({p.type().name() for p in geo.prims()})})")

    cam = place_camera(sop, RES)
    karma = make_karma(cam, RES)

    ref_path = os.path.join(OUT, "018_karma_ref.png")
    ref_time = shoot(karma, REFERENCE, ref_path)
    size, ref_px = gray(ref_path)
    mask = [i for i, v in enumerate(ref_px) if MID_LO <= v <= MID_HI]
    black = sum(1 for v in ref_px if v == 0)
    white = sum(1 for v in ref_px if v == 255)
    print(f"\n基準画 {REFERENCE}サンプル: {ref_time:.1f}秒")
    print(f"  真っ黒 {black} / 白飛び {white} / 測る対象 {len(mask)} 画素"
          f"（全体の {100.0 * len(mask) / len(ref_px):.1f}%）")

    rows = []
    print(f"\n{'サンプル':>8} {'時間(秒)':>9} {'ノイズ':>8} {'前段との比':>10} "
          f"{'予測(0.7071)':>12}")
    prev = None
    for spp in SAMPLES:
        path = os.path.join(OUT, f"018_karma_spp{spp:04d}.png")
        elapsed = shoot(karma, spp, path)
        _, px = gray(path)
        noise = rms(px, ref_px, mask)
        ratio = None if prev is None else noise / prev
        rows.append({"spp": spp, "sec": elapsed, "raw": noise,
                     "ratio": ratio})
        print(f"{spp:8d} {elapsed:9.2f} {noise:8.3f} "
              f"{('' if ratio is None else f'{ratio:.4f}'):>10} "
              f"{('' if ratio is None else '0.7071'):>12}")
        prev = noise

    # 基準画に残るノイズを差し引く。測定値² = σ(spp)² + σ(基準)²
    first = rows[0]
    sigma0 = first["raw"] / math.sqrt(1.0 + SAMPLES[0] / REFERENCE)
    sigma_ref = sigma0 * math.sqrt(SAMPLES[0] / REFERENCE)
    print(f"\n基準画に残っているノイズの推定: {sigma_ref:.4f}")
    print(f"\n{'サンプル':>8} {'測定値':>9} {'補正後':>9} {'式の予測':>9} {'ずれ%':>8}")
    for row in rows:
        corrected = math.sqrt(max(row["raw"] ** 2 - sigma_ref ** 2, 0.0))
        predicted = sigma0 / math.sqrt(row["spp"] / SAMPLES[0])
        row["corrected"] = corrected
        row["predicted"] = predicted
        row["gap_pct"] = 100.0 * (corrected - predicted) / predicted
        print(f"{row['spp']:8d} {row['raw']:9.3f} {corrected:9.3f} "
              f"{predicted:9.3f} {row['gap_pct']:8.2f}")

    fixed, per_sample = fit_line([r["spp"] for r in rows], [r["sec"] for r in rows])
    print(f"\n時間の内訳: 固定費 {fixed:.2f}秒 + 1サンプルあたり "
          f"{per_sample * 1000:.2f}ミリ秒")
    print(f"  {SAMPLES[0]}サンプルでは固定費が "
          f"{100.0 * fixed / rows[0]['sec']:.0f}%、"
          f"{SAMPLES[-1]}サンプルでは {100.0 * fixed / rows[-1]['sec']:.0f}%")

    # --- 同じ煙を OpenGL ROP でも描く ---
    gl_path = os.path.join(OUT, "018_opengl.png")
    hou_tools.render_preview(sop.path(), gl_path, res=RES, shading="smooth",
                             frame_bbox=sop.geometry().boundingBox())
    _, gl_px = gray(gl_path)

    def describe(px):
        drawn = [v for v in px if v > 0]
        if not drawn:
            return {"pixels": 0, "levels": 0, "sd": 0.0}
        mean = sum(drawn) / len(drawn)
        sd = math.sqrt(sum((v - mean) ** 2 for v in drawn) / len(drawn))
        return {"pixels": len(drawn), "levels": len(set(drawn)), "sd": sd}

    gl = describe(gl_px)
    ka = describe(ref_px)
    print(f"\n同じ煙を2つのレンダラーで描いた結果（黒でない画素だけを見る）")
    print(f"  OpenGL ROP : {gl['pixels']:6d}画素 / 階調 {gl['levels']:3d}段 / "
          f"濃淡のばらつき {gl['sd']:6.2f}")
    print(f"  Karma      : {ka['pixels']:6d}画素 / 階調 {ka['levels']:3d}段 / "
          f"濃淡のばらつき {ka['sd']:6.2f}")

    # --- 掲載用 ---
    cam = place_camera(sop, SHOWCASE_RES)
    karma.parm("resolutionx").set(SHOWCASE_RES[0])
    karma.parm("resolutiony").set(SHOWCASE_RES[1])
    show_time = shoot(karma, REFERENCE, os.path.join(OUT, "018_karma_showcase.png"))
    print(f"\n掲載用 {SHOWCASE_RES[0]}x{SHOWCASE_RES[1]} / {REFERENCE}サンプル: "
          f"{show_time:.1f}秒")

    with open(os.path.join(OUT, "018_stats.json"), "w", encoding="utf-8") as fp:
        json.dump({
            "frame": FRAME, "res": list(RES), "lights": {"dome": DOME, "key": KEY},
            "mid_range": [MID_LO, MID_HI],
            "reference_spp": REFERENCE, "reference_sec": ref_time,
            "mask_pixels": len(mask), "black": black, "white": white,
            "sigma_ref": sigma_ref, "rows": rows,
            "time_fixed_sec": fixed, "time_per_sample_sec": per_sample,
            "opengl": gl, "karma": ka, "showcase_sec": show_time,
        }, fp, ensure_ascii=False, indent=2)

    hou_tools.write_graph("/obj/pyro_test", os.path.join(OUT, "018_graph.json"),
                          title="実験018 — Karma でのレンダリング")
    hou_tools.save_hip(os.path.join(OUT, "018_karma.hipnc"))
    print("\n保存: out/018_stats.json, out/018_graph.json, out/018_karma.hipnc")


if __name__ == "__main__":
    main()
