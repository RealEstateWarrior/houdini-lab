"""実験021の連番を撮る。1条件につき1プロセス。

同じ hython の中で2条件目を作ろうとすると止まる（CPUを使わないまま10分以上）。
hipFile.clear() のあとに ROP が残っているのが原因と見ている。
プロセスを分ければ確実なので、そうする。

    hython examples/021_frames.py heat       … 温度あり。ここで箱を決めて保存する
    hython examples/021_frames.py density    … 温度なし。保存された箱で撮る
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

EXPERIMENT = os.path.join(HERE, "examples", "021_smoke_structure.py")
namespace = {"__name__": "notmain", "__file__": EXPERIMENT}
exec(compile(open(EXPERIMENT, encoding="utf-8").read(), EXPERIMENT, "exec"), namespace)
build = namespace["build"]
CASES = namespace["CASES"]

FRAMES = list(range(2, 49, 3))
BBOX_FILE = os.path.join(OUT, "021_bbox.json")


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "heat"
    geo, solver = build(**CASES[case])

    if case == "heat":
        hou.setFrame(FRAMES[-1])
        bbox = hou_tools.bbox_over_frames(solver.path(), [FRAMES[-1]])
        low, high = bbox.minvec(), bbox.maxvec()
        with open(BBOX_FILE, "w", encoding="utf-8") as fp:
            json.dump({"min": list(low), "max": list(high)}, fp)
        print("箱を保存:", list(low), list(high))
    else:
        with open(BBOX_FILE, encoding="utf-8") as fp:
            saved = json.load(fp)
        bbox = hou.BoundingBox(*saved["min"], *saved["max"])
        print("保存された箱を使う")

    paths = hou_tools.render_sequence(solver.path(), OUT, f"021f_{case}", FRAMES,
                                      res=(360, 460), shading="smooth",
                                      frame_bbox=bbox)
    print(f"{case}: {len(paths)}枚")


if __name__ == "__main__":
    main()
