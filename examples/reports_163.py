# -*- coding: utf-8 -*-
"""実験163 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "163_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    tri = {r["grid"]: r for r in rows if r["mesh"] == "triangles"}
    quad = {r["grid"]: r for r in rows if r["mesh"] == "quads"}
    ok_d = all(r["constraints"]["distance"] == tri[r["grid"]]["edges"] for r in rows)
    ok_b = all(r["constraints"]["bend"] == tri[r["grid"]]["inner_edges"] for r in rows)
    same = all(quad[g]["constraints"] == tri[g]["constraints"] for g in quad)
    line_chart(os.path.join(OUT, "163_counts.png"),
               [{"label": "distance（伸び）", "points": [(tri[g]["points"], tri[g]["constraints"]["distance"]) for g in tri], "color": PALETTE[0]},
                {"label": "bend（曲げ）", "points": [(tri[g]["points"], tri[g]["constraints"]["bend"]) for g in tri], "color": PALETTE[1]},
                {"label": "三角形にした網の辺の数", "points": [(tri[g]["points"], tri[g]["edges"]) for g in tri], "color": PALETTE[4], "dash": True}],
               title="vellumconstraints（Cloth）: grid の点の数と、拘束の本数",
               x_label="点の数", y_label="拘束の本数")
    q = quad["10×10"]
    payload = {
        "title": "vellumconstraints の Cloth は網を三角形にしてから、辺ごとに伸びの拘束、内側の辺ごとに曲げの拘束を作る",
        "summary":
            "rows × cols の grid（四角形の網）と、先に divide で三角形にした網に、vellumconstraints（Constraint Type = Cloth）をかけ、"
            "2つ目の出力の拘束を type 属性ごとに数えた。\n\n"
            f"**伸び（distance）の拘束は、三角形にした網の辺の数と{'3通りとも一致' if ok_d else '一致しないものがあった'}。**"
            f"四角形のまま渡しても、四角形の対角線にも拘束が張られる（10×10 で辺 {q['edges']} 本に対して {q['constraints']['distance']} 本 = 辺 + 面の数）。\n\n"
            f"**曲げ（bend）の拘束は、三角形にした網の内側の辺の数と{'一致' if ok_b else '一致しないものがあった'}。**"
            "2枚の三角形にはさまれた辺ごとに1本で、縁の辺には付かない。\n\n"
            f"**四角形で渡しても、三角形で渡しても、拘束の数は同じ**（{'3通りとも同じ' if same else '違うものがあった'}）。"
            "Cloth は中で三角形に分けてから拘束を作っている。\n\n"
            f"**拘束づくりは 1 回 0.16 秒前後。**網の大きさ（9〜100 点）にはほとんど左右されない（最初の1回だけ {rows[0]['sec']:.2f} 秒）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "網と拘束の本数",
            "images": [{"path": "163_counts.png", "caption": "伸び（青）は点線（三角形の網の辺の数）に重なる。"}],
            "per_row": 1,
            "columns": ["grid", "網", "点", "面", "辺", "内側の辺", "distance", "bend", "合計", "秒"],
            "rows": [[r["grid"], r["mesh"], r["points"], r["faces"], r["edges"], r["inner_edges"],
                      r["constraints"].get("distance", 0), r["constraints"].get("bend", 0), r["total"], f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>伸びの拘束 = 三角形の辺、曲げの拘束 = 内側の辺。</strong>本数は計算で出せる。",
            "<strong>四角形の網でも対角線に伸びの拘束が張られる。</strong>対角線の向きは divide と同じとは限らない（確かめていない）。",
            "<strong>点を倍にすると拘束もほぼ倍。</strong>計算の重さの見積もりに使える。",
        ],
        "next": ["Hair（線）のときの拘束の本数", "Stretch Stiffness を変えたときの伸び方"],
    }
    with open(os.path.join(OUT, "163_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 163_report.json", ok_d, ok_b, same)


if __name__ == "__main__":
    main()
