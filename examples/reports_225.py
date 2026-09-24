# -*- coding: utf-8 -*-
"""実験225 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def main():
    with open(os.path.join(OUT, "225_stats.json"), encoding="utf-8") as fp:
        t = {(r["kind"], r["count"]): r for r in json.load(fp)["rows"]}
    font = _font(15)
    w, h = 480, 270
    shots = [(("lights", 100), "ライト 100 個"), (("glow", 100), "光る球 100 個"), (("lights", 1000), "ライト 1000 個"), (("glow", 1000), "光る球 1000 個")]
    sheet = Image.new("RGB", (w * 2, (h + 26) * 2), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, lab) in enumerate(shots):
        x, y = (i % 2) * w, (i // 2) * (h + 26)
        sheet.paste(Image.open(os.path.join(OUT, f"225_{k[0]}_{k[1]}.png")).convert("RGB"), (x, y + 26))
        dr.text((x + 8, y + 4), f"{lab}・16 サンプル  {t[k]['sec']:.1f} 秒・ざらつき {t[k]['noise'] * 100:.0f}%", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "225_grid.png"))
    table = [[("ライト（point）" if k == "lights" else "光る球"), str(n), f"{t[(k, n)]['sec']:.1f}", f"{t[(k, n)]['sec_ref64']:.1f}",
              f"{t[(k, n)]['noise'] * 100:.1f}", f"{t[(k, n)]['mean']:.3f}"] for k in ("lights", "glow") for n in (1, 10, 100, 1000)]
    L = lambda n, f: t[("lights", n)][f]  # noqa: E731
    G = lambda n, f: t[("glow", n)][f]  # noqa: E731
    payload = {
        "title": f"明かりを何百も置く場面は、照らすのをライトで。1000 個でも 16 サンプル {L(1000, 'sec'):.0f} 秒・ざらつき {L(1000, 'noise') * 100:.0f}%。"
                 f"小さな光る球で照らすと、ざらつき {G(100, 'noise') * 100:.0f}% で、64 サンプルでも光が拾いきれない",
        "summary":
            "**課題: 夜の街の窓明かりや街灯を何百も置きたい。1 つずつライト（hlight の point）で置くのと、小さな光る球（Emission の材質）で置くのとで、"
            "Karma の時間とざらつきはどう違うか。何個まで置けるか。**\n\n"
            "40 m 四方の地面に箱 20 個（建物のつもり）を並べ、その上 3〜4.4 m に明かりを 1・10・100・1000 個、格子状に置いた。明かりの合計の強さは個数によらず同じにした"
            "（ライトは Intensity 400 ÷ 個数。光る球は半径 0.1 m で、同じ強さのライトと同じだけ光を出すよう Emission を式で決めた）。"
            "480×270 を 16 サンプルで撮った時間と、64 サンプルで撮った画との差（地面と箱の部分の、明るさに対する割合）をざらつきとした。"
            "ライトが 1 つも無いと Karma が自動で明かりを足すので、明るさ 0 の環境ライトを置いて止めた（はじめはこれを忘れ、光る球の場面が自動の明かりで照らされていた）。\n\n"
            f"**ライトは、1000 個でもなめらか。**1・10・100・1000 個で、撮る時間は {L(1, 'sec'):.1f}・{L(10, 'sec'):.1f}・{L(100, 'sec'):.1f}・{L(1000, 'sec'):.1f} 秒、"
            f"ざらつきは {L(1, 'noise') * 100:.1f}・{L(10, 'noise') * 100:.1f}・{L(100, 'noise') * 100:.1f}・{L(1000, 'noise') * 100:.1f}%。"
            "時間はライトの数とともに延びるが、1000 個でも 30 秒ほど。\n\n"
            f"**小さな光る球で照らすと、ひどくざらつく。**1・10・100・1000 個で、ざらつきは {G(1, 'noise') * 100:.0f}・{G(10, 'noise') * 100:.0f}・{G(100, 'noise') * 100:.0f}・{G(1000, 'noise') * 100:.0f}%。"
            f"16 サンプルの時間は {G(1, 'sec'):.1f}〜{G(1000, 'sec'):.1f} 秒と短いが、画は砂嵐のようになった。"
            f"64 サンプルでも、地面の明るさは 1・10・100・1000 個で {G(1, 'mean'):.3f}・{G(10, 'mean'):.3f}・{G(100, 'mean'):.3f}・{G(1000, 'mean'):.3f} と、"
            "光の合計は同じなのに大きく変わった。小さな光る物は、ライトのように光の出どころとして直接は調べられず、たまたま当たったときしか光が届かないためと考えられる（確かめてはいない）。"
            "数が多いほど当たりやすくなるので、明るさが増えて見える（まだ正しい明るさに落ち着いていない）。"
            f"64 サンプルで撮る時間は、光る球 100 個で {G(100, 'sec_ref64'):.0f} 秒と、ライト 100 個（{L(100, 'sec_ref64'):.0f} 秒）より長かった。\n\n"
            "**決め方: 照らすのはライト、画に写る電球は光る物で作る。**ライト（point）は画に写らないので、窓や電球の見た目には光る物を置き、"
            "その光で周りを照らそうとはしない。何百個でもライトでよい（1000 個で 16 サンプル約 30 秒）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "ライトと光る球（480×270・16 サンプル）",
             "images": [{"path": "225_grid.png", "caption": "左がライト、右が光る球。光る球は球そのものは写るが、地面はざらつく。"}],
             "per_row": 1, "columns": ["明かり", "個数", "16 サンプルの時間（秒）", "64 サンプルの時間（秒）", "ざらつき（%）", "地面の明るさ（64 サンプル）"],
             "rows": table},
        ],
        "notes": [
            f"<strong>ライト（point）は 1000 個でも 16 サンプル {L(1000, 'sec'):.0f} 秒・ざらつき {L(1000, 'noise') * 100:.0f}%。</strong>",
            f"<strong>小さな光る球で照らすと、ざらつき {G(10, 'noise') * 100:.0f}〜{G(100, 'noise') * 100:.0f}%。</strong>64 サンプルでも光が拾いきれない。",
            "<strong>照らすのはライト、写る電球は光る物。</strong>",
            "<strong>ライトが無い場面では、Karma が自動で明かりを足す。</strong>比べるときは明るさ 0 の環境ライトで止める。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "225_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
