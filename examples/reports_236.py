# -*- coding: utf-8 -*-
"""実験236 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def main():
    with open(os.path.join(OUT, "236_stats.json"), encoding="utf-8") as fp:
        t = {r["refraction_limit"]: r for r in json.load(fp)["rows"]}
    font = _font(15)
    w, h = 240, 320
    shots = (1, 2, 4, 8, 16)
    sheet = Image.new("RGB", (w * len(shots), h + 44), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(shots):
        sheet.paste(Image.open(os.path.join(OUT, f"236_rl{k}.png")).convert("RGB").crop((200, 30, 440, 350)), (i * w, 44))
        dr.text((i * w + 6, 4), f"Refraction Limit {k}{'（既定）' if k == 4 else ''}", fill=(30, 30, 30), font=font)
        dr.text((i * w + 6, 22), f"暗い所 {t[k]['dark_share'] * 100:.0f}%・{t[k]['sec']:.0f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "236_grid.png"))
    table = [[str(k) + ("（既定）" if k == 4 else ""), f"{t[k]['sec']:.1f}", f"{t[k]['glass_mean']:.3f}", f"{t[k]['dark_share'] * 100:.1f}"] for k in shots]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": f"氷の入ったグラスの水は、Karma の Refraction Limit 既定 4 では氷がまだ黒く残る。8 で透明になり（暗い所 {g(4, 'dark_share') * 100:.0f}% → {g(8, 'dark_share') * 100:.0f}%）、"
                 f"時間は {g(4, 'sec'):.0f} → {g(8, 'sec'):.0f} 秒。16 は 8 と同じ",
        "summary":
            "**課題: ガラスのコップに水と氷を入れて撮ると、氷や水の奥が黒く抜けることがある。光はガラスの外側・内側・水・氷と何度も境目を通り抜けるので、"
            "途中で追うのをやめると、そこが黒くなる。Karma の Refraction Limit（既定 4）はいくつにすればよいか。**\n\n"
            "実践「氷の入ったグラスの水」の場面で、Refraction Limit を 1・2・4・8・16 にし、640×360・32 サンプル（ノイズ除去なし）で撮った。"
            "グラスの中（画の真ん中の縦長の窓）の明るさの平均と、暗い画素（明るさ 0.03 未満）の割合を数えた。\n\n"
            f"**既定の 4 では、氷がまだ黒い。**暗い画素の割合は 1・2・4・8・16 で {g(1, 'dark_share') * 100:.0f}・{g(2, 'dark_share') * 100:.0f}・{g(4, 'dark_share') * 100:.1f}・"
            f"{g(8, 'dark_share') * 100:.1f}・{g(16, 'dark_share') * 100:.1f}%。"
            "1 ではグラスの中がほぼ真っ黒、2 では水は透けるが氷が黒い塊、4 では氷の奥の面が黒く残り、8 で氷も透明になった。"
            f"明るさの平均は {g(1, 'glass_mean'):.2f}・{g(2, 'glass_mean'):.2f}・{g(4, 'glass_mean'):.2f}・{g(8, 'glass_mean'):.2f}・{g(16, 'glass_mean'):.2f} で、8 と 16 はほぼ同じ。\n\n"
            f"**時間は 8 まで延びて、そこで止まる。**{g(1, 'sec'):.0f}・{g(2, 'sec'):.0f}・{g(4, 'sec'):.0f}・{g(8, 'sec'):.0f}・{g(16, 'sec'):.0f} 秒。"
            "光が 8 回より多く境目を通る道は、この場面にはほとんど無いと考えられる。\n\n"
            "**決め方: 透明な物が重なる場面（グラスに水と氷、ガラス越しのガラス）は、Refraction Limit を 8 にする。**それ以上は上げても変わらない。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Refraction Limit とグラスの水（640×360・32 サンプル、グラスのまわりを切り出し）",
             "images": [{"path": "236_grid.png", "caption": "左から 1・2・4（既定）・8・16。4 では氷の奥が黒く、8 で透明になる。"}],
             "per_row": 1, "columns": ["Refraction Limit", "撮る時間（秒）", "グラスの中の明るさ", "暗い画素（%）"], "rows": table},
        ],
        "notes": [
            f"<strong>既定の Refraction Limit 4 では、氷の奥が黒く残る（暗い所 {g(4, 'dark_share') * 100:.0f}%）。</strong>",
            f"<strong>8 で透明になる（{g(8, 'dark_share') * 100:.0f}%）。16 は 8 と同じ。</strong>時間は {g(4, 'sec'):.0f} → {g(8, 'sec'):.0f} 秒。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "236_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
