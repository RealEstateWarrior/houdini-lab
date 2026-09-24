# -*- coding: utf-8 -*-
"""実験228 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def main():
    with open(os.path.join(OUT, "228_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(16)
    shots = [("points_100k", "点のまま 10 万個"), ("points_10000k", "点のまま 1000 万個"), ("spheres_30k", "球をパック 3 万個")]
    sheet = Image.new("RGB", (640 * 3, 360 + 28), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, lab) in enumerate(shots):
        im = Image.open(os.path.join(OUT, f"228_{k}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (20, 20, 20, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (i * 640, 28))
        dr.text((i * 640 + 8, 5), f"{lab}  1 回目 {t[k]['sec_first']:.1f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "228_grid.png"))
    lab = {"points": "点のまま", "spheres": "球をパックして並べる"}
    table = [[lab[r["kind"]], f"{r['count']:,}", f"{r['sec_first']:.1f}", f"{r['sec_again']:.1f}"] for r in t.values()]
    s = lambda k, f="sec_first": t[k][f]  # noqa: E731
    payload = {
        "title": f"粒は点のまま Karma に渡す。1000 万個でも {s('points_10000k'):.0f} 秒（640×360・8 サンプル）。"
                 f"小さな球をパックして並べると 3 万個で {s('spheres_30k'):.0f} 秒かかり、その 8 割は場面を渡す時間",
        "summary":
            "**課題: 火花・雪・雨・砂ぼこりのような粒は、何十万〜何百万個になる。/obj の Karma に点のまま渡すと、Karma は点を小さな球として描く（半径は pscale）。"
            "実験222 では、パックした形を何万個も渡すと、場面を渡すだけで何分もかかった。粒ならどうか。**\n\n"
            "4 m 四方・高さ 4 m の箱の中に、半径 5 mm の粒を乱数で散らし、640×360・8 サンプル＋ノイズ除去で撮った。"
            "はじめに小さく 1 枚撮って捨て、同じ画を 2 回続けて撮った（1 回目は場面を Karma に渡す分を含み、2 回目は変わっていない場面をそのまま使う）。"
            "はじめは scatter で点をまいたが、scatter は 100 万個が上限で、1000 万を指定しても 100 万個だった。pointgenerate で点を作り、VEX で散らすようにした。\n\n"
            f"**点のままなら、1000 万個でも数秒。**1 万・10 万・100 万・1000 万個で、1 回目 {s('points_10k'):.1f}・{s('points_100k'):.1f}・{s('points_1000k'):.1f}・{s('points_10000k'):.1f} 秒。"
            f"2 回目も {s('points_10k', 'sec_again'):.1f}・{s('points_100k', 'sec_again'):.1f}・{s('points_1000k', 'sec_again'):.1f}・{s('points_10000k', 'sec_again'):.1f} 秒で、"
            "場面を渡す時間はほとんど無い。\n\n"
            f"**小さな球をパックして並べると、場面を渡すだけで時間がかかる。**1 万・3 万個で、1 回目 {s('spheres_10k'):.1f}・{s('spheres_30k'):.1f} 秒、"
            f"2 回目 {s('spheres_10k', 'sec_again'):.1f}・{s('spheres_30k', 'sec_again'):.1f} 秒。3 万個では 1 回目の {(1 - s('spheres_30k', 'sec_again') / s('spheres_30k')) * 100:.0f}% が場面を渡す分だった。"
            "映像は毎フレーム粒が動くので、毎フレームこの 1 回目の時間がかかる。\n\n"
            "**決め方: 丸い粒は、点のまま（pscale で大きさ）Karma に渡す。**形のある粒（葉・破片）を何万も並べるなら、Solaris の sopimport で Create Point Instancer にする（実験222）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "粒の数と撮る時間（640×360・8 サンプル＋ノイズ除去）",
             "images": [{"path": "228_grid.png", "caption": "点のまま 10 万個・1000 万個と、球をパックして並べた 3 万個。"}],
             "per_row": 1, "columns": ["渡し方", "粒の数", "1 回目（秒）", "2 回目（秒）"], "rows": table},
        ],
        "notes": [
            f"<strong>粒は点のまま渡すと、1000 万個でも {s('points_10000k'):.0f} 秒。</strong>",
            f"<strong>小さな球をパックして並べると、3 万個で {s('spheres_30k'):.0f} 秒。</strong>大半は場面を渡す時間で、動く映像では毎フレームかかる。",
            "<strong>scatter は 100 万個が上限。</strong>それ以上は pointgenerate で点を作る。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "228_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
