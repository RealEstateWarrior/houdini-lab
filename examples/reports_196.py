# -*- coding: utf-8 -*-
"""実験196 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def rounded(r):
    return (1 - 2 * r) ** 3 + 6 * r * (1 - 2 * r) ** 2 + 3 * math.pi * r * r * (1 - 2 * r) + 4 / 3 * math.pi * r ** 3


def r_eff(v):
    lo, hi = 0.0, 0.5
    for _ in range(60):
        mid = (lo + hi) / 2
        if rounded(mid) > v:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    with open(os.path.join(OUT, "196_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, vox = d["rows"], d["voxel"]
    for r in rows:
        if r["operation"] == "open":
            r["r_eff"] = r_eff(r["volume"])
    opens = [r for r in rows if r["operation"] == "open"]
    closes = [r for r in rows if r["operation"] == "close"]
    line_chart(os.path.join(OUT, "196_open.png"),
               [{"label": "Open（測った体積）", "points": [(r["r"], r["volume"]) for r in opens], "color": PALETTE[0]},
                {"label": "角を丸めた箱の式（半径 r）", "points": [(r["r"], r["want"]) for r in opens], "color": PALETTE[4], "dash": True},
                {"label": "Close（測った体積）", "points": [(r["r"], r["volume"]) for r in closes], "color": PALETTE[1]}],
               title="vdbreshapesdf（1×1×1 の箱・Voxel 0.01）: Offset × 升 = r と体積",
               x_label="r = Offset × Voxel Size", y_label="体積")
    payload = {
        "title": "vdbreshapesdf の Open は箱の角を r より少し大きく丸める — Close も凸な箱を少しだけ削る",
        "summary":
            "1 × 1 × 1 の箱を vdbfrompolygons（Voxel Size 0.01）で SDF にし、vdbreshapesdf の Open・Close を Offset 5・10・20 升（r = 0.05・0.1・0.2）でかけた。"
            f"面に戻す前の元の体積は {d['base_volume']:.6f}。\n\n"
            "**Open は角を丸めたが、式の半径 r より大きく削れた。**半径 r で角を丸めた箱の体積（実験152 の式）に比べて、"
            + "、".join(f"r = {r['r']:g} で {r['volume']:.4f}（式 {r['want']:.4f}）" for r in opens)
            + "。同じ体積になる丸みの半径は "
            + "・".join(f"{r['r_eff']:.3f}" for r in opens)
            + f"（r の {opens[0]['r_eff'] / opens[0]['r']:.2f}〜{opens[-1]['r_eff'] / opens[-1]['r']:.2f} 倍。Offset が小さいほど倍率が大きい）。\n\n"
            "**Close は、へこみの無い箱を変えないはずだが、少し削った**（"
            + "・".join(f"r = {r['r']:g} で {(r['volume'] - 1) * 100:+.2f}%" for r in closes)
            + "）。Offset が SDF の帯（既定 3 升）を超えるほど大きいと、太らせて戻す途中で角の情報が失われるとみられるが、確かめていない。\n\n"
            "**実験195 の球では Open・Close はほぼ何もしなかった。**角のある形でだけ、この差が出る。\n\n"
            "**訂正（実験198・199）: 上の「同じ体積の丸み半径」は、三つの面が集まる角の形も混ざった値だった。**辺の断面に円を当てはめると、丸みは円弧で、半径は Offset × 升 + 約 3 升（r = 0.05・0.1・0.2 で 0.075・0.130・0.232）。「Offset が小さいほど倍率が大きい」のは、この一定の足し分のため。帯の幅を変えても足し分は変わらなかった。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Operation・Offset と体積",
            "images": [{"path": "196_open.png", "caption": "Open（青）は式（点線）より下。Close（橙）も 1 から少し下がる。"}],
            "per_row": 1,
            "columns": ["Operation", "Offset（升）", "r", "体積", "式", "同じ体積の丸み半径", "秒"],
            "rows": [[r["operation"], r["offset"], f"{r['r']:g}", f"{r['volume']:.6f}", f"{r['want']:.6f}",
                      f"{r['r_eff']:.4f}" if "r_eff" in r else "—", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>Open で角を丸めると、Offset × 升より少し大きい丸みになる。</strong>辺の断面を測ると、足し分は倍率ではなく約 3 升で一定だった（実験198・199）。欲しい半径 R なら Offset ≒ R ÷ 升 − 3。",
            "<strong>凸な形に Close をかけても、少し削れる。</strong>Offset が大きいほど。",
            "<strong>角を正確な半径で丸めたいなら polybevel（実験152）。</strong>",
        ],
        "next": ["SDF の帯を広げたときの Close（実験197）", "Open の丸みの形（実験198）"],
    }
    with open(os.path.join(OUT, "196_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 196_report.json", [round(r["r_eff"], 4) for r in opens])


if __name__ == "__main__":
    main()
