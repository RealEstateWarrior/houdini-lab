# -*- coding: utf-8 -*-
"""実験208 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LABELS = {"default": "既定", "vox050": "Voxel Scale 0.5", "vox150": "Voxel Scale 1.5", "infl2": "Influence Scale 2",
          "infl5": "Influence Scale 5", "spherical": "Method = Spherical", "filter": "Filtering（Dilate・Smooth・Erode）",
          "neural": "Method = Neural Point Surface"}


def main():
    with open(os.path.join(OUT, "208_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    wv = d["water_volume"]
    font = _font(16)
    w, h = 560, 360
    sheet = Image.new("RGB", (w * 2, (h + 28) * 4), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(LABELS):
        im = Image.open(os.path.join(OUT, f"208_{k}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
        x, y = (i % 2) * w, (i // 2) * (h + 28)
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (x, y + 28))
        f36 = t[k]["f36"]
        dr.text((x + 8, y + 5), f"{LABELS[k]}　{f36['sec']:.2f} 秒・体積 {f36['volume'] / wv:.0%}", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "208_grid.png"))
    table = []
    for k, lab in LABELS.items():
        a, b = t[k]["f36"], t[k]["f60"]
        table.append([lab, f"{a['sec']:.2f}", f"{a['polys']:,}", f"{a['volume'] / wv:.1%}", f"{a['area']:.2f}", f"{b['volume'] / wv:.1%}"])
    s = lambda k: t[k]["f36"]["sec"]  # noqa: E731
    v = lambda k, f=36: t[k][f"f{f}"]["volume"] / wv  # noqa: E731
    ar = lambda k: t[k]["f36"]["area"]  # noqa: E731
    payload = {
        "title": f"FLIP の水を面にするとき、形を決めるのは Influence Scale と Method — Spherical はつぶつぶ、Influence 5 は体積 {v('infl5'):.0%}。なめらかにするなら Filtering（既定の {s('filter') / s('default'):.1f} 倍の時間）",
        "summary":
            "**課題: FLIP を回したあと、粒を水の面にする（particlefluidsurface）。粒のつぶつぶが残る・しぶきが消える・水が増える、といった見た目の問題が出たとき、どのつまみを触ればよいか。重くなるのはどれか。**\n\n"
            f"実験200 と同じダムブレイク（0.6 × 0.9 × 1 m の水、体積 {wv:.2f} m³、Particle Separation {d['sep']}）を 60 フレーム回し（{d['sim_sec']:.0f} 秒）、"
            "右の壁にぶつかって跳ね上がるフレーム 36 と、落ち着いてきたフレーム 60 で、particlefluidsurface の設定を 8 通りにして面にした。"
            "面にかかる時間（1 つ前のフレームを作ってから戻して 4 回作り、1 回目を除いたいちばん短い回）・面の数・体積（最初の水と比べる）・表面積（でこぼこが多いほど大きい）を測った。\n\n"
            f"**既定（Average Position・Voxel Scale 0.75・Influence Scale 3）は、体積 {v('default'):.0%} で {s('default'):.2f} 秒。**"
            "壁ぎわのしぶきは、粒の先が丸くつながった形になる。\n\n"
            f"**Voxel Scale は、細かさと重さだけを変える。**0.5 で面の数 {t['vox050']['f36']['polys']:,}（既定の {t['vox050']['f36']['polys'] / t['default']['f36']['polys']:.1f} 倍）・{s('vox050'):.2f} 秒、"
            f"1.5 で {t['vox150']['f36']['polys']:,}・{s('vox150'):.2f} 秒。体積は {v('vox050'):.0%}・{v('vox150'):.0%} で、形の大きさはあまり変わらない。1.5 はしぶきの先が丸く太る。\n\n"
            f"**Influence Scale は、水の太り方を変える。**2 で体積 {v('infl2'):.0%}・表面積 {ar('infl2'):.2f}（しぶきが細かく残る）、5 で {v('infl5'):.0%}・{ar('infl5'):.2f}（しぶきが丸まって水が痩せる）。"
            f"既定の 3 は {v('default'):.0%}・{ar('default'):.2f}。\n\n"
            f"**Method = Spherical は、粒 1 つずつの球が残ってつぶつぶになる。**表面積 {ar('spherical'):.2f} で、8 通りの中でいちばん大きい。時間は {s('spherical'):.2f} 秒と短い。\n\n"
            f"**なめらかにするなら Filtering。**Dilate・Smooth・Erode を入れる（値は既定のまま）と、表面積 {ar('filter'):.2f}・体積 {v('filter'):.0%}・{s('filter'):.2f} 秒（既定の {s('filter') / s('default'):.1f} 倍）。"
            "しぶきの形を残したまま、平らな所のさざ波が消えた。\n\n"
            f"**Neural Point Surface（H21 の新しい方式）は、既定の {s('neural') / s('default'):.1f} 倍の時間。**{s('neural'):.2f} 秒で、形は既定とフィルタの間くらい、体積 {v('neural'):.0%}。"
            "最初に使うときだけ、読み込みで数秒余分にかかった（はじめの測り方で、1 回目が平均を大きく引き上げた）。\n\n"
            f"**面にする時間は、粒の計算の 1 フレーム分と同じくらい。**60 フレームの計算は 1 フレーム平均 {d['sim_sec'] / 60:.2f} 秒、面にするのは既定で {s('default'):.2f} 秒。"
            f"Voxel Scale 0.5 では {s('vox050'):.2f} 秒で、粒の計算の約 2 倍になる。\n\n"
            f"**フレーム 60 では、どの設定でも体積が減った**（既定 {v('default', 60):.0%}）。実験200 と同じく、粒が減っているため（面の作り方ではない）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "フレーム 36（右の壁で跳ね上がる所）を面にした形",
             "images": [{"path": "208_grid.png", "caption": "同じ粒から作った 8 通りの面。かっこは面にかかった時間と、最初の水に対する体積。"}],
             "per_row": 1,
             "columns": ["設定", "秒（36）", "面の数（36）", "体積（36）", "表面積 m²（36）", "体積（60）"], "rows": table},
        ],
        "notes": [
            f"<strong>しぶきの細かさは Influence Scale で決める。</strong>2 で細かく残り（体積 {v('infl2'):.0%}）、5 で丸まって痩せる（{v('infl5'):.0%}）。",
            f"<strong>さざ波やつぶつぶを消すなら Filtering を入れる。</strong>時間は {s('filter'):.2f} 秒（既定の {s('filter') / s('default'):.1f} 倍）。",
            "<strong>Method = Spherical はつぶつぶが残る。</strong>水の面には既定の Average Position の方が向く。",
            f"<strong>Voxel Scale は細かさと重さ。</strong>0.5 で面が 1.9 倍・時間 {s('vox050') / s('default'):.1f} 倍。形の大きさはほとんど変わらない。",
            f"<strong>Neural Point Surface は既定の {s('neural') / s('default'):.1f} 倍の時間。</strong>この場面では、フィルタを入れた既定と見た目の差は小さかった。",
            "<strong>面にする時間を測るときは、1 つ前のフレームから戻して作り直させる。</strong>つまみをごくわずかに動かすだけでは作り直さず、0.01 秒台と出た。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "208_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 208_report.json")
    print(payload["title"])
    print({k: (round(v(k), 3), round(v(k, 60), 3), t[k]["f60"]["sec"]) for k in LABELS})


if __name__ == "__main__":
    main()
