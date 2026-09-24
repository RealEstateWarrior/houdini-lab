# -*- coding: utf-8 -*-
"""実験204 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font  # noqa: E402

LABELS = [("raw", "そのまま（Volume 6つ）"), ("vdb", "VDB にする"), ("vdb_half", "VDB＋16 bit"),
          ("vdb_half_prune", "VDB＋16 bit＋小さい値を捨てる"), ("vdb_half_velmask", "vel を煙のある所だけ＋VDB＋16 bit"),
          ("novel", "vel を捨てる"), ("vdb_novel", "vel を捨てる＋VDB"), ("vdb_half_novel", "vel を捨てる＋VDB＋16 bit")]


def bars(path, rows):
    """横棒: 48 フレーム分の合計 MB。Voxel Size 0.04 と 0.02 を並べる。"""
    f, fs = _font(20), _font(16)
    w, rowh, left = 1100, 58, 360
    h = 90 + rowh * len(LABELS) + 40
    im = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((20, 18), "48 フレーム（2 秒）を .bgeo.sc に書いたときの合計", fill=(20, 20, 20), font=f)
    top = max(r["sizes"]["raw"] for r in rows) / 1e6
    for j, r in enumerate(rows):
        d.rectangle((left + j * 220, 58, left + j * 220 + 14, 72), fill=PALETTE[j])
        d.text((left + j * 220 + 20, 54), f"Voxel Size {r['vox']}", fill=(40, 40, 40), font=fs)
    for i, (k, lab) in enumerate(LABELS):
        y = 90 + i * rowh
        d.text((20, y + 12), lab, fill=(30, 30, 30), font=fs)
        for j, r in enumerate(rows):
            mb = r["sizes"][k] / 1e6
            x1 = left + (w - left - 120) * mb / top
            d.rectangle((left, y + 4 + j * 24, max(left + 2, x1), y + 24 + j * 24), fill=PALETTE[j])
            d.text((max(left + 2, x1) + 6, y + 4 + j * 24), f"{mb:.1f} MB", fill=(40, 40, 40), font=fs)
    im.save(path)


def main():
    with open(os.path.join(OUT, "204_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows = sorted(d["rows"], key=lambda r: -r["vox"])     # 0.04, 0.02
    a, b = rows
    bars(os.path.join(OUT, "204_size.png"), rows)
    mb = lambda r, k: r["sizes"][k] / 1e6  # noqa: E731
    ratio = lambda r, k: r["sizes"]["raw"] / r["sizes"][k]  # noqa: E731
    fill = a["filled"]
    dh = a["diff"]["vdb_half@48"]
    dv = a["diff"]["vdb@48"]
    dr = a["diff"]["raw@48"]
    table = []
    for k, lab in LABELS:
        table.append([lab, f"{mb(a, k):.1f}", f"{ratio(a, k):.1f} 倍", f"{mb(b, k):.1f}", f"{ratio(b, k):.1f} 倍",
                      f"{a['write_sec'][k]:.2f}", f"{a['read_sec'][k]:.2f}"])
    payload = {
        "title": f"焚き火の Pyro のキャッシュは、9 割以上が速度（vel）— vel を煙のある所だけに残して VDB・16 bit にすると {ratio(a, 'vdb_half_velmask'):.0f} 分の 1、描画に使う値のずれは {dh['density']['max']:.5f}",
        "summary":
            "**課題: 焚き火の Pyro をキャッシュ（ファイル）に書くと何 MB になるか。何を削れば小さくなり、そのとき炎や煙の値はどれだけ変わるか。**\n\n"
            "実験202 と同じ焚き火（平たい球を Source Burn で燃やす）を Voxel Size 0.04 と 0.02 で 48 フレーム（2 秒）回し、"
            "毎フレーム 8 通りのやり方で .bgeo.sc に書いた。書いたファイルは File で読み戻し、Volume Wrangle で元の値との差を取った。\n\n"
            f"**そのまま書くと、Voxel Size 0.04 で 48 フレーム {mb(a, 'raw'):.0f} MB、0.02 で {mb(b, 'raw'):.0f} MB。**"
            f"中身は Volume が 6 つ（density・temperature・flame と、速度の vel.x・vel.y・vel.z）。\n\n"
            f"**容量のほとんどは vel。**vel を捨てるだけで {mb(a, 'novel'):.1f} MB（{ratio(a, 'novel'):.0f} 分の 1）になった。"
            f"フレーム 48 で、煙が入っている升（density > 0.001）は全体の {fill['density>0.001']:.1%} しかないのに、"
            f"速さが 0.01 を超える升は {fill['|vel|>0.01']:.0%} あった。煙の無い所でも空気は動いていて、そこの 0 でない値が圧縮で縮まない。\n\n"
            f"**VDB にするだけでは小さくならない。**convertvdb で VDB にすると {mb(a, 'vdb'):.0f} MB で、むしろ少し増えた。"
            f"VDB は 0 の所を持たないのが得意だが、vel は 0 ではないので効かない。Prune Tolerance を 0.01 にしても {mb(a, 'vdb_half_prune'):.0f} MB で変わらなかった。\n\n"
            f"**16 bit（half）で書くと、約半分。**VDB の intrinsic `vdb_is_saved_as_half_float` を 1 にすると {mb(a, 'vdb_half'):.1f} MB（VDB の {a['sizes']['vdb_half'] / a['sizes']['vdb']:.0%}）。"
            f"読み戻した値のずれは、最大 {dh['density']['max']:.5f}（density の最大 {dh['density']['field_max']:.2f} に対して）、平均 {dh['density']['mean']:.1e}。"
            f"32 bit の VDB は最大 {dv['density']['max']:.1e}、そのままのファイルは {dr['density']['max']:.1e} で、これは比べ方（位置から値を読む volumesample）の分のずれ。\n\n"
            f"**モーションブラーに vel を残したいときは、煙の無い所の vel を 0 にする。**Volume Wrangle で「density も flame も 0.001 未満なら v@vel = 0」として VDB・16 bit で書くと、"
            f"{mb(a, 'vdb_half_velmask'):.1f} MB（そのままの {ratio(a, 'vdb_half_velmask'):.0f} 分の 1）。Voxel Size 0.02 では {mb(b, 'raw'):.0f} MB → {mb(b, 'vdb_half_velmask'):.0f} MB（{ratio(b, 'vdb_half_velmask'):.0f} 分の 1）。"
            "煙のある所の vel は変えていない。\n\n"
            f"**Voxel Size を半分にすると、そのままなら {b['sizes']['raw'] / a['sizes']['raw']:.1f} 倍。**升の数は約 8 倍になるが、"
            f"外側の升は 0 に近く圧縮で縮む。いちばん小さい書き方（vel を捨てて VDB・16 bit）は {mb(a, 'vdb_half_novel'):.1f} MB → {mb(b, 'vdb_half_novel'):.1f} MB。\n\n"
            f"書く時間はどれも短い（そのまま 48 フレームで {a['write_sec']['raw']:.2f} 秒、VDB にすると変換を含めず {a['write_sec']['vdb']:.2f} 秒）。"
            f"**同じ VDB でも、.vdb 形式のファイルは .bgeo.sc より大きかった。**VDB＋16 bit で {a['vdbfile']['vdb_half'] / 1e6:.0f} MB（.bgeo.sc の {a['vdbfile']['vdb_half'] / a['sizes']['vdb_half']:.2f} 倍）、"
            f"vel を煙のある所だけにしたもので {a['vdbfile']['vdb_half_velmask'] / 1e6:.1f} MB（{a['vdbfile']['vdb_half_velmask'] / a['sizes']['vdb_half_velmask']:.2f} 倍）。"
            ".bgeo.sc は中身をさらに圧縮して書くためと考えられる（確かめていない）。ほかのソフトに渡すのでなければ .bgeo.sc でよい。表は .bgeo.sc の値。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "48 フレーム分のキャッシュの大きさ",
             "images": [{"path": "204_size.png", "caption": "青が Voxel Size 0.04、橙が 0.02。vel を捨てるか、煙のある所だけに残すと一気に小さくなる。"}],
             "per_row": 1,
             "columns": ["書き方", "0.04 の MB", "0.04 の縮み", "0.02 の MB", "0.02 の縮み", "書く秒（0.04）", "読む秒（0.04）"],
             "rows": table},
        ],
        "notes": [
            "<strong>Pyro のキャッシュの大半は vel。</strong>煙のある升は 4% なのに、vel は 6 割以上の升で 0 でない。描画に要らなければ blast で捨てる（24 分の 1）。",
            f"<strong>モーションブラーに vel が要るなら、煙の無い所の vel を 0 にしてから VDB・16 bit。</strong>{ratio(a, 'vdb_half_velmask'):.0f} 分の 1 になり、煙のある所の値は残る。",
            "<strong>VDB にするだけ・Prune Tolerance 0.01 だけでは小さくならない。</strong>0 でない値を持つ vel が残るため。",
            f"<strong>16 bit で書くと約半分。</strong>値のずれは最大 {dh['density']['max']:.5f}（値の最大 1 に対して）。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "204_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 204_report.json")
    print({k: round(mb(a, k), 2) for k, _ in LABELS})
    print({k: [round(r["vdbfile"].get(k, 0) / 1e6, 1) for r in rows] for k, _ in LABELS})


if __name__ == "__main__":
    main()
