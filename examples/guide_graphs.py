"""手順ページ用に、各手順の最終的なノードグラフを書き出す。

各手順は作業のあと .hipnc を残している。それを読み直し、
中の SOP ネットワークの接続を JSON にする。あとは graph_report.py が
いつもと同じ見た目の図に描く。

    hython examples/guide_graphs.py <手順のid>
    hython examples/guide_graphs.py            … 一覧を出すだけ

1プロセスにつき1つだけ開く。hython は1プロセスで何度もシーンを
作り直すと固まるため（実験022以降の癖）。
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

GUIDES = os.path.join(HERE, "guides.json")


def load_guides():
    with open(GUIDES, encoding="utf-8") as fp:
        return json.load(fp)["guides"]


def main_network():
    """/obj の中の geo で、子ノードが一番多いものを選ぶ。

    型を geo に絞るのが肝心。レンダ用に作ったライトやカメラも /obj に
    ぶら下がっていて、中に子ノードを持つものがある（report_key など）。
    数だけで選ぶと、そちらを掴んでしまう。
    """
    best = None
    for child in hou.node("/obj").children():
        if child.type().name() != "geo":
            continue
        if not child.children():
            continue
        if best is None or len(child.children()) > len(best.children()):
            best = child
    return best


def main(guide_id):
    guides = {g["id"]: g for g in load_guides()}
    if guide_id not in guides:
        raise SystemExit(f"知らない手順: {guide_id}")
    guide = guides[guide_id]
    hip = os.path.join(OUT, guide["hip"])
    if not os.path.exists(hip):
        raise SystemExit(f"シーンが無い: {hip}")

    hou.hipFile.load(hip, suppress_save_prompt=True,
                     ignore_load_warnings=True)
    network = main_network()
    if network is None:
        raise SystemExit("ネットワークが見つからない")

    path = os.path.join(OUT, f"guide_{guide_id}_graph.json")
    hou_tools.write_graph(network.path(), path,
                          title=f"手順 — {guide['title']}")
    print(f"{guide_id}: {network.path()} "
          f"（{len(network.children())}ノード） → {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        for guide in load_guides():
            print(f"  {guide['id']:10s} {guide['hip']}")
    else:
        main(sys.argv[1])
