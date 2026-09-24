# -*- coding: utf-8 -*-
"""実験210 — 181〜209 の振り返り点検。台本を全部流し直して、記録と突き合わせる。

30件ごとの点検（030・060・090・121・150・180 に続いて7回目）。やり方は実験180 と同じ:
  1. out/NNN_*.json（記録。_report.json と、つなぎ方の図の _graph.json は除く）を控えに退避する
  2. examples/NNN_*.py を流し直す（記録が上書きされる）
  3. 新しい値と控えを、数字1つずつ比べる（時間の項目 sec などは除く）
  4. 控えを元に戻す（記録は変えない）
180 と違うのは、200 から台本が「条件ごとに 1 プロセス」になったこと。条件の一覧は、記録の部分ファイル（NNN_part_*.json）の名前から作る。

    python examples/210_audit.py          （中で hython を呼ぶ。1 時間ほどかかる）
    python examples/210_audit.py 200 201  （番号を選んで）
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
SKIP_KEYS = {"sec", "secs", "seconds", "time", "ms", "elapsed", "wall", "cook_sec", "first", "cook_ms"}
TOL = 1e-6

sys.path.insert(0, os.path.join(HERE, "examples"))
from importlib import import_module  # noqa: E402
_a180 = import_module("180_audit")
leaves, compare = _a180.leaves, _a180.compare


def kind(no, key, old, new):
    """ずれの種類: 時間・ファイルの大きさ・項目の追加・値（reports_210.py と同じ分け方）。"""
    k = key.lower()
    if old is None or new is None:
        return "add"
    if any(s in k for s in ("us_per", "_ms", "per_ms", "sec", "time", "first")):
        return "time"
    if no in ("204", "209") and any(s in k for s in ("sizes", "vdbfile", "per_frame")):
        return "file"
    return "value"


def summarize(no, diffs):
    counts = {"time": 0, "file": 0, "add": 0, "value": 0}
    worst = {"file": 0.0, "value": 0.0}
    for _f, key, old, new in diffs:
        kd = kind(no, key, old, new)
        counts[kd] += 1
        if kd in worst and isinstance(old, (int, float)) and isinstance(new, (int, float)) and old:
            worst[kd] = max(worst[kd], abs(new / old - 1))
    return counts, worst


def parts(no, prefix="part_"):
    return sorted(os.path.basename(p)[len(f"{no}_{prefix}"):-5] for p in glob.glob(os.path.join(OUT, f"{no}_{prefix}*.json")))


def plan(no):
    """番号 → 流すコマンドの並び（台本, 引数, hython か）。"""
    s = lambda name: os.path.join("examples", name)  # noqa: E731
    if no == 200:
        f = s("200_flip_dambreak_res.py")
        cmds = [(f, [f"{int(p) / 1000:g}"], True) for p in parts(200)]
        cmds += [(f, [f"{int(p) / 1000:g}", "short"], True) for p in parts(200, "short_part_")]
        cmds += [(f, [f"{int(p) / 1000:g}", "noreseed"], True) for p in parts(200, "noreseed_part_")]
        return cmds + [(f, ["combine"], True)]
    if no == 201:
        f = s("201_pyro_flame_height.py")
        return [(f, [c], True) for c in parts(201)] + [(f, ["combine"], True)]
    if no == 202:
        f = s("202_pyro_campfire_cost.py")
        return [(f, [c], True) for c in parts(202)] + [(f, ["combine"], True)]
    if no == 204:
        f = s("204_pyro_cache_size.py")
        return [(f, ["0.04"], True), (f, ["0.02"], True), (f, ["combine"], False)]
    if no == 205:
        f = s("205_karma_dof_mblur_cost.py")
        return [(f, [], True), (f, ["strong"], True), (f, ["tune"], True), (f, ["combine"], False)]
    if no == 206:
        return [(s("206_vellum_cloth_preview_res.py"), [], True)]
    if no == 207:
        f = s("207_karma_fire_steprate.py")
        return [(f, ["0.03"], True), (f, ["0.06"], True), (f, ["0.03", "extra"], True), (f, ["combine"], False)]
    script = sorted(glob.glob(os.path.join(HERE, "examples", f"{no}_*.py")))
    return [(os.path.relpath(script[0], HERE), [], True)] if script else []


def main():
    nos = [int(x) for x in sys.argv[1:]] or list(range(181, 210))
    path = os.path.join(OUT, "210_checks.json")
    results = []
    if os.path.exists(path) and sys.argv[1:]:
        with open(path, encoding="utf-8") as fp:
            results = [r for r in json.load(fp) if int(r["no"]) not in nos]
    for no in nos:
        tag = f"{no:03d}"
        records = [p for p in glob.glob(os.path.join(OUT, f"{tag}_*.json"))
                   if not p.endswith(("_report.json", "_graph.json"))]
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
            shutil.move(dst, src)               # 記録は元に戻す
        counts, worst = summarize(tag, diffs)
        results.append({"no": tag, "commands": len(cmds), "records": [os.path.basename(r) for r in records],
                        "returncodes": codes, "errors": errs, "values": compared,
                        "diffs": diffs[:40], "n_diffs": len(diffs), "sec": round(sec, 1),
                        "kinds": counts, "worst": worst,
                        "per_file": {os.path.basename(src): sum(1 for x in diffs if x[0] == os.path.basename(src) and kind(tag, x[1], x[2], x[3]) == "value")
                                     for src in backup}})
        print(tag, "値", compared, "ずれ", len(diffs), f"{sec:.1f}秒", errs[:1], flush=True)
        results.sort(key=lambda r: r["no"])
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(results, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    sys.exit(main())
