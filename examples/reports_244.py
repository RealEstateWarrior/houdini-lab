# -*- coding: utf-8 -*-
"""実験244 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

VALUES = (0.0, 0.05, 0.1, 0.2, 0.4)


def png(tag):
    return os.path.join(OUT, f"244_{tag}.png".replace("0.", "0p"))


def main():
    with open(os.path.join(OUT, "244_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(15)
    shots = [("d0.1", "実践のまま（火元から煙を出さない）"), ("d0_smoke", "煙を出す・Dissipation 0"), ("d0.1_smoke", "煙を出す・0.1（既定）"), ("d0.4_smoke", "煙を出す・0.4")]
    sheet = Image.new("RGB", (400 * 4, 225 + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, lab) in enumerate(shots):
        im = Image.open(png(k)).convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB").resize((400, 225)), (i * 400, 26))
        dr.text((i * 400 + 6, 4), lab, fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "244_grid.png"))
    mode = {"": "実践のまま", "_free": "Set Flame Density 切り", "_smoke": "火元から煙を出す"}
    table = []
    for m in ("", "_free", "_smoke"):
        for d in VALUES:
            r = t[f"d{d:g}{m}"]
            table.append([mode[m], f"{d:g}", f"{r['smoke_voxels']:,}", f"{r['top']:.2f}", f"{r['density_sum']:.1f}", f"{r['sim_sec']:.1f}"])
    s = lambda d, f: t[f"d{d:g}_smoke"][f]  # noqa: E731
    prod = [s(d, "density_sum") * d for d in (0.05, 0.1, 0.2, 0.4)]
    payload = {
        "title": f"焚き火の煙の量は Dissipation にほぼ反比例する（0.05・0.1・0.2・0.4 で {s(0.05, 'density_sum'):.0f}・{s(0.1, 'density_sum'):.0f}・{s(0.2, 'density_sum'):.0f}・{s(0.4, 'density_sum'):.0f}）。"
                 "ただし実践の焚き火は火元から煙を出しておらず、Dissipation はまったく効かなかった",
        "summary":
            "**課題: 焚き火や煙突の煙を、すぐ消える薄い煙にしたい・高くまで残る煙にしたい。pyrosolver の Dissipation（煙が薄れて消える速さ、既定 0.1）を変えると、"
            "煙の高さと量はどう変わるのか。**\n\n"
            "実践「焚き火」の場面で、Dissipation を 0・0.05・0.1・0.2・0.4 にして 96 フレーム（4 秒）回した。煙の濃さ（density）が 0.02 を超える升の数と、"
            "そのいちばん高い所、濃さの合計（升の体積 × 濃さの和）を測り、実践と同じカメラと明かりで Karma で撮った。\n\n"
            f"**実践のままでは、Dissipation はまったく効かなかった。**5 つの値で、煙の升の数・高さ・合計がすべて同じ（{t['d0.1']['smoke_voxels']:,} 升、高さ {t['d0.1']['top']:.2f} m）。"
            "Set Flame Density を切ると、濃さはどこにも無くなった。実践の火元（pyrosource の Source Burn）が付ける値は burn・temperature だけで、"
            "煙の濃さ（density）を出していない。画に写っていた濃さは、Set Flame Density で炎から作られたものだけと考えられる。\n\n"
            "**火元から煙を出すと、Dissipation がはっきり効く。**火元の点に density = 1 を足して升目に移すと（add_smoke）、"
            f"Dissipation 0・0.05・0.1・0.2・0.4 で、煙の濃さの合計は {s(0, 'density_sum'):.0f}・{s(0.05, 'density_sum'):.0f}・{s(0.1, 'density_sum'):.0f}・{s(0.2, 'density_sum'):.1f}・{s(0.4, 'density_sum'):.1f}、"
            f"いちばん高い所は {s(0, 'top'):.1f}・{s(0.05, 'top'):.1f}・{s(0.1, 'top'):.1f}・{s(0.2, 'top'):.1f}・{s(0.4, 'top'):.1f} m。\n\n"
            "**煙の量は Dissipation にほぼ反比例する。**出る量と消える量が釣り合うと、煙の量は「出る速さ ÷ 消える速さ」になるはず。"
            f"Dissipation × 合計は 0.05・0.1・0.2・0.4 で {prod[0]:.2f}・{prod[1]:.2f}・{prod[2]:.2f}・{prod[3]:.2f} と、ほぼ一定だった。0 では消えないので、4 秒たってもたまり続けた（{s(0, 'density_sum'):.0f}）。\n\n"
            f"**煙が多いほど、計算も重い。**96 フレームで {s(0, 'sim_sec'):.1f}・{s(0.05, 'sim_sec'):.1f}・{s(0.1, 'sim_sec'):.1f}・{s(0.2, 'sim_sec'):.1f}・{s(0.4, 'sim_sec'):.1f} 秒"
            "（煙のある所だけ計算するので、煙が広がるほど升目が大きくなる）。\n\n"
            "**決め方: 煙を出すなら、まず火元に density を入れる。**そのうえで、煙の量を半分にしたければ Dissipation を倍にする。"
            "炎を見せたい焚き火なら 0.2〜0.4、煙を立ちのぼらせたいなら 0.05〜0.1。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Dissipation と煙（96 フレーム目）",
             "images": [{"path": "244_grid.png", "caption": "左: 実践のまま（煙は出ない）。右 3 つ: 火元から煙を出して Dissipation 0・0.1・0.4。"}],
             "per_row": 1, "columns": ["火元", "Dissipation", "煙の升（濃さ 0.02 超）", "いちばん高い所（m）", "濃さの合計", "計算 96 フレーム（秒）"], "rows": table},
        ],
        "notes": [
            "<strong>実践の焚き火は、火元から煙（density）を出していなかった。</strong>Dissipation を変えても何も変わらない。",
            f"<strong>火元から煙を出すと、煙の量は Dissipation にほぼ反比例する（値 × 量 ≈ {sum(prod) / 4:.1f}）。</strong>",
            "<strong>煙が多いほど計算も重い。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "244_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
