# -*- coding: utf-8 -*-
"""実験248 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"principled_cpu": "principledshader・CPU", "principled_xpu": "principledshader・XPU", "mtlx_cpu": "MaterialX・CPU", "mtlx_xpu": "MaterialX・XPU"}


def main():
    with open(os.path.join(OUT, "248_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(15)
    w, h = 280, 330
    sheet = Image.new("RGB", (w * 4, h + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(LAB):
        sheet.paste(Image.open(os.path.join(OUT, f"248_{k}.png")).convert("RGB").crop((180, 20, 460, 350)), (i * w, 26))
        dr.text((i * w + 6, 4), f"{LAB[k]}  {t[k]['sec']:.0f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "248_grid.png"))
    table = [[LAB[k], f"{t[k]['sec']:.1f}", f"{t[k]['mean']:.1f}", f"{t[k]['diff_to_cpu']:.1f}"] for k in LAB]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": f"グラスの場面も、材質を MaterialX にすると Karma の CPU と XPU がほぼ同じ絵になった（差 {g('mtlx_xpu', 'diff_to_cpu'):.1f}、principledshader では {g('principled_xpu', 'diff_to_cpu'):.1f}）。"
                 f"XPU は {g('mtlx_xpu', 'sec'):.0f} 秒、CPU は {g('mtlx_cpu', 'sec'):.0f} 秒",
        "summary":
            "**課題: 実験232 で、氷の入ったグラスの水を XPU で撮ると、全体が明るく飛んだ。この場面には点の色 Cd が無いので、実験243（Cd があると principledshader の色が置き換わる）とは別の原因。"
            "材質を MaterialX（mtlxstandard_surface）に替えると揃うのか。**\n\n"
            "実践「氷の入ったグラスの水」の /mat の材質 5 つ（幕・ガラス・水・氷・氷の芯）を、同じ色・Roughness・IOR の mtlxstandard_surface に差し替え"
            "（透明なものは transmission に Transparency の値）、CPU と XPU で撮った（640×360・32 サンプル・ノイズ除去なし、条件ごとに別の hython）。"
            "差し替えでは、水の Transmission Color・Distance（水のわずかな色）は移していない。\n\n"
            f"**MaterialX なら、CPU と XPU がほぼ同じ。**画の差（0〜255）は MaterialX で {g('mtlx_xpu', 'diff_to_cpu'):.1f}、principledshader で {g('principled_xpu', 'diff_to_cpu'):.1f}。"
            f"画の明るさの平均は、principledshader の CPU {g('principled_cpu', 'mean'):.0f}・XPU {g('principled_xpu', 'mean'):.0f}、MaterialX の CPU {g('mtlx_cpu', 'mean'):.0f}・XPU {g('mtlx_xpu', 'mean'):.0f}。\n\n"
            "**明るさがほかと違ったのは、principledshader の CPU の方だった。**principledshader の XPU と、MaterialX の 2 つは、同じくらい明るかった。"
            "画でも、principledshader の CPU だけ水と氷が暗く沈み、ほかの 3 つは水が明るく透けた。"
            "どちらが本物に近いかは、この実験では決めていない（MaterialX には水の色を移していないので、そのぶんも明るい）。\n\n"
            f"**時間: XPU はどちらも約 {g('mtlx_xpu', 'sec'):.0f} 秒。CPU は MaterialX で {g('mtlx_cpu', 'sec'):.0f} 秒と、principledshader（{g('principled_cpu', 'sec'):.0f} 秒）より長かった。**\n\n"
            "**決め方: XPU で試し撮りして CPU で仕上げるなら、材質は MaterialX で作る（両方が同じ絵になる）。**principledshader のまま XPU で試すと、仕上げの CPU と違う絵になる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "材質と Engine（640×360・32 サンプル、グラスのまわりを切り出し）",
             "images": [{"path": "248_grid.png", "caption": "principledshader の CPU だけ水と氷が暗い。MaterialX は CPU と XPU がほぼ同じ。"}],
             "per_row": 1, "columns": ["材質・Engine", "撮る時間（秒）", "画の明るさの平均", "同じ材質の CPU との差"], "rows": table},
        ],
        "notes": [
            f"<strong>MaterialX なら、グラスの場面も CPU と XPU がほぼ同じ絵（差 {g('mtlx_xpu', 'diff_to_cpu'):.1f}）。</strong>",
            "<strong>明るさが違ったのは principledshader の CPU の方。</strong>どちらが本物に近いかは決めていない。",
            "<strong>XPU で試して CPU で仕上げるなら、材質は MaterialX で作る。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "248_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
