# -*- coding: utf-8 -*-
"""実験の台本を流し直して、シーンファイル（hip）とノードのつなぎ方の画だけを残す。

実験091 以降は測る台本（sop_bench）が hip を保存していなかった。記事の数値や画像を変えずに hip を足すため、
台本を動かすあいだ out/ への書き込みはすべて一時フォルダへ逃がし、レンダも止める。
台本が終わった時点のシーンを out/NNN_scene.hipnc に保存し、/obj の中のネットワークを out/NNN_graph.json にする（画は graph_report.py で別に作る。hython の中からは PIL が読めない）。
条件を振る台本では、最後に組んだ条件のシーンが残る。

    hython examples/hip_export.py 091
"""
import builtins
import glob
import os
import runpy
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))


def main():
    no = sys.argv[1]
    script = glob.glob(os.path.join(HERE, "examples", f"{no}_*.py"))[0]
    scratch = tempfile.mkdtemp(prefix=f"hip{no}_")
    real_open = builtins.open
    out_norm = os.path.normcase(os.path.abspath(OUT))

    def guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)) and any(m in mode for m in "wax"):
            path = os.path.abspath(os.fsdecode(file))
            if os.path.normcase(path).startswith(out_norm):
                file = os.path.join(scratch, os.path.basename(path))
        return real_open(file, mode, *args, **kwargs)

    builtins.open = guarded_open
    import hou
    import hou_tools
    hou_tools.render_preview = lambda *a, **k: None
    hou_tools.render_sequence = lambda *a, **k: []
    hou_tools.save_hip = lambda path: path
    real_save = hou.hipFile.save
    hou.hipFile.save = lambda *a, **k: None
    sys.argv = [script] + sys.argv[2:]
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit:
        pass
    finally:
        builtins.open = real_open
        hou.hipFile.save = real_save
    hip = os.path.join(OUT, f"{no}_scene.hipnc")
    real_save(hip)
    nets = [n for n in hou.node("/obj").children()]
    if nets:
        # いちばんノードの多いネットワークを画にする
        net = max(nets, key=lambda n: len(n.children()))
        import importlib
        importlib.reload(hou_tools)
        hou_tools.write_graph(net.path(), os.path.join(OUT, f"{no}_graph.json"), title=f"実験{no}")
    print("HIP", no, hip, os.path.getsize(hip))


if __name__ == "__main__":
    main()
