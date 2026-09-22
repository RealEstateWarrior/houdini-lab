# -*- coding: utf-8 -*-
"""実験190 の図とレポートを、測った値から組み立てる。"""
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
    with open(os.path.join(OUT, "190_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "190_size.png"),
               [{"label": ".usdc の大きさ（MB）", "points": [(i, r["bytes"] / 1e6) for i, r in enumerate(rows)], "color": PALETTE[0]},
                {"label": "読み込み＋書き出しの秒", "points": [(i, r["sec"] + r["write_sec"]) for i, r in enumerate(rows)], "color": PALETTE[1]}],
               title="箱 1 万個: 0 パックしない / 1 Native Instances / 2 Point Instancer / 3 Xforms / 4 Unpack",
               x_label="読み込み方の番号", y_label="MB ・ 秒")
    by = {r["mode"]: r for r in rows}
    pi, ni, xf, up, pl = by["pointinstancer"], by["nativeinstances"], by["xforms"], by["unpack"], by["—"]
    payload = {
        "title": "箱 1 万個の USD — Point Instancer は 0.32 MB・8 ミリ秒、Native Instances は 4.6 倍、Unpack は 7.4 倍の大きさ",
        "summary":
            "実験189 の続き。箱を 100 × 100 = 1 万個並べて sopimport で USD にし、読み込み時間と、ステージを .usdc で書き出したファイルの大きさを比べた"
            "（USD の立ち上げは先に済ませた）。\n\n"
            f"**Point Instancer がいちばん軽く、速い。**プリム {pi['prims']}、ファイル {pi['bytes'] / 1e6:.2f} MB、読み込み {pi['sec'] * 1000:.0f} ミリ秒。"
            "1 万個の位置と向きを、1 つのプリムの配列として持つ。\n\n"
            f"**Native Instances はプリムが 1 万を超え、ファイルは {ni['bytes'] / pi['bytes']:.1f} 倍**（{ni['bytes'] / 1e6:.2f} MB、読み込み {ni['sec'] * 1000:.0f} ミリ秒、書き出し {ni['write_sec']:.2f} 秒）。"
            f"Xforms は {xf['bytes'] / 1e6:.2f} MB（{xf['bytes'] / pi['bytes']:.1f} 倍、書き出し {xf['write_sec']:.2f} 秒）、"
            f"Unpack は {up['bytes'] / 1e6:.2f} MB（{up['bytes'] / pi['bytes']:.1f} 倍）でいちばん大きい。\n\n"
            "**Xforms（形を 1 万回持つ）は、Unpack より小さかった。**同じ形のメッシュを、書き出すときにまとめている可能性があるが、確かめていない。"
            "実験189 で「Xforms は重くなる」と書いたのは、Native Instances や Point Instancer と比べたときの話で、Unpack よりは軽い。\n\n"
            f"**パックせずに読むと、1 万個の箱が Mesh 1 つになり {pl['bytes'] / 1e6:.2f} MB。**1 個ずつ扱えない代わりに、ファイルは Native Instances より小さい。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "読み込み方と、プリム・時間・ファイル",
            "images": [{"path": "190_size.png", "caption": "Point Instancer（2）が大きさも時間もいちばん下。"}],
            "per_row": 1,
            "columns": ["SOP", "Packed Primitives", "プリム", "読み込みの秒", "書き出しの秒", ".usdc の大きさ", "Point Instancer の何倍"],
            "rows": [[r["case"], MODE[r["mode"]], f"{r['prims']:,}", f"{r['sec']:.4f}", f"{r['write_sec']:.4f}", f"{r['bytes'] / 1e6:.2f} MB",
                      f"{r['bytes'] / pi['bytes']:.1f}"] for r in rows]}],
        "notes": [
            "<strong>たくさん並べるなら Point Instancer。</strong>1 万個で 0.32 MB。",
            "<strong>Native Instances は、1 個ずつがプリムになる分だけ重い。</strong>1 万個で 1.5 MB、書き出し 0.4 秒。",
            "<strong>Unpack がいちばん大きい。</strong>パックを USD に渡すとき、わざわざ解く必要はない。",
        ],
        "next": ["Point Instancer と Native Instances の Karma でのレンダー時間", "10 万個にしたときの伸び方"],
    }
    with open(os.path.join(OUT, "190_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 190_report.json")


if __name__ == "__main__":
    main()
