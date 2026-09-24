# -*- coding: utf-8 -*-
"""実験247 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"s4_optix": "4 サンプル＋OptiX", "s4_off": "4 サンプル・なし", "s16_off": "16 サンプル・なし", "s16_optix": "16 サンプル＋OptiX"}


def main():
    with open(os.path.join(OUT, "247_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(15)
    sheet = Image.new("RGB", (400 * 4, 225 + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(LAB):
        sheet.paste(Image.open(os.path.join(OUT, f"247_{k}.png")).convert("RGB").resize((400, 225)), (i * 400, 26))
        dr.text((i * 400 + 6, 4), f"{LAB[k]}  12 枚 {t[k]['sec12']:.0f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "247_grid.png"))
    table = [[LAB[k], f"{t[k]['sec12']:.1f}", f"{t[k]['sky_flicker'] * 100:.2f}"] for k in LAB]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": f"映像にノイズ除去（OptiX）を使っても、動かない空のちらつきは増えなかった（4 サンプルで {g('s4_off', 'sky_flicker') * 100:.2f}% → {g('s4_optix', 'sky_flicker') * 100:.2f}%）。"
                 f"4 サンプル＋OptiX は 16 サンプル（なし）と同じくらいで、時間は 12 枚 {g('s4_optix', 'sec12'):.0f} 秒と {g('s16_off', 'sec12'):.0f} 秒",
        "summary":
            "**課題: 実験241 で、静止画なら 4 サンプル＋ノイズ除去で 32 サンプル（なし）並みになった。映像では、ノイズ除去はフレームごとに別々にかかるので、"
            "動かない所までちらつくことがある。どれだけちらつくのか。**\n\n"
            "実践「冬の朝の七里ヶ浜」を、フレーム 20〜31 の 12 枚、640×360 で撮った（4・16 サンプル × ノイズ除去なし・OptiX）。"
            "動かない所（空＝画の上 35%）で、画素ごとに 12 枚の明るさの標準偏差を取り、明るさの平均で割って平均した（ちらつき）。条件ごとに別の hython。\n\n"
            f"**ノイズ除去で、ちらつきはむしろ減った。**4 サンプル: なし {g('s4_off', 'sky_flicker') * 100:.2f}%、OptiX {g('s4_optix', 'sky_flicker') * 100:.2f}%。"
            f"16 サンプル: なし {g('s16_off', 'sky_flicker') * 100:.2f}%、OptiX {g('s16_optix', 'sky_flicker') * 100:.2f}%。"
            "4 サンプル＋OptiX は、16 サンプル（なし）と同じくらいだった。\n\n"
            f"**時間は、この海の場面ではサンプル数ほどは変わらない。**12 枚で、4 サンプル {g('s4_off', 'sec12'):.0f}・{g('s4_optix', 'sec12'):.0f} 秒、16 サンプル {g('s16_off', 'sec12'):.0f}・{g('s16_optix', 'sec12'):.0f} 秒"
            "（海の場面は 1 枚ごとに画の大きさによらない時間が大きい。実験239）。\n\n"
            "**測った範囲の注意:** ちらつきは空だけで測った。空はもともとざらつきが少ない（0.5% 以下）。水面・砂は波とともに動くので、この方法ではちらつきと動きを分けられず、測っていない。\n\n"
            "**決め方: 映像でも、ノイズ除去は入れてよい。**空のような動かない所のちらつきは増えなかった。水面などの細かい所は、映像を見て確かめる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "サンプル数とノイズ除去（フレーム 26）",
             "images": [{"path": "247_grid.png", "caption": "4 サンプル＋OptiX・4 サンプル・16 サンプル・16 サンプル＋OptiX。"}],
             "per_row": 1, "columns": ["設定", "12 枚を撮る時間（秒）", "空のちらつき（%）"], "rows": table},
        ],
        "notes": [
            "<strong>ノイズ除去（OptiX）で、動かない空のちらつきは増えず、むしろ減った。</strong>",
            "<strong>4 サンプル＋OptiX は、16 サンプル（なし）と同じくらいのちらつき。</strong>",
            "<strong>水面など動く所のちらつきは、この方法では測れていない。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "247_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
