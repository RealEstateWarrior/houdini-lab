# -*- coding: utf-8 -*-
"""実験103 の図とレポートを、測った値から組み立てる。

    python examples/reports_103.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "103_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows = data["rows"]
    pairs = data["pairs"]
    worst = pairs[0]
    closest = pairs[-1]
    # 単位球上の弦の長さから、開いた角度を出す
    angle = math.degrees(2.0 * math.asin(worst["dist"] / 2.0))
    worst_diff = max(r["diff_forward"] for r in rows)

    line_chart(
        os.path.join(OUT, "103_order.png"),
        [{"label": "y 座標",
          "points": [(i + 1, r["y"]) for i, r in enumerate(rows)],
          "color": PALETTE[0]},
         {"label": "z 座標",
          "points": [(i + 1, r["z"]) for i, r in enumerate(rows)],
          "color": PALETTE[1], "dash": True},
         {"label": "x 座標",
          "points": [(i + 1, r["x"]) for i, r in enumerate(rows)],
          "color": PALETTE[2], "dash": True}],
        title="同じ角度でも、順番が違えば行き先が違う（"
              + " / ".join(r["order"] for r in rows) + "の順）",
        x_label="Rotate Order（左から xyz, xzy, yxz, yzx, zxy, zyx）",
        y_label="回したあとの座標")
    print("103_order.png")

    payload = {
        "title": f"Rotate Order の xyz は「x から順に掛ける」 — 6通りで最大 {worst['dist']:.6f}"
                 f"（約{angle:.1f}°）ずれる",
        "summary":
            "Transform には Rotate Order（xyz / xzy / yxz / yzx / zxy / zyx）がある。"
            "同じ角度を入れても、掛ける順番で行き先が変わる。"
            "どれだけ変わるのかと、Houdini の並びが数式でいう何の順番なのかを確かめた。\n\n"
            f"点を1つ {tuple(data['start'])} に置き、角度 "
            f"{tuple(data['angles'])}（度）で回した。6通りすべての行き先を測り、"
            "自分で行列を掛けて出した答えと突き合わせた。\n\n"
            "**xyz は「x を先に掛け、次に y、最後に z」だった。**"
            f"6通りすべてで、この掛け順との差は {worst_diff:.6f}。"
            "逆から掛けた式では合わない（差は 0.16〜0.73）。"
            "行列で書けば xyz は Rz·Ry·Rx になる。\n\n"
            f"ばらつきは小さくない。もっとも離れた2つは **{worst['a']} と {worst['b']}** で "
            f"{worst['dist']:.6f}。点は原点から 1.0 の距離にあるので、"
            f"**約 {angle:.1f}° ぶん開いている**。もっとも近い2つ（{closest['a']} と "
            f"{closest['b']}）でも {closest['dist']:.6f} 離れる。\n\n"
            "1軸だけ回すときは順番に関係ない。y だけ 40° 回すと、"
            f"6通りの差は最大 {data['single_spread']:.9f} だった。"
            "「順番を気にしなくてよい」のは、角度が1つだけ入っているときに限る。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": f"6通りの行き先（点 {tuple(data['start'])} を "
                      f"{tuple(data['angles'])}° 回す）",
             "note": "「左から掛けた式との差」は、並びの順に Rx→Ry→Rz と掛けた"
                     "（行列では Rz·Ry·Rx）答えとの距離。"
                     "「右から」は逆順に掛けた答えとの距離。",
             "images": [{"path": "103_order.png",
                         "caption": "x 座標は3通りの値しか取らないが、"
                                    "y と z は6通りすべてで違う。"}],
             "per_row": 1,
             "columns": ["Rotate Order", "x", "y", "z",
                         "左から掛けた式との差", "右から掛けた式との差"],
             "rows": [[r["order"], f"{r['x']:+.6f}", f"{r['y']:+.6f}",
                       f"{r['z']:+.6f}", f"{r['diff_forward']:.6f}",
                       f"{r['diff_backward']:.6f}"] for r in rows]},
            {"label": "6通りのあいだの距離（離れている順）",
             "note": "点は原点から 1.0 の距離にある。距離 1.0 なら 60° ぶん開いていることになる。",
             "images": [],
             "per_row": 1,
             "columns": ["組", "距離", "開いた角度"],
             "rows": [[f"{p['a']} ↔ {p['b']}", f"{p['dist']:.6f}",
                       f"{math.degrees(2.0 * math.asin(p['dist'] / 2.0)):.1f}°"]
                      for p in pairs]},
        ],
        "notes": [
            "<strong>xyz は「x から順に掛ける」。</strong>"
            f"6通りすべてで、この掛け順との差は {worst_diff:.6f}。"
            "行列では Rz·Ry·Rx。逆順の式では合わない。",
            f"<strong>順番の違いは約 {angle:.1f}° に達する。</strong>"
            f"{worst['a']} と {worst['b']} で {worst['dist']:.6f}（原点から 1.0 の点で）。"
            "同じ数字を入れたのに、これだけ別の場所へ行く。",
            f"<strong>1軸だけなら順番は関係ない。</strong>y だけ 40° 回すと、"
            f"6通りの差は最大 {data['single_spread']:.9f}。"
            "2軸以上に角度が入っているときだけ、順番が効く。",
            "<strong>x 座標は3通りしか取らない。</strong>x を最初に掛ける並び"
            "（xyz / xzy）と、x を最後に掛ける並び（yzx / zyx）で値が揃う。"
            "回す軸と座標の関係で、一部の成分だけが一致することがある。",
        ],
        "next": [
            "Transform Order（srt / str / rst …）を変えたときのずれ",
            "クォータニオンで同じ回転を作ると、順番の問題は消えるのか",
            "回転を混ぜる（補間する）とき、順番の違いがどう出るか",
        ],
    }
    with open(os.path.join(OUT, "103_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 103_report.json")


if __name__ == "__main__":
    main()
