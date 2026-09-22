# -*- coding: utf-8 -*-
"""実験144 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def f(n):
    """内接正 n 角形の面積 ÷ 円の面積。"""
    return n * math.sin(2 * math.pi / n) / (2 * math.pi)


def main():
    with open(os.path.join(OUT, "144_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, wa, wv = d["rows"], d["want_area"], d["want_volume"]
    for x in rows:
        x["pred_vol"] = wv * f(x["rows"]) * f(x["cols"])
    ra = [x for x in rows if x["cols"] == 96]
    ca = [x for x in rows if x["rows"] == 96]
    line_chart(os.path.join(OUT, "144_torus.png"),
               [{"label": "面積（Rows を変える）", "points": [(x["rows"], x["area"] / wa) for x in ra], "color": PALETTE[0]},
                {"label": "面積（Columns を変える）", "points": [(x["cols"], x["area"] / wa) for x in ca], "color": PALETTE[1]},
                {"label": "体積（どちらを変えても同じ）", "points": [(x["rows"], x["volume"] / wv) for x in ra],
                 "color": PALETTE[2]}],
               title="torus（R=1, r=0.25）: もう片方は 96 に固定",
               x_label="変えた分割の数", y_label="式に対する比")
    worst = max(abs(x["volume"] - x["pred_vol"]) for x in rows)
    a6r, a6c = ra[0], ca[0]
    payload = {
        "title": "torus の Rows は管の断面、Columns は大きな輪 — 体積は2つの内接多角形の積で決まる",
        "summary":
            "Radius = (1, 0.25) の torus（Polygon）で、Rows と Columns を片方ずつ 6〜96 に変え、面積と体積を測った。"
            f"式は面積 4π²Rr = {wa:.6f}、体積 2π²Rr² = {wv:.6f}。\n\n"
            "**Rows は管の断面を刻み、Columns は大きな輪を刻む。**Rows を増やすと点の高さの種類が増え"
            f"（Rows 6 で {ra[0]['heights']}、96 で {ra[-1]['heights']}）、Columns では変わらない。\n\n"
            "**体積は Rows と Columns を入れ替えても同じ値になった**"
            f"（Rows 6 でも Columns 6 でも {a6r['volume']:.6f}）。"
            "断面も輪も内接正多角形なので、体積 = 式 × f(Rows) × f(Columns)、f(n) = n·sin(2π/n)/2π "
            f"と置くと、9通りすべて {worst:.0e} 以内で合った。\n\n"
            "**面積は入れ替えると違う。**6分割のとき、Rows を減らすと "
            f"{a6r['area']:.4f}（{(a6r['area'] / wa - 1) * 100:+.1f}%）、Columns を減らすと "
            f"{a6c['area']:.4f}（{(a6c['area'] / wa - 1) * 100:+.1f}%）。大きな輪（Columns）を粗くするほうが面積は大きく減る。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Rows・Columns と面積・体積",
            "note": "予測の体積 = 2π²Rr² × f(Rows) × f(Columns)。",
            "images": [{"path": "144_torus.png", "caption": "緑の体積は2本とも同じ線に重なる。"}],
            "per_row": 1,
            "columns": ["Rows", "Columns", "点", "高さの種類", "面積", "面積の比", "体積", "予測の体積", "秒"],
            "rows": [[x["rows"], x["cols"], f"{x['points']:,}", x["heights"], f"{x['area']:.6f}",
                      f"{x['area'] / wa:.4f}", f"{x['volume']:.6f}", f"{x['pred_vol']:.6f}", f"{x['sec']:.4f}"]
                     for x in rows]}],
        "notes": [
            "<strong>Rows = 管の太さ方向、Columns = 輪の周方向。</strong>名前から逆に思いやすいので注意。",
            "<strong>体積は2つの分割の掛け算。</strong>どちらを粗くしても同じだけ減る。",
            "<strong>面積は輪の分割に敏感。</strong>見た目を保ちたいなら Columns を先に確保する。",
        ],
        "next": ["Radius の r を R に近づけたとき（自分に食い込む手前）", "polysoup で作ったときの速さ"],
    }
    with open(os.path.join(OUT, "144_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 144_report.json", worst)


if __name__ == "__main__":
    main()
