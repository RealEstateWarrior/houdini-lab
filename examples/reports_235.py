# -*- coding: utf-8 -*-
"""実験235 の図とレポートを、測った値から組み立てる。白く飛んだ画素（R・G・B すべて 250 以上）の数は PNG から数える。"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font, line_chart  # noqa: E402


def main():
    with open(os.path.join(OUT, "235_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["volume_limit"]: r for r in d["rows"]}
    for k, r in t.items():
        a = np.asarray(Image.open(os.path.join(OUT, f"235_vl{k}.png")).convert("RGB"))
        keep = np.ones(a.shape[:2], bool)
        keep[int(a.shape[0] * 0.85):, int(a.shape[1] * 0.7):] = False
        r["white_px"] = int(((a.min(axis=2) >= 250) & keep).sum())
    line_chart(os.path.join(OUT, "235_curve.png"),
               [{"label": "雲の上半分", "points": [(k, t[k]["top"]) for k in sorted(t)]},
                {"label": "雲の下半分", "points": [(k, t[k]["bottom"]) for k in sorted(t)]}],
               "Volume Limit と雲の明るさ（明るさの平均、1 を超えると白く飛ぶ）", "Volume Limit", "明るさ")
    font = _font(15)
    w, h = 400, 225
    sheet = Image.new("RGB", (w * 4, h + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate((0, 1, 4, 16)):
        sheet.paste(Image.open(os.path.join(OUT, f"235_vl{k}.png")).convert("RGB").resize((w, h)), (i * w, 26))
        dr.text((i * w + 6, 4), f"Volume Limit {k}{'（既定）' if k == 0 else ''}  {t[k]['sec']:.0f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "235_grid.png"))
    table = [[str(k) + ("（既定）" if k == 0 else ""), f"{t[k]['sec']:.0f}", f"{t[k]['top']:.3f}", f"{t[k]['bottom']:.3f}", f"{t[k]['white_px']:,}"] for k in sorted(t)]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": f"雲は、Karma の Volume Limit を上げるほど明るくなる（底の明るさ 0 → 16 で {g(0, 'bottom'):.2f} → {g(16, 'bottom'):.2f}）。"
                 f"16 でもまだ明るくなり続け、時間は {g(0, 'sec'):.0f} → {g(16, 'sec'):.0f} 秒。上げたら日差しを弱めないと白く飛ぶ",
        "summary":
            "**課題: 本物の積雲は、日陰の側や底でも明るい灰白色で、中から光っているように見える。CG の雲は底が暗く重たくなりやすい。"
            "Karma の Volume Limit（雲の中で光が散らばるのを何回まで追うか。既定 0）を上げると、雲はどう変わるのか。時間はどれだけ延びるのか。**\n\n"
            "実践「もくもくの雲を浮かべる」の場面（太陽 distant 強さ 4・空のドーム 0.5）で、Volume Limit を 0・1・2・4・8・16 にし、640×360・32 サンプル（ノイズ除去なし）で撮った。"
            "雲の写っている所（Volume Limit 16 の画で明るさ 0.15 超）を上半分と下半分に分け、明るさの平均を比べた。\n\n"
            f"**上げるほど、雲は明るくなる。**明るさの平均は、上半分が 0・1・2・4・8・16 で {g(0, 'top'):.2f}・{g(1, 'top'):.2f}・{g(2, 'top'):.2f}・{g(4, 'top'):.2f}・{g(8, 'top'):.2f}・{g(16, 'top'):.2f}、"
            f"下半分が {g(0, 'bottom'):.2f}・{g(1, 'bottom'):.2f}・{g(2, 'bottom'):.2f}・{g(4, 'bottom'):.2f}・{g(8, 'bottom'):.2f}・{g(16, 'bottom'):.2f}。"
            "8 → 16 でもまだ 1 割明るくなり、落ち着かなかった。雲は光をほとんど吸わず、中で何度も散らばってから外へ出るので、追う回数を打ち切るほど暗くなると考えられる。\n\n"
            f"**時間は大きく延びる。**{g(0, 'sec'):.0f}・{g(1, 'sec'):.0f}・{g(2, 'sec'):.0f}・{g(4, 'sec'):.0f}・{g(8, 'sec'):.0f}・{g(16, 'sec'):.0f} 秒。1 で既定の {g(1, 'sec') / g(0, 'sec'):.0f} 倍になる。\n\n"
            f"**明るくなるほど、白く飛んで陰影が消える。**白く飛んだ画素（R・G・B すべて 250 以上）は {g(0, 'white_px'):,}・{g(1, 'white_px'):,}・{g(2, 'white_px'):,}・{g(4, 'white_px'):,}・{g(8, 'white_px'):,}・{g(16, 'white_px'):,} 個。"
            "既定の 0 は、もこもこの塊ごとの陰影が見えたが、4 以上では雲がほぼ真っ白な塊になった。\n\n"
            "**決め方: 雲を本物らしく明るくするなら、Volume Limit を上げ、そのぶん日差しを弱める。**時間が許すなら 4 以上。"
            "試し撮りは既定の 0 で形を見て、仕上げで上げる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Volume Limit と雲（640×360・32 サンプル）",
             "images": [{"path": "235_grid.png", "caption": "左から 0（既定）・1・4・16。上げるほど明るく、白く飛んで陰影が消える。"},
                        {"path": "235_curve.png", "caption": "16 でもまだ明るくなり続ける。"}],
             "per_row": 1, "columns": ["Volume Limit", "撮る時間（秒）", "上半分の明るさ", "下半分の明るさ", "白く飛んだ画素"], "rows": table},
        ],
        "notes": [
            f"<strong>Volume Limit を上げるほど、雲は明るくなる。</strong>16 でもまだ落ち着かない（8 → 16 で 1 割増）。",
            f"<strong>時間は 0 → 16 で {g(0, 'sec'):.0f} → {g(16, 'sec'):.0f} 秒。</strong>",
            "<strong>上げたら日差しを弱めないと、白く飛んで陰影が消える。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "235_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])
    print({k: t[k]["white_px"] for k in sorted(t)})


if __name__ == "__main__":
    main()
