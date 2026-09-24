# -*- coding: utf-8 -*-
"""実験242 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"A": "色ピンク・Use Point Color 切り・Cd なし", "B": "色ピンク・Use Point Color 入り・Cd なし（アイシング）",
       "C": "色 白・Use Point Color 入り・Cd ピンク（生地）", "D": "色ピンク・Use Point Color 入り・Cd 白",
       "E": "光る色 白・Use Point Color 入り・Cd ピンク（海の空）", "F": "光る色ピンク・Use Point Color 切り"}


def main():
    with open(os.path.join(OUT, "242_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    font = _font(15)
    sheet = Image.new("RGB", (640, 400 + 60), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 6), "上: CPU　下: XPU（左から A〜F）", fill=(30, 30, 30), font=font)
    sheet.paste(Image.open(os.path.join(OUT, "242_cpu.png")).convert("RGB"), (0, 30))
    sheet.paste(Image.open(os.path.join(OUT, "242_xpu.png")).convert("RGB"), (0, 250))
    sheet.save(os.path.join(OUT, "242_grid.png"))
    f = lambda c: "（" + "・".join(f"{v:.2f}" for v in c) + "）"  # noqa: E731
    table = [[k, LAB[k], f(t[k]["cpu"]), f(t[k]["xpu"])] for k in LAB]
    payload = {
        "title": "Karma XPU では、principledshader の色（Base Color）が効かずに白くなる。点の色（Cd）は効く。"
                 "実験232 でアイシングが白くなったのはこのため",
        "summary":
            "**課題: 実験232 で、XPU で撮るとドーナツのアイシングと海の空が白くなった。アイシングの材質は「色ピンク・Use Point Color 入り・点の色 Cd なし」、"
            "海の空は「光る色を Use Point Color で点の色から取る」だった。どの組み合わせで XPU の色が CPU と変わるのか。**\n\n"
            "球を 6 つ並べ、principledshader の組み合わせを変えて、白いドームの明かりで CPU と XPU で撮った（640×200・32 サンプル、別の hython）。"
            "球の真ん中の色（RGB）の平均を比べた。\n\n"
            f"**XPU では、材質の色（Base Color）が効かない。**色ピンクの A（Use Point Color 切り）・B（入り・Cd なし）・D（入り・Cd 白）は、"
            f"CPU ではピンク {f(t['A']['cpu'])}、XPU では白 {f(t['A']['xpu'])}・{f(t['B']['xpu'])}・{f(t['D']['xpu'])} になった。\n\n"
            f"**点の色（Cd）は、XPU でも効く。**色を白にして Cd をピンクにした C は、XPU でもピンク {f(t['C']['xpu'])}（CPU {f(t['C']['cpu'])}）。"
            "ドーナツの生地（色は白、揚げ色は Cd）が XPU でも揚げ色だったのと合う。\n\n"
            f"**光る材質は、XPU では白い面の上に光が乗ったように明るくなった。**E（光る色を Cd から）{f(t['E']['xpu'])}、F（光る色ピンク）{f(t['F']['xpu'])}。"
            f"CPU ではどちらも {f(t['E']['cpu'])}。色（Base Color）が黒でも効かずに白い面になり、そこに明かりが当たった分が足されていると考えられる"
            "（海の空が白く飛んだのと合う）。\n\n"
            f"時間は CPU {d['cpu_sec']:.1f} 秒、XPU {d['xpu_sec']:.1f} 秒。\n\n"
            "**決め方: XPU で撮るなら、色は点の色（Cd）で付ける（材質の色は白、Use Point Color 入り）。**光る物は、XPU では明るさが変わるので CPU で撮る。"
            "XPU で材質の色を効かせる方法（MaterialX の材質など）は、まだ試していない。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "材質の組み合わせと、CPU・XPU の色",
             "images": [{"path": "242_grid.png", "caption": "上が CPU、下が XPU。XPU は Cd をピンクにした C 以外が白い。"}],
             "per_row": 1, "columns": ["球", "材質", "CPU の色（RGB）", "XPU の色（RGB）"], "rows": table},
        ],
        "notes": [
            "<strong>Karma XPU では、principledshader の Base Color が効かずに白くなった。</strong>",
            "<strong>点の色（Cd）は XPU でも効く。</strong>XPU で撮るなら色は Cd で付ける。",
            "<strong>光る材質は、XPU では白い面の上に光が乗ったように明るくなった。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "242_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
