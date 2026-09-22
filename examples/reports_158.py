# -*- coding: utf-8 -*-
"""実験158 の図とレポートを、測った値から組み立てる。"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "158_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    its = sorted({r["iterations"] for r in rows})
    mean = lambda key, it: statistics.mean(r[key] for r in rows if r["iterations"] == it)
    line_chart(os.path.join(OUT, "158_relax.png"),
               [{"label": "かけらの体積の変動係数", "points": [(it, mean("cv", it)) for it in its], "color": PALETTE[0]},
                {"label": "壁から 0.02 以内の種の割合", "points": [(it, mean("near_wall", it)) for it in its], "color": PALETTE[1]}],
               title="scatter の Relax Iterations と、voronoifracture のかけら（種 50 個・3 通りの平均）",
               x_label="Relax Iterations", y_label="値")
    neg = sum(1 for r in rows if r["wall_mean"] < 0)
    payload = {
        "title": "種を relax すると、voronoifracture のかけらはそろうどころかばらつく — 種が箱の壁へ押し出される",
        "summary":
            "実験157 と同じ 1×1×1 の箱に scatter で 50 個の種を撒き、Relax Iterations を 0〜100 と変えて voronoifracture で割った。"
            "Global Seed は 3 通り。かけらの体積の変動係数（標準偏差 ÷ 平均）を比べた。\n\n"
            f"**relax を強くするほど、かけらの大きさはばらついた。**変動係数は 0 回で平均 {mean('cv', 0):.2f}、"
            f"100 回で {mean('cv', 100):.2f}。「relax で種を広げればそろう」という予想（実験157 の次の課題）は外れた。\n\n"
            f"**理由: relax は種を箱の壁へ押し出す。**壁から 0.02 以内にある種は 0 回で平均 {mean('near_wall', 0) * 100:.0f}%、"
            f"100 回で {mean('near_wall', 100) * 100:.0f}%。壁までの距離の平均は、15 通りのうち {neg} 通りでマイナス（箱の外）になった。"
            "壁に張りついた種は、壁ぞいの薄いかけらと、中の大きなかけらを作る。\n\n"
            "**種どうしの最短距離は伸びる。**relax 自体は「点どうしを離す」ことをしている。ただし、壁で止まらない。\n\n"
            "**relax なしでも、壁から 0.02 以内の種が約 3 割あった。**一様に撒けば約 12% のはずで、isooffset で作った中身の範囲が"
            "箱より少し広いためとみられるが、確かめていない。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Relax Iterations・Seed ごとのかけら",
            "images": [{"path": "158_relax.png", "caption": "変動係数（青）と、壁ぎわの種の割合（橙）が一緒に上がる。"}],
            "per_row": 1,
            "columns": ["Relax", "Seed", "かけら", "体積の合計", "変動係数", "最大 ÷ 最小", "種の最短距離", "壁から 0.02 以内", "壁までの平均", "秒"],
            "rows": [[r["iterations"], r["seed"], r["pieces"], f"{r['total']:.6f}", f"{r['cv']:.3f}", f"{r['max_over_min']:g}",
                      f"{r['seed_dmin']:.4f}", f"{r['near_wall'] * 100:.0f}%", f"{r['wall_mean']:+.4f}", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>かけらをそろえる目的で scatter の relax を使うと逆効果。</strong>種が壁に寄る。",
            "<strong>体積の合計は、relax しても 1 のまま。</strong>かけらの数も 50 のまま。",
            "<strong>壁の外に出た種もある。</strong>割る形の中に種が収まっているか確かめてから使う。",
        ],
        "next": ["箱より小さい範囲に撒いてから relax したとき", "pointrelax（relax SOP）で種を広げたとき"],
    }
    with open(os.path.join(OUT, "158_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 158_report.json", neg)


if __name__ == "__main__":
    main()
