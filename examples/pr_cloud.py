# -*- coding: utf-8 -*-
"""実践「もくもくの雲を浮かべる」— 球を集めた形をボリュームにし、ノイズで縁を削って積雲にする。

本物の積雲（夏のもくもくした雲）は、上がカリフラワーのように丸く盛り上がり、底は平ら（水蒸気が雲になる高さがそろっている）。
日の当たる上は白く輝き、底は影になって灰色。縁はふわふわで、はっきりした面は無い。

    hython examples/pr_cloud.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("cloud", "もくもくの雲を浮かべる",
                  "大きさの違う球を寄せ集めて雲の大まかな形を作り、底を平らに切る。cloud ノードでボリューム（濃さの升目）にし、"
                  "cloudnoise で縁を削ると、ふわふわの積雲になる。明かりは強い日差しと青い空の2つ。",
                  tags=["モデリング", "ボリューム", "雲", "Karma"])
    g.shot_dir = (1.0, 0.25, 1.2)
    base = g.node("sphere", "cloud_base", type="polymesh", rad=(4, 1.6, 2.6), rows=24, cols=48)
    spots = g.node("scatter::2.0", "puff_spots", [base], npts=26, seed=5, relaxpoints=1)
    sizes = g.node("attribwrangle", "puff_sizes", [spots], snippet=(
        "// 上の点ほど大きな球にする（上がもくもく盛り上がる）\n"
        "f@pscale = fit(@P.y, -1.6, 1.6, 0.9, 2.1) * fit01(rand(@ptnum + 2), 0.75, 1.2);"))
    puff = g.node("sphere", "puff", type="polymesh", rad=(1, 1, 1), rows=16, cols=24)
    puffs = g.node("copytopoints::2.0", "puffs", [puff, sizes])
    flat = g.node("clip", "flat_bottom", [puffs], dir=(0, 1, 0), dist=-0.6)   # 向き (0,1,0) の側（上）を残す
    g.step(flat, "球を集めて、底を平らにする",
           "横長の <code>sphere</code>（8 × 3.2 × 5.2）の表面に <code>scatter</code> で 26 個の点をまき、"
           "<code>attribwrangle</code> で <strong>上の点ほど大きな pscale</strong> にする。小さな球を <code>copytopoints</code> で並べると、"
           "上がもくもくした塊になる。<code>clip</code> の Direction を (0, 1, 0)、Distance を −0.6 にして、高さ −0.6 より下を切り、底を平らにする（本物の積雲も底が平ら）。"
           "Direction の向いている側が残る。(0, −1, 0) にすると上が消えて、下のお椀だけが残った。",
           cap="球を寄せ集めた雲の形。", shading="smooth", ui_parm="dist")

    vol = g.node("cloud::2.0", "to_cloud", [flat], samplediv=160, densitymultiplier=3.0)
    g.step(vol, "ボリュームにする",
           "<code>cloud</code> ノードにつなぐと、面の内側が濃さ（density）の升目で満たされたボリュームになる。"
           "<strong>Uniform Sampling Divs 160</strong>（長い辺を160に割る）、Density Multiplier 3。",
           cap="ボリュームになった雲（まだ縁がのっぺり）。", shading="smooth", ui_parm="samplediv")

    fluff = g.node("cloudnoise", "fluffy_edges", [vol], noiseamount=0.45, noiseelementsize=1.2, noiseoctaves=5)
    g.step(fluff, "ノイズで縁を削る",
           "<code>cloudnoise</code> で、縁の濃さをノイズで削る。<strong>Amplitude 0.45・Element Size 1.2・Octaves 5</strong>。"
           "大きな渦から細かい渦まで重なって、縁がふわふわになる。Amplitude を上げるほど、深く削れる。",
           cap="縁がふわふわになった雲。", shading="smooth", ui_parm="noiseamount")

    sun = hou.node("/obj").createNode("hlight::2.0", "sun")
    sun.parm("light_type").set("distant")
    sun.parm("light_intensity").set(4.0)
    sun.parmTuple("light_color").set((1.0, 0.96, 0.9))
    sun.parmTuple("r").set((-35, 40, 0))
    g.step(fluff, "日差しと空の明かり",
           "<code>hlight</code> を Distant（太陽）にして、斜め上から Intensity 4 で当てる。空の青い明かりは弱いドーム光で足す。"
           "雲は光を中で何度も散らすので、日の当たる上は白く、底は自分の影で灰色になる。",
           cap="明かりを置いた状態。", shot=False)
    g.hero(fluff, "Karma で撮った仕上がり。上は日差しで白く、底は影で灰色の積雲。", direction=(1.0, 0.1, 1.2),
           key=0.0, rim=0.0, dome=0.5, dome_color=(0.45, 0.62, 1.0), spp=64, margin=1.12,
           backdrop=(0.03, 0.07, 0.16), backdrop_reflect=0.0, denoise=True)

    # ---- 落とし穴を測る ----
    def filled(node):
        geo = node.geometry()
        total = 0
        for prim in geo.prims():
            if prim.type() == hou.primType.VDB and prim.attribValue("name") == "density":
                total += prim.activeVoxelCount()
        return total

    a = filled(vol)
    b = filled(fluff)
    bottom = flat.geometry().boundingBox().minvec()[1]
    flat.bypass(True)
    bottom_free = flat.geometry().boundingBox().minvec()[1]
    flat.bypass(False)
    more = "増えた" if b > a else ("減った" if b < a else "変わらなかった")
    traps = [
        {"title": "底は clip で平らにそろえる",
         "body": f"clip を外すと、いちばん下は高さ {bottom_free:.2f}（球が下へ出っぱる）。入れると {bottom:.2f} でそろった。"
                 "積雲らしさは平らな底で決まるので、底の高さは clip の Distance で決める。",
         "img": "", "cap": ""},
        {"title": "cloudnoise のあとの升の数",
         "body": f"cloud の出口で値の入った升は {a:,} 個、cloudnoise のあとは {b:,} 個（{more}）。"
                 "雲の大きさを変えたいときは、cloudnoise ではなく元の球の大きさで決める。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "9個（明かり1つ）"], ["升の分け方", "長い辺を160"]], traps=traps)


if __name__ == "__main__":
    main()
