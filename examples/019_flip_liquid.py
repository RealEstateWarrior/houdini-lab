"""実験019 — FLIP 液体。粒の数は体積を表しているのか。

017で組み方が分からず保留にした実験。付属ヘルプを読んで配線が解けた。

    tank/source ──→ container(入力1) ──┬─出力1─→ solver(入力1)
                                       ├─出力2─→ solver(入力2)
                                       └─出力3─→ solver(入力3)

コンテナは単なる箱ではなく、3つのチャンネルを束ねる中継点だった。
さらに Sources チャンネルを流れているのは粒ではなく<名前付きのVDB>で、
source という名前のものだけが液体を湧かせる（019_channel.py で確認）。

ここからが本題。液体は押し縮められないので体積が保たれる。
FLIP は液体を粒で表すので、粒1つが一定の体積を担うなら
「粒の数」がそのまま体積の代わりに使えるはず。2つの向きから確かめる。

  A. 水の量を変えたとき、粒の数は体積に比例するか
  B. 時間が進んでも粒の数は保たれるか

    hython examples/019_flip_liquid.py
"""

import json
import os
import sys
import time

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SEP = 0.08
BOX = 3.0                       # コンテナは 3x3x3、原点中心なので y は −1.5〜+1.5
HEIGHTS = [-1.0, -0.5, 0.0, 0.5, 1.0]
CHECK_FRAMES = [1, 5, 10, 20, 30, 40]


def build(waterline=None, narrowband=True, reseeding=True, source_box=None):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "flip")

    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((BOX, BOX, BOX))
    container.parm("particlesep").set(SEP)

    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)   # コンテナと必ず同じ値にする
    solver.parm("donarrowband").set(narrowband)
    solver.parm("doreseeding").set(reseeding)
    if waterline is not None:
        solver.parm("dowaterline").set(True)
        solver.parm("waterline").set(waterline)

    sources = container
    source_index = 0
    if source_box is not None:
        box = geo.createNode("box", "blob")
        box.parmTuple("size").set(source_box[0])
        box.parmTuple("t").set(source_box[1])
        src = geo.createNode("flipsource", "src")
        src.setInput(0, box)
        src.parm("particlesep").set(SEP)
        src.parm("volumename").set("source")   # 名前が役割を決める
        merge = geo.createNode("merge", "merge_sources")
        merge.setInput(0, container, 0)
        merge.setInput(1, src)
        sources, source_index = merge, 0

    solver.setInput(0, sources, source_index)
    solver.setInput(1, container, 1)
    solver.setInput(2, container, 2)
    return geo, container, solver


def count_at(solver, frame):
    hou.setFrame(frame)
    geo = solver.geometry(0)
    return 0 if geo is None else len(geo.points())


def fit_line(xs, ys):
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    return slope, (sy - slope * sx) / n


def main():
    stats = {"sep": SEP, "box": BOX}

    # ---------- A. 水の量と粒の数 ----------
    print("A. 水位を変えて、粒の数が体積に比例するか見る")
    print(f"{'水位':>7} {'水の体積':>10} {'帯あり':>9} {'帯なし':>9}")
    rows = []
    for height in HEIGHTS:
        volume = BOX * BOX * (height + BOX / 2.0)
        _, _, solver_on = build(waterline=height, narrowband=True)
        on = count_at(solver_on, 1)
        _, _, solver_off = build(waterline=height, narrowband=False)
        off = count_at(solver_off, 1)
        rows.append({"waterline": height, "volume": volume,
                     "band_on": on, "band_off": off})
        print(f"{height:7.2f} {volume:10.4f} {on:9d} {off:9d}")
    stats["heights"] = rows

    volumes = [r["volume"] for r in rows]
    slope_on, base_on = fit_line(volumes, [r["band_on"] for r in rows])
    slope_off, base_off = fit_line(volumes, [r["band_off"] for r in rows])
    print(f"\n  帯あり: 粒の数 = {slope_on:8.1f} × 体積 {base_on:+9.1f}")
    print(f"  帯なし: 粒の数 = {slope_off:8.1f} × 体積 {base_off:+9.1f}")
    print(f"  体積に比例する分の比: {slope_off / slope_on:.1f}倍")

    worst = 0.0
    print(f"\n  帯なしの当てはまり")
    for r in rows:
        predicted = slope_off * r["volume"] + base_off
        gap = 100.0 * (r["band_off"] - predicted) / predicted
        r["fit_gap_pct"] = gap
        worst = max(worst, abs(gap))
        print(f"    体積 {r['volume']:7.3f}: 実測 {r['band_off']:7d} / "
              f"予測 {predicted:9.1f} / ずれ {gap:+6.2f}%")
    print(f"  最大のずれ {worst:.2f}%")
    print(f"  切片 {base_off:.0f} は、帯ありのときの粒の数 "
          f"{sum(r['band_on'] for r in rows) / len(rows):.0f} に近い")

    per_point = 1.0 / slope_off
    print(f"\n  体積が増えたぶんの粒1つが担う体積: {per_point:.6f}"
          f"（= sep³ の {per_point / SEP ** 3:.3f}倍）")
    stats["fit"] = {"slope_on": slope_on, "base_on": base_on,
                    "slope_off": slope_off, "base_off": base_off,
                    "worst_pct": worst, "per_point": per_point,
                    "per_point_over_sep3": per_point / SEP ** 3}

    # ---------- B. 時間が進んでも保たれるか ----------
    print("\nB. 40フレーム進めたときの粒の数（水位 0.0、帯なし）")
    series = {}
    for reseeding in (True, False):
        _, _, solver = build(waterline=0.0, narrowband=False, reseeding=reseeding)
        start = time.perf_counter()
        counts = [count_at(solver, f) for f in CHECK_FRAMES]
        elapsed = time.perf_counter() - start
        spread = max(counts) - min(counts)
        key = "on" if reseeding else "off"
        series[key] = {"frames": CHECK_FRAMES, "counts": counts,
                       "spread": spread, "spread_pct": 100.0 * spread / counts[0],
                       "sec": elapsed}
        print(f"  reseeding {'あり' if reseeding else 'なし'}: "
              + " ".join(f"F{f}:{c}" for f, c in zip(CHECK_FRAMES, counts))
              + f"  幅 {spread} ({100.0 * spread / counts[0]:.2f}%) / {elapsed:.1f}秒")
    stats["reseeding"] = series

    # ---------- 落ちる水 ----------
    print("\n落下する水の連番")
    geo, container, solver = build(narrowband=False,
                                   source_box=((1.0, 1.0, 1.0), (0.0, 0.9, 0.0)))
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    frames = list(range(1, 49, 3))
    bbox = hou.BoundingBox(-BOX / 2, -BOX / 2, -BOX / 2, BOX / 2, BOX / 2, BOX / 2)
    paths = hou_tools.render_sequence(solver.path(), OUT, "019_drop", frames,
                                      res=(420, 320), shading="smooth",
                                      frame_bbox=bbox)
    drop_counts = [count_at(solver, f) for f in frames]
    stats["drop"] = {"frames": frames, "counts": drop_counts}
    print(f"  {len(paths)} 枚 / 粒の数 "
          + " ".join(f"F{f}:{c}" for f, c in zip(frames, drop_counts)))

    hou_tools.write_graph(geo.path(), os.path.join(OUT, "019_graph.json"),
                          title="実験019 — FLIP 液体")
    hou_tools.save_hip(os.path.join(OUT, "019_flip.hipnc"))
    with open(os.path.join(OUT, "019_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/019_stats.json, out/019_graph.json, out/019_flip.hipnc")


if __name__ == "__main__":
    main()
