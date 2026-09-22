# -*- coding: utf-8 -*-
"""実験181 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "181_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "181_speed.png"),
               [{"label": "1 点あたり（マイクロ秒）", "points": [(i, r["us_per_point"]) for i, r in enumerate(rows)], "color": PALETTE[0]}],
               title="半径 0.05・最大 50 点の平均（10 万点）: 0 pcfind / 1 nearpoints / 2 pcopen+pcfilter / 3 pcfind だけ",
               x_label="書き方の番号", y_label="1 点あたり（マイクロ秒）")
    a, b, c, d = rows
    payload = {
        "title": "pcfind と nearpoints は同じ結果・同じ速さ — pcopen + pcfilter は 1.6 倍遅く、距離で重みを付けた平均になる",
        "summary":
            "実験178 と同じ 10 万点で、全部の点について「半径 0.05 以内・最大 50 点」の位置の平均を、3通りの書き方で出した（2 回の速い方）。\n\n"
            f"**pcfind と nearpoints は、結果が1点も違わなかった**（差 {b['max_diff_vs_pcfind']:g}）。時間も {a['sec'] * 1000:.1f} と {b['sec'] * 1000:.1f} ミリ秒でほぼ同じ。"
            "どちらも見つかる数は平均 38.41（端の点で少なくなる）。\n\n"
            f"**pcopen + pcfilter は {c['sec'] * 1000:.1f} ミリ秒（{c['sec'] / a['sec']:.1f} 倍）。**値も少し違い、平均の差は {c['mean_diff_vs_pcfind']:.4f}、"
            f"いちばん大きくて {c['max_diff_vs_pcfind']:.4f}。pcfilter は近い点ほど重く数える平均なので、ただの平均とはずれる。\n\n"
            f"**見つけた点の P を point() で読む手間は小さい。**数えるだけなら {d['sec'] * 1000:.1f} ミリ秒、P を読んで平均すると {a['sec'] * 1000:.1f} ミリ秒（+{(a['sec'] / d['sec'] - 1) * 100:.0f}%）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "書き方と、時間・結果",
            "images": [{"path": "181_speed.png", "caption": "2（pcopen + pcfilter）だけが高い。"}],
            "per_row": 1,
            "columns": ["書き方", "秒（10 万点）", "1 点あたり（マイクロ秒）", "見つかった数の平均", "pcfind との差（平均）", "差（最大）"],
            "rows": [[r["method"], f"{r['sec']:.4f}", f"{r['us_per_point']:.3f}", f"{r['mean_found']:g}",
                      f"{r['mean_diff_vs_pcfind']:.5f}" if i < 3 else "（比べない）", f"{r['max_diff_vs_pcfind']:.5f}" if i < 3 else "—"]
                     for i, r in enumerate(rows)]}],
        "notes": [
            "<strong>近くの点の番号が欲しいなら pcfind か nearpoints。</strong>どちらでも同じ。",
            "<strong>pcfilter は重み付きの平均。</strong>ただの平均が欲しいなら、番号を取って自分で足す。",
            "<strong>見つけた点の値を読むのは安い。</strong>重いのは探すところ（実験178）。",
        ],
        "next": ["pcfilter の重みの形（距離との関係）", "pcfind_radius（点ごとの半径）の速さ"],
    }
    with open(os.path.join(OUT, "181_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 181_report.json")


if __name__ == "__main__":
    main()
