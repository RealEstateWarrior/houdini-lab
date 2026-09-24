# -*- coding: utf-8 -*-
"""実験223 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def main():
    with open(os.path.join(OUT, "223_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    with open(os.path.join(OUT, "223_sens.json"), encoding="utf-8") as fp:
        sens = {r["case"]: r["cusp_threshold"] for r in json.load(fp)}
    t = {r["wind"]: r for r in rows}
    font = _font(17)
    sheet = Image.new("RGB", (480 * 3, 480 + 34), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, u in enumerate((5, 10, 15)):
        sheet.paste(Image.open(os.path.join(OUT, f"223_top_{u}.png")).convert("RGB"), (i * 480, 34))
        dr.text((i * 480 + 8, 7), f"風 {u} m/秒・白波 {t[u]['whitecap_pct']:.2f}%（cusp > {t[u]['cusp_threshold']:.3f}）",
                fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "223_grid.png"))
    table = [[str(u), f"{t[u]['hs_pm']:.2f}", f"{t[u]['ampscale']:.3f}", f"{t[u]['whitecap_pct']:.2f}", f"{t[u]['cusp_threshold']:.3f}",
              f"{t[u]['pct_at_055']:.3f}", f"{t[u]['cusp_max']:.2f}"] for u in sorted(t)]
    th = lambda u: t[u]["cusp_threshold"]  # noqa: E731
    payload = {
        "title": f"海の白波の cusp のしきい値は、風 5 m/秒で {th(5):.2f}・10 m/秒で {th(10):.2f}・15 m/秒で {th(15):.2f}"
                 "（波の高さを本物に合わせたとき）。0.55 では風 15 m/秒でもほぼ白波が出ない",
        "summary":
            "**課題: oceanevaluate の Cusp Attribute（波の頭のとがり）で白波の色を付けるとき、しきい値をいくつにすれば、その風の強さの本物の海と同じ量の白波になるか。**\n\n"
            "実践「夕暮れの海」（風 7 m/秒）は、しきい値 0.55 で白波が 0% だった。そこで、答えの出る 2 つの式と突き合わせた。"
            "本物の白波が海面を覆う割合 W = 3.84 × 10⁻⁶ × U^3.41（Monahan と O'Muircheartaigh, 1980。U は風速 m/秒）と、"
            "十分に発達した海の波の高さ Hs = 0.21 × U² / g（Pierson と Moskowitz）。\n\n"
            "200 m 四方の板（512 × 512）を oceanspectrum（Grid Size 200・Resolution Exponent 9・Chop 0.9）で動かし、"
            "Amplitude の Scale を、高さの標準偏差が Hs / 4 になるように決めた。そのうえで、cusp がしきい値を超える点の割合が W になるしきい値を、"
            "3 つの時刻（1・3・5 秒）の点を合わせて求めた。\n\n"
            f"**本物の量の白波にするしきい値は、風 5・7・10・12・15 m/秒で {th(5):.3f}・{th(7):.3f}・{th(10):.3f}・{th(12):.3f}・{th(15):.3f}。**"
            f"白波の割合は {t[5]['whitecap_pct']:.2f}%・{t[7]['whitecap_pct']:.2f}%・{t[10]['whitecap_pct']:.2f}%・{t[12]['whitecap_pct']:.2f}%・{t[15]['whitecap_pct']:.2f}%。"
            "風が強いほど波がとがるので、しきい値は上がる。\n\n"
            f"**しきい値 0.55 では、ほとんど白波が出ない。**風 15 m/秒でも {t[15]['pct_at_055']:.3f}%（本物は {t[15]['whitecap_pct']:.1f}%）。"
            f"cusp のいちばん大きい値が、風 10 m/秒で {t[10]['cusp_max']:.2f}、15 m/秒で {t[15]['cusp_max']:.2f} しかない。"
            "夕暮れの海で白波が 0% だったのは、しきい値が高すぎたため。\n\n"
            f"**しきい値は Chop でいちばん変わる。**風 10 m/秒で、Chop 0.6・0.9・1.3 のしきい値は {sens['Chop 0.6']:.3f}・{th(10):.3f}・{sens['Chop 1.3']:.3f}。"
            f"Resolution Exponent 8・9・10 では {sens['Resolution Exponent 8']:.3f}・{th(10):.3f}・{sens['Resolution Exponent 10']:.3f} と、あまり変わらない。\n\n"
            "**決め方: 波の高さを本物に合わせたうえで、Chop 0.9 なら上の表のしきい値を使う。**Chop を変えたら、しきい値もほぼ同じ割合で変える。"
            "波の高さ（Amplitude の Scale）を本物より高くしていると cusp も大きくなるので、この表はそのままでは使えない。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "風の強さと白波（上から見た 60 m 四方）",
             "images": [{"path": "223_grid.png", "caption": "しきい値を超えた所を白く塗った。風 5 m/秒ではほとんど無く、15 m/秒で筋が増える。"}],
             "per_row": 1, "columns": ["風（m/秒）", "有義波高 Hs（m）", "Amplitude の Scale", "本物の白波（%）", "しきい値", "0.55 での白波（%）", "cusp の最大"],
             "rows": table},
        ],
        "notes": [
            f"<strong>本物の量の白波にするしきい値は、風 5 m/秒 {th(5):.2f}・10 m/秒 {th(10):.2f}・15 m/秒 {th(15):.2f}。</strong>（Chop 0.9、高さを本物に合わせたとき）",
            "<strong>しきい値 0.55 では、風 15 m/秒でもほぼ白波が出ない。</strong>",
            "<strong>しきい値は Chop にほぼ比例して変わる。</strong>細かさ（Resolution Exponent）ではあまり変わらない。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "223_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
