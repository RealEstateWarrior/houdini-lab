# -*- coding: utf-8 -*-
"""実験197 の図とレポートを、測った値から組み立てる（実験196 と並べる）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402
from reports_196 import r_eff  # noqa: E402


def load(n):
    with open(os.path.join(OUT, f"{n}_stats.json"), encoding="utf-8") as fp:
        return json.load(fp)


def main():
    a, b = load(196), load(197)
    pick = lambda d, op: [r for r in d["rows"] if r["operation"] == op]
    o3, o25, c3, c25 = pick(a, "open"), pick(b, "open"), pick(a, "close"), pick(b, "close")
    for r in o3 + o25:
        r["r_eff"] = r_eff(r["volume"])
    line_chart(os.path.join(OUT, "197_band.png"),
               [{"label": "Close・帯 3 升（実験196）", "points": [(r["r"], r["volume"]) for r in c3], "color": PALETTE[1]},
                {"label": "Close・帯 25 升", "points": [(r["r"], r["volume"]) for r in c25], "color": PALETTE[0]},
                {"label": "Open・帯 3 升（実験196）", "points": [(r["r"], r["volume"]) for r in o3], "color": PALETTE[3]},
                {"label": "Open・帯 25 升", "points": [(r["r"], r["volume"]) for r in o25], "color": PALETTE[2]},
                {"label": "角を丸めた箱の式（半径 r）", "points": [(r["r"], r["want"]) for r in o3], "color": PALETTE[4], "dash": True}],
               title="vdbreshapesdf（1×1×1 の箱・Voxel 0.01）: SDF の帯の幅と体積",
               x_label="r = Offset × Voxel Size", y_label="体積")
    pct = lambda v: f"{(v - 1) * 100:+.2f}%"
    payload = {
        "title": "SDF の帯を 25 升に広げると、vdbreshapesdf の Close は箱をほとんど削らなくなる — Open の丸みはかえって大きくなる",
        "summary":
            "実験196 と同じ 1 × 1 × 1 の箱（Voxel Size 0.01）で、vdbfrompolygons の Exterior Band Voxels・Interior Band Voxels を既定の 3 から 25 に広げ、"
            "vdbreshapesdf の Open・Close を Offset 5・10・20 升でかけ直した。\n\n"
            "**Close の削れは小さくなった。**帯 3 升では "
            + "・".join(pct(r["volume"]) for r in c3) + "、帯 25 升では "
            + "・".join(pct(r["volume"]) for r in c25)
            + "（Offset 5・10・20 の順）。0 にはならず、Offset が大きいほど少し削れる。\n\n"
            "**Open は、帯を広げるとかえって多く削れた。**体積は帯 3 升で "
            + "・".join(f"{r['volume']:.4f}" for r in o3) + "、帯 25 升で "
            + "・".join(f"{r['volume']:.4f}" for r in o25)
            + "（式 " + "・".join(f"{r['want']:.4f}" for r in o3) + "）。同じ体積になる丸みの半径は帯 25 升で "
            + "・".join(f"{r['r_eff']:.3f}" for r in o25)
            + f"（r の {o25[0]['r_eff'] / o25[0]['r']:.2f}〜{o25[-1]['r_eff'] / o25[-1]['r']:.2f} 倍）。帯が狭いときは、帯の外の情報が無いことで削りが途中で止まっていたとみられるが、確かめていない。\n\n"
            "**時間は帯 25 升のほうがかかった**（1 回 " + f"{min(r['sec'] for r in o25 + c25):.1f}〜{max(r['sec'] for r in o25 + c25):.1f}" + " 秒。帯 3 升では "
            + f"{min(r['sec'] for r in o3 + c3):.1f}〜{max(r['sec'] for r in o3 + c3):.1f}" + " 秒）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "帯の幅・Operation・Offset と体積",
            "images": [{"path": "197_band.png", "caption": "Close は帯 25 升（青）で 1 に近づく。Open は帯 25 升（緑）のほうが式（点線）から遠い。"}],
            "per_row": 1,
            "columns": ["帯（升）", "Operation", "Offset（升）", "r", "体積", "式", "同じ体積の丸み半径", "秒"],
            "rows": [[band, r["operation"], r["offset"], f"{r['r']:g}", f"{r['volume']:.6f}", f"{r['want']:.6f}",
                      f"{r['r_eff']:.4f}" if "r_eff" in r else "—", f"{r['sec']:.3f}"]
                     for band, rs in ((3, o3 + c3), (25, o25 + c25)) for r in rs]}],
        "notes": [
            "<strong>Close で凸な形を削りたくないなら、SDF の帯を Offset より広く。</strong>それでも 0.2〜0.4% は削れる。",
            "<strong>Open の丸みは、帯を広げると r の 1.15〜1.45 倍になる（小さい丸みほど倍率が大きい）。</strong>狙いの半径が要るなら polybevel（実験152）。",
            "<strong>帯を広げると時間が増える。</strong>",
        ],
        "next": ["Open の丸みの形（本当に円弧か）", "vdbsmoothsdf と Open の違い"],
    }
    with open(os.path.join(OUT, "197_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 197_report.json", [round(r["r_eff"], 4) for r in o25], [round(r["r_eff"], 4) for r in o3])


if __name__ == "__main__":
    main()
