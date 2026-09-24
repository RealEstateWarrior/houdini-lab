# -*- coding: utf-8 -*-
"""実験231 の図とレポートを、測った値から組み立てる（条件ごとの out/231_part_*.json）。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

PARTS = [("fire", "0", "炎のボリュームだけ"), ("light", "12.07", "ライトだけ（炎は消す）"), ("fire_light", "12.07", "炎＋ライト")]


def main():
    t = {}
    for k, i, _ in PARTS:
        with open(os.path.join(OUT, f"231_part_{k}_{i}.json"), encoding="utf-8") as fp:
            t[k] = json.load(fp)
    with open(os.path.join(OUT, "231_part_light_1.json"), encoding="utf-8") as fp:
        one = json.load(fp)
    with open(os.path.join(OUT, "231_part_light_4.json"), encoding="utf-8") as fp:
        four = json.load(fp)
    rows = list(t.values()) + [one, four]
    import sop_bench
    sop_bench.save(231, rows, {"frame": 60, "res": [640, 360]})
    font = _font(16)
    sheet = Image.new("RGB", (640 * 3, 360 + 28), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, inten, lab) in enumerate(PARTS):
        im = Image.open(os.path.join(OUT, f"231_{k}_{inten}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (i * 640, 28))
        dr.text((i * 640 + 8, 5), f"{lab}  ざらつき {t[k]['noise16'] * 100:.1f}%", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "231_grid.png"))
    table = [[lab, f"{t[k]['lamp_intensity']:g}", f"{t[k]['sec16']:.1f}", f"{t[k]['sec128']:.1f}", f"{t[k]['noise16'] * 100:.1f}", f"{t[k]['ground']:.3f}"]
             for k, _, lab in PARTS]
    table += [["ライトだけ（強さを決める）", "1", f"{one['sec16']:.1f}", f"{one['sec128']:.1f}", f"{one['noise16'] * 100:.1f}", f"{one['ground']:.3f}"],
              ["ライトだけ（強さを決める）", "4", f"{four['sec16']:.1f}", f"{four['sec128']:.1f}", f"{four['noise16'] * 100:.1f}", f"{four['ground']:.3f}"]]
    g = lambda k, f: t[k][f]  # noqa: E731
    base = one["ground"] - (four["ground"] - one["ground"]) / 3
    payload = {
        "title": f"焚き火の炎のボリュームで周りを照らしても、ざらつきは {g('fire', 'noise16') * 100:.1f}%（16 サンプル）で、ライト（{g('light', 'noise16') * 100:.1f}%）と同じくらい。"
                 "ライトを足すと炎まで照らされて白く飛ぶ",
        "summary":
            "**課題: 焚き火や松明の場面で、周りの地面や薪を炎の光で照らしたい。実験225 では、小さな光る球で照らすとひどくざらついた（21〜54%）。"
            "Pyro の炎（kma_pyroshader の光るボリューム）で照らすとどうか。炎の中にライトを足すとどうなるか。**\n\n"
            "実践「焚き火」の場面（フレーム 60）を使い、実践で入れていた補助の明かり（キー・リム・ドーム）は 0 にした。"
            "640×360 を 16 サンプル（ノイズ除去なし）で撮り、同じ条件の 128 サンプルの画との差（画の下の地面・薪・石の部分の、明るさに対する割合）をざらつきとした。"
            "ライト（橙の point）の強さは、炎を消してライトだけで照らした地面が、炎だけのときと同じ明るさになるように決めた"
            f"（強さ 1 と 4 で撮って比で求めた。強さ 1 で {one['ground']:.4f}、4 で {four['ground']:.4f} と、ライトの分は強さに比例した。炎を消しても残るライトによらない分 {base:.4f} を除いて 12.07）。"
            "条件ごとに別の hython で撮った（同じ hython で続けて撮ると、ライトの強さや入り切りを変えても、Karma が前の場面を使い回した）。\n\n"
            f"**炎のボリュームの光だけで、なめらかに照らせる。**ざらつきは炎だけ {g('fire', 'noise16') * 100:.1f}%、ライトだけ {g('light', 'noise16') * 100:.1f}%。"
            f"時間は 16 サンプルで {g('fire', 'sec16'):.1f} 秒と {g('light', 'sec16'):.1f} 秒。小さな光る球（実験225）とは違い、炎のボリュームはライトと同じくらいきれいに周りを照らした。\n\n"
            "**見た目は炎だけがいちばん自然。**炎だけでは、炎の形と揺れのとおりに、手前の薪と地面が照らされた。ライトだけでは、炎の無い所まで一様に明るくなった。\n\n"
            f"**炎＋ライトでは、ライトが炎のボリュームまで照らして、炎が白く飛んだ。**ざらつきは {g('fire_light', 'noise16') * 100:.1f}%。"
            f"画の下の部分の明るさは {g('fire_light', 'ground'):.3f} で、炎だけ（{g('fire', 'ground'):.3f}）とライトだけ（{g('light', 'ground'):.3f}）の足し算より明るかった。"
            "測った範囲に炎の下の方が入っていて、その炎がライトの光を受けて明るく写ったためと考えられる。\n\n"
            "**決め方: 焚き火の明かりは、炎のボリュームの光に任せる。**ライトを足すと炎が白く飛ぶので、足すなら炎の外（上や後ろ）に置く（まだ測っていない）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "焚き火の照らし方（640×360・16 サンプル、ノイズ除去なし）",
             "images": [{"path": "231_grid.png", "caption": "左: 炎だけ。中: ライトだけ（炎は消した）。右: 炎＋ライト（炎が白く飛ぶ）。"}],
             "per_row": 1, "columns": ["照らし方", "ライトの強さ", "16 サンプル（秒）", "128 サンプル（秒）", "ざらつき（%）", "画の下の明るさ"], "rows": table},
        ],
        "notes": [
            f"<strong>炎のボリュームで照らしても、ざらつきは {g('fire', 'noise16') * 100:.1f}%。</strong>ライトと同じくらいなめらか。",
            "<strong>ライトを炎の中に足すと、炎まで照らされて白く飛ぶ。</strong>",
            "<strong>積んだ薪の内側（高さ 25 cm）に置いたライトは、薪にさえぎられて周りを照らさなかった。</strong>",
            "<strong>同じ hython で続けて撮ると、ライトの変更が画に出ないことがある。</strong>比べるときは条件ごとに起動し直す。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "231_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
