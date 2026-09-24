# -*- coding: utf-8 -*-
"""実験240 — 211〜239 の振り返り点検。台本を全部流し直して、記録と突き合わせる（8 回目）。

やり方は実験210 と同じ（examples/210_audit.py の比べ方を使う）:
  1. out/NNN_*.json（記録。_report.json と _graph.json は除く）を控えに退避する
  2. examples/NNN_*.py を流し直す（記録が上書きされる）
  3. 新しい値と控えを、数字 1 つずつ比べる。時間の項目と、時間から出した値（倍率・百万画素あたりの秒など）は「時間」として分ける
  4. 控えを元に戻す（記録は変えない）
215（草の本数と Karma）は、流し直すと 1 条件で 13 分かかる条件を含むので外す。

    python examples/240_audit.py          （中で hython を呼ぶ。2〜3 時間）
    python examples/240_audit.py 219 221  （番号を選んで）
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
HYTHON = r"C:\Program Files\Side Effects Software\Houdini 21.0.700\bin\hython.exe"
PY = sys.executable
sys.path.insert(0, os.path.join(HERE, "examples"))
from importlib import import_module  # noqa: E402
_a180 = import_module("180_audit")
compare = _a180.compare
SKIP = {215}
TIME_WORDS = ("us_per", "_ms", "per_ms", "sec", "time", "first", "again", "per_mpx", "ratio_1080", "fixed")


def kind(no, key, old, new):
    k = key.lower()
    if old is None or new is None:
        return "add"
    if any(s in k for s in TIME_WORDS):
        return "time"
    return "value"


def summarize(no, diffs):
    counts = {"time": 0, "add": 0, "value": 0}
    worst = {"value": 0.0}
    for _f, key, old, new in diffs:
        kd = kind(no, key, old, new)
        counts[kd] += 1
        if kd == "value" and isinstance(old, (int, float)) and isinstance(new, (int, float)) and old:
            worst["value"] = max(worst["value"], abs(new / old - 1))
    return counts, worst


def plan(no):
    s = lambda name: os.path.join("examples", name)  # noqa: E731
    if no == 211:
        return [(s("211_vellum_cloth_thickness.py"), [], True)]
    if no == 220:
        f = s("220_pyro_turbulence_control.py")
        cmds = [(f, [c, r], True) for c in ("base", "ctrl", "free", "ctrl_on") for r in ("1", "2")]
        return cmds + [(s("_220_density.py"), [], True), (f, ["combine"], False)]
    if no == 222:
        return [(s("222_grass_cost_split.py"), [], True), (s("222_grass_lop.py"), [], True)]
    if no == 231:
        f = s("231_campfire_light.py")
        cmds = [(f, a, True) for a in (["fire", "0"], ["light", "1"], ["light", "4"], ["light", "12.07"], ["fire_light", "12.07"])]
        return cmds + [(s("reports_231.py"), [], False)]
    if no == 232:
        f = s("232_karma_xpu_scenes.py")
        return [(f, [g], True) for g in ("ocean_winter", "campfire", "glasscup", "snowman", "donut", "neon")] + [(f, ["combine"], False)]
    if no == 233:
        f = s("233_pyro_voxel_render.py")
        return [(f, [v], True) for v in ("0.08", "0.06", "0.04", "0.03", "0.02")] + [(f, ["combine"], False)]
    if no == 239:
        f = s("239_karma_resolution_time.py")
        return [(f, ["donut"], True), (f, ["ocean_winter"], True), (f, ["combine"], False)]
    script = [p for p in sorted(glob.glob(os.path.join(HERE, "examples", f"{no}_*.py")))]
    return [(os.path.relpath(script[0], HERE), [], True)] if script else []


def main():
    nos = [int(x) for x in sys.argv[1:]] or [n for n in range(211, 240) if n not in SKIP]
    path = os.path.join(OUT, "240_checks.json")
    results = []
    if os.path.exists(path) and sys.argv[1:]:
        with open(path, encoding="utf-8") as fp:
            results = [r for r in json.load(fp) if int(r["no"]) not in nos]
    for no in nos:
        tag = f"{no:03d}"
        records = [p for p in glob.glob(os.path.join(OUT, f"{tag}_*.json")) if not p.endswith(("_report.json", "_graph.json"))]
        cmds = plan(no)
        if not cmds or not records:
            results.append({"no": tag, "status": "記録か台本が無い", "records": [os.path.basename(r) for r in records]})
            print(results[-1], flush=True)
            continue
        backup = {r: r + ".audit_bak" for r in records}
        for src, dst in backup.items():
            shutil.copy2(src, dst)
        t0 = time.perf_counter()
        codes, errs = [], []
        for script, args, hy in cmds:
            proc = subprocess.run([HYTHON if hy else PY, script] + args, cwd=HERE, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
            codes.append(proc.returncode)
            if proc.returncode:
                errs.append(f"{script} {args}: {proc.stderr[-300:]}")
        sec = time.perf_counter() - t0
        compared, diffs = 0, []
        for src, dst in backup.items():
            with open(dst, encoding="utf-8") as fp:
                old = json.load(fp)
            try:
                with open(src, encoding="utf-8") as fp:
                    new = json.load(fp)
            except (OSError, ValueError):
                new = None
            n, d = compare(old, new) if new is not None else (0, [("(読めない)", None, None)])
            compared += n
            diffs += [(os.path.basename(src),) + x for x in d]
            shutil.move(dst, src)
        counts, worst = summarize(tag, diffs)
        results.append({"no": tag, "commands": len(cmds), "records": [os.path.basename(r) for r in records],
                        "returncodes": codes, "errors": errs, "values": compared, "diffs": diffs[:60], "n_diffs": len(diffs),
                        "sec": round(sec, 1), "kinds": counts, "worst": worst})
        print(tag, "値", compared, "ずれ", len(diffs), counts, f"{sec:.1f}秒", errs[:1], flush=True)
        results.sort(key=lambda r: r["no"])
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(results, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    sys.exit(main())
