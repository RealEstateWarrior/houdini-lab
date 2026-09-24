# -*- coding: utf-8 -*-
"""実験229 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def main():
    with open(os.path.join(OUT, "229_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(16)
    shots = [("curves_100k", "曲線 10 万本"), ("curves_1000k", "曲線 100 万本"), ("polywire_30k", "polywire 3 万本")]
    sheet = Image.new("RGB", (640 * 3, 360 + 28), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, lab) in enumerate(shots):
        im = Image.open(os.path.join(OUT, f"229_{k}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (i * 640, 28))
        dr.text((i * 640 + 8, 5), f"{lab}  {t[k]['sec_first']:.1f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "229_grid.png"))
    lab = {"curves": "曲線のまま", "polywire": "polywire（筒の面）"}
    table = [[lab[r["kind"]], f"{r['count']:,}", f"{r['prims']:,}", f"{r['points']:,}", f"{r['sec_first']:.1f}", f"{r['sec_again']:.1f}"] for r in t.values()]
    s = lambda k, f="sec_first": t[k][f]  # noqa: E731
    payload = {
        "title": f"毛は曲線のまま Karma に渡す。100 万本でも {s('curves_1000k'):.0f} 秒（640×360・8 サンプル）。"
                 f"polywire で筒の面にすると 1 本あたりが重く、3 万本で {s('polywire_30k'):.0f} 秒",
        "summary":
            "**課題: 動物の毛並みや芝生を作ると、毛が何十万本にもなる。/obj の Karma は曲線を、太さ（width）のある毛として描ける。"
            "曲線のまま渡すのと、polywire で細い筒の面にして渡すのとで、時間はどう違うか。何本まで撮れるか。**\n\n"
            "半径 0.5 m の球の表面に N 本の毛を生やした（VEX で 1 本 8 点の曲線、長さ 8 cm、根元の太さ 1 mm → 先 0.2 mm）。"
            "640×360・8 サンプル＋ノイズ除去で、はじめに小さく 1 枚撮って捨て、同じ画を 2 回続けて撮った。\n\n"
            f"**曲線のままなら、100 万本でも十数秒。**1 万・10 万・100 万本で {s('curves_10k'):.1f}・{s('curves_100k'):.1f}・{s('curves_1000k'):.1f} 秒。"
            f"2 回目も {s('curves_10k', 'sec_again'):.1f}・{s('curves_100k', 'sec_again'):.1f}・{s('curves_1000k', 'sec_again'):.1f} 秒で、場面を渡す時間はほとんど無い。"
            "本数が 100 倍でも時間は 3 倍に満たなかった。\n\n"
            f"**polywire で筒の面にすると、1 本あたりが重い。**1 万・3 万本で {s('polywire_10k'):.1f}・{s('polywire_30k'):.1f} 秒。"
            f"面は 1 本 30 枚（3 万本で {t['polywire_30k']['prims']:,} 枚）になり、3 万本で曲線 10 万本と同じくらいの時間がかかった。\n\n"
            "**決め方: 毛・芝・髪は、曲線のまま（width で太さ）Karma に渡す。**polywire は、毛を別のソフトへ書き出すなど、面が要るときだけ使う。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "毛の本数と撮る時間（640×360・8 サンプル＋ノイズ除去）",
             "images": [{"path": "229_grid.png", "caption": "曲線 10 万本・100 万本と、polywire 3 万本。"}],
             "per_row": 1, "columns": ["渡し方", "本数", "面・曲線の数", "点の数", "1 回目（秒）", "2 回目（秒）"], "rows": table},
        ],
        "notes": [
            f"<strong>毛は曲線のまま渡すと、100 万本でも {s('curves_1000k'):.0f} 秒。</strong>",
            f"<strong>polywire で筒の面にすると、3 万本で {s('polywire_30k'):.0f} 秒。</strong>曲線 10 万本と同じくらい。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "229_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
