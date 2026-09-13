"""起動中の Houdini GUI を操作して、実物のスクリーンショットを撮る。

自動生成の接続図と違い、これは本物の Houdini の画面なので、
「自分の Houdini で同じものを見るにはどうすればいいか」がそのまま分かる。

前提: Houdini GUI で bridge_server.start() を実行しておくこと。

実行は Houdini 同梱の Python で（rpyc が入っているため）:
    "C:/Program Files/Side Effects Software/Houdini 21.0.700/python311/python.exe"
        gui_capture.py out/008_scatter_copy.hipnc /obj/scatter_copy copy_oriented 008

UI の操作は必ず Houdini のメインスレッドで行う必要がある。RPC の呼び出しは
別スレッドで走るので、hdefereval.executeDeferred でメインスレッドに渡し、
完了を待ってから次に進む。これをしないと無視されるか落ちる。
"""

import os
import subprocess
import sys
import textwrap
import time

import rpyc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CAPTURE = os.path.join(HERE, "capture_window.ps1")
PORT = 18811

WRAPPER = """
import threading
import traceback
import hdefereval

_done = threading.Event()
_err = [None]


def _job():
    try:
{body}
    except Exception:
        _err[0] = traceback.format_exc()
    finally:
        _done.set()


hdefereval.executeDeferred(_job)
_done.wait({timeout})
"""


def connect(host="127.0.0.1", port=PORT):
    conn = rpyc.classic.connect(host, port)
    conn._config["sync_request_timeout"] = None
    return conn


def run_in_houdini(conn, code, timeout=120):
    """Houdini のメインスレッドでコードを実行し、例外があれば文字列で返す。"""
    body = textwrap.indent(textwrap.dedent(code).strip(), " " * 8)
    conn.execute(WRAPPER.format(body=body, timeout=timeout))
    error = conn.eval("_err[0]")
    if error:
        raise RuntimeError(f"Houdini 側でエラー:\n{error}")
    if not conn.eval("_done.is_set()"):
        raise RuntimeError("Houdini 側の処理が時間内に終わらなかった")


def capture(out_png):
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", CAPTURE,
         "-Out", out_png],
        cwd=HERE, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"キャプチャ失敗:\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def load_scene(conn, hip_path):
    run_in_houdini(conn, f"""
        import hou
        hou.hipFile.load({os.path.abspath(hip_path)!r}, suppress_save_prompt=True)
    """)


def show_network(conn, network_path):
    """ネットワークエディタを目的の階層に合わせ、全体が入るようにする。

    ペインの拡大と枠合わせは別々に投げる。同じ処理の中で続けて呼ぶと、
    拡大後の大きさがまだ反映されておらず、狭いままの寸法で枠が計算されて
    ノードが画面外にはみ出す。"""
    run_in_houdini(conn, f"""
        import hou
        node = hou.node({network_path!r})
        if node is None:
            raise ValueError("そのネットワークがない: " + {network_path!r})
        editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        if editor is None:
            desktop = hou.ui.curDesktop()
            editor = desktop.createFloatingPaneTab(hou.paneTabType.NetworkEditor)
        editor.setPwd(node)
        editor.setIsCurrentTab()
        pane = editor.pane()
        if pane is not None:
            pane.setIsMaximized(True)
    """)
    time.sleep(0.8)                      # ペインの大きさが確定するのを待つ
    run_in_houdini(conn, f"""
        import hou
        node = hou.node({network_path!r})
        editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        # NetworkEditor に「全体を表示」はない。全部選んでから選択範囲に合わせる。
        for child in node.children():
            child.setSelected(True, clear_all_selected=False)
        editor.homeToSelection()
        for child in node.children():
            child.setSelected(False)
    """)


def show_parameters(conn, node_path):
    """パラメータペインに対象ノードを表示する。

    ここでは拡大しない。ビューポートと並んだ標準のレイアウトのままの方が、
    「結果」と「そのときの設定」が1枚に収まって分かりやすいため。"""
    run_in_houdini(conn, f"""
        import hou
        node = hou.node({node_path!r})
        if node is None:
            raise ValueError("そのノードがない: " + {node_path!r})
        node.setCurrent(True, clear_all_selected=True)
        parm_pane = hou.ui.paneTabOfType(hou.paneTabType.Parm)
        if parm_pane is None:
            desktop = hou.ui.curDesktop()
            parm_pane = desktop.createFloatingPaneTab(hou.paneTabType.Parm)
        parm_pane.setCurrentNode(node)
        parm_pane.setIsCurrentTab()
    """)


def restore_layout(conn):
    run_in_houdini(conn, """
        import hou
        for tab in hou.ui.curDesktop().paneTabs():
            pane = tab.pane()
            if pane is not None and pane.isMaximized():
                pane.setIsMaximized(False)
    """)


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        return 1

    hip_path, network_path, node_name, prefix = sys.argv[1:5]
    node_path = f"{network_path}/{node_name}"

    conn = connect()
    print("接続しました")

    load_scene(conn, hip_path)
    print(f"読み込み: {hip_path}")

    show_network(conn, network_path)
    time.sleep(2.5)                      # 再描画を待つ（OpenGLのペインは遅れる）
    network_png = os.path.join(OUT, f"{prefix}_ui_network.png")
    print(capture(network_png))

    restore_layout(conn)                 # 拡大を戻してから標準レイアウトで撮る
    show_parameters(conn, node_path)
    time.sleep(2.5)
    parms_png = os.path.join(OUT, f"{prefix}_ui_parms.png")
    print(capture(parms_png))

    print("完了")
    return 0


if __name__ == "__main__":
    sys.exit(main())
