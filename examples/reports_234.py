# -*- coding: utf-8 -*-
"""実験234 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font, line_chart  # noqa: E402


def main():
    with open(os.path.join(OUT, "234_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["diffuse_limit"]: r for r in d["rows"]}
    ref = d["ref"]
    line_chart(os.path.join(OUT, "234_curve.png"),
               [{"label": "部屋の明るさ（Diffuse Limit 16・256 サンプルを 100%）", "points": [(k, t[k]["mean_ratio"] * 100) for k in sorted(t)]}],
               "Diffuse Limit と部屋の明るさ", "Diffuse Limit", "明るさ（%）")
    font = _font(15)
    w, h = 400, 225
    shots = [0, 1, 4, 16]
    sheet = Image.new("RGB", (w * 4, h + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(shots):
        sheet.paste(Image.open(os.path.join(OUT, f"234_dl{k}.png")).convert("RGB").resize((w, h)), (i * w, 26))
        dr.text((i * w + 6, 4), f"Diffuse Limit {k}{'（既定）' if k == 1 else ''}  明るさ {t[k]['mean_ratio'] * 100:.0f}%・{t[k]['sec']:.0f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "234_grid.png"))
    table = [[str(k) + ("（既定）" if k == 1 else ""), f"{t[k]['sec']:.1f}", f"{t[k]['mean_ratio'] * 100:.1f}", f"{t[k]['rms_to_ref'] * 100:.1f}"] for k in sorted(t)]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": f"窓の光で照らす部屋は、Karma の Diffuse Limit 既定 1 では明るさが {g(1, 'mean_ratio') * 100:.0f}% しか出ない。"
                 f"4 で {g(4, 'mean_ratio') * 100:.0f}%、8 で {g(8, 'mean_ratio') * 100:.0f}%。時間は 1 → 4 で {g(4, 'sec') / g(1, 'sec'):.1f} 倍",
        "summary":
            "**課題: 室内を窓の光だけで照らすと、部屋が暗く写ることがある。Karma の Diffuse Limit（光が面で跳ね返るのを何回まで追うか）は既定 1。"
            "いくつにすれば部屋の明るさが落ち着くのか。時間はどう変わるか。**\n\n"
            "6 × 5 m・高さ 3 m の部屋（壁・床・天井は色 0.7 の principledshader）の一方の壁に 1.6 × 1.2 m の窓を開け、外から太陽（distant）と空（envlight）で照らした。"
            "カメラは部屋の中から奥を見る。Diffuse Limit を 0・1・2・4・8・16 にして、640×360・32 サンプル（ノイズ除去なし）で撮った。"
            "基準は Diffuse Limit 16・256 サンプルの画（右下の透かしは除いて明るさの平均を比べた）。\n\n"
            f"**既定の 1 では、部屋が暗い。**明るさは基準に対して、Diffuse Limit 0・1・2・4・8・16 で {g(0, 'mean_ratio') * 100:.0f}・{g(1, 'mean_ratio') * 100:.0f}・"
            f"{g(2, 'mean_ratio') * 100:.0f}・{g(4, 'mean_ratio') * 100:.0f}・{g(8, 'mean_ratio') * 100:.0f}・{g(16, 'mean_ratio') * 100:.0f}%。"
            "壁が明るい（色 0.7）部屋では、光が何度も跳ね返って奥まで届くので、跳ね返りを数回で打ち切ると、その分だけ暗くなる。"
            "画でも、0・1 は奥の壁や天井が暗く、4 以上で部屋全体が明るくなった。\n\n"
            f"**時間は、跳ね返りを追うほど延びる。**{g(0, 'sec'):.0f}・{g(1, 'sec'):.0f}・{g(2, 'sec'):.0f}・{g(4, 'sec'):.0f}・{g(8, 'sec'):.0f}・{g(16, 'sec'):.0f} 秒。"
            f"基準（256 サンプル）は {ref['sec']:.0f} 秒。\n\n"
            f"**ざらつきは、32 サンプルでは残る。**基準との差（明るさに対する割合）は 4 で {g(4, 'rms_to_ref') * 100:.0f}%、8 で {g(8, 'rms_to_ref') * 100:.0f}%。\n\n"
            "**決め方: 窓の光で照らす室内は、Diffuse Limit を 4 以上にする（明るい壁の部屋なら 8）。**既定の 1 は、外の場面や、明かりが直接当たる場面向け。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Diffuse Limit と部屋の明るさ（640×360・32 サンプル）",
             "images": [{"path": "234_grid.png", "caption": "左から 0・1（既定）・4・16。1 では奥が暗い。"},
                        {"path": "234_curve.png", "caption": "4 で 9 割、8 でほぼ落ち着く。"}],
             "per_row": 1, "columns": ["Diffuse Limit", "撮る時間（秒）", "明るさ（基準に対して %）", "基準との差（%）"], "rows": table},
        ],
        "notes": [
            f"<strong>窓の光の部屋は、既定の Diffuse Limit 1 では明るさが {g(1, 'mean_ratio') * 100:.0f}%。</strong>",
            f"<strong>4 で {g(4, 'mean_ratio') * 100:.0f}%、8 で {g(8, 'mean_ratio') * 100:.0f}%。</strong>時間は 1 → 4 で {g(4, 'sec') / g(1, 'sec'):.1f} 倍。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "234_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
