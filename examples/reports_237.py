# -*- coding: utf-8 -*-
"""実験237 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"r1.5": "1.5", "r2": "2", "r3": "3（実践）", "r4": "4", "r6": "6", "r3_soft": "3・膜 10²", "r3_hard": "3・膜 10⁴"}


def main():
    with open(os.path.join(OUT, "237_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    font = _font(15)
    shots = ["r1.5", "r3", "r6", "r3_hard"]
    sheet = Image.new("RGB", (360 * 4, 400 + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(shots):
        im = Image.open(os.path.join(OUT, f"237_{k.replace('.', 'p')}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (i * 360, 26))
        dr.text((i * 360 + 6, 4), f"Rest Length Scale {LAB[k]}  体積 {t[k]['ratio_final']:.2f} 倍", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "237_grid.png"))
    table = [[LAB[k], f"{r['stiffness_exp']}", f"{r['ratio_final']:.3f}", str(r["settle_frame"]), f"{r['height'] * 100:.1f}", f"{r['width'] * 100:.1f}", f"{r['aspect']:.2f}"]
             for k, r in t.items()]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": "Vellum の風船の体積は、Pressure の Rest Length Scale の倍率ちょうどになる（3 なら 3.00 倍）。2 フレームで落ち着く。"
                 f"ただし 2 倍を超えるとしずく形が消えて球になり、膜が柔らかい（10²）と横につぶれる",
        "summary":
            "**課題: 実践「風船をふくらませる」では、Pressure の Rest Length Scale を 3 にした（「今の 3 倍の体積が本来の大きさ」）。"
            "体積は本当に 3 倍になるのか。ゴムの膜の硬さで、ふくらみ方は変わるのか。何フレームで落ち着くのか。**\n\n"
            f"実践と同じ、しぼんだしずく形の風船（体積 {d['v0'] * 1000:.2f} L、縦 ÷ 横 {d['aspect0']:.2f}）に、Cloth（Stretch Stiffness 1 × 10³）と Pressure をかけ、"
            "重力 0・Substeps 5 で 48 フレーム回した。Rest Length Scale を 1.5・2・3・4・6 にし、3 では膜の硬さを 10²・10⁴ にしたものも回した。"
            "体積は閉じた面の体積（三角形ごとの符号付き体積の和）で、はじめとの比を取った。\n\n"
            f"**体積は、Rest Length Scale の倍率ちょうどになる。**48 フレーム目の体積は 1.5・2・3・4・6 で {g('r1.5', 'ratio_final'):.3f}・{g('r2', 'ratio_final'):.3f}・"
            f"{g('r3', 'ratio_final'):.3f}・{g('r4', 'ratio_final'):.3f}・{g('r6', 'ratio_final'):.3f} 倍。膜の硬さを 10²・10⁴ にしても {g('r3_soft', 'ratio_final'):.3f}・{g('r3_hard', 'ratio_final'):.3f} 倍。"
            "どれも 2 フレーム目で最後の 95% に届き、あとはほとんど動かなかった。\n\n"
            f"**2 倍を超えると、しずく形が消えて球になる。**縦 ÷ 横は、はじめ {d['aspect0']:.2f}、1.5・2・3・4・6 で {g('r1.5', 'aspect'):.2f}・{g('r2', 'aspect'):.2f}・"
            f"{g('r3', 'aspect'):.2f}・{g('r4', 'aspect'):.2f}・{g('r6', 'aspect'):.2f}。6 では横長になった。\n\n"
            f"**膜が柔らかいと、横につぶれる。**Rest Length Scale 3 で、膜の硬さ 10²・10³・10⁴ の縦 ÷ 横は {g('r3_soft', 'aspect'):.2f}・{g('r3', 'aspect'):.2f}・{g('r3_hard', 'aspect'):.2f}。"
            "体積は同じでも、柔らかい膜では形が崩れた。\n\n"
            "**決め方: ふくらませたい体積の倍率を、そのまま Rest Length Scale に入れる。**しずく形を残したいなら 2 倍までにして、しぼんだ形をはじめから大きめに作る。"
            "膜の硬さは 10³ 以上にする。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Rest Length Scale と風船の形（48 フレーム目）",
             "images": [{"path": "237_grid.png", "caption": "左から 1.5・3・6（膜 10³）・3（膜 10⁴）。1.5 はしずく形が残り、3 以上は球になる。"}],
             "per_row": 1, "columns": ["Rest Length Scale", "膜の硬さ（10 の何乗）", "体積の倍率", "落ち着いたフレーム", "縦（cm）", "横（cm）", "縦 ÷ 横"], "rows": table},
        ],
        "notes": [
            "<strong>体積は Rest Length Scale の倍率ちょうどになり、2 フレームで落ち着く。</strong>膜の硬さによらない。",
            f"<strong>2 倍を超えると、しずく形が消えて球になる。</strong>縦 ÷ 横 {d['aspect0']:.2f} → {g('r3', 'aspect'):.2f}。",
            f"<strong>膜が柔らかい（10²）と、横につぶれる（縦 ÷ 横 {g('r3_soft', 'aspect'):.2f}）。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "237_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
