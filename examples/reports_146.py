# -*- coding: utf-8 -*-
"""実験146 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "146_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    for r in rows:
        r["want"] = r["want_above"] if r["op"] == "above" else r["want_below"] if r["op"] == "below" else None
    series = []
    for i, (res, op) in enumerate([(48, "above"), (192, "above"), (48, "below"), (192, "below")]):
        series.append({"label": f"{op}・分割 {res}×{res * 2}",
                       "points": [(r["c"], r["area"] / r["want"]) for r in rows if r["res"] == res and r["op"] == op],
                       "color": PALETTE[i]})
    line_chart(os.path.join(OUT, "146_clip.png"), series,
               title="clip で切った球（半径1）の面積 ÷ 2πh", x_label="切る高さ c（Distance）", y_label="式に対する比")
    hi = [r for r in rows if r["res"] == 192 and r["op"] != "both"]
    worst = max(abs(r["area"] / r["want"] - 1) for r in hi)
    ratio = hi[0]["full"] / 12.566371
    payload = {
        "title": "clip で切った球の面積は 2πh — 比は切る高さに関係なく、球全体と同じだけずれる",
        "summary":
            "半径 1 の球（Polygon Mesh）を、Direction = (0,1,0)、Distance = c の面で clip し、残った面積を測った。"
            "球帯の面積は高さ h だけで決まる（2πRh）。\n\n"
            "**Above は面より上（y ≥ c）、Below は下が残る。**Distance は原点からその向きに進んだ距離。\n\n"
            "**面積は 2πh に合う。**分割 192×384 で、8通りすべて式から "
            f"{worst * 100:.3f}% 以内。式に対する比は、どの高さでもほぼ球全体の比（{ratio:.5f}）と同じ。"
            "切り口の位置によらず、同じ分割の網を切っているだけだから。\n\n"
            "**切り口の点は面の上に乗る。**どの場合も列の数（48 分割なら 96、192 分割なら 384）だけ、y = c ちょうどの点ができた。\n\n"
            "**Both は2つに分けるが、切り口の点は共有のまま。**48 分割・c = 0.3 で、元の球 4,418 点・4,512 面が "
            "4,514 点（+96）・4,608 面（+96）。点は複製されないので、上下を引き離すには別に割る処理が要る。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "切る高さ・残す側・面積",
            "note": "式: Above は 2π(1 − c)、Below は 2π(1 + c)。Both は球全体。",
            "images": [{"path": "146_clip.png", "caption": "線が水平 = 比が高さによらない。細かい分割（192）ほど 1 に近い。"}],
            "per_row": 1,
            "columns": ["分割", "c", "Keep", "点", "面", "y の範囲", "面上の点", "面積", "式", "秒"],
            "rows": [[f"{r['res']}×{r['res'] * 2}", f"{r['c']:g}", r["op"], f"{r['points']:,}", f"{r['prims']:,}",
                      f"{r['ymin']:g}〜{r['ymax']:g}", r["on_plane"], f"{r['area']:.6f}",
                      f"{r['want']:.6f}" if r["want"] else "—", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>Distance は原点から Direction の向きに進んだ位置。</strong>Above はその先（向きの側）を残す。",
            "<strong>切り口は面の上にちょうど乗る。</strong>あとで cap や polyfill で塞ぐとき、平らに閉じる。",
            "<strong>Both の上下は点を共有している。</strong>別々に動かすなら、切ったあとに割る処理を足す。",
        ],
        "next": ["切り口を polyfill で塞いだときの体積（球冠の式）", "Direction を斜めにしたとき"],
    }
    with open(os.path.join(OUT, "146_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 146_report.json", worst, ratio)


if __name__ == "__main__":
    main()
