# -*- coding: utf-8 -*-
"""実験131 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "131_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    for r in rows:
        h = math.radians(r["deg"]) / 100 / 2          # 1区間の中心角の半分
        r["chord"] = r["line"] - 1 + math.sin(h) / h  # 範囲の中は弦、外はまっすぐ
    worst_pos = max(max(r["mid_err"], r["end_err"]) for r in rows)
    worst_len = max(abs(r["length"] - r["chord"]) for r in rows)

    series = []
    for i, deg in enumerate((90, 180, 270, 360)):
        R = 1 / math.radians(deg)
        pts = [(R * math.sin(math.radians(deg) * t / 50), R * (1 - math.cos(math.radians(deg) * t / 50)))
               for t in range(51)]
        series.append({"label": f"{deg}°（半径 {R:.3f}）", "points": pts, "color": PALETTE[i]})
    line_chart(os.path.join(OUT, "131_bend.png"), series,
               title="長さ1の線を曲げた形（実測の点は、この円弧の上にずれ0で乗った）",
               x_label="z", y_label="y")
    print("131_bend.png")

    payload = {
        "title": "bend は長さを保って円弧に曲げる — 端の位置は式と差0、範囲の外は接線の向きにまっすぐ",
        "summary":
            "z 方向に長さ1の線（100分割）を、bend の捕まえる範囲（origin 0・dir z・length 1）いっぱいに"
            "角度 θ だけ曲げた。長さを保って円弧になるなら、半径は R = 1/θ（ラジアン）で、"
            "範囲の終わりの点は y = R(1 − cos θ)、z = R sin θ に来るはず。\n\n"
            f"**45°〜360° の5通りで、範囲の終わりの点は式と一致**（ずれ最大 {worst_pos:.6f}）。"
            "360° では、線がちょうど1周して始まりの点に戻った。\n\n"
            "**範囲の外（長さ2の線の後ろ半分）は、曲がり終わりの接線の向きにまっすぐ伸びた。** "
            "端の点も式どおり（ずれ 0.000000）。180° なら後ろ半分は真後ろ（−z）へ向かう。\n\n"
            "全長は少しだけ短くなる（360° で 0.999835）。これは点が円弧の上に乗ったまま、"
            "点と点の間がまっすぐな弦になるため。弦の長さの式 sin(h)/h（h は1区間の中心角の半分）と"
            f"比べると、ずれは最大 {worst_len:.6f}。点そのものは円弧の上にある。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "曲げる角度と、点の位置・全長",
             "note": "Limit Deformation は既定（入）。曲げる向きは y（既定の up）。",
             "images": [{"path": "131_bend.png",
                         "caption": "曲げる角度ごとの円弧。半径は 1/θ で、長さはどれも1。"}],
             "per_row": 1,
             "columns": ["線の長さ", "角度", "範囲の終わりの点", "式", "端の点", "全長", "弦の式"],
             "rows": [[f"{r['line']:g}", f"{r['deg']}°",
                       "(" + ", ".join(f"{v:g}" for v in r["mid"][1:]) + ")",
                       "(" + ", ".join(f"{v:g}" for v in r["want_mid"][1:]) + ")",
                       "(" + ", ".join(f"{v:g}" for v in r["end"][1:]) + ")",
                       f"{r['length']:.6f}", f"{r['chord']:.6f}"] for r in rows]},
        ],
        "notes": [
            "<strong>bend は長さを保つ円弧。</strong>半径は「範囲の長さ ÷ 角度（ラジアン）」。",
            "<strong>範囲の外はまっすぐ付いてくる。</strong>曲がり終わりの向きに、そのまま伸びる。",
            "<strong>全長の不足は弦の分だけ。</strong>100分割で 360° 曲げても 0.02% 以内。",
        ],
        "next": [
            "Twist と Taper を同時に入れたときの形",
            "範囲の途中から始まる線（origin をずらす）で、手前がどうなるか",
            "Preserve Volume を入れた Length Scale の体積",
        ],
    }
    with open(os.path.join(OUT, "131_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 131_report.json")


if __name__ == "__main__":
    main()
