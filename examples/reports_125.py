# -*- coding: utf-8 -*-
"""実験125 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

SHAPE = {"box": "箱（8点・6面）", "grid": "格子 5×5（25点・16面）", "sphere": "球 12×24（242点・264面）"}


def main():
    with open(os.path.join(OUT, "125_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    dv = [r for r in rows if r["test"] == "divide"]
    fc = [r for r in rows if r["test"] == "facet_unique"]
    cl = [r for r in rows if r["test"] == "convertline"]
    ps = [r for r in rows if r["test"] == "polysoup"]
    ed = [r for r in rows if r["test"] == "edgedivide"]
    ok_dv = all(r["after"]["prims"] == r["want_prims"] for r in dv)
    ok_fc = all(r["after"]["points"] == r["want_points"] for r in fc)
    ok_cl = all(r["after"]["prims"] == r["want_prims"] for r in cl if r["want_prims"])
    ok_ed = all(r["after"]["points"] == r["want_points"] and
                r["after_shared"]["points"] == r["want_shared"] for r in ed)

    line_chart(
        os.path.join(OUT, "125_counts.png"),
        [{"label": "edgedivide の点（既定）", "points": [(r["k"], r["after"]["points"]) for r in ed],
          "color": PALETTE[1]},
         {"label": "8 + 24(k−1)", "points": [(r["k"], r["want_points"]) for r in ed],
          "color": PALETTE[1], "dash": True},
         {"label": "Share New Points を入れた点", "points": [(r["k"], r["after_shared"]["points"]) for r in ed],
          "color": PALETTE[0]},
         {"label": "8 + 12(k−1)", "points": [(r["k"], r["want_shared"]) for r in ed],
          "color": PALETTE[0], "dash": True}],
        title="箱の辺を全部 k 分割: 既定では面ごとに点を作るので、約2倍になる",
        x_label="Divisions k", y_label="点の数")
    print("125_counts.png")

    sph = next(r for r in cl if r["shape"] == "sphere")
    payload = {
        "title": "点と面の数は式で先に分かる — divide は n−2、convertline は V+F−2。edgedivide は既定で点が2倍",
        "summary":
            "形を変える箱を通したとき、点と面の数が式どおりになるかを、5つの箱で確かめた。"
            "数えるのは intrinsic の pointcount・primitivecount・vertexcount。\n\n"
            f"**divide: n 角形1枚は、三角形 n−2 枚になる**（3〜100角形の6通りで{'すべて一致' if ok_dv else '不一致あり'}）。\n\n"
            f"**facet の Unique Points: 点の数は頂点の数になる**（箱 8→24、格子 25→64、球 242→1,008 で"
            f"{'一致' if ok_fc else '不一致'}）。面ごとに自分の点を持つので、角がくっきりする代わりに点が増える。\n\n"
            "**convertline: 線の本数は辺の数。** 閉じた形ではオイラーの式から 辺 = 点 + 面 − 2 で、"
            f"箱 12 本・球 {sph['after']['prims']} 本と{'一致' if ok_cl else '不一致'}。"
            "開いた格子 5×5 は 40 本（縦20＋横20）。\n\n"
            "**polysoup: 面が1つになり、頂点の数が点の数まで減る**（箱 24→8、球 1,008→242）。"
            "同じ点を使う頂点をまとめる（Merge Identical Vertices が既定で入っている）。\n\n"
            "**edgedivide は、既定では点が思ったより多い。** 箱の12本の辺を k 分割すると、"
            "点は 8 + 12(k−1) ではなく **8 + 24(k−1)** になった。隣り合う2つの面が、"
            "それぞれ自分の新しい点を作るため。Share New Points を入れると 8 + 12(k−1) になる"
            f"（{'すべて一致' if ok_ed else '不一致あり'}）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "divide（n 角形1枚 → 三角形）",
             "note": "circle を Polygon で n 分割したもの。",
             "images": [{"path": "125_counts.png",
                         "caption": "edgedivide の既定（橙）は、辺ごとに点を2倍作る。"}],
             "per_row": 1,
             "columns": ["n", "三角形", "n−2", "頂点"],
             "rows": [[str(r["n"]), str(r["after"]["prims"]), str(r["want_prims"]),
                       str(r["after"]["vertices"])] for r in dv]},
            {"label": "facet・convertline・polysoup",
             "note": "前 = 元の形。後 = 箱を通したあと。",
             "images": [],
             "per_row": 1,
             "columns": ["箱", "形", "前の点・面・頂点", "後の点・面・頂点", "式"],
             "rows": [[r["test"], SHAPE[r["shape"]],
                       f"{r['before']['points']}・{r['before']['prims']}・{r['before']['vertices']}",
                       f"{r['after']['points']}・{r['after']['prims']}・{r['after']['vertices']}",
                       str(r.get("want_points") or r.get("want_prims") or "—")] for r in fc + cl + ps]},
            {"label": "edgedivide（箱の12本の辺を全部 k 分割）",
             "note": "",
             "images": [],
             "per_row": 1,
             "columns": ["k", "点（既定）", "8+24(k−1)", "点（Share New Points）", "8+12(k−1)"],
             "rows": [[str(r["k"]), str(r["after"]["points"]), str(r["want_points"]),
                       str(r["after_shared"]["points"]), str(r["want_shared"])] for r in ed]},
        ],
        "notes": [
            "<strong>divide は n−2 枚。</strong>三角形の数は、割る前に分かる。",
            "<strong>facet の Unique Points は、点を頂点の数まで増やす。</strong>球 12×24 で約4倍。",
            "<strong>閉じた形の辺の数は、点 + 面 − 2。</strong>convertline の本数で確かめられる。",
            "<strong>edgedivide は既定で辺ごとに点を2つずつ作る。</strong>形がつながったままでいてほしいなら Share New Points を入れる。",
        ],
        "next": [
            "edgedivide の既定の出力で、面と面の間に隙間ができているか（fuse で元に戻るか）",
            "divide の Maximum Edges を 4 にしたとき、n 角形が何枚の四角形になるか",
            "穴のある形（トーラス）で、オイラーの式が V − E + F = 0 になるか",
        ],
    }
    with open(os.path.join(OUT, "125_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 125_report.json")


if __name__ == "__main__":
    main()
