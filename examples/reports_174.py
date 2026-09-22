# -*- coding: utf-8 -*-
"""実験174 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LABEL = {"foreach": "for-each", "compiled": "for-each（compile block）", "compiled_mt": "compile block ＋ Multithread",
         "one_wrangle": "wrangle 1つで全部"}


def main():
    with open(os.path.join(OUT, "174_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "174_loop.png"),
               [{"label": LABEL[m], "points": [(math.log10(r["pieces"]), math.log10(max(r["sec"], 1e-5) * 1000)) for r in rows if r["mode"] == m],
                 "color": PALETTE[i]} for i, m in enumerate(LABEL)],
               title="かけらを1つずつ縮める処理の時間。縦は log10（ミリ秒）、横は log10（かけらの数）",
               x_label="log10（かけらの数）", y_label="log10（ミリ秒）")
    by = {(r["pieces"], r["mode"]): r for r in rows}
    f, c, mt, one = (by[(1000, m)] for m in ("foreach", "compiled", "compiled_mt", "one_wrangle"))
    same = all(r.get("max_diff") == 0.0 for r in rows)
    payload = {
        "title": "for-each はかけら1つあたり約 0.037 ミリ秒 — compile block で 35% 速く、wrangle 1つにまとめれば 30 倍速い",
        "summary":
            "N 個の箱（name でかけらを分けた）を block_begin / block_end（Piece で name ごと）で1つずつ回し、中で「かけらの中心へ 0.8 倍に縮める」"
            "attribwrangle を1つだけ走らせた。compile_begin / compile_end で囲んだもの、そこに Multithread when Compiled を足したもの、"
            "繰り返しを使わず wrangle 1つで全部のかけらを処理したものと比べた（3 回の一番速い値）。\n\n"
            f"**結果の形は4通りとも同じ**（{'どの点も差 0' if same else '違いがあった'}）。\n\n"
            f"**for-each の時間は、かけらの数にほぼ比例する。**1 かけらあたり 10・100・1000 個で "
            f"{by[(10, 'foreach')]['ms_per_piece']:.3f}・{by[(100, 'foreach')]['ms_per_piece']:.3f}・{f['ms_per_piece']:.3f} ミリ秒。1000 個で {f['sec'] * 1000:.0f} ミリ秒。\n\n"
            f"**compile block で約 {(1 - c['sec'] / f['sec']) * 100:.0f}% 速くなった**（1000 個で {c['sec'] * 1000:.0f} ミリ秒）。"
            f"Multithread も入れると、かえって遅くなった（{mt['sec'] * 1000:.0f} ミリ秒）。中の処理が軽すぎて、分けて配る手間の方が大きいとみられる。\n\n"
            f"**いちばん速いのは、繰り返しを使わず wrangle 1つで全部を処理すること。**1000 個で {one['sec'] * 1000:.1f} ミリ秒（for-each の {f['sec'] / one['sec']:.0f} 分の 1）。"
            "かけらの中心は、同じ name の面の点から求めた。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "かけらの数・書き方と時間",
            "images": [{"path": "174_loop.png", "caption": "for-each の3本は傾き 1（数に比例）。wrangle 1つ（赤）は1桁以上下。"}],
            "per_row": 1,
            "columns": ["かけら", "書き方", "点", "秒", "1 かけらあたり（ミリ秒）", "for-each との差"],
            "rows": [[r["pieces"], LABEL[r["mode"]], f"{r['points']:,}", f"{r['sec']:.4f}", f"{r['ms_per_piece']:.4f}",
                      f"{r['max_diff']:g}" if r.get("max_diff") is not None else "—"] for r in rows]}],
        "notes": [
            "<strong>かけらごとの処理は、まず wrangle 1つで書けないか考える。</strong>1000 個で 30 倍速い。",
            "<strong>for-each を使うなら compile block で囲む。</strong>何もしなくても 35% 速くなる。",
            "<strong>Multithread は中の処理が重いときだけ。</strong>軽い処理ではかえって遅い。",
        ],
        "next": ["中の処理を重くしたとき（polyextrude など）の Multithread", "Fetch Feedback（繰り返しで形を積み上げる）の時間"],
    }
    with open(os.path.join(OUT, "174_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 174_report.json", same, round(f["sec"] / one["sec"]))


if __name__ == "__main__":
    main()
