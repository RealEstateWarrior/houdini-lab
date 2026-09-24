"""手順ページ用に、本物の Houdini 画面でノードグラフを撮る。

自動生成の接続図と違い、これは実際のネットワークエディタの画面なので、
「自分の Houdini で同じものを見たらこう見える」がそのまま分かる。

前提: Houdini GUI で bridge_server.start() を実行しておくこと。

実行は Houdini 同梱の Python で（rpyc が入っているため）:
    "C:/Program Files/Side Effects Software/Houdini 21.0.700/python311/python.exe"
        guide_ui_capture.py grow
    引数なしで一覧を出す。all ですべて撮る。
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gui_capture  # noqa: E402

OUT = os.path.join(HERE, "out")
GUIDES = os.path.join(HERE, "guides.json")


def load_guides():
    with open(GUIDES, encoding="utf-8") as fp:
        guides = json.load(fp)["guides"]
    # 同じページに載せた「もう一つの版」（variants）も、1 本の実践として撮る
    return guides + [v for g in guides for v in g.get("variants", [])]


def main_network(conn):
    """/obj の中の geo で、子ノードが一番多いものの path を返す。

    型を geo に絞るのが肝心。レンダ用のライトやカメラも /obj にいて、
    中に子ノードを持つものがある（report_key など）。
    数だけで選ぶとそちらを掴む。
    """
    # 実行されるコードは関数の中に入るので、そのまま代入すると
    # ローカル変数になり、あとから conn.eval で読めない。global で外に出す。
    gui_capture.run_in_houdini(conn, """
        import hou
        global _picked
        best = None
        for child in hou.node("/obj").children():
            if child.type().name() != "geo":
                continue
            if not child.children():
                continue
            if best is None or len(child.children()) > len(best.children()):
                best = child
        _picked = best.path() if best is not None else ""
    """)
    return conn.eval("_picked")


def shoot(conn, guide):
    hip = os.path.join(OUT, guide["hip"])
    if not os.path.exists(hip):
        print(f"  シーンが無い: {hip}")
        return False

    gui_capture.load_scene(conn, hip)
    path = main_network(conn)
    if not path:
        print("  ネットワークが見つからない")
        return False

    gui_capture.show_network(conn, path)
    # Houdini は前面に無いあいだ描き直しを間引く。放っておくと、
    # 画面には前のシーンが残ったままになり、そのまま写る。
    gui_capture.run_in_houdini(conn, """
        import hou
        hou.ui.setUpdateMode(hou.updateMode.AutoUpdate)
        hou.ui.triggerUpdate()
    """)
    time.sleep(3.0)                      # 再描画を待つ（OpenGLのペインは遅れる）

    png = os.path.join(OUT, f"guide_{guide['id']}_ui.png")
    # 1回目は捨てる。撮影がウィンドウを前面に出すので、それで初めて
    # 描き直しが走る。1回だけだと、前のシーンの画がそのまま写ることがある。
    gui_capture.capture(png)
    time.sleep(1.5)
    print(" ", gui_capture.capture(png))
    return True


def main():
    guides = load_guides()
    if len(sys.argv) < 2:
        for guide in guides:
            print(f"  {guide['id']:10s} {guide['hip']}")
        return 0

    wanted = sys.argv[1]
    targets = guides if wanted == "all" else \
        [g for g in guides if g["id"] == wanted]
    if not targets:
        print(f"知らない手順: {wanted}")
        return 1

    conn = gui_capture.connect()
    print("接続しました")
    for guide in targets:
        print(f"{guide['id']}: {guide['hip']}")
        shoot(conn, guide)
    gui_capture.restore_layout(conn)
    print("完了")
    return 0


if __name__ == "__main__":
    sys.exit(main())
