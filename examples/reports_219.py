# -*- coding: utf-8 -*-
"""実験219 の図とレポートを、測った値から組み立てる。

画から 2 つ足して測る（960×540 の PNG）:
  きらめきの粒 … 水面（縦 306〜415 行。水平線から砂の手前まで）で、R・G・B がすべて 240 を超える画素の数
  泡の網目のくっきり具合 … 手前の水面（縦 330〜415 行）の、となりの画素との明るさの差の平均（大きいほど細かい模様がくっきり）
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

LAB = {"full": "1400×1600（224 万点）", "half": "990×1131（112 万点）", "quarter": "700×800（56 万点）", "sixteenth": "350×400（14 万点）"}


def main():
    with open(os.path.join(OUT, "219_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    for name, row in t.items():
        im = np.asarray(Image.open(os.path.join(OUT, f"219_{name}.png")).convert("RGB"), dtype=float)
        water = im[306:415]
        row["sparks"] = int((water.min(axis=2) > 240).sum())
        lum = im[330:415].mean(axis=2)
        row["detail"] = round(float(np.abs(np.diff(lum, axis=1)).mean() + np.abs(np.diff(lum, axis=0)).mean()), 2)
    font = _font(16)
    cw, ch = 600, 180
    sheet = Image.new("RGB", (cw * 2, (ch + 28) * 2), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, name in enumerate(LAB):
        x, y = (i % 2) * cw, (i // 2) * (ch + 28)
        sheet.paste(Image.open(os.path.join(OUT, f"219_{name}.png")).convert("RGB").crop((150, 290, 750, 470)), (x, y + 28))
        dr.text((x + 8, y + 5), f"{LAB[name]}  撮る時間 {t[name]['render_sec']:.1f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "219_grid.png"))
    f, hf, q, s = (t[k] for k in ("full", "half", "quarter", "sixteenth"))
    pct = lambda a, b: (a / b - 1) * 100  # noqa: E731
    table = [[LAB[k], f"{t[k]['cook_sec']:.2f}", f"{t[k]['render_sec']:.1f}", str(t[k]["sparks"]), f"{t[k]['detail']:.2f}",
              f"{t[k]['diff']['far_sea']:.1f}", f"{t[k]['diff']['near']:.1f}"] for k in LAB]
    payload = {
        "title": f"海の板の点を半分にすると、撮る時間は {-pct(hf['render_sec'], f['render_sec']):.0f}% 減り、きらめきの粒も {-pct(hf['sparks'], f['sparks']):.0f}% 減る。"
                 f"1/4 で時間 {-pct(q['render_sec'], f['render_sec']):.0f}% 減・粒 {-pct(q['sparks'], f['sparks']):.0f}% 減。1/16 でも時間は {s['render_sec'] / f['render_sec'] * 100:.0f}% までしか減らない",
        "summary":
            "**課題: 実践「冬の朝の七里ヶ浜」の映像は 1 枚 11.8 秒かかった。海の板（grid 1400 × 1600、224 万点）の点を減らすと、撮る時間と見た目はどう変わるか。どこまで減らしてよいか。**\n\n"
            "板の Rows・Columns を 1400×1600・990×1131（1/2 の点）・700×800（1/4）・350×400（1/16）にし、フレーム 30 を映像と同じ 960×540・16 サンプルで撮った。"
            "1 通りずつ、ほかの処理は回さずに測った。画の差は、1400×1600 の画との画素ごとの差の平均（0〜255）。"
            "あわせて、水面のきらめきの粒（R・G・B すべて 240 超の画素）の数と、手前の泡の網目のくっきり具合（となりの画素との明るさの差の平均）を数えた。\n\n"
            f"**撮る時間は、点に比例しては減らない。**224 万・112 万・56 万・14 万点で {f['render_sec']:.1f}・{hf['render_sec']:.1f}・{q['render_sec']:.1f}・{s['render_sec']:.1f} 秒。"
            f"点を 1/16 にしても、時間は {s['render_sec'] / f['render_sec'] * 100:.0f}% までしか減らなかった。残りは、空・砂浜・光の計算にかかる分。"
            f"板から泡までを作る時間は {f['cook_sec']:.2f}・{hf['cook_sec']:.2f}・{q['cook_sec']:.2f}・{s['cook_sec']:.2f} 秒で、撮る時間に比べて小さい。\n\n"
            f"**半分では、きらめきの粒が {-pct(hf['sparks'], f['sparks']):.0f}% 減る。**1/2 の粒は {hf['sparks']} 個（元は {f['sparks']} 個）、泡の網目のくっきり具合は {hf['detail']:.2f}（元は {f['detail']:.2f}）。"
            f"画を並べると、違いは光の道の粒の数くらいで、小さい。\n\n"
            f"**1/4 からは、きらめきと泡の細かさが落ちる。**粒は 1/4 で {q['sparks']} 個、1/16 で {s['sparks']} 個。"
            f"網目のくっきり具合は {q['detail']:.2f}・{s['detail']:.2f}。画では、光の道の粒がまばらになり、泡の網目がぼやけた。"
            f"元の画との差は、沖（水平線から約 30 m まで）で {hf['diff']['far_sea']:.1f}・{q['diff']['far_sea']:.1f}・{s['diff']['far_sea']:.1f}、"
            f"手前で {hf['diff']['near']:.1f}・{q['diff']['near']:.1f}・{s['diff']['near']:.1f}。点が粗くなると、さざ波（1.3 m）の細かい傾きが面に乗らなくなる。空は差 0。\n\n"
            f"**決め方: 仕上げは 1400×1600 のまま。動きの確かめは 990×1131 か 700×800 で撮る。**990×1131 なら 1 枚 {f['render_sec'] - hf['render_sec']:.1f} 秒、120 枚で約 {(f['render_sec'] - hf['render_sec']) * 120 / 60:.0f} 分の節約。"
            "点を減らしても時間は半分より下がらないので、もっと速くしたいときは、解像度やサンプル数を下げる方が効く。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "板の点の数を変えた画（フレーム 30、光の道と泡のあたりを切り出し）",
             "images": [{"path": "219_grid.png", "caption": "左上が元（224 万点）。1/2（右上）は粒が少し減る。1/4（左下）・1/16（右下）で粒が減り、網目がぼやける。"}],
             "per_row": 1,
             "columns": ["板（Rows × Columns）", "作る時間（秒）", "撮る時間（秒）", "きらめきの粒", "網目のくっきり具合", "差: 沖", "差: 手前"],
             "rows": table},
        ],
        "notes": [
            f"<strong>点を減らしても、撮る時間は点に比例して減らない。</strong>1/16 の点で {s['render_sec'] / f['render_sec'] * 100:.0f}% の時間。",
            f"<strong>半分（112 万点）では、1 枚 {f['render_sec'] - hf['render_sec']:.1f} 秒速く、きらめきの粒が {-pct(hf['sparks'], f['sparks']):.0f}% 減る。</strong>違いは小さい。",
            f"<strong>1/4 からは、きらめきの粒と泡の網目の細かさが落ちる。</strong>粒 {f['sparks']} → {q['sparks']} 個。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "219_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])
    for k in LAB:
        print(k, t[k]["sparks"], t[k]["detail"])


if __name__ == "__main__":
    main()
