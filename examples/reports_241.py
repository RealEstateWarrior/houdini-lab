# -*- coding: utf-8 -*-
"""実験241 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font, line_chart  # noqa: E402

DN = {"off": "ノイズ除去なし", "oidn": "OIDN", "optix": "OptiX"}
SC = {"donut": "ドーナツ", "snowman": "雪だるま"}


def main():
    with open(os.path.join(OUT, "241_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    t = {(r["scene"], r["spp"], r["denoiser"]): r for r in rows}
    series = []
    for sc in SC:
        for dn in DN:
            series.append({"label": f"{SC[sc]}・{DN[dn]}", "points": [(t[(sc, s, dn)]["sec"], t[(sc, s, dn)]["diff"]) for s in (4, 8, 16, 32)]})
    line_chart(os.path.join(OUT, "241_curve.png"), series, "撮る時間と、512 サンプルの画との差（4・8・16・32 サンプル）", "撮る時間（秒）", "差（0〜255）")
    font = _font(15)
    box = (240, 120, 400, 220)
    shots = [("4_off", "4 サンプル・なし"), ("4_oidn", "4 サンプル・OIDN"), ("4_optix", "4 サンプル・OptiX"), ("32_off", "32 サンプル・なし"), ("ref", "512 サンプル（基準）")]
    sheet = Image.new("RGB", (320 * 5, 200 + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, lab) in enumerate(shots):
        sheet.paste(Image.open(os.path.join(OUT, f"241_donut_{k}.png")).convert("RGB").crop(box).resize((320, 200)), (i * 320, 26))
        dr.text((i * 320 + 6, 4), lab, fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "241_grid.png"))
    table = [[SC[sc], str(s), DN[dn], f"{t[(sc, s, dn)]['sec']:.1f}", f"{t[(sc, s, dn)]['diff']:.2f}"] for sc in SC for s in (4, 8, 16, 32) for dn in DN]
    d = lambda sc, s, dn: t[(sc, s, dn)]["diff"]  # noqa: E731
    sec = lambda sc, s, dn: t[(sc, s, dn)]["sec"]  # noqa: E731
    payload = {
        "title": f"Karma のノイズ除去は、4 サンプルでも 32 サンプル（なし）と同じくらい基準に近い（ドーナツ 差 {d('donut', 4, 'optix'):.2f} と {d('donut', 32, 'off'):.2f}）。"
                 f"時間は 1/5。OptiX と OIDN はほぼ同じで、OptiX がわずかに近い",
        "summary":
            "**課題: 試し撮りや映像は、サンプルを減らしてノイズ除去で仕上げたい。Karma の Denoiser には Intel OIDN と NVIDIA OptiX がある。"
            "どちらが速く、どちらが本物（たくさんサンプルを取った画）に近いか。何サンプルまで減らしてよいか。**\n\n"
            "実践 2 本（ドーナツ＝細かいスプリンクル、雪だるま＝SSS のなめらかな雪）を 640×360 で、4・8・16・32 サンプル × ノイズ除去なし・OIDN・OptiX で撮った。"
            "基準は 512 サンプル・ノイズ除去なし。差は画素ごとの差の平均（0〜255、右下の透かしは除く）。はじめにそれぞれ 1 枚撮って捨てた。\n\n"
            f"**4 サンプル＋ノイズ除去で、32 サンプル（なし）と同じくらい。**ドーナツは 4 サンプルで、なし {d('donut', 4, 'off'):.2f}・OIDN {d('donut', 4, 'oidn'):.2f}・OptiX {d('donut', 4, 'optix'):.2f}、"
            f"32 サンプルなしで {d('donut', 32, 'off'):.2f}。雪だるまは 4 サンプルで、なし {d('snowman', 4, 'off'):.2f}・OIDN {d('snowman', 4, 'oidn'):.2f}・OptiX {d('snowman', 4, 'optix'):.2f}、"
            f"32 サンプルなしで {d('snowman', 32, 'off'):.2f}（なめらかな面ほど、ノイズ除去がよく効く）。"
            f"時間は 4 サンプル {sec('donut', 4, 'optix'):.1f} 秒、32 サンプル {sec('donut', 32, 'off'):.1f} 秒（ドーナツ）。画でも、4 サンプル＋ノイズ除去のスプリンクルは形が崩れていなかった。\n\n"
            f"**OptiX と OIDN はほぼ同じ。**どのサンプル数でも OptiX がわずかに基準に近く（ドーナツ 16 サンプルで {d('donut', 16, 'optix'):.2f} と {d('donut', 16, 'oidn'):.2f}）、"
            "ノイズ除去にかかる時間は、どちらも撮る時間に 1 秒も足さなかった。\n\n"
            "**サンプルを増やしても、ノイズ除去した画はあまり良くならない。**ドーナツ・OptiX で 4・8・16・32 サンプルの差は "
            f"{d('donut', 4, 'optix'):.2f}・{d('donut', 8, 'optix'):.2f}・{d('donut', 16, 'optix'):.2f}・{d('donut', 32, 'optix'):.2f}。\n\n"
            "**決め方: 試し撮りと映像は 4〜8 サンプル＋OptiX（NVIDIA の GPU が無ければ OIDN）。**仕上げの静止画は 16〜32 サンプル＋ノイズ除去。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "ノイズ除去とサンプル数（640×360）",
             "images": [{"path": "241_grid.png", "caption": "ドーナツの真ん中を切り出し。4 サンプル＋ノイズ除去でも、スプリンクルの形は崩れない。"},
                        {"path": "241_curve.png", "caption": "ノイズ除去あり（OIDN・OptiX）は、少ないサンプルでも基準との差が小さい。"}],
             "per_row": 1, "columns": ["場面", "サンプル", "ノイズ除去", "撮る時間（秒）", "基準との差（0〜255）"], "rows": table},
        ],
        "notes": [
            f"<strong>4 サンプル＋ノイズ除去で、32 サンプル（なし）と同じくらい基準に近い。</strong>時間は約 1/5。",
            "<strong>OptiX と OIDN はほぼ同じ。OptiX がわずかに近い。</strong>ノイズ除去の時間は 1 秒未満。",
            "<strong>なめらかな面（雪）ほど、ノイズ除去がよく効く。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "241_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
