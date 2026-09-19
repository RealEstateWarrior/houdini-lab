"""手順ページ用に、各段階のノードを選んだ状態の Houdini 画面を撮る。

guide_ui_capture.py はネットワーク全体を1枚撮る。こちらは手順の1段ごとに、
その段で使うノードを選んだ状態で撮る。標準のレイアウトのまま撮るので、
1枚に「ネットワークのどこか」「そのときの結果（ビューポート）」
「そのときのパラメータ」が並ぶ。

段とノードの対応は guides.json の step["node"] から決める。
ノードの型名（attribwrangle など）ならその型のノードを、
パラメータ名（materialtype など）ならそのパラメータを持つノードを選ぶ。

前提: Houdini GUI で bridge_server.start() を実行しておくこと。
実行は Houdini 同梱の Python で:
    "C:/Program Files/Side Effects Software/Houdini 21.0.700/python311/python.exe"
        guide_parm_capture.py all
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gui_capture  # noqa: E402
from guide_ui_capture import load_guides, main_network  # noqa: E402

OUT = os.path.join(HERE, "out")
MAP_PATH = os.path.join(OUT, "guide_parm_map.json")


def pick_node(conn, network, wanted, used):
    """段の node 欄から、実際に選ぶノードの path を返す。見つからなければ None。

    同じ型が複数あるときは、まだ使っていないものを上から順に使う
    （Vellum の constraints が2つある手順など）。"""
    gui_capture.run_in_houdini(conn, f"""
        import hou
        global _picked
        net = hou.node({network!r})
        # 手順には「copy to points」のように空白入りで書いてある。型名は copytopoints
        wanted = {wanted!r}.lower().replace(" ", "")
        used = set({sorted(used)!r})
        top = sorted(net.children(), key=lambda n: -n.position()[1])
        # 中の階層は、同じ階層に無いときだけ探す（popsolver は DOP の中にしかない）。
        # 先に中まで混ぜると、mpmsolver の中身のように HDA の内部を拾ってしまう
        sub = [n for n in net.allSubChildren() if n.parent() != net]

        def by_type(nodes):
            return [n for n in nodes
                    if n.type().name().lower() == wanted
                    or n.type().name().lower().startswith(wanted + "::")
                    or n.type().name().lower().split("::")[-1] == wanted]

        def by_parm(nodes):
            return [n for n in nodes
                    if n.parm(wanted) is not None or n.parmTuple(wanted) is not None]

        pick = None
        for pool in (top, sub):
            hits = by_type(pool) or by_parm(pool)
            if hits:
                fresh = [n for n in hits if n.path() not in used]
                pick = (fresh or hits)[0]
                break
        _picked = pick.path() if pick is not None else None
    """)
    return conn.eval("_picked")


def show_standard(conn, network):
    """最大化を解いた標準レイアウトで、ネットワークを目的の階層に合わせる。"""
    gui_capture.restore_layout(conn)
    time.sleep(0.6)
    gui_capture.run_in_houdini(conn, f"""
        import hou
        net = hou.node({network!r})
        editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        editor.setPwd(net)
        editor.setIsCurrentTab()
        for child in net.children():
            child.setSelected(True, clear_all_selected=False)
        editor.homeToSelection()
        for child in net.children():
            child.setSelected(False)
        # ビューポートは前のシーンの寄り方のまま残るので、全体に合わせ直す
        viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
        if viewer is not None:
            viewer.curViewport().frameAll()
    """)


def refresh(conn):
    gui_capture.run_in_houdini(conn, """
        import hou
        hou.ui.setUpdateMode(hou.updateMode.AutoUpdate)
        hou.ui.triggerUpdate()
    """)


def shoot_guide(conn, guide, record):
    hip = guide.get("hip") or ""
    path = os.path.join(OUT, hip)
    if not hip or not os.path.isfile(path):
        print(f"  シーンが無いので飛ばす: {guide['id']}")
        return 0

    gui_capture.load_scene(conn, path)
    network = main_network(conn)
    if not network:
        print("  ネットワークが見つからない")
        return 0
    show_standard(conn, network)

    used = set()
    shots = 0
    first = True
    for index, step in enumerate(guide.get("steps", []), start=1):
        wanted = (step.get("node") or "").strip()
        if not wanted:
            continue
        # 同じ名前のパラメータを持つノードが複数あるときは、guides.json の
        # ui_node（ネットワーク内のノード名）で写すノードを指定する。
        # /obj のライトや /out の出力ノードのように外にあるものは、/ から書く
        if step.get("ui_node"):
            ui = step["ui_node"]
            node = ui if ui.startswith("/") else f"{network}/{ui}"
        else:
            node = pick_node(conn, network, wanted, used)
        if not node:
            print(f"  {index}: {wanted} に当たるノードが無い")
            continue
        used.add(node)
        # 段がパラメータ名（groundfriction など）なら、それが入っているタブを開く。
        # 開かないと最初のタブが写り、肝心のパラメータが画面に無い
        focus = step.get("ui_parm") or wanted   # 開いて見せたいパラメータ
        gui_capture.run_in_houdini(conn, f"""
            import hou
            node = hou.node({node!r})
            parm = node.parm({focus!r}) or (node.parmTuple({focus!r}) or [None])[0]
            if parm is not None and {bool(step.get("ui_parm"))!r}:
                # 見せたい項目が下のほうにあるときは、関係のない折りたたみ欄を閉じて上へ寄せる
                mine = set(t.name() for t in parm.containingFolderSetParmTuples())
                for tup in node.parmTuples():
                    tmpl = tup.parmTemplate()
                    if (tmpl.type() == hou.parmTemplateType.FolderSet
                            and tup.name() not in mine
                            and tmpl.folderType() == hou.folderType.Collapsible):
                        tup[0].set(0)
            if parm is not None:
                sets = parm.containingFolderSetParmTuples()
                for tup, index in zip(sets, parm.containingFolderIndices()):
                    # タブは「何番目を開くか」、折りたたみ欄は「開く＝1」。
                    # 折りたたみ欄に番号の 0 を入れると閉じてしまう（Sequence が閉じて写った）
                    kind = tup.parmTemplate().folderType()
                    if kind in (hou.folderType.Collapsible, hou.folderType.Simple):
                        tup[0].set(1)
                    else:
                        tup[0].set(index)
        """)
        gui_capture.show_parameters(conn, node)
        refresh(conn)
        if step.get("ui_parm"):
            # 下のほうにある項目は、パラメータ欄をそこまでスクロールしてから撮る
            gui_capture.run_in_houdini(conn, f"""
                import hou
                pane = hou.ui.paneTabOfType(hou.paneTabType.Parm)
                pane.scrollTo({focus!r})
            """)
            refresh(conn)
        time.sleep(2.0)                     # ビューポートとパラメータの描き直し待ち
        png = os.path.join(OUT, f"guide_{guide['id']}_p{index}.png")
        if first:
            gui_capture.capture(png)        # 1枚目は窓を前に出すための捨て撮り
            time.sleep(1.2)
            first = False
        gui_capture.capture(png)
        record.setdefault(guide["id"], {})[str(index)] = {
            "node": node, "wanted": wanted, "png": os.path.basename(png)}
        print(f"  {index}: {wanted:22s} -> {node}")
        shots += 1
    return shots


def main():
    guides = load_guides()
    wanted = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = guides if wanted == "all" else [g for g in guides if g["id"] == wanted]

    record = {}
    if os.path.exists(MAP_PATH):
        with open(MAP_PATH, encoding="utf-8") as fp:
            record = json.load(fp)

    conn = gui_capture.connect()
    print("接続しました")
    total = 0
    for guide in targets:
        print(f"{guide['id']}: {guide.get('hip') or '(シーンなし)'}")
        try:
            total += shoot_guide(conn, guide, record)
        except Exception as error:          # 1本こけても残りは撮る
            print(f"  失敗: {error}")
        with open(MAP_PATH, "w", encoding="utf-8") as fp:
            json.dump(record, fp, ensure_ascii=False, indent=2)
    gui_capture.restore_layout(conn)
    print(f"完了: {total} 枚")
    return 0


if __name__ == "__main__":
    sys.exit(main())
