# -*- coding: utf-8 -*-
"""実験150 — 122〜149 の振り返り点検。28本すべてを測り直して、記録と突き合わせる。

30件ごとの点検（030・060・090・121 に続いて5回目）。090 までは数件を選んで測り直したが、
091 からは実験の台本がどれも数秒で終わるので、30本全部を流し直す。

やり方:
  1. out/NNN_*.json（記録）を控えに退避する
  2. examples/NNN_*.py を hython で流し直す（記録が上書きされる）
  3. 新しい値と控えを、数字1つずつ比べる（時間の項目 sec などは除く）
  4. 控えを元に戻す（記録は変えない）

    python examples/150_audit.py        （中で hython を呼ぶ）
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
SKIP_KEYS = {"sec", "secs", "seconds", "time", "ms", "elapsed", "wall", "cook_sec"}
TOL = 1e-6


def leaves(obj, path=""):
    """JSON の中の数字と文字を (道筋, 値) で全部並べる。時間の項目は飛ばす。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in SKIP_KEYS or k.endswith("_sec") or k.startswith("sec_"):
                continue
            yield from leaves(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, obj


def compare(old, new):
    a, b = dict(leaves(old)), dict(leaves(new))
    diffs = []
    for key in sorted(set(a) | set(b)):
        x, y = a.get(key), b.get(key)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) \
                and not isinstance(x, bool):
            if abs(x - y) > TOL * max(1.0, abs(x)):
                diffs.append((key, x, y))
        elif x != y:
            diffs.append((key, x, y))
    return len(a), diffs


def main():
    results = []
    for no in range(122, 150):
        tag = f"{no:03d}"
        scripts = [p for p in glob.glob(os.path.join(HERE, "examples", f"{tag}_*.py"))]
        records = [p for p in glob.glob(os.path.join(OUT, f"{tag}_*.json"))
                   if not p.endswith("_report.json")]
        if not scripts or not records:
            results.append({"no": tag, "status": "記録か台本が無い", "script": scripts,
                            "records": [os.path.basename(r) for r in records]})
            print(results[-1])
            continue
        backup = {r: r + ".audit_bak" for r in records}
        for src, dst in backup.items():
            shutil.copy2(src, dst)
        t0 = time.perf_counter()
        proc = subprocess.run([HYTHON, scripts[0]], cwd=HERE, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
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
        results.append({"no": tag, "script": os.path.basename(scripts[0]),
                        "records": [os.path.basename(r) for r in records],
                        "returncode": proc.returncode, "values": compared,
                        "diffs": diffs[:20], "n_diffs": len(diffs), "sec": round(sec, 1)})
        print(tag, "値", compared, "ずれ", len(diffs), f"{sec:.1f}秒",
              "" if proc.returncode == 0 else proc.stderr[-300:])
    path = os.path.join(OUT, "150_checks.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(results, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    sys.exit(main())
