# -*- coding: utf-8 -*-
"""実験119 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

METHOD = {"distancealonggeometry_edge": "distancealonggeometry・Edge",
          "distancealonggeometry_surface": "distancealonggeometry・Surface",
          "distancealonggeometry_heat": "distancealonggeometry・Heat Geodesic",
          "heatgeodesic": "heatgeodesic",
          "attribfill_eikonal": "attribfill・Arrival Time"}
MESH = {"quad": "四角の網", "tri": "三角の網", "remesh": "remesh した網"}


def main():
    with open(os.path.join(OUT, "119_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]

    def get(mesh, method):
        return next(r for r in rows if r["mesh"] == mesh and r["method"] == method)

    series = []
    for i, m in enumerate(METHOD):
        series.append({"label": METHOD[m],
                       "points": [(j, get(mesh, m)["mean_abs"]) for j, mesh in enumerate(MESH)],
                       "color": PALETTE[i], "dash": m == "attribfill_eikonal"})
    line_chart(os.path.join(OUT, "119_distance.png"), series,
               title="真ん中からの距離のずれ（0=四角の網、1=三角の網、2=remesh）",
               x_label="網の種類", y_label="ずれの平均（絶対値）")
    print("119_distance.png")

    same = all(get(m, "distancealonggeometry_edge")["mean_abs"] == get(m, "attribfill_eikonal")["mean_abs"]
               for m in MESH)
    q = {m: get("quad", m) for m in METHOD}
    payload = {
        "title": "面に沿った距離は Surface が正解 — Edge と attribfill は辺の道のり、Heat は約1%短い",
        "summary":
            "2×2 の平らな板の真ん中から、面に沿った距離を5通りの方法で測り、本当の距離 √(x²+z²) と比べた。"
            "網は、四角（41×41）・三角（同じ点を三角形でつないだもの）・remesh（向きがばらばらの三角形）の3つ。\n\n"
            "**distancealonggeometry の Surface（既定）は、ほぼ正解。** 四角の網でずれ "
            f"{q['distancealonggeometry_surface']['max_abs']:.6f}、三角の網・remesh でも最大 0.0003 未満。"
            "辺をたどるのではなく、面の上をまっすぐ進んだ距離を出している。\n\n"
            "**Edge は、辺をたどった道のり。** 四角の網では |x|+|z| になり、角で最大 "
            f"{q['distancealonggeometry_edge']['max_abs']:.4f}（= 2 − √2）ずれる。"
            f"attribfill の Arrival Time は、3つの網すべてで Edge と{'同じ値' if same else '違う値'}だった"
            "（実験115 の「縦横の道のり」の正体）。remesh した網では辺の向きがばらけるので、"
            f"ずれの平均は {get('remesh', 'distancealonggeometry_edge')['mean_abs']:.3f} まで減る。\n\n"
            "**Heat Geodesic は、どの網でも少し短く出る**（平均で "
            f"{-q['distancealonggeometry_heat']['mean']:.4f}、heatgeodesic ノードは "
            f"{-q['heatgeodesic']['mean']:.4f}）。網の向きには左右されにくい。\n\n"
            "速さは、どれも 1,700〜1,900 点で 0.04 秒以下（最初の1回を除く）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "網と測り方ごとの、本当の距離とのずれ",
             "note": "始まりは板の真ん中の点。remesh では原点に一番近い点を始まりにして、全体をずらして原点に合わせた。",
             "images": [{"path": "119_distance.png",
                         "caption": "Surface（緑）はどの網でも0に近い。Edge と attribfill（破線）は重なる。"}],
             "per_row": 1,
             "columns": ["網", "測り方", "ずれの平均", "ずれの最大", "ずれの向き（平均）", "秒"],
             "rows": [[MESH[r["mesh"]], METHOD[r["method"]], f"{r['mean_abs']:.6f}",
                       f"{r['max_abs']:.6f}", f"{r['mean']:+.6f}", f"{r['sec']:.4f}"] for r in rows]},
        ],
        "notes": [
            "<strong>面に沿った本当の距離がほしいなら、distancealonggeometry の Surface。</strong>既定のまま使える。",
            "<strong>Edge と attribfill の Arrival Time は、辺の道のり。</strong>網の向きに引っぱられる。"
            "四角の網では最大で約 41%（2 − √2 を √2 で割った割合）長くなる。",
            "<strong>Heat Geodesic は約1%短い。</strong>向きには強いが、ぴったりではない。",
            "<strong>remesh すると辺の道のりのずれは小さくなる</strong>が、0 にはならない。",
        ],
        "next": [
            "曲がった面（球・波打つ面）で、Surface がどこまで正確か",
            "findshortestpath の cost が Edge と同じになるか",
            "Heat Geodesic の Smoothing を変えると、短く出る分が変わるか",
        ],
    }
    with open(os.path.join(OUT, "119_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 119_report.json")


if __name__ == "__main__":
    main()
