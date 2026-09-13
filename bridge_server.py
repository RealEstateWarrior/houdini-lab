"""Start an RPC bridge inside a running Houdini GUI session.

hython だけで実験は回せるが、スクリーンショットを撮るには GUI を操作する必要が
あるため、外部から Houdini の UI を触れる口を開ける。

使い方: Houdini の Windows > Python Source Editor に貼って実行する。

    import sys
    sys.path.append("D:/Claude/houdini")
    import bridge_server
    print(bridge_server.start())

Houdini 同梱の hrpyc.start_server() は 0.0.0.0 にバインドする（＝LAN内の誰でも
任意のコードを実行できる）ため、127.0.0.1 固定のこちらを使う。
"""

import threading

import rpyc
from rpyc.core import SlaveService
from rpyc.utils.server import ThreadedServer

PORT = 18811

_state = {}


def start(port=PORT):
    if _state.get("server"):
        return f"bridge already running on 127.0.0.1:{_state['port']}"

    server = ThreadedServer(
        SlaveService,
        hostname="127.0.0.1",
        port=port,
        reuse_addr=True,
        authenticator=None,
        registrar=None,
        auto_register=False,
    )
    server.logger.quiet = True
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    _state.update(server=server, thread=thread, port=port)
    return f"bridge listening on 127.0.0.1:{port}"


def stop():
    server = _state.pop("server", None)
    if server is None:
        return "bridge not running"
    server.close()
    _state.clear()
    return "bridge stopped"


if __name__ == "__main__":
    print(start())
