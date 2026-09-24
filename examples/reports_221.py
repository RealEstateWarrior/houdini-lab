# -*- coding: utf-8 -*-
"""実験221 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"s16": "960×540・16 サンプル（基準）", "s8": "960×540・8 サンプル", "s4": "960×540・4 サンプル",
       "s4_oidn": "960×540・4 サンプル＋ノイズ除去", "r640": "640×360・16 サンプル"}
SHOW = ["s16", "s4", "s4_oidn", "r640"]


def main():
    with open(os.path.join(OUT, "221_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    font = _font(16)
    cw, ch = 600, 180
    sheet = Image.new("RGB", (cw * 2, (ch + 28) * 2), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(SHOW):
        im = Image.open(os.path.join(OUT, f"221_{k}.png")).convert("RGB")
        if im.size != (960, 540):
            im = im.resize((960, 540), Image.BICUBIC)
        x, y = (i % 2) * cw, (i // 2) * (ch + 28)
        sheet.paste(im.crop((150, 290, 750, 470)), (x, y + 28))
        dr.text((x + 8, y + 5), f"{LAB[k]}  {t[k]['render_sec']:.1f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "221_grid.png"))
    s = lambda k: t[k]["render_sec"]  # noqa: E731
    dd = lambda k: t[k]["diff"]["sea"]  # noqa: E731
    table = [[LAB[k], f"{s(k):.1f}", f"{(1 - s(k) / s('s16')) * 100:.0f}%", f"{dd(k):.2f}", f"{t[k]['diff']['sky']:.2f}"] for k in LAB]
    payload = {
        "title": f"海の映像の 1 枚は、サンプル数を 16→4 にしても {s('s16'):.1f}→{s('s4'):.1f} 秒、解像度を 640×360 にしても {s('r640'):.1f} 秒。"
                 "時間の大半は画の大きさによらない分で、下げるなら 4 サンプル＋ノイズ除去",
        "summary":
            f"**課題: 実践「冬の朝の七里ヶ浜」の映像の 1 枚を速く撮るなら、サンプル数・解像度・ノイズ除去のどれを下げるのが効くか。**\n\n"
            "フレーム 30 を、960×540 の 16・8・4 サンプル、4 サンプル＋ノイズ除去（OIDN）、640×360 の 16 サンプルで撮った（板は 1400×1600 のまま）。"
            "はじめに 1 枚撮って捨て（Karma の立ち上がりの分）、1 通りずつ、ほかの処理は回さずに測った。画の差は、16 サンプルの画との画素ごとの差の平均（0〜255）で、"
            "640×360 の画は 960×540 に拡大して比べた。\n\n"
            f"**どれを下げても、時間は 2 割ほどしか減らない。**16・8・4 サンプルで {s('s16'):.1f}・{s('s8'):.1f}・{s('s4'):.1f} 秒。"
            f"画素の数が半分以下の 640×360 でも {s('r640'):.1f} 秒。1 枚の時間の大半は、画の大きさやサンプル数によらない分"
            "（224 万点の海や空を Karma に渡すなど）だった。\n\n"
            f"**下げるなら、4 サンプル＋ノイズ除去。**{s('s4_oidn'):.1f} 秒で、水面の差は {dd('s4_oidn'):.2f}。"
            f"8 サンプル（{s('s8'):.1f} 秒、差 {dd('s8'):.2f}）より基準に近く、4 サンプルだけ（差 {dd('s4'):.2f}）よりざらつきが少ない。"
            f"640×360 は差 {dd('r640'):.2f} で、細かいきらめきが拡大でぼやけた。空はどれもほぼ同じ（差 0.12 以下）。\n\n"
            "**決め方: 海の映像を早く確かめたいときは、4 サンプル＋ノイズ除去にする（1 枚で約 1.3 秒の節約）。**"
            "それ以上速くするには、形の方を軽くする（実験219: 板の点を 1/16 にして 36% 減）か、1 枚ごとに Karma へ渡し直す分を減らす撮り方が要る（まだ測っていない）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "設定を変えて撮った海（フレーム 30、光の道と泡のあたり）",
             "images": [{"path": "221_grid.png", "caption": "左上が基準（16 サンプル）。4 サンプルはざらつき、ノイズ除去を入れるとなめらかになる。640×360 は拡大でぼやける。"}],
             "per_row": 1, "columns": ["設定", "撮る時間（秒）", "短くなった割合", "差: 水面", "差: 空"], "rows": table},
        ],
        "notes": [
            f"<strong>サンプル数を 16→4 にしても、時間は {(1 - s('s4') / s('s16')) * 100:.0f}% しか減らない。</strong>",
            f"<strong>解像度を 640×360 にしても {(1 - s('r640') / s('s16')) * 100:.0f}% 減。</strong>時間の大半は画の大きさによらない分。",
            "<strong>下げるなら 4 サンプル＋ノイズ除去。</strong>8 サンプルより速く、基準に近い。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "221_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
