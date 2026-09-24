# -*- coding: utf-8 -*-
"""実験243 の図とレポートを、測った値から組み立てる（2 回目＝Cd を持つ球と同じ形の中、1 回目＝Cd の無い形 out/243_first.json）。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"P": "principledshader・色ピンク（Cd は merge で付いた既定の白）", "Pw": "principledshader・色ピンク・Cd 白", "Pk": "principledshader・色ピンク・Cd 黒",
       "M": "MaterialX・色ピンク", "Mw": "MaterialX・色ピンク・Cd 白", "MR": "MaterialX・色 赤", "ME": "MaterialX・光る色ピンク"}


def main():
    with open(os.path.join(OUT, "243_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    with open(os.path.join(OUT, "243_first.json"), encoding="utf-8") as fp:
        first = {r["case"]: r for r in json.load(fp)["rows"]}
    t = {r["case"]: r for r in d["rows"]}
    font = _font(15)
    sheet = Image.new("RGB", (640, 200 * 2 + 60), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 6), "上: CPU　下: XPU（左から P・Pw・Pk・M・Mw・MR・ME）", fill=(30, 30, 30), font=font)
    sheet.paste(Image.open(os.path.join(OUT, "243_cpu_withcd.png")).convert("RGB"), (0, 30))
    sheet.paste(Image.open(os.path.join(OUT, "243_xpu_withcd.png")).convert("RGB"), (0, 250))
    sheet.save(os.path.join(OUT, "243_grid.png"))
    f = lambda c: "（" + "・".join(f"{v:.2f}" for v in c) + "）"  # noqa: E731
    table = [[k, LAB[k], f(t[k]["cpu"]), f(t[k]["xpu"])] for k in LAB]
    table += [["P（Cd の無い形）", "principledshader・色ピンク。形のどこにも Cd が無い", f(first["P"]["cpu"]), f(first["P"]["xpu"])]]
    payload = {
        "title": "Karma XPU では、形に点の色 Cd があると、principledshader の色が Cd に置き換わる（Use Point Color を切っていても）。"
                 "Cd の無い形なら材質の色が出る。MaterialX の材質は、Cd があっても CPU と同じ色",
        "summary":
            "**課題: 実験242 で、XPU では principledshader の色が白くなった。XPU で材質の色を効かせるにはどうすればよいか。MaterialX の材質（mtlxstandard_surface）なら出るか。**\n\n"
            "球を並べ、principledshader と MaterialX の材質を当てて、CPU と XPU で撮った（640×200・32 サンプル、別の hython）。"
            "はじめは Cd の無い球 4 つだけで撮り、次に Cd を白・黒にした球を足して、同じ形（1 つの merge）にまとめて撮った。\n\n"
            f"**Cd の無い形なら、XPU でも principledshader の色が出た。**1 回目、色ピンクの P は XPU で {f(first['P']['xpu'])}（CPU {f(first['P']['cpu'])}）。"
            "実験242 の A と同じ材質なのに、ピンクに写った。\n\n"
            f"**形に Cd があると、XPU では principledshader の色が Cd に置き換わる。**2 回目、Cd を白にした Pw は {f(t['Pw']['xpu'])}、黒にした Pk は {f(t['Pk']['xpu'])}。"
            f"Cd を付けていない P も、Cd のある球と merge したので Cd（既定の白）が付き、{f(t['P']['xpu'])} と白くなった。材質の Use Point Color は切ってある。"
            "CPU では、どれも材質の色（ピンク）だった。実験242 で球がすべて白くなったのは、Cd を付けた球と同じ形にまとめていたため。\n\n"
            f"**MaterialX の材質は、Cd があっても CPU と同じ色。**M {f(t['M']['xpu'])}、Cd 白の Mw {f(t['Mw']['xpu'])}、赤の MR {f(t['MR']['xpu'])}、"
            f"光る ME {f(t['ME']['xpu'])}。CPU との差は、どれも 0.001 以下。\n\n"
            "**ドーナツのアイシングが白くなったのも同じ理由と考えられる。**アイシングは Cd を消していたが、揚げ色の Cd を持つ生地と同じ形にまとめていたので、"
            "merge で既定の白の Cd が付いた（ドーナツの最終の形には Cd がある）。\n\n"
            "**決め方: XPU で撮るなら、材質は MaterialX（mtlxstandard_surface）で作る。**principledshader のまま XPU で撮るなら、色は Cd で付ける（Cd のある形では材質の色は使われない）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Cd のある形での、材質ごとの色（CPU と XPU）",
             "images": [{"path": "243_grid.png", "caption": "上が CPU、下が XPU。principledshader の 3 つ（左）は XPU で Cd の色になり、MaterialX の 4 つ（右）は CPU と同じ。"}],
             "per_row": 1, "columns": ["球", "材質", "CPU の色（RGB）", "XPU の色（RGB）"], "rows": table},
        ],
        "notes": [
            "<strong>XPU では、形に Cd があると、principledshader の色が Cd に置き換わる。</strong>Use Point Color を切っていても同じ。",
            "<strong>Cd の無い形なら、XPU でも principledshader の色が出る。</strong>",
            "<strong>MaterialX の材質は、Cd があっても CPU と同じ色。</strong>XPU で撮るなら MaterialX で作る。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "243_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
