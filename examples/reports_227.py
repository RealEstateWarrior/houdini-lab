# -*- coding: utf-8 -*-
"""実験227 の図とレポートを、測った値から組み立てる。陰影図は保存した高さ（out/227_h_*.npy）から描く。"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

CASES = [("before", "削る前"), ("freeze5", "5 フレーム（既定）"), ("freeze20", "20 フレーム"), ("freeze50", "50 フレーム"), ("freeze100", "100 フレーム")]


def shade(h, sp=2.0, az=315, alt=45):
    """陰影図: 北西（方位 315°）・高さ 45° から光を当てたときの明るさ。"""
    gy, gx = np.gradient(h, sp)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a, e = np.radians(az), np.radians(alt)
    return np.clip(np.sin(e) * np.cos(slope) + np.cos(e) * np.sin(slope) * np.cos(a - aspect), 0, 1)


def main():
    with open(os.path.join(OUT, "227_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(15)
    size = 320
    sheet = Image.new("RGB", (size * 5, size + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, lab) in enumerate(CASES):
        s = shade(np.load(os.path.join(OUT, f"227_h_{k}.npy")))[125:375, 125:375]
        sheet.paste(Image.fromarray((s * 255).astype(np.uint8)).resize((size, size)).convert("RGB"), (i * size, 26))
        dr.text((i * size + 6, 4), lab + ("" if k == "before" else f"  {t[k]['sec']:.1f} 秒"), fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "227_grid.png"))
    table = [[lab, f"{t[k]['sec']:.2f}", f"{t[k]['h_std']:.1f}", f"{t[k]['slope_mean']:.1f}", f"{t[k]['rough']:.3f}", f"{t[k]['diff_mean']:.1f}", f"{t[k]['diff_max']:.1f}"]
             for k, lab in CASES]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": f"地形を削る heightfield_erode は、既定の 5 フレームでもう谷筋が刻まれる。20 フレームで谷の出口に土砂が広がり、"
                 f"100 フレームでは谷が埋まって山が低くなる（高さのばらつき {g('before', 'h_std'):.0f} → {g('freeze100', 'h_std'):.0f} m）。時間はどれも 3 秒以内",
        "summary":
            "**課題: 山の地形に川筋や崖を刻みたい。heightfield_erode（::3.0）は、フレームを進めながら少しずつ削り、Freeze at Frame（既定 5）で止まる。"
            "何フレームまで削ればよいのか。時間はどれだけかかるのか。**\n\n"
            "heightfield（1000 m 四方、Grid Spacing 2 → 500 × 500）に heightfield_noise（Amplitude 500 は既定、Element Size 300）で山を作り、"
            "Freeze at Frame を 5・20・50・100 にして削った（Iterations per Frame は 1 のまま）。削る時間は 1 通りずつ、ほかの処理は回さずに測った。"
            "見た目は、高さから描いた陰影図（北西から光を当てた地図。真ん中の 500 m 四方）で比べた。\n\n"
            f"**時間は小さい。**5・20・50・100 フレームで {g('freeze5', 'sec'):.2f}・{g('freeze20', 'sec'):.2f}・{g('freeze50', 'sec'):.2f}・{g('freeze100', 'sec'):.2f} 秒。\n\n"
            "**既定の 5 フレームで、もう「削った地形」になる。**削る前はただのでこぼこだったが、5 フレームで尾根と谷筋が刻まれた。"
            f"削る前との高さの差は平均 {g('freeze5', 'diff_mean'):.1f} m、いちばん大きい所で {g('freeze5', 'diff_max'):.0f} m。\n\n"
            "**20 フレームで、谷の出口に土砂が扇のように広がる。**50・100 フレームでは谷が土砂で埋まって平らな野が広がり、山は低く、斜面はゆるくなった。"
            f"高さのばらつき（標準偏差）は削る前・5・20・50・100 で {g('before', 'h_std'):.1f}・{g('freeze5', 'h_std'):.1f}・{g('freeze20', 'h_std'):.1f}・"
            f"{g('freeze50', 'h_std'):.1f}・{g('freeze100', 'h_std'):.1f} m、斜面の傾きの平均は {g('before', 'slope_mean'):.1f}・{g('freeze5', 'slope_mean'):.1f}・"
            f"{g('freeze20', 'slope_mean'):.1f}・{g('freeze50', 'slope_mean'):.1f}・{g('freeze100', 'slope_mean'):.1f}°。"
            f"100 フレームでは、いちばん深い所で {g('freeze100', 'diff_max'):.0f} m 削られた。\n\n"
            "**決め方: 険しい山に谷を刻むなら 5〜20 フレーム。平野や扇状地を広げたいなら 50 フレーム以上。**時間はどれも数秒なので、見た目で選んでよい。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "削るフレーム数と地形（陰影図、真ん中の 500 m 四方）",
             "images": [{"path": "227_grid.png", "caption": "左から削る前・5・20・50・100 フレーム。5 で谷筋が刻まれ、20 で扇状地が広がり、100 で谷が埋まる。"}],
             "per_row": 1, "columns": ["条件", "時間（秒）", "高さのばらつき（m）", "斜面の傾き（°）", "細かい凸凹（m）", "削る前との差 平均（m）", "最大（m）"],
             "rows": table},
        ],
        "notes": [
            "<strong>既定の 5 フレームで、もう谷筋が刻まれる。</strong>",
            f"<strong>20 フレームで扇状地が広がり、100 フレームで谷が埋まって山が低くなる。</strong>高さのばらつき {g('before', 'h_std'):.0f} → {g('freeze100', 'h_std'):.0f} m。",
            f"<strong>時間はどれも数秒（100 フレームで {g('freeze100', 'sec'):.1f} 秒）。</strong>見た目で選んでよい。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "227_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
