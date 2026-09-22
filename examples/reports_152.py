# -*- coding: utf-8 -*-
"""実験152 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def chamfer(d):
    return 1 - 6 * d * d + 16 / 3 * d ** 3


def main():
    with open(os.path.join(OUT, "152_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    for r in rows:
        r["want_chamfer"] = round(chamfer(r["offset"]), 6)
        r["ratio"] = r["volume"] / r["want_round"]
    line_chart(os.path.join(OUT, "152_round.png"),
               [{"label": f"Offset {d:g}", "points": [(math.log2(r["divisions"]), r["ratio"]) for r in rows
                                                     if r["offset"] == d and r["shape"] == "round"], "color": PALETTE[i]}
                for i, d in enumerate((0.05, 0.1, 0.2))],
               title="polybevel（Round）: 体積 ÷ 角を丸めた箱の式（横は log2 Divisions）",
               x_label="log2（Divisions）", y_label="式に対する比")
    solid = [r for r in rows if r["shape"] == "solid"]
    same = all(abs(r["volume"] - [x for x in rows if x["offset"] == r["offset"] and x["shape"] == "round" and x["divisions"] == 1][0]["volume"]) < 1e-9 for r in solid)
    cham_ok = max(abs(r["volume"] - r["want_chamfer"]) for r in solid)
    d16 = {r["offset"]: r for r in rows if r["divisions"] == 16}
    payload = {
        "title": "polybevel の Round は、分割を増やすと「角を丸めた箱」の体積に近づく — 平らな面取りは 1 − 6d² + (16/3)d³",
        "summary":
            "1×1×1 の箱の辺を全部 polybevel（Offset = d）にかけ、Fillet Shape と Divisions を変えて体積を測った。"
            "比べる式は、半径 d で角を丸めた箱 (1−2d)³ + 6d(1−2d)² + 3πd²(1−2d) + (4/3)πd³。\n\n"
            f"**Divisions = 1 の Round は Solid と同じ形。**体積が{'3通りとも一致した' if same else '一致しないものがあった'}。"
            f"平らな面取りの体積は 1 − 6d² + (16/3)d³ と合った（差は最大 {cham_ok:.0e}）。"
            "辺を削る 12 本ぶん（6d²）から、角で2重に削った分（(16/3)d³）が戻る形。\n\n"
            "**Round は、Divisions を倍にするたびに式との差が 1/3.6〜1/6 に縮んだ（およそ 1/4）。**"
            f"Offset 0.1・Divisions 16 で {d16[0.1]['volume']:.6f}（式 {d16[0.1]['want_round']:.6f}）。"
            "Offset は丸みの半径そのものとして効いている。\n\n"
            f"**Offset 0.2・Divisions 16 だけは、式をわずかに超えた**（{d16[0.2]['volume']:.6f} ＞ {d16[0.2]['want_round']:.6f}、"
            f"{(d16[0.2]['ratio'] - 1) * 100:+.4f}%）。角の丸みがちょうどの球面になっていない可能性があるが、確かめていない。\n\n"
            "**点の数は Divisions とともに増える**（1 で 24、2 で 56、4 で 152、8 で 488、16 で 1,736）。Offset には左右されない。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Offset・Fillet Shape・Divisions と体積",
            "images": [{"path": "152_round.png", "caption": "Divisions 4 で 0.6% 以内、16 で 0.01% 以内。"}],
            "per_row": 1,
            "columns": ["Offset", "Fillet Shape", "Divisions", "点", "面", "体積", "丸めた箱の式", "比", "平らな面取りの式", "秒"],
            "rows": [[f"{r['offset']:g}", r["shape"], r["divisions"], f"{r['points']:,}", f"{r['prims']:,}",
                      f"{r['volume']:.6f}", f"{r['want_round']:.6f}", f"{r['ratio']:.5f}", f"{r['want_chamfer']:.6f}",
                      f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>Offset は丸みの半径。</strong>Round の体積は、その半径で丸めた箱の式に近づく。",
            "<strong>Divisions 1 の Round は、ただの面取り（Solid）。</strong>Divisions 4 で、丸めた箱の式との差が 0.6% 以内になった。",
            "<strong>面取りした箱の体積は 1 − 6d² + (16/3)d³。</strong>d = 0.1 で 0.945333。",
        ],
        "next": ["Offset 0.2 で式を超えた理由（角のパッチの形）", "Profile Ramp で丸み以外の形にしたときの体積"],
    }
    with open(os.path.join(OUT, "152_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 152_report.json", same, cham_ok)


if __name__ == "__main__":
    main()
