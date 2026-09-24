# -*- coding: utf-8 -*-
"""実験246 — ガラスの割れ方が回ごとに揺れるのは、計算を何本も並べて走らせる（マルチスレッド）ためか。

制作の問い: 実験226 で、つながりを弱めたガラスは、同じ設定で回しても割れ方が毎回違った（強さ 0.6 で動いた破片 54〜116 個）。
同じ設定なら同じ結果になってほしい（レンダーをやり直したら割れ方が変わった、を避けたい）。計算を 1 本（1 スレッド）にすると揃うのか。

  実験226 の台本（examples/226_rbd_glass_pieces.py）で、条件「ひび 80 本・強さ 0.6」と「ひび 80 本・強さ 0.5」だけを、
  ふつう（Houdini が使えるだけのスレッド）と、環境変数 HOUDINI_MAXTHREADS=1（1 スレッド）で、それぞれ 5 回ずつ、別の hython で回す。
  測るもの: 48 フレーム目までに 5 cm 以上動いた破片の数と、Bullet の 48 フレームの時間。

    python examples/246_rbd_determinism.py
"""
import ast
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
HYTHON = r"C:\Program Files\Side Effects Software\Houdini 21.0.700\bin\hython.exe"
RUNS = 5


def one(case, threads):
    env = dict(os.environ, ONLY=case)
    if threads:
        env["HOUDINI_MAXTHREADS"] = str(threads)
    proc = subprocess.run([HYTHON, os.path.join("examples", "226_rbd_glass_pieces.py")], cwd=HERE, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in proc.stdout.splitlines():
        if line.startswith("{'case'"):
            return ast.literal_eval(line)
    raise RuntimeError(proc.stderr[-400:])


def main():
    keep = os.path.join(OUT, "226_stats.json")
    saved = open(keep, encoding="utf-8").read()          # 226 の記録は台本が上書きするので、控えて戻す
    rows = []
    try:
        for case in ("r80_g06", "r80_g05"):
            for threads in (0, 1):
                moved, secs = [], []
                for _ in range(RUNS):
                    r = one(case, threads)
                    moved.append(r["moved"])
                    secs.append(r["sim_sec"])
                row = {"case": f"{case}_{'t1' if threads else 'all'}", "glass": case, "threads": threads or "all",
                       "moved": moved, "sim_sec": secs}
                rows.append(row)
                print(row, flush=True)
    finally:
        open(keep, "w", encoding="utf-8").write(saved)
    sys.path.insert(0, os.path.join(HERE, "examples"))
    import sop_bench
    sop_bench.save(246, rows, {"runs": RUNS})


if __name__ == "__main__":
    main()
