# -*- coding: utf-8 -*-
"""実験207 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def main():
    with open(os.path.join(OUT, "207_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["tag"]: r for r in d["rows"]}
    sim = {p["vox"]: p for p in d["parts"]}
    # 図: 3 枚を並べる（炎のまわりを切り出す）
    font = _font(17)
    pics = [("v03_s0.25", "Voxel 0.03・Step Rate 0.25（既定）"), ("v03_s1.0", "Voxel 0.03・Step Rate 1"),
            ("v06_s0.25", "Voxel 0.06・Step Rate 0.25")]
    ims = [Image.open(os.path.join(OUT, f"207_{k}.png")).convert("RGB").crop((220, 90, 740, 540)) for k, _ in pics]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * 3, h + 30), (20, 20, 22))
    dr = ImageDraw.Draw(sheet)
    for i, (im, (k, lab)) in enumerate(zip(ims, pics)):
        sheet.paste(im, (i * w, 30))
        dr.text((i * w + 8, 5), f"{lab}（{t[k]['sec']:.1f} 秒）", fill=(235, 235, 235), font=font)
    sheet.save(os.path.join(OUT, "207_compare.png"))
    table = []
    for k, r in t.items():
        res = r.get("res", "960x540")
        name = "炎を外す" if "nofire" in k else f"Voxel {r['vox']}・Step Rate {r['step']}"
        diff = r.get("diff_fire", r.get("diff_fire_vs_big_s0.125"))
        table.append([name, res.replace("x", "×"), f"{r['sec']:.1f}", "—" if diff is None or "nofire" in k else f"{diff:.2f}"])
    s = lambda k: t[k]["sec"]  # noqa: E731
    payload = {
        "title": f"焚き火を Karma で撮るとき、Volume Step Rate を粗くしても速くならない — 1920×1080 では 1 が {s('v03_big_s1.0'):.0f} 秒、0.125 が {s('v03_big_s0.125'):.0f} 秒。Pyro を粗くしても撮る時間は同じで、炎の形だけ変わる",
        "summary":
            "**課題: 焚き火を何百フレームも撮るなら、1 枚を短くしたい。Karma の Volume Step Rate（ボリュームの中を進む歩幅の細かさ。既定 0.25）を粗くすると、どれだけ速くなり、見た目はどれだけ変わるか。Pyro を粗い升で回した炎は、撮っても見劣りしないか。**\n\n"
            "実践「焚き火を燃やす」のシーン（Voxel Size 0.03）を開き、フレーム 60 まで燃やして、960×540・16 サンプル＋ノイズ除去（実験205 で決めた撮り方）で撮った。"
            "Volume Step Rate を 1・0.5・0.25・0.125、Voxel Size を 0.03 と 0.06（升の数が約 8 分の 1）にした。"
            "見た目の差は、Voxel 0.03・Step Rate 0.125 の画との差（画素の値 0〜255 の差の平均）を、炎のまわりで測った。\n\n"
            f"**Step Rate を粗くしても、速くならない。**960×540 で 1・0.5・0.25・0.125 は {s('v03_s1.0'):.1f}・{s('v03_s0.5'):.1f}・{s('v03_s0.25'):.1f}・{s('v03_s0.125'):.1f} 秒。"
            f"1920×1080 にすると、1 が {s('v03_big_s1.0'):.1f} 秒、0.125 が {s('v03_big_s0.125'):.1f} 秒で、粗い方が {s('v03_big_s1.0') / s('v03_big_s0.125') - 1:.0%} 遅かった。"
            "粗く進むとざらつきが増え、ざらつきを見てサンプルを足す決め方（実験205）が長く回るためと考えられるが、画素ごとのサンプル数は確かめていない。\n\n"
            f"**見た目の差も小さい。**炎のまわりの差は、Step Rate 1 で {t['v03_s1.0']['diff_fire']:.2f}、0.5 で {t['v03_s0.5']['diff_fire']:.2f}、0.25 で {t['v03_s0.25']['diff_fire']:.2f}（0〜255 のうち）。並べても見分けられない。\n\n"
            f"**炎は 1 枚の時間の約 6 割。**炎を外して撮ると {s('v03_nofire'):.1f} 秒（炎ありは {s('v03_s0.25'):.1f} 秒）。\n\n"
            f"**Pyro の升を粗くしても、撮る時間は変わらない。**Voxel Size 0.06（升 {sim[0.06]['res'][0]}×{sim[0.06]['res'][1]}×{sim[0.06]['res'][2]}）は 0.03（{sim[0.03]['res'][0]}×{sim[0.03]['res'][1]}×{sim[0.03]['res'][2]}）と同じく {s('v06_s0.25'):.1f} 秒。"
            f"60 フレームの計算は {sim[0.03]['sim_sec']:.1f} 秒 → {sim[0.06]['sim_sec']:.1f} 秒と短くなるが、炎の形そのものが変わり、炎のまわりの差は {t['v06_s0.25']['diff_fire']:.1f} になった（ぼけた柔らかい炎になる）。\n\n"
            "**決め方: Volume Step Rate は既定の 0.25 のまま。**撮る時間を縮めたいなら、サンプル数とノイズ除去（実験205）や画の大きさで決める。Voxel Size は、撮る時間ではなく炎の形で決める。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "炎のまわり（960×540・16 サンプル＋ノイズ除去）",
             "images": [{"path": "207_compare.png", "caption": "左と中（Step Rate 0.25 と 1）は見分けられない。右（Voxel 0.06）は炎の形が変わる。"}],
             "per_row": 1, "columns": ["条件", "画の大きさ", "秒", "炎のまわりの差（0〜255）"], "rows": table},
        ],
        "notes": [
            f"<strong>Volume Step Rate は既定の 0.25 のままでよい。</strong>1 に粗くしても速くならず、1920×1080 ではかえって {s('v03_big_s1.0') / s('v03_big_s0.125') - 1:.0%} 遅かった。",
            f"<strong>焚き火の炎は、1 枚の時間の約 6 割。</strong>炎を外すと {s('v03_s0.25'):.1f} 秒 → {s('v03_nofire'):.1f} 秒。",
            "<strong>Pyro の Voxel Size は撮る時間に効かない。</strong>形で決める。0.06 にすると炎がぼけて柔らかくなった。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "207_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 207_report.json")
    print(payload["title"])


if __name__ == "__main__":
    main()
