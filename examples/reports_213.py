# -*- coding: utf-8 -*-
"""実験213 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"none": "SSS なし", "d001": "Distance 0.01", "d005": "0.05", "d010": "0.1（既定）", "d030": "0.3", "d100": "1",
       "rw010": "Random Walk 0.1"}


def strip(path, light, names, gain):
    font = _font(16)
    size = 260
    im = Image.new("RGB", (size * len(names), size + 28), (20, 20, 22))
    dr = ImageDraw.Draw(im)
    for i, n in enumerate(names):
        p = Image.open(os.path.join(OUT, f"213_{light}_{n}.png")).convert("RGB").crop((100, 60, 540, 500)).resize((size, size))
        if gain != 1:
            p = ImageEnhance.Brightness(p).enhance(gain)
        im.paste(p, (i * size, 28))
        dr.text((i * size + 8, 5), LAB[n], fill=(235, 235, 235), font=font)
    im.save(path)


def main():
    with open(os.path.join(OUT, "213_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    names = ["none", "d010", "d030", "d100", "rw010"]
    strip(os.path.join(OUT, "213_back.png"), "back", names, 3.0)
    strip(os.path.join(OUT, "213_front.png"), "front", names, 1.0)
    b = lambda k: t[k]["back_center"] / t["none"]["back_center"]  # noqa: E731
    f = lambda k: t[k]["front_all"] / t["none"]["front_all"]  # noqa: E731
    table = [[LAB[k], f"{t[k]['back_center']:.4f}", f"{b(k):.1f}", f"{t[k]['back_edge']:.4f}", f"{t[k]['front_all']:.3f}", f"{f(k):.2f}"]
             for k in LAB]
    payload = {
        "title": f"SSS で透けて見せるなら、半径 0.5 の球では Subsurface Distance 0.1〜0.3 — 0.3 のとき逆光の真ん中が {b('d030'):.1f} 倍明るい。1 にするとかえって暗く、正面から見ても {f('d100'):.0%} に沈む",
        "summary":
            "**課題: ろうそく・雪・肌・石けんのような「光が中に入って透ける」物を作りたい。principledshader の Subsurface を入れたとき、Subsurface Distance（光が中で散らばる距離、既定 0.1）をいくつにすると、どれだけ透けて見えるのか。**\n\n"
            "半径 0.5 の球に Base Color (0.9, 0.85, 0.75) の材質を当て、Subsurface 1 で Distance を 0.01〜1 にした。実践と同じ正面寄りの明かりと、キーの明かりを球の真後ろに回した逆光の 2 通りで、"
            "640×640・16 サンプル＋ノイズ除去・EXR で撮り、OpenImageIO で明るさを測った。逆光の画では、球の真ん中（厚い所）と縁（薄い所）を分けて測った。\n\n"
            f"**逆光で透けが見え始めるのは 0.1 から。**真ん中の明るさは SSS なしを 1 として、0.01 で {b('d001'):.2f}、0.05 で {b('d005'):.2f}、0.1 で {b('d010'):.1f}、0.3 で {b('d030'):.1f}。"
            "0.05 までは、逆光の画は SSS なしとほとんど変わらない。\n\n"
            f"**大きすぎると、かえって暗い。**1 では真ん中が {b('d100'):.1f} 倍で、0.3 より暗かった。正面から撮った画も、球の平均の明るさが SSS なしの {f('d100'):.0%}（0.3 で {f('d030'):.0%}）に下がり、"
            "ざらつきも増えた。光が中で遠くまで散らばって、外へ出てくる量が減るためと考えられる（確かめていない）。\n\n"
            f"**Random Walk（Karma）は、同じ距離でもよく透ける。**0.1 で真ん中が {b('rw010'):.1f} 倍（既定の方式は {b('d010'):.1f} 倍）。正面から見た明るさは {f('rw010'):.0%} で、暗くならない。\n\n"
            "**目安: 半径 0.5 の球で透けを出すなら、Distance 0.1〜0.3。**Distance は長さ（m）なので、物の大きさが違えば合う値も変わると考えられるが、"
            "ここで確かめたのは半径 0.5 の球だけ。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "逆光で撮った球（表示だけ明るさを 3 倍にした）",
             "images": [{"path": "213_back.png", "caption": "左から SSS なし・0.1・0.3・1・Random Walk 0.1。SSS なしは真っ暗、0.1〜0.3 で内側から明るい。"},
                        {"path": "213_front.png", "caption": "同じ材質を正面寄りの明かりで。1 は暗く、ざらつく。"}],
             "per_row": 1,
             "columns": ["設定", "逆光・真ん中", "SSS なしとの比", "逆光・縁", "正面・球の平均", "SSS なしとの比"], "rows": table},
        ],
        "notes": [
            f"<strong>半径 0.5 の球で透けを出すなら Subsurface Distance 0.1〜0.3。</strong>0.3 のとき、逆光の真ん中が {b('d030'):.1f} 倍明るかった。",
            "<strong>0.05 以下では、ほとんど透けない。</strong>逆光の画は SSS なしとほぼ同じ。",
            f"<strong>大きくしすぎると暗くなる。</strong>1 では正面から見ても明るさ {f('d100'):.0%}、ざらつきも増えた。",
            f"<strong>Random Walk（Karma）は同じ距離でもよく透け、暗くならない。</strong>0.1 で逆光の真ん中が {b('rw010'):.1f} 倍。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "213_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 213_report.json")
    print(payload["title"])


if __name__ == "__main__":
    main()
