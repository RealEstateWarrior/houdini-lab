# -*- coding: utf-8 -*-
"""実験193 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "193_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, tracks = d["rows"], d["tracks"]
    line_chart(os.path.join(OUT, "193_birth.png"),
               [{"label": "Rate 1000・Life 100 秒", "points": [(i + 1, c) for i, c in enumerate(tracks["r1000_l100"])], "color": PALETTE[0]},
                {"label": "Rate 1000・Life 0.5 秒", "points": [(i + 1, c) for i, c in enumerate(tracks["r1000_l0.5"])], "color": PALETTE[1]},
                {"label": "1000 × 0.5 = 500", "points": [(1, 500), (49, 500)], "color": PALETTE[4], "dash": True}],
               title="popsource（Constant Birth Rate 1000）: 粒の数とフレーム（24 fps）",
               x_label="フレーム", y_label="粒の数")
    by = {(r["rate"], r["life"]): r for r in rows}
    r10, r100, r1k, r24, rl = by[(10.0, 100.0)], by[(100.0, 100.0)], by[(1000.0, 100.0)], by[(2400.0, 100.0)], by[(1000.0, 0.5)]
    expect10 = 10 * 49 / 24
    payload = {
        "title": "popsource の Constant Birth Rate は1秒あたり — 端数の粒はフレームごとに運で決まり、Life 0.5 秒の粒は 11 フレームで消える",
        "summary":
            "grid の面から popsource（Emission Type = Surface）で粒を生み続け、24 fps でフレームごとの粒の数を数えた。\n\n"
            f"**Constant Birth Rate は 1 秒あたりの数。**Rate 2400 なら 1 フレームにちょうど 100 粒で、24 フレームで {r24['frame24']:,}、49 フレームで {r24['frame49']:,}。\n\n"
            "**1 フレームあたりが整数にならないとき、端数はフレームごとに運で決まる。**Rate 100（1 フレーム 4.17 粒）では毎フレーム 4 か 5、"
            f"Rate 10（0.42 粒）では 0 か 1。端数を持ち越して合わせる仕組みではないので、合計はずれる: Rate 10 の 49 フレームで {r10['frame49']} 粒"
            f"（期待 {expect10:.1f}）、Rate 100 で {r100['frame49']}（{100 * 49 / 24:.1f}）、Rate 1000 で {r1k['frame49']:,}（{1000 * 49 / 24:.0f}）。"
            "少ない Rate ほど、割合のずれは大きい。\n\n"
            f"**Life Expectancy 0.5 秒（ばらつき 0）の粒は、11 フレームで消える。**数は {rl['frame24']}〜{rl['frame49']} で止まり、"
            f"Rate × Life = 500 より少ない（1 フレーム約 42 粒 × 11 フレーム ≈ 460）。0.5 秒 = 12 フレームより 1 フレーム早い。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Rate・Life と粒の数",
            "images": [{"path": "193_birth.png", "caption": "Life 0.5 秒（橙）は 460 前後で止まり、点線の 500 に届かない。"}],
            "per_row": 1,
            "columns": ["Constant Birth Rate", "Life", "フレーム 1", "24", "25", "49", "49 フレームの期待値", "1 フレームで生まれた数", "秒"],
            "rows": [[f"{r['rate']:g}", f"{r['life']:g}", r["frame1"], r["frame24"], r["frame25"], r["frame49"],
                      f"{r['rate'] * 49 / 24:.1f}" if r["life"] > 10 else f"{r['rate'] * r['life']:.0f}（止まる数）",
                      "・".join(map(str, r["per_frame_set"])), f"{r['sec_49f']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>決まった数を生みたいなら、Rate を fps の倍数に。</strong>2400（24 fps で 100 粒/フレーム）ならぴったり。",
            "<strong>少ない Rate は、運で数が揺れる。</strong>Rate 10 では 2 秒で 20 のはずが 27。",
            "<strong>Life は 1 フレーム早く尽きる。</strong>0.5 秒なら 11 フレーム。ぴったり 12 フレーム残したいなら 0.54 秒に（実験194）。",
        ],
        "next": ["Substeps を上げたとき、Life で消えるフレームが変わるか", "Impulse Birth Rate の数"],
    }
    with open(os.path.join(OUT, "193_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 193_report.json")


if __name__ == "__main__":
    main()
