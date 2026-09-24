# -*- coding: utf-8 -*-
"""実験231 — 焚き火の炎の光で周りを照らすとき、炎のボリュームの光だけで足りるか。ライトを足すとどうなるか。

制作の問い: 焚き火や松明の場面で、周りの地面や薪を炎の光で照らしたい。実験225 では、小さな光る球で照らすとひどくざらついた。
Pyro の炎（kma_pyroshader の光るボリューム）で照らすとどうか。炎の中にライト（point）を足すと、ざらつきと時間はどう変わるか。

  実践「焚き火」の場面（out/pr_campfire.hipnc、フレーム 60）を使う。実践で入れていた補助の明かり（キー・リム・ドーム）は 0 にする
  （ドームは明るさ 0 のまま残し、Karma が自動で明かりを足さないようにする）。
    fire          … 炎のボリュームの光だけ
    fire_light    … 炎＋炎の中（高さ 50 cm）に橙の point ライト 1 つ（強さは、ライトだけで照らした地面が炎だけのときと同じ明るさになるように決める）
    light         … 炎を画から消して（display を切って）、ライトだけ（強さを決めるため）
  640×360 を 16 サンプル（ノイズ除去なし）で撮り、同じ条件の 128 サンプルの画との差（地面・薪・石の部分の、明るさに対する割合）をざらつきとする。

    hython examples/231_campfire_light.py fire 0          （条件 と ライトの強さ）
    hython examples/231_campfire_light.py light 1        （強さ 1 で撮り、炎だけと同じ明るさになる強さを比で決める）
    hython examples/231_campfire_light.py fire_light <強さ>
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
FRAME = 60
RES = (640, 360)


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.load(os.path.join(OUT, "pr_campfire.hipnc"), suppress_save_prompt=True)
    for name in ("hero_key", "hero_rim"):
        n = hou.node("/obj/" + name)
        if n is not None:
            n.parm("light_intensity").set(0)
    hou.node("/obj/hero_dome").parm("light_intensity").set(0)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    karma.parm("denoiser").set("off")
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1])):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    geo = hou.node("/obj/campfire")
    final = [c for c in geo.children() if c.isDisplayFlagSet()][0]
    # 炎のボリュームだけを消す枝（炎の材質が付いた面を消す）
    fire_path = hou.node("/mat/fire_mat").path()
    nofire = geo.createNode("blast", "hide_fire")
    nofire.setFirstInput(final)
    nofire.parm("group").set(f'@shop_materialpath="{fire_path}"')
    nofire.parm("grouptype").set(4) if nofire.parm("grouptype") else None
    lamp = hou.node("/obj").createNode("hlight::2.0", "fire_lamp")
    lamp.parm("light_type").set("point")
    lamp.parmTuple("light_color").set((1.0, 0.55, 0.2))
    lamp.parmTuple("t").set((0, 0.5, 0))   # はじめは 25 cm にしたら、積んだ薪の内側で光がさえぎられて届かなかった
    # 炎を作る（Pyro は 1 フレーム目から順に）
    t0 = time.perf_counter()
    for f in range(1, FRAME + 1):
        hou.setFrame(f)
        final.geometry()
    sim_sec = time.perf_counter() - t0

    def shoot(tag, spp):
        exr = os.path.join(OUT, f"_231_{tag}_{spp}.exr")
        karma.parm("samplesperpixel").set(spp)
        karma.parm("varianceaa_maxsamples").set(spp)
        karma.parm("picture").set(exr.replace("\\", "/"))
        t = time.perf_counter()
        karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
        sec = time.perf_counter() - t
        px = oiio.ImageBuf(exr).get_pixels(oiio.FLOAT)[:, :, :3]
        return px, sec

    lum = lambda x: x @ np.array([0.2126, 0.7152, 0.0722])  # noqa: E731
    mask = (slice(int(RES[1] * 0.62), RES[1]), slice(0, int(RES[0] * 0.8)))   # 下の地面・薪・石（右下の透かしは外す）

    def setup(tag):
        show_fire = tag != "light"
        final.setDisplayFlag(show_fire)
        final.setRenderFlag(show_fire)
        nofire.setDisplayFlag(not show_fire)
        nofire.setRenderFlag(not show_fire)
        lamp.parm("light_enable").set(0 if tag == "fire" else 1)

    # 条件ごとに別の hython で撮る
    tag, intensity = sys.argv[1], float(sys.argv[2])
    setup(tag)
    lamp.parm("light_intensity").set(intensity)
    ref, sec_ref = shoot(tag, 128)
    img, sec = shoot(tag, 16)
    la, lb = lum(img[mask]), lum(ref[mask])
    noise = float(np.sqrt(np.mean((la - lb) ** 2)) / max(lb.mean(), 1e-6))
    row = {"case": tag, "lamp_intensity": intensity, "sec16": round(sec, 2), "sec128": round(sec_ref, 2), "noise16": round(noise, 4),
           "ground": round(float(lb.mean()), 5), "sim_sec": round(sim_sec, 1)}
    print(row, flush=True)
    view = np.clip(img, 0, 1) ** (1 / 2.2)
    ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
    ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
    ob.write(os.path.join(OUT, f"231_{tag}_{intensity:g}.png"))
    for f in os.listdir(OUT):
        if f.startswith("_231_") and f.endswith(".exr"):
            os.remove(os.path.join(OUT, f))
    import json
    with open(os.path.join(OUT, f"231_part_{tag}_{intensity:g}.json"), "w", encoding="utf-8") as fp:
        json.dump(row, fp)
    if tag != "fire_light":
        return
    setup("fire_light")
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "231_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "231_graph.json"), title="実験231")


if __name__ == "__main__":
    main()
