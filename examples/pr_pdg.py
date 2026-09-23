# -*- coding: utf-8 -*-
"""実践「PDG で形違いを一度に書き出す」— 1つの石の作り方から、形の違う石を何個も自動で書き出す（TOPs の wedge）。

本物の制作では、同じ作り方で「少しずつ違う物」をたくさん用意したいことが多い（岩・木・建物）。
PDG（TOP ネットワーク）の wedge は、番号を変えながら同じ処理を何回も回し、それぞれの結果をファイルに書き出す。

    hython examples/pr_pdg.py
"""
import glob
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

COUNT = 5


def main():
    import hou
    g = kit.Guide("pdg", "PDG で形違いを一度に書き出す",
                  "石の作り方を1つ組み、乱数のずらしを「wedge の番号」で変える式にしておく。TOP ネットワークの wedge で番号 0〜4 の"
                  "5つの作業を作り、ropgeometry で1つずつファイルに書き出す。手で5回やり直す代わりに、1回の実行で5個の石ができる。",
                  tags=["PDG", "TOPs", "ツール", "Karma"])
    hou.hipFile.setName(os.path.join(kit.OUT, "pr_pdg.hipnc").replace("\\", "/"))   # $HIP を out/ にする
    g.shot_dir = (1.0, 0.5, 1.2)
    base = g.node("sphere", "base", type="polymesh", rows=40, cols=80, rad=(0.5, 0.35, 0.42))
    big = g.node("mountain::2.0", "big_lumps", [base], height=0.22, elementsize=0.55, rough=0.45)
    big.parmTuple("offset")[0].setExpression("@wedgeindex * 7.31")
    big.parmTuple("offset")[1].setExpression("@wedgeindex * 3.17")
    fine = g.node("mountain::2.0", "fine_detail", [big], height=0.03, elementsize=0.08, rough=0.6, oct=6)
    rock = g.node("normal", "rock_out", [fine])
    g.step(rock, "石の作り方を組み、ずらしを番号の式にする",
           "つぶれた <code>sphere</code> に <code>mountain</code> を2つ重ねて石にする（実践「岩を作る」と同じ考え方）。"
           "1つ目の mountain の <strong>Offset</strong>（ノイズをずらす量）に、式 <strong>@wedgeindex * 7.31</strong> を入れる。"
           "@wedgeindex は、あとで PDG が作る作業の番号（0, 1, 2, …）。番号が変わるとノイズの場所がずれて、別の形の石になる。"
           "PDG の外で見ると番号は 0 なので、今は0番の石が見えている。",
           cap="0番の石。", shading="smooth", ui_parm="offset")

    top = g.geo.parent().createNode("topnet", "make_rocks")
    wedge = top.createNode("wedge", "five_variants")
    wedge.parm("wedgecount").set(COUNT)
    wedge.parm("wedgeattributes").set(0)
    write = top.createNode("ropgeometry", "write_rock")
    write.setFirstInput(wedge)
    write.parm("soppath").set(rock.path())
    write.parm("sopoutput").set("$HIP/pr_pdg_geo/rock_`@wedgeindex`.bgeo.sc")
    top.layoutChildren()
    for old in glob.glob(os.path.join(kit.OUT, "pr_pdg_geo", "*.bgeo.sc")):
        os.remove(old)
    # ropgeometry の作業は、別の Houdini（hython）が「保存された hip」を開いて行う。保存しないと何も書き出されなかった
    hou.hipFile.save()
    t0 = time.perf_counter()
    write.cookWorkItems(block=True)
    cook_sec = time.perf_counter() - t0
    files = sorted(glob.glob(os.path.join(kit.OUT, "pr_pdg_geo", "rock_*.bgeo.sc")))
    g.step(write, "wedge で番号を作り、1つずつ書き出す",
           "<code>topnet</code>（TOP ネットワーク）の中に <code>wedge</code> を置き、<strong>Wedge Count を 5</strong> にする。"
           "番号 0〜4 の5つの「作業」ができる（属性は足さなくてよい。番号 @wedgeindex は自動で付く）。"
           "後ろに <code>ropgeometry</code> をつなぎ、SOP Path に石の最後のノード、Output File に "
           "<strong>$HIP/pr_pdg_geo/rock_`@wedgeindex`.bgeo.sc</strong> と書く（番号がファイル名に入る）。"
           f"ropgeometry を右クリック → Cook Node で実行すると、{len(files)} 個のファイルが {cook_sec:.1f} 秒で書き出された。",
           cap="", shot=False, ui_parm="sopoutput")
    print("書き出し", len(files), "個", cook_sec)

    loaded = []
    for i, path in enumerate(files):
        f = g.node("file", f"rock_{i}", file=f"$HIP/pr_pdg_geo/{os.path.basename(path)}")
        loaded.append(g.node("xform", f"place_{i}", [f], t=((i - (len(files) - 1) / 2) * 1.15, 0, (i % 2) * 0.35)))
    row = g.node("merge", "row_of_rocks", loaded)
    sit = row
    g.step(sit, "書き出した石を並べて読み込む",
           f"<code>file</code> を {len(files)} 個置いて、書き出した bgeo.sc をそれぞれ読み込み、<code>xform</code> で横に並べる。"
           "同じ作り方から、形の違う石が並ぶ。",
           cap=f"{len(files)} 個の違う石。", shading="smooth")
    stone = g.mat("rock_mat", basecolor=(0.3, 0.28, 0.25), rough=0.85)
    final = g.assign(sit, stone, "assign_rock")
    g.hero(final, "Karma で撮った仕上がり。1回の実行で書き出した、形の違う5つの石。", direction=(0.3, 0.45, 1.2),
           key=3.2, rim=5.0, dome=0.4, spp=48, margin=1.05, backdrop=(0.16, 0.17, 0.18))

    # ---- 落とし穴を測る ----
    sizes = [os.path.getsize(p) // 1024 for p in files]
    same_dir = os.path.join(kit.OUT, "pr_pdg_same")
    for old in glob.glob(os.path.join(same_dir, "*")):
        os.remove(old)
    write.parm("sopoutput").set("$HIP/pr_pdg_same/rock.bgeo.sc")
    hou.hipFile.save()
    write.dirtyAllWorkItems(False)
    write.cookWorkItems(block=True)
    n_same = len(glob.glob(os.path.join(same_dir, "*.bgeo.sc")))
    write.parm("sopoutput").set("$HIP/pr_pdg_geo/rock_`@wedgeindex`.bgeo.sc")
    traps = [
        {"title": "ファイル名に番号を入れないと、上書きされる",
         "body": f"Output File を番号なしの rock.bgeo.sc にして実行すると、5つの作業が同じ名前に書き、残ったファイルは {n_same} 個だった。"
                 "<code>`@wedgeindex`</code> を名前に入れて、作業ごとに別のファイルにする。",
         "img": "", "cap": ""},
        {"title": "実行する前に hip を保存する",
         "body": "ropgeometry の作業は、裏で別の Houdini が起動し、ディスクに保存された hip を開いて行う。"
                 "hip を一度も保存しないまま Cook すると、エラーも出ずに1つも書き出されなかった。変えたら保存してから Cook する。",
         "img": "", "cap": ""},
        {"title": "書き出したファイルの大きさ",
         "body": f"5つの bgeo.sc は {'・'.join(str(s) for s in sizes)} KB。形が違っても、点と面の数は同じなので大きさはほぼそろう。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "石4個・TOP 2個・読み込み10個"], ["書き出し", f"{len(files)}個・{cook_sec:.1f}秒"]], traps=traps)


if __name__ == "__main__":
    main()
