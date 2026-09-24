# -*- coding: utf-8 -*-
"""実験217 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"b-3": "曲げの硬さ 0.001", "b-1": "0.1（既定）", "b1": "10", "b3": "1000"}


def main():
    with open(os.path.join(OUT, "217_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    font = _font(17)
    w, h = 560, 360
    sheet = Image.new("RGB", (w * 2, (h + 30) * 2), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(LAB):
        im = Image.open(os.path.join(OUT, f"217_{k.replace('-', 'm')}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
        x, y = (i % 2) * w, (i // 2) * (h + 30)
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (x, y + 30))
        dr.text((x + 8, y + 6), LAB[k], fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "217_grid.png"))
    hem = lambda k: sum(t[k]["hem"].values()) / 4  # noqa: E731
    out = lambda k: (t[k]["side_x_mean"] - 0.6) * 100  # noqa: E731
    table = []
    for k, lab in LAB.items():
        r = t[k]
        tf = r.get("to_default")
        table.append([lab, f"{r['lowest']:.3f}", f"{hem(k):.3f}", f"{out(k):.1f}", f"{r['side_x_std_mm']:.1f}",
                      f"{tf['mean'] * 100:.1f}" if tf else "—"])
    payload = {
        "title": f"テーブルクロスの曲げの硬さは、既定 0.1 から下げても形はほぼ同じ（差 {t['b-3']['to_default']['mean'] * 100:.1f} cm）。10 に上げると布が張って机から {out('b1'):.0f} cm 張り出し、裾が {(hem('b1') - hem('b-1')) * 100:.0f} cm 上がる",
        "summary":
            "**課題: 薄い布と厚い布を見せ分けたい。vellumconstraints の Cloth の曲げの硬さ（Bend の Stiffness、既定 1 × 10⁻¹ = 0.1）をいくつにすると、ひだと垂れ方がどう変わるのか。**\n\n"
            f"実験206・211 と同じ机と布（{d['grid_rows']}×{d['grid_cols']}）を {d['last']} フレーム落とし、曲げの硬さだけを 0.001・0.1・10・1000 にした（Stiffness 1 のまま、× の指数を −3・−1・1・3）。"
            "机の +x 側、脚の間に垂れた面（天板より下）で、布の点が机の縁（x = 0.6）からどれだけ外にあるか（張り出し）と、その出入りのばらつきを測った。\n\n"
            f"**既定より柔らかくしても、ほとんど変わらない。**0.001 は、既定との形の差が平均 {t['b-3']['to_default']['mean'] * 100:.1f} cm。"
            f"張り出し {out('b-3'):.1f} cm（既定 {out('b-1'):.1f} cm）、裾の高さも同じ。角だけ {(t['b-1']['lowest'] - t['b-3']['lowest']) * 100:.1f} cm 長く垂れた。"
            "既定の 0.1 で、この布はもう十分柔らかい。\n\n"
            f"**10 以上にすると、布が板のように張る。**10 では机の縁から {out('b1'):.1f} cm 外へ張り出し（既定 {out('b-1'):.1f} cm）、四辺の裾は平均 {hem('b1'):.3f} m（既定 {hem('b-1'):.3f} m）、"
            f"角のいちばん低い点は {t['b1']['lowest']:.3f} m（既定 {t['b-1']['lowest']:.3f} m）。1000 もほぼ同じ形（張り出し {out('b3'):.1f} cm）。既定との形の差は平均 {t['b1']['to_default']['mean'] * 100:.1f} cm。\n\n"
            f"**ひだの出入りは、硬いほど大きい。**脚の間の面の出入りのばらつきは 0.001・0.1・10・1000 で {t['b-3']['side_x_std_mm']:.0f}・{t['b-1']['side_x_std_mm']:.0f}・{t['b1']['side_x_std_mm']:.0f}・{t['b3']['side_x_std_mm']:.0f} mm。"
            "柔らかい布はまっすぐ下へ落ち、硬い布は大きく波打ったまま止まる。\n\n"
            "**決め方: この大きさの布（1.9 × 1.45 m、66×84）では、0.1 と 10 の間で見せ分ける。**0.1 より下げても見た目は変わらない。"
            "間の値（1 など）は試していない。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "曲げの硬さを変えたテーブルクロス（72 フレーム目）",
             "images": [{"path": "217_grid.png", "caption": "0.001 と 0.1 はほぼ同じ。10 と 1000 は布が張って机から突き出す。"}],
             "per_row": 1, "columns": ["曲げの硬さ", "いちばん低い点（m）", "裾の高さ（m）", "張り出し（cm）", "出入りのばらつき（mm）", "既定との差 平均（cm）"],
             "rows": table},
        ],
        "notes": [
            "<strong>曲げの硬さを既定の 0.1 より下げても、形はほとんど変わらない。</strong>",
            f"<strong>10 に上げると布が張る。</strong>机の縁から {out('b1'):.0f} cm 張り出し、裾が {(hem('b1') - hem('b-1')) * 100:.0f} cm 上がった。",
            "<strong>硬いほど、ひだは大きく波打ったまま止まる。</strong>柔らかい布はまっすぐ落ちる。",
            "<strong>0.1〜10 の間（1 など）は試していない。</strong>見せ分けはこの間で探す。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "217_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 217_report.json")
    print(payload["title"])


if __name__ == "__main__":
    main()
