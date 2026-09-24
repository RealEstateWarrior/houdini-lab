# -*- coding: utf-8 -*-
"""実験216 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font, line_chart  # noqa: E402


def main():
    with open(os.path.join(OUT, "216_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    font = _font(15)
    tags = [("s025", "0.25"), ("s050", "0.5"), ("s100", "1"), ("s200", "2"), ("s400", "4"), ("s400_step1", "4・Step 1"),
            ("s400_step005", "4・Step 0.05")]
    w, h = 200, 150
    im = Image.new("RGB", (w * len(tags), h + 26), (20, 20, 22))
    dr = ImageDraw.Draw(im)
    for i, (tg, lab) in enumerate(tags):
        p = Image.open(os.path.join(OUT, f"216_{tg}.png")).convert("RGB").crop((170, 80, 470, 305)).resize((w, h))
        im.paste(p, (i * w, 26))
        dr.text((i * w + 6, 4), f"DS {lab}", fill=(230, 230, 230), font=font)
    im.save(os.path.join(OUT, "216_strip.png"))
    base = [r for r in d["rows"] if r["L"] == 0.5 and r["step"] == 0.25]
    xs = [0.25 * k for k in range(0, 17)]
    line_chart(os.path.join(OUT, "216_chart.png"),
               [{"label": "式 exp(−Density Scale × 0.5 m)", "points": [(x, math.exp(-x * 0.5)) for x in xs], "color": PALETTE[4]},
                {"label": "測った値（Step Rate 0.25・既定）", "points": [(r["scale"], r["T"]) for r in base], "color": PALETTE[0]},
                {"label": "測った値（Step Rate 1）", "points": [(4.0, t["s400_step1"]["T"])], "color": PALETTE[2]},
                {"label": "測った値（Step Rate 0.05）", "points": [(2.0, t["s200_step005"]["T"]), (4.0, t["s400_step005"]["T"])], "color": PALETTE[1]}],
               title="煙の向こうから届く光の割合（厚み 0.5 m）", x_label="Density Scale", y_label="届いた割合 T", y_range=(0, 1))
    table = [[r["case"].replace("_", " "), f"{r['scale']:g}", f"{r['L']:g}", f"{r['step']:g}", f"{r['T']:.4f}", f"{r['T_if_k1']:.4f}",
              f"{r['T'] / r['T_if_k1'] - 1:+.1%}", f"{r['k']:.3f}"] for r in d["rows"]]
    T = lambda k: t[k]["T"]  # noqa: E731
    payload = {
        "title": f"煙の透け具合は光の吸収の式 exp(−Density Scale × 濃さ × 厚み[m]) どおり — Density Scale を倍にすると、届く光は 2 乗に減る。ただし Volume Step Rate 0.25（既定）では濃い煙が少し明るく出て、1 で式とぴったり",
        "summary":
            "**課題: 煙が薄すぎる・濃すぎるとき、kma_pyroshader の Density Scale をいくつにすればよいか。倍にすると倍濃くなるのか。煙の厚みとどう関係するのか。**\n\n"
            "真っ白に光る板（Emission 1）の手前に、濃さ 1 の一様な煙の箱（1 × 1 × 厚み L）を置き、明かりを入れずに正面から撮った（煙は光を減らすだけにする。Enable Scatter は既定の切）。"
            "板の光のうち、煙を通って届いた割合 T を、EXR の明るさ（煙の中 ÷ 煙の外）で測った。光の吸収の式（ベールの法則）では T = exp(−k × Density Scale × 濃さ × L)。\n\n"
            f"**式とほぼ合う。k は 1（1 m あたり）。**厚み 0.5 m で Density Scale 0.25・0.5・1・2・4 のとき、T は {T('s025'):.3f}・{T('s050'):.3f}・{T('s100'):.3f}・{T('s200'):.3f}・{T('s400'):.3f}"
            f"（式では {t['s025']['T_if_k1']:.3f}・{t['s050']['T_if_k1']:.3f}・{t['s100']['T_if_k1']:.3f}・{t['s200']['T_if_k1']:.3f}・{t['s400']['T_if_k1']:.3f}）。"
            f"厚みを 1 m にすると {T('s100_L1'):.3f}（式 {t['s100_L1']['T_if_k1']:.3f}）で、Density Scale 2・厚み 0.5 m とほぼ同じ。**Density Scale と厚みは掛け算で効く。**\n\n"
            "**だから「倍にすると倍濃い」ではない。**Density Scale を倍にすると、届く光の割合は 2 乗になる（0.61 → 0.37 → 0.14）。\n\n"
            f"**濃い煙ほど、式より少し明るく出た。**Density Scale 4 で T = {T('s400'):.3f}（式 {t['s400']['T_if_k1']:.3f}、+{T('s400') / t['s400']['T_if_k1'] - 1:.0%}）。"
            f"Karma の Volume Step Rate（既定 0.25）を 1 に上げると {T('s400_step1'):.4f} で、式と 4 桁一致した。0.05 に下げると {T('s400_step005'):.3f} で、煙をほとんど素通りした。"
            "**Volume Step Rate は、大きいほど細かく煙の中を進む。**（実験207 では逆に「1 は粗い」と書いていたので、そちらを訂正した）\n\n"
            "**決め方: 煙の濃さは Density Scale と厚みの掛け算で決まる。濃い煙を正しい濃さで撮りたいときは Volume Step Rate を上げる**（焚き火では、上げると時間が延びた。実験207）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "光る板の手前の煙の箱（厚み 0.5 m）",
             "images": [{"path": "216_strip.png", "caption": "DS は Density Scale。上げるほど箱が暗い（光を通さない）。右の 2 枚は Density Scale 4 で Volume Step Rate を 1 と 0.05 にしたもの。0.05 は煙がほとんど消える。"},
                        {"path": "216_chart.png", "caption": "灰色の線が式。青（既定の Step Rate 0.25）は濃い所で少し上にずれ、緑（1）は式に乗る。"}],
             "per_row": 1,
             "columns": ["条件", "Density Scale", "厚み m", "Step Rate", "届いた割合 T", "式（k = 1）", "式との差", "k"], "rows": table},
        ],
        "notes": [
            "<strong>煙の透け具合は exp(−Density Scale × 濃さ × 厚み[m])。</strong>Density Scale と厚みは掛け算で効く。",
            "<strong>Density Scale を倍にすると、届く光は 2 乗に減る。</strong>「倍にすると倍濃い」ではない。",
            f"<strong>既定の Volume Step Rate 0.25 では、濃い煙が少し明るく出る</strong>（Density Scale 4 で +{T('s400') / t['s400']['T_if_k1'] - 1:.0%}）。1 に上げると式どおり。",
            "<strong>Volume Step Rate は大きいほど細かい。</strong>0.05 に下げると煙をほぼ素通りした。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "216_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 216_report.json")
    print(payload["title"])


if __name__ == "__main__":
    main()
