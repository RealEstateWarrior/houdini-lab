# -*- coding: utf-8 -*-
"""前に作った実践の hip を開いて、動き（pr_<id>_anim.mp4）だけを後から撮る（2026-09-23）。

    hython examples/pr_anim_add.py jelly 36 "キャプション" [node_path]

node_path を省くと、studio・report_・hero_ 以外の最初の geo の表示ノードを撮る。
カメラの枠は、最後のフレームの形と最初のフレームの形を合わせた箱で決める（動いてもはみ出さない）。
キャプションは out/_anim_caps.json に置き、practice_merge.py が guides.json に混ぜる。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402
import hou  # noqa: E402


def main():
    gid, last, cap = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    with open(os.path.join(kit.HERE, "guides.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    guide = next(g for g in data["guides"] if g["id"] == gid)
    hou.hipFile.load(os.path.join(kit.OUT, guide["hip"]), suppress_save_prompt=True, ignore_load_warnings=True)
    if len(sys.argv) > 4:
        node = hou.node(sys.argv[4])
    else:
        objs = [o for o in hou.node("/obj").children() if o.type().name() == "geo"
                and not o.name().startswith(("studio", "report_", "hero_")) and o.isDisplayFlagSet()]
        node = objs[0].displayNode()
    print("撮るノード:", node.path())
    hou.setFrame(1)
    box = node.geometry().boundingBox()
    for f in range(2, last + 1):
        hou.setFrame(f)
        b = node.geometry().boundingBox()
        box.enlargeToContain(b)
    if os.environ.get("ANIM_BOXFRAME"):
        # 粒が遠くまで散るものは、全フレームを合わせた枠だと小さく写る。決めたフレームの枠に合わせる
        hou.setFrame(int(os.environ["ANIM_BOXFRAME"]))
        box = node.geometry().boundingBox()
    g = kit.Guide.__new__(kit.Guide)
    g.id = gid
    g.shot_dir = (1.0, 0.62, 1.15)
    hou.setFrame(1)
    g.anim(node, (1, last), cap, bbox=box, every=int(os.environ.get("ANIM_EVERY", "1")),
           keep_color=not os.environ.get("ANIM_NOCD"))
    # guides.json はほかの作業と同時に書き換えないよう、キャプションは別の小さなファイルに置く
    caps_path = os.path.join(kit.OUT, "_anim_caps.json")
    caps = json.load(open(caps_path, encoding="utf-8")) if os.path.exists(caps_path) else {}
    caps[gid] = cap
    with open(caps_path, "w", encoding="utf-8") as fp:
        json.dump(caps, fp, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
