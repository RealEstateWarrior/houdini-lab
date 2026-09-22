# -*- coding: utf-8 -*-
"""実験159 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "159_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    s1 = [r for r in rows if r["fps"] == 24 and r["scale"] == 1.0]
    modes = ["Backward Difference", "Central Difference", "Forward Difference"]
    line_chart(os.path.join(OUT, "159_vel.png"),
               [{"label": m, "points": [(r["frame"], r["v"]) for r in s1 if r["mode"] == m], "color": PALETTE[i]} for i, m in enumerate(modes)]
               + [{"label": "正しい値 0.2·F·24", "points": [(F, 0.2 * F * 24) for F in (10, 20)], "color": PALETTE[4], "dash": True}],
               title="trail（24 fps・x = 0.1F²）: フレーム 10 と 20 の速さ v.x",
               x_label="フレーム", y_label="v.x（1秒あたり）")
    worst = max(abs(r["v"] - r["want_v"]) for r in rows)
    c = [r for r in rows if r["mode"] == "Central Difference"]
    acc_ok = max(abs(r["accel"] - r["exact_accel"] * r["scale"] ** 2) for r in c)
    zero = all(r["accel"] == 0 for r in rows if r["mode"] != "Central Difference")
    payload = {
        "title": "trail の速さは1秒あたり、差分の式どおり — 加速度は Central Difference のときだけ出て、Velocity Scale の2乗で縮む",
        "summary":
            "点を x = 0.1·F²（F はフレーム）で動かし、trail（Result Type = Compute Velocity）で v と加速度を出した。"
            "fps は 24 と 30、Velocity Approximation は3通り、Velocity Scale は 1 と 0.5。\n\n"
            f"**v は1秒あたりで、差分の式と合った**（24通りで差は最大 {worst:.0e}）。"
            "Backward は (x(F) − x(F−1))·fps、Forward は (x(F+1) − x(F))·fps、Central は2つの平均。"
            "x が2次式なので Central だけが正しい値 0.2·F·fps にぴったり重なり、Backward は 0.1·fps 小さく、Forward は同じだけ大きい"
            "（24 fps・フレーム 10 で 45.6 / 48 / 50.4）。\n\n"
            f"**Compute Acceleration は Central Difference のときだけ値が入った。**Backward と Forward では{'すべて 0' if zero else '0 でないものがあった'}。"
            "Central での値は 0.2·fps²（24 fps で 115.2）と合った。\n\n"
            f"**Velocity Scale は v を掛け算し、加速度はその2乗で掛かる。**Scale 0.5 で v は半分、加速度は 1/4（115.2 → 28.8。差は最大 {acc_ok:.4f}）。"
            "時間の進みを縮めたのと同じ効き方。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "fps・差分・Scale ごとの v と加速度",
            "images": [{"path": "159_vel.png", "caption": "Central（橙）だけが点線に重なる。"}],
            "per_row": 1,
            "columns": ["fps", "Velocity Approximation", "Scale", "フレーム", "x", "v.x", "差分の式", "正しい値", "加速度", "正しい値", "秒"],
            "rows": [[r["fps"], r["mode"], f"{r['scale']:g}", r["frame"], f"{r['x']:g}", f"{r['v']:.4f}", f"{r['want_v']:.4f}",
                      f"{r['exact_v']:g}", f"{r['accel']:.3f}" if r["accel"] is not None else "—", f"{r['exact_accel']:g}",
                      f"{r['sec']:.5f}"] for r in rows]}],
        "notes": [
            "<strong>v は 1 秒あたり。</strong>1 フレームあたりにしたいなら fps で割る。",
            "<strong>動きが加速しているなら Central Difference。</strong>Backward・Forward は半フレームずれた速さになる。",
            "<strong>加速度が 0 なら、差分が Central になっているか見る。</strong>",
        ],
        "next": ["Match by Attribute（id）で点の数が変わるときの v", "Compute Angular Velocity の単位"],
    }
    with open(os.path.join(OUT, "159_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 159_report.json", worst, acc_ok, zero)


if __name__ == "__main__":
    main()
