# -*- coding: utf-8 -*-
"""実践「焚き火を燃やす」— 薪と石を並べ、Pyro で炎を出して Karma で撮る。設定は実験201 で決めた値。

    hython examples/pr_campfire.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

FRAME = 60
VOX = 0.03


def main():
    import hou
    g = kit.Guide("campfire", "焚き火を燃やす",
                  "薪と石を並べ、その真ん中から炎を出す。Pyro は既定のままだと炎が柱になって伸び続けるので、"
                  "炎の寿命・浮き上がる力・冷め方の3つを下げて、焚き火の大きさにする（実験201）。",
                  tags=["シミュレーション", "Pyro", "炎", "Karma", "制作"])
    g.shot_dir = (0.9, 0.7, 1.1)
    log = g.node("tube", "log", type="poly", rad1=0.07, rad2=0.07, height=0.9, cols=16, orient=0, cap=1, ty=0.07)
    tilt = g.node("copyxform", "three_logs", [log], ncy=3, ry=60, ty=0.06)
    g.step(tilt, "薪を組む",
           "<code>tube</code> で半径 0.07・長さ 0.9 の丸太を作り（Orientation を X 軸）、<code>copyxform</code> で <strong>60度ずつ回し、0.06 ずつ持ち上げて3本</strong>にする。"
           "真上から見ると、真ん中で交わる星の形になり、上の薪が下の薪に乗る。",
           cap="3本の薪。", shading="smoothwire", ui_parm="ncy")
    ring = g.node("circle", "stone_ring", type="poly", orient=2, radx=0.55, rady=0.55, divs=12)
    stone = g.node("sphere", "stone", type="polymesh", rows=8, cols=12, rad=(0.11, 0.07, 0.09), t=(0, 0.05, 0))
    bumpy = g.node("mountain::2.0", "stone_bumps", [stone], height=0.03, elementsize=0.12)
    stones = g.node("copytopoints::2.0", "stones", [bumpy, ring])
    g.step(stones, "石で囲む",
           "<code>circle</code>（半径 0.55・12分割）の点に、<code>mountain</code> で少しでこぼこにした小さな球を "
           "<code>copytopoints</code> で並べる。炎の大きさの目安にもなる。",
           cap="12個の石の輪。", shading="smoothwire")
    emit = g.node("sphere", "fire_source", type="polymesh", rows=16, cols=24, rad=(0.22, 0.08, 0.22), t=(0, 0.12, 0))
    src = g.node("pyrosource", "src", [emit])
    src.parm("initialize").set("sourceburn")
    src.parm("initialize").pressButton()
    made = [src.parm(f"attribute{i + 1}").evalAsString() for i in range(src.parm("attributes").eval())]
    g.step(src, "炎の出どころを作る",
           "薪の交わるところに、平たい球（半径 0.22・厚み 0.08）を置き、<code>pyrosource</code> の <strong>Initialize を Source Burn</strong> にする。"
           f"球の中に点が詰まり、燃やすための値（{'・'.join(made)}）が付く。",
           cap="発生源の点。", shading="smoothwire", ui_parm="initialize")
    rast = g.node("volumerasterizeattributes", "to_voxels", [src], attributes=" ".join(made), voxelsize=VOX)
    g.step(rast, "点を升目にする",
           f"<code>volumerasterizeattributes</code> で点の値を升目（ボリューム）に移す。Attributes に {' '.join(made)}、"
           f"<strong>Voxel Size は {VOX}</strong>。Pyro は升目の上で計算する。",
           cap="発生源のボリューム。", ui_parm="voxelsize")
    solver = g.node("pyrosolver", "burn", [rast], divsize=VOX, addflamefield=1, doflamedensity=1, flamedensity=1.0,
                    flames_lifespan=0.25, buoyancylift=0.25, tempcooling=1.0,
                    enable_turbulence=1, turbulence=3.0, turbulence_usecontrol=0)
    g.step(solver, "焚き火の大きさにして燃やす",
           "<code>pyrosolver</code> で燃やす。既定のままだと炎が 1 秒に約 6 m 伸び続けるので、実験201 で決めた値に変える。"
           "<strong>Flame Lifespan 0.25・Buoyancy Scale 0.25・Cooling Rate 1</strong>。"
           "炎を揺らすのは <strong>Turbulence 3</strong>で、<strong>Use Control Field を切る</strong>（切らないと何も変わらない）。"
           "Create Flame Field と Flame Density（1）を入れて、炎から煙も出す。",
           cap="フレーム60の炎（ビューポートの表示）。", ui_parm="flames_lifespan", shot=False)
    fire = g.mat("fire_mat", kind="kma_pyroshader")
    fire.parm("enablefire").set(1)
    fire.parm("fireintscale").set(1.5)
    fire.parm("densityscale").set(0.6)
    # 明るさと色を flame（炎の場）から取る。既定の temperature は Cooling Rate 1 ですぐ冷めるので、根元しか光らない
    fire.parm("fireint_volumename").set("flame")
    fire.parm("firecolor_volumename").set("flame")
    fire.parm("firecolormode").set("0")
    fire.parm("firecolorramp").set(hou.Ramp((hou.rampBasis.Linear,) * 4, (0.0, 0.3, 0.65, 1.0),
                                            ((0, 0, 0), (0.6, 0.06, 0.01), (1.0, 0.35, 0.05), (1.0, 0.85, 0.45))))
    fire_a = g.assign(solver, fire, "assign_fire")
    wood = g.mat("wood_mat", basecolor=(0.05, 0.028, 0.016), rough=0.85)
    rock = g.mat("stone_mat", basecolor=(0.12, 0.115, 0.11), rough=0.8)
    wood_a = g.assign(tilt, wood, "assign_wood")
    rock_a = g.assign(stones, rock, "assign_stone")
    final = g.node("merge", "campfire", [wood_a, rock_a, fire_a])
    g.step(final, "炎の材質を当てて撮る",
           "<code>/mat</code> に <code>kma_pyroshader</code>（Karma の炎用の材質）を作り、<strong>Enable Fire</strong> を入れて "
           "Intensity Scale を 1.5 にする（上げすぎると根元が白く飛ぶ）。<strong>Intensity Volume と Color Volume を flame</strong> に変え、Fire Color Ramp を黒→赤→橙→黄白にする。薪と石には <code>principledshader</code>。<code>merge</code> でまとめ、"
           f"<strong>フレーム {FRAME}</strong>（2.5 秒）で撮る。炎の光で薪と石が照らされる。",
           cap="材質を当てた状態。", shot=False)
    t0 = time.perf_counter()
    for f in range(1, FRAME + 1):
        hou.setFrame(f)
        solver.geometry()
    sim_sec = time.perf_counter() - t0
    g.hero(final, f"Karma で撮った仕上がり（フレーム{FRAME}）。明かりは炎だけに近い。", direction=(0.95, 0.35, 1.2),
           key=0.15, rim=0.3, dome=0.03, spp=48, margin=1.05, frame=FRAME,
           bbox=hou.BoundingBox(-0.75, 0, -0.75, 0.75, 1.5, 0.75))
    fl = [p for p in solver.geometry().prims() if p.type() == hou.primType.Volume and p.attribValue("name") == "flame"]
    res = fl[0].resolution() if fl else ()
    traps = [
        {"title": "既定の Pyro では焚き火にならない",
         "body": "pyrosolver を既定のまま（Flame Lifespan 2 秒など）にすると、炎は 1 秒に約 6 m 伸び、3 秒たっても 14 m 近い柱のまま（実験201）。"
                 "焚き火のような小さな炎は、寿命・浮き上がる力・冷め方の3つを下げて作る。",
         "img": "", "cap": ""},
        {"title": "Turbulence は Use Control Field を切らないと効かない",
         "body": "既定では Turbulence は煙（density）の濃い所にだけ効く。炎の近くは煙が薄いので、強さを 1 にしても形は小数3桁まで同じだった（実験201）。",
         "img": "", "cap": ""},
        {"title": "炎の材質は、既定では温度で光る",
         "body": "kma_pyroshader の明るさ（Intensity Volume）と色（Color Volume）は、既定で temperature を見る。"
                 "Cooling Rate 1 だと温度は発生源のすぐ上で下がるので、既定のまま撮ると、根元の平たい円盤だけが光って炎が写らなかった。flame に変える。",
         "img": "", "cap": ""},
        {"title": "炎は升目の細かさで重さが決まる",
         "body": f"Voxel Size {VOX} で {FRAME} フレーム回すのに {sim_sec:.1f} 秒、炎の升目は {' × '.join(map(str, res))}。"
                 "升を半分にすると升の数は 8 倍になる。形を決めるまでは粗く回す。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "15個（材質3つ）"], [f"{FRAME} フレームの計算", f"{sim_sec:.1f}秒"]], traps=traps, exp="201")


if __name__ == "__main__":
    main()
