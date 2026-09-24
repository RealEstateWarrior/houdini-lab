# -*- coding: utf-8 -*-
"""実験218 の図とレポートを、測った値から組み立てる。

光の道の「粒っぽさ」は、見る用の PNG（0〜1 に切ったもの）で、光の道の列の明るさの むら（標準偏差 ÷ 平均）として測る。
粒が細かく散っていると大きく、べったり白い帯になると小さい。
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

ROUGH = (0.005, 0.02, 0.04, 0.08, 0.15)
AMP = (0.4, 1.6, 3.2)


def png(r, a):
    return os.path.join(OUT, f"218_r{r:g}_a{a:g}".replace(".", "p") + ".png")


def main():
    with open(os.path.join(OUT, "218_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    y0, y1 = d["band_rows"]
    t = {(r["rough"], r["amp"]): r for r in d["rows"]}
    # むら（標準偏差 ÷ 平均）を PNG から
    for (r, a), row in t.items():
        lum = np.asarray(Image.open(png(r, a)).convert("L"), dtype=float) / 255
        band = lum[y0:y1]
        if row["span"]:
            c0, c1 = row["span"]
            sub = band[:, c0:c1 + 1]
            row["cv"] = round(float(sub.std() / sub.mean()), 3)
        else:
            row["cv"] = None
    # 図: 光の道のまわりを切り出して 5 × 3 に並べる
    font = _font(15)
    cw, ch, top, left = 300, 110, 26, 110
    sheet = Image.new("RGB", (left + cw * 5, top + ch * 3), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, r in enumerate(ROUGH):
        dr.text((left + i * cw + 8, 5), f"Roughness {r:g}", fill=(30, 30, 30), font=font)
    for j, a in enumerate(AMP):
        dr.text((6, top + j * ch + 40), f"さざ波の高さ\n{a:g}", fill=(30, 30, 30), font=font)
        for i, r in enumerate(ROUGH):
            im = Image.open(png(r, a)).convert("RGB").crop((36, 120, 336, 230))
            sheet.paste(im, (left + i * cw, top + j * ch))
    sheet.save(os.path.join(OUT, "218_grid.png"))
    g = lambda r, a: t[(r, a)]  # noqa: E731
    table = []
    for a in AMP:
        for r in ROUGH:
            row = g(r, a)
            table.append([f"{r:g}", f"{a:g}", str(row["width_px"]), f"{row['width_px'] * 0.18:.1f}",
                          f"{row['energy']:.3f}", "—" if row["cv"] is None else f"{row['cv']:.2f}", f"{row['bg']:.3f}"])
    w = lambda r, a: g(r, a)["width_px"]  # noqa: E731
    cv = lambda r, a: g(r, a)["cv"]  # noqa: E731
    payload = {
        "title": f"海の光の道は、Roughness を上げると太い白い帯になり（0.02→0.15 で幅 {w(0.02, 1.6)}→{w(0.15, 1.6)} 列）、"
                 f"さざ波を高くすると粒のまま広がる（0.4→3.2 で {w(0.04, 0.4)}→{w(0.04, 3.2)} 列）",
        "summary":
            "**課題: 海の画で太陽の下の光の道を「もっと広く」「もっと細かくきらめかせたい」とき、水の材質の Roughness と、さざ波の高さのどちらを動かせばよいか。**\n\n"
            "実践「冬の朝の七里ヶ浜」の場面（太陽は高さ 15°・左へ 12°、砂浜の目の高さ 1.5 m から撮る）で、水の Roughness を 0.005・0.02・0.04・0.08・0.15、"
            "さざ波（Grid Size 1.3 m の oceanspectrum）の Amplitude の Scale を 0.4・1.6・3.2 にした 15 通りを、Karma で 480×270 の EXR に撮った。"
            f"カメラから約 12〜60 m 先の水面（縦 {y0}〜{y1} 行）で、列ごとの明るさが太陽から離れた所の 3 倍を超える列の数を「光の道の幅」とした（1 列は約 0.18°）。\n\n"
            f"**Roughness を上げると、光の道は太くなるが、白い帯になる。**さざ波 1.6 で、Roughness 0.02・0.04・0.08・0.15 の幅は "
            f"{w(0.02, 1.6)}・{w(0.04, 1.6)}・{w(0.08, 1.6)}・{w(0.15, 1.6)} 列。明るさの合計は 0.014 → 0.459 と 30 倍以上になった。"
            f"ただし光の道の中の明るさのむら（標準偏差 ÷ 平均）は {cv(0.02, 1.6):.2f} → {cv(0.15, 1.6):.2f} と下がり、画で見ても粒が消えてべったり白く光った。\n\n"
            f"**さざ波を高くすると、粒のまま広がる。**Roughness 0.04 で、さざ波 0.4・1.6・3.2 の幅は {w(0.04, 0.4)}・{w(0.04, 1.6)}・{w(0.04, 3.2)} 列、"
            f"むらは {cv(0.04, 0.4):.2f}・{cv(0.04, 1.6):.2f}・{cv(0.04, 3.2):.2f}。水面が傾く向きがばらけるので、太陽を映す面が広く散らばる。"
            f"さざ波を高くすると、光の道の外の水面は暗くなった（太陽から離れた所の明るさ {g(0.04, 0.4)['bg']:.3f} → {g(0.04, 3.2)['bg']:.3f}）。"
            "3.2 では、さざ波の設計図のくり返し（1.3 m ごと）が横縞になって見えた。\n\n"
            f"**Roughness 0.005 では、光の道がほとんど出ない。**さざ波 0.4 で幅 {w(0.005, 0.4)} 列、1.6 で {w(0.005, 1.6)} 列。"
            "太陽は見かけ 0.54° と小さいので、面の向きがちょうど合った所だけが光る。\n\n"
            "**決め方: 写真のように広い範囲を細かくきらめかせるなら、Roughness は 0.02〜0.04 に抑えて、さざ波を高くする。**"
            "Roughness は光の道を太くしたいときに少し上げる（0.08 から白い帯に見え始める）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Roughness（横）とさざ波の高さ（縦）を変えた光の道（フレーム 30）",
             "images": [{"path": "218_grid.png", "caption": "右へ行くほど白い帯に、下へ行くほど粒が広く散らばる。"}],
             "per_row": 1,
             "columns": ["Roughness", "さざ波の高さ", "光の道の幅（列）", "幅（度）", "明るさの合計", "むら", "外の水面の明るさ"],
             "rows": table},
        ],
        "notes": [
            f"<strong>Roughness を上げると光の道は太くなるが、白い帯になる。</strong>0.02→0.15 で幅 {w(0.02, 1.6)}→{w(0.15, 1.6)} 列、むら {cv(0.02, 1.6):.2f}→{cv(0.15, 1.6):.2f}。",
            f"<strong>さざ波を高くすると、粒のまま広がる。</strong>0.4→3.2 で幅 {w(0.04, 0.4)}→{w(0.04, 3.2)} 列（Roughness 0.04）。",
            "<strong>さざ波を高くすると、光の道の外の水面は暗くなる。</strong>高すぎると、設計図のくり返しが横縞に見える。",
            "<strong>細かくきらめかせるなら、Roughness は 0.02〜0.04 に抑え、さざ波で広げる。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "218_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 218_report.json")
    print(payload["title"])
    for k in sorted(t):
        print(k, t[k]["width_px"], t[k]["cv"])


if __name__ == "__main__":
    main()
