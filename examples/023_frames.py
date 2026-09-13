"""実験023の連番。1条件ずつ別プロセスで動かす。

    hython examples/023_frames.py fire        … ここで箱を決めて保存する
    hython examples/023_frames.py fire_shred  … 保存された箱で撮る
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

EXPERIMENT = os.path.join(HERE, "examples", "023_fire.py")
namespace = {"__name__": "notmain", "__file__": EXPERIMENT}
exec(compile(open(EXPERIMENT, encoding="utf-8").read(), EXPERIMENT, "exec"), namespace)
build = namespace["build"]
CASES = namespace["CASES"]

FRAMES = list(range(2, 45, 3))
BBOX_FILE = os.path.join(OUT, "023_bbox.json")


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "fire"
    geo, solver, made = build(**CASES[case])

    if case == "fire":
        hou.setFrame(FRAMES[-1])
        bbox = hou_tools.bbox_over_frames(solver.path(), [FRAMES[-1]])
        with open(BBOX_FILE, "w", encoding="utf-8") as fp:
            json.dump({"min": list(bbox.minvec()), "max": list(bbox.maxvec())}, fp)
        print("箱を保存:", list(bbox.minvec()), list(bbox.maxvec()))
    else:
        with open(BBOX_FILE, encoding="utf-8") as fp:
            saved = json.load(fp)
        bbox = hou.BoundingBox(*saved["min"], *saved["max"])

    paths = hou_tools.render_sequence(solver.path(), OUT, f"023f_{case}", FRAMES,
                                      res=(340, 460), shading="smooth",
                                      frame_bbox=bbox)
    print(f"{case}: {len(paths)}枚")


if __name__ == "__main__":
    main()
