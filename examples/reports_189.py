# -*- coding: utf-8 -*-
"""実験189 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

MODE = {"—": "パックしない", "nativeinstances": "Native Instances（既定）", "pointinstancer": "Point Instancer",
        "xforms": "Xforms", "unpack": "Unpack"}


def main():
    with open(os.path.join(OUT, "189_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows = d["rows"]
    line_chart(os.path.join(OUT, "189_prims.png"),
               [{"label": "USD のプリムの数", "points": [(i, r["prims"]) for i, r in enumerate(rows)], "color": PALETTE[0]}],
               title="箱 100 個を sopimport: 0 パックしない / 1 Native Instances / 2 Point Instancer / 3 Xforms / 4 Unpack",
               x_label="読み込み方の番号", y_label="プリムの数")
    by = {r["mode"]: r for r in rows}
    payload = {
        "title": "箱 100 個を USD にすると、パックしなければメッシュ 1 つ、Point Instancer なら 6 プリム、Xforms なら 202 プリム",
        "summary":
            "SOP で箱を 100 個並べ（copytopoints）、パックしたもの（Pack and Instance）としないものを LOP の sopimport で読み込み、"
            "できた USD のプリムを種類ごとに数えた（SOP では、パックしない方が面 600 枚、パックした方がパック 100 個）。\n\n"
            f"**パックしないと、100 個の箱は Mesh 1 つにまとまる**（プリムは全部で {by['—']['prims']}）。1 つずつ動かしたり選んだりはできない。\n\n"
            f"**パックしたものは、Packed Primitives の扱いでまったく違う形になる。**"
            f"既定の Native Instances では Xform {by['nativeinstances']['types'].get('Xform', 0)}・インスタンス {by['nativeinstances']['instances']}・元の形（プロトタイプ）{by['nativeinstances']['prototypes']}。"
            f"Point Instancer では PointInstancer が 1 つで、プリムは全部で {by['pointinstancer']['prims']}。"
            f"Xforms では Xform と Mesh が 100 個ずつ（{by['xforms']['prims']}）で、同じ形を 100 回持つ。Unpack では Mesh 100 個（{by['unpack']['prims']}）。\n\n"
            "**読み込みの時間はどれも数ミリ秒。**ただし、そのセッションで最初の LOP だけは 21 秒かかった（USD の立ち上げ）。"
            "時間をはかるときは、先に1回読み込んでおく必要がある。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "読み込み方と USD のプリム",
            "images": [{"path": "189_prims.png", "caption": "Xforms（3）が一番多く、Point Instancer（2）が一番少ない。"}],
            "per_row": 1,
            "columns": ["SOP", "Packed Primitives", "プリムの数", "種類", "インスタンス", "プロトタイプ", "秒"],
            "rows": [[r["case"], MODE[r["mode"]], r["prims"], "・".join(f"{k} {v}" for k, v in r["types"].items()), r["instances"],
                      r["prototypes"], f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>数を増やすなら Point Instancer。</strong>100 個でもプリムは 6。",
            "<strong>1 個ずつ別の見た目にしたいなら Native Instances か Xforms。</strong>Xforms は形を 100 回持つので重くなる。",
            "<strong>パックせずに読み込むと、全部が1つのメッシュになる。</strong>",
        ],
        "next": ["1 万個にしたときの読み込み時間とファイルの大きさ", "Point Instancer をレンダーしたときの時間"],
    }
    with open(os.path.join(OUT, "189_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 189_report.json")


if __name__ == "__main__":
    main()
