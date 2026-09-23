# -*- coding: utf-8 -*-
"""実験203 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "203_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r["sec"] for r in d["rows"]}
    slope_o = (t["opaque_spp64"] - t["opaque_all"]) / 48
    slope_t = (t["full_spp64"] - t["full"]) / 48
    base = t["opaque_all"] - 16 * slope_o
    px = (1280 * 720) / (480 * 270)
    est96 = base + px * slope_t * 96
    est16 = base + px * (t["full"] - base)
    line_chart(os.path.join(OUT, "203_spp.png"),
               [{"label": "3つとも不透明", "points": [(16, t["opaque_all"]), (64, t["opaque_spp64"])], "color": PALETTE[0]},
                {"label": "ガラス・水・氷（透明）", "points": [(16, t["full"]), (64, t["full_spp64"])], "color": PALETTE[1]}],
               title="480×270 で撮る時間とサンプル数", x_label="1画素あたりのサンプル（最大）", y_label="秒")
    font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 15)
    pics = [("full", "透明（ガラス・水・氷）"), ("opaque_all", "3つとも不透明"), ("refr2", "Refraction Limit 2")]
    ims = [Image.open(os.path.join(OUT, f"pr_exp203_{c}_hero.png")).convert("RGB") for c, _ in pics]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * 3, h + 26), (20, 20, 22))
    dr = ImageDraw.Draw(sheet)
    for i, (im, (c, lab)) in enumerate(zip(ims, pics)):
        sheet.paste(im, (i * w, 26))
        dr.text((i * w + 6, 4), f"{lab}（{t[c]:.0f} 秒）", fill=(230, 230, 230), font=font)
    sheet.save(os.path.join(OUT, "203_compare.png"))
    rows_order = [("opaque_all", "3つとも不透明"), ("glass", "ガラスだけ"), ("glass_water", "ガラス＋水"), ("full", "ガラス＋水＋氷"),
                  ("refr2", "↑ Refraction Limit 2"), ("refr8", "↑ Refraction Limit 8"), ("opaque_ice", "↑ 氷だけ不透明"),
                  ("nogap", "↑ 水とガラスのすき間 0"), ("full_dim", "↑ 明かりを 1/4"), ("opaque_dim", "不透明＋明かり 1/4"),
                  ("opaque_spp64", "不透明・64 サンプル"), ("full_spp64", "透明・64 サンプル"), ("full_960_spp16", "透明・960×540")]
    payload = {
        "title": f"氷の入ったグラスを Karma で撮ると、サンプル1つあたり不透明の {slope_t / slope_o:.0f} 倍の時間がかかる — 重ねた水と氷は +{t['full'] / t['glass'] - 1:.0%} だけ。16 サンプル＋ノイズ除去なら約 {est16 / 60:.0f} 分",
        "summary":
            "**課題: 実践「氷の入ったグラスの水」を 1280×720・96 サンプルで撮ろうとしたら、25 分たっても終わらなかった。何が時間を食っているのか。どうすれば短くなるか。**\n\n"
            "グラス（厚い底の断面を revolve）・水（内側に 0.2 mm すき間）・氷3つを、実践と同じ撮り方（暗い幕・キー・リム・ドーム）で、"
            f"480×270・最大 {d['spp']} サンプルに下げて1枚ずつ撮り、時間を測った（1 枚目は起動の分を捨てた）。"
            "Karma の既定の決め方は Convergence Mode = Variance（画素ごとに、ざらつきが 0.01 より小さくなったらサンプルを打ち切る。最小 1・最大はサンプル数）。\n\n"
            f"**効いているのは、サンプル数を増やしたときの伸び方。**不透明にした場面は 16 サンプルで {t['opaque_all']:.1f} 秒・64 サンプルで {t['opaque_spp64']:.1f} 秒、"
            f"透明な場面は {t['full']:.1f} 秒・{t['full_spp64']:.1f} 秒。サンプルを 1 増やすごとに、不透明は {slope_o:.2f} 秒、透明は {slope_t:.2f} 秒（{slope_t / slope_o:.1f} 倍）増えた。"
            "不透明な所は途中でざらつきが下がって打ち切られ、屈折した所は最大まで回っていると考えられるが、画素ごとのサンプル数は確かめていない。\n\n"
            f"**1 枚ごとの準備の時間は約 {base:.0f} 秒。**不透明の 2 点を結んだ線の、サンプル 0 の所の値。小さな画で試すときは、この分が大半になる。\n\n"
            f"**重ねた物の数は、あまり効かない。**16 サンプルで、ガラスだけ {t['glass']:.1f} 秒、＋水 {t['glass_water']:.1f} 秒、＋氷 {t['full']:.1f} 秒（ガラスだけの {t['full'] / t['glass']:.2f} 倍）。"
            f"氷だけ不透明にすると {t['opaque_ice']:.1f} 秒、水とガラスのすき間を 0 にしても {t['nogap']:.1f} 秒で、ほとんど変わらない。\n\n"
            f"**屈折の回数の上限（Refraction Limit、既定 4）は少し効く。**2 で {t['refr2']:.1f} 秒（{1 - t['refr2'] / t['full']:.0%} 短い）、8 で {t['refr8']:.1f} 秒。"
            f"明かりを 1/4 に弱めても {t['full_dim']:.1f} 秒で、{1 - t['full_dim'] / t['full']:.0%} しか縮まない。\n\n"
            f"**画素の数には比例する。**960×540（4 倍の画素）・16 サンプルは {t['full_960_spp16']:.1f} 秒で、準備の時間を除くと 480×270 の {(t['full_960_spp16'] - base) / (t['full'] - base):.1f} 倍。\n\n"
            f"**見積もり: 1280×720・96 サンプルは約 {est96 / 60:.0f} 分。**（{slope_t:.2f} 秒 × 96 × 画素 {px:.1f} 倍 ＋ 準備）。25 分で終わらなかったのと合う。"
            f"16 サンプルならおよそ {est16 / 60:.0f} 分で、ざらつきはノイズ除去（OIDN）で消す。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "480×270・16 サンプルで撮った画",
             "images": [{"path": "203_compare.png", "caption": "左から 透明・不透明・Refraction Limit 2。かっこは撮るのにかかった秒。"}],
             "per_row": 1, "columns": [], "rows": []},
            {"label": "サンプル数と時間",
             "images": [{"path": "203_spp.png", "caption": "透明な場面は、サンプルを増やすと不透明の6倍の割合で時間が延びる。"}],
             "per_row": 1, "columns": ["条件", "秒"],
             "rows": [[lab, f"{t[c]:.1f}"] for c, lab in rows_order]},
        ],
        "notes": [
            f"<strong>透明な物を撮るときは、サンプル数を上げない。</strong>サンプル1つあたり、不透明の {slope_t / slope_o:.0f} 倍の時間がかかった。16 サンプルにしてノイズ除去で仕上げる。",
            "<strong>透明な物を重ねたこと（水・氷）は、時間をあまり増やさない（+27%）。</strong>すき間の有無も時間には効かなかった。",
            f"<strong>Refraction Limit を 4 → 2 にすると {1 - t['refr2'] / t['full']:.0%} 短い。</strong>それ以上減らしたいときの手。",
            f"<strong>試し撮りの小さな画では、1 枚あたり約 {base:.0f} 秒の準備が大半になる。</strong>比べるときは、サンプル数を2通り撮って差を見る。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "203_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 203_report.json", round(slope_o, 3), round(slope_t, 3), round(base, 1), round(est96 / 60, 1), round(est16 / 60, 1))


if __name__ == "__main__":
    main()
