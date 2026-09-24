# -*- coding: utf-8 -*-
"""実験212 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font, line_chart  # noqa: E402


def main():
    with open(os.path.join(OUT, "212_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows = d["rows"]
    t = {r["rough"]: r for r in rows}
    font = _font(17)
    size = 300
    strip = Image.new("RGB", (size * 4, (size + 30) * 2), (20, 20, 22))
    dr = ImageDraw.Draw(strip)
    for i, r in enumerate(rows):
        im = Image.open(os.path.join(OUT, f"212_r{int(r['rough'] * 100):03d}.png")).convert("RGB").crop((100, 60, 540, 500)).resize((size, size))
        x, y = (i % 4) * size, (i // 4) * (size + 30)
        strip.paste(im, (x, y + 30))
        dr.text((x + 8, y + 5), f"Roughness {r['rough']:g}", fill=(235, 235, 235), font=font)
    strip.save(os.path.join(OUT, "212_strip.png"))
    p0 = t[0.0]["peak"]
    a0 = t[0.0]["half_area_frac"]
    line_chart(os.path.join(OUT, "212_chart.png"),
               [{"label": "いちばん明るい所（Roughness 0 を 1 とした比）", "points": [(r["rough"], r["peak"] / p0) for r in rows], "color": PALETTE[0]},
                {"label": "ハイライトの広さ（同じく比）", "points": [(r["rough"], r["half_area_frac"] / a0) for r in rows], "color": PALETTE[1]}],
               title="Roughness とハイライト", x_label="Roughness", y_label="Roughness 0 との比")
    table = [[f"{r['rough']:g}", f"{r['peak']:.2f}", f"{r['peak'] / p0:.2f}", f"{r['half_area_frac']:.2%}", f"{r['half_area_frac'] / a0:.2f}",
              f"{r['mean_on_sphere']:.3f}"] for r in rows]
    pk = lambda r: t[r]["peak"] / p0  # noqa: E731
    ar = lambda r: t[r]["half_area_frac"] / a0  # noqa: E731
    payload = {
        "title": f"金属の Roughness は 0.2 まで見た目がほぼ同じ — ハイライトが広がり始めるのは 0.3 から。0.5 で明るさ {pk(0.5):.0%}・広さ {ar(0.5):.1f} 倍、0.7 で {pk(0.7):.0%}・{ar(0.7):.1f} 倍",
        "summary":
            "**課題: 金属を「つやつや」から「つや消し」まで見せ分けたい。principledshader の Roughness をいくつにすると、ハイライト（明かりの映り込み）がどれだけ広がって、どれだけ暗くなるのか。**\n\n"
            "半径 0.5 の球に、Base Color 0.9・Metallic 1 の金属を当て、Roughness を 0〜0.7 の 7 段階にして、実践と同じ撮り方（暗い幕・板のキー・リム・弱いドーム）で "
            f"{d['res'][0]}×{d['res'][1]}・16 サンプル＋ノイズ除去で撮った。画は EXR（1 を超える明るさも切れない）で書き、OpenImageIO で読んで測った。"
            "キーの映り込みのいちばん明るい画素の明るさ（輝度）と、その半分より明るい画素の数（ハイライトの広さ。球の画素数に対する割合）を比べる。\n\n"
            f"**0.2 までは、ハイライトの広さがほとんど変わらない。**球の {a0:.2%}（0）→ {t[0.2]['half_area_frac']:.2%}（0.2）。明るさも {pk(0.2):.0%} までしか下がらない。"
            "並べると、0〜0.1 は鏡のまま、0.2 で映り込みの縁が少しぼけるだけ。キーの明かりは板（球の大きさの 1.2 倍）なので、映り込みの形はまず板の形で決まり、粗さのぼけが板より小さいうちは広がらないと考えられる。\n\n"
            f"**0.3 から広がり、暗くなる。**0.3 で明るさ {pk(0.3):.0%}・広さ {ar(0.3):.2f} 倍、0.5 で {pk(0.5):.0%}・{ar(0.5):.2f} 倍、0.7 で {pk(0.7):.0%}・{ar(0.7):.1f} 倍。"
            "0.7 では、板の四角い形はもう分からない。\n\n"
            f"**球全体の明るさは、ほとんど変わらない。**球の画素の平均は {t[0.0]['mean_on_sphere']:.3f}〜{max(r['mean_on_sphere'] for r in rows):.3f}。"
            "光の量は同じまま、集まっているか広がっているかが変わる。\n\n"
            "**目安: この撮り方（板のキー）で見分けがつくのは 0.2 → 0.3 → 0.5 → 0.7 の段。**"
            "0 と 0.05・0.1 は、キーの映り込みの縁がわずかに柔らかくなるだけだった。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Roughness を変えた金属の球",
             "images": [{"path": "212_strip.png", "caption": "上の段 0・0.05・0.1・0.2、下の段 0.3・0.5・0.7。0.2 までは鏡に近く、0.3 から映り込みがぼける。"},
                        {"path": "212_chart.png", "caption": "Roughness 0 を 1 とした、いちばん明るい所とハイライトの広さ。"}],
             "per_row": 1, "columns": ["Roughness", "いちばん明るい所", "0 との比", "ハイライトの広さ（球に対して）", "0 との比", "球の平均の明るさ"],
             "rows": table},
        ],
        "notes": [
            f"<strong>Roughness 0〜0.2 は、見た目がほとんど同じ。</strong>ハイライトの広さは変わらず、明るさも {1 - pk(0.2):.0%} しか下がらない（板の明かりのとき）。",
            f"<strong>映り込みをぼかすなら 0.5 以上。</strong>0.5 で明るさ {pk(0.5):.0%}・広さ {ar(0.5):.1f} 倍。0.7 で四角い映り込みが消えた。",
            f"<strong>球全体の明るさはほぼ同じ。</strong>平均 {min(r['mean_on_sphere'] for r in rows):.2f}〜{max(r['mean_on_sphere'] for r in rows):.2f}。変わるのは光の集まり方。",
            "<strong>明かりの形が映り込む。</strong>板の明かりの四角が、0.2 まではそのまま見えた。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "212_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 212_report.json")
    print(payload["title"])


if __name__ == "__main__":
    main()
