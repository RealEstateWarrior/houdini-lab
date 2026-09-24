# -*- coding: utf-8 -*-
"""実験232 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"ocean_winter": "冬の朝の七里ヶ浜", "campfire": "焚き火", "glasscup": "氷の入ったグラスの水", "snowman": "雪だるま",
       "donut": "ドーナツ", "neon": "ネオン管"}


def main():
    with open(os.path.join(OUT, "232_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(15)
    w, h = 400, 225
    order = ["donut", "glasscup", "ocean_winter", "snowman", "campfire", "neon"]
    sheet = Image.new("RGB", (w * 2, (h + 24) * len(order) + 24), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 4), "CPU", fill=(30, 30, 30), font=font)
    dr.text((w + 8, 4), "XPU", fill=(30, 30, 30), font=font)
    for i, g in enumerate(order):
        y = 24 + i * (h + 24)
        r = t[g]
        dr.text((8, y + 3), f"{LAB[g]}  CPU {r['cpu_sec']:.1f} 秒 / XPU {r['xpu_sec']:.1f} 秒・差 {r['diff']:.0f}", fill=(30, 30, 30), font=font)
        for j, eng in enumerate(("cpu", "xpu")):
            sheet.paste(Image.open(os.path.join(OUT, f"232_{g}_{eng}.png")).convert("RGB").resize((w, h)), (j * w, y + 24))
    sheet.save(os.path.join(OUT, "232_grid.png"))
    table = [[LAB[g], f"{t[g]['cpu_sec']:.1f}", f"{t[g]['xpu_sec']:.1f}", f"{t[g]['cpu_sec'] / t[g]['xpu_sec']:.1f}", f"{t[g]['diff']:.1f}",
              f"{t[g]['cpu_mean']:.0f} → {t[g]['xpu_mean']:.0f}"] for g in order]
    s = lambda g, f: t[g][f]  # noqa: E731
    payload = {
        "title": f"Karma XPU は、ガラス・雪・ドーナツで CPU の {min(s(g, 'cpu_sec') / s(g, 'xpu_sec') for g in ('glasscup', 'snowman', 'donut')):.0f}〜{max(s(g, 'cpu_sec') / s(g, 'xpu_sec') for g in ('glasscup', 'snowman', 'donut')):.0f} 倍速い（グラスの水 {s('glasscup', 'cpu_sec'):.0f} 秒 → {s('glasscup', 'xpu_sec'):.0f} 秒）。"
                 "ただしドーナツのアイシングと海の空は色が出ずに白くなり、ガラスの場面は明るく飛んだ。雪と炎はほぼ同じ絵",
        "summary":
            "**課題: 実践「夕暮れの海」では、XPU（GPU で撮る Karma）は速かったが、点の色で光らせた空が白く飛んだ。どの場面なら XPU に任せてよいのか。どれだけ速いのか。**\n\n"
            "実践 6 本の hip を読み、仕上がりを撮る Karma の Rendering Engine だけを CPU・XPU に切り替えて、640×360・32 サンプル・ノイズ除去なしで撮った。"
            "場面ごとに別の hython で、CPU・XPU それぞれはじめに 1 枚撮って捨て（XPU は GPU の準備の分）、2 枚目の時間を測った。"
            "画の違いは、CPU の画との画素ごとの差の平均（0〜255。右下の透かしは除く）。GPU は GeForce RTX 4070。\n\n"
            f"**速さ: 多くの場面で数倍〜十数倍。**グラスの水 {s('glasscup', 'cpu_sec'):.1f} → {s('glasscup', 'xpu_sec'):.1f} 秒、"
            f"雪だるま {s('snowman', 'cpu_sec'):.1f} → {s('snowman', 'xpu_sec'):.1f} 秒、ドーナツ {s('donut', 'cpu_sec'):.1f} → {s('donut', 'xpu_sec'):.1f} 秒、"
            f"ネオン管 {s('neon', 'cpu_sec'):.1f} → {s('neon', 'xpu_sec'):.1f} 秒、焚き火 {s('campfire', 'cpu_sec'):.1f} → {s('campfire', 'xpu_sec'):.1f} 秒。"
            f"冬の海だけは {s('ocean_winter', 'cpu_sec'):.1f} → {s('ocean_winter', 'xpu_sec'):.1f} 秒で速くならなかった。\n\n"
            f"**材質の色が出ずに白くなる所があった。**ドーナツのアイシング（principledshader の色がピンク、Coat 0.5）は、CPU ではピンク、XPU では白だった（差 {s('donut', 'diff'):.0f}）。"
            "Coat を 0 にしても XPU では白いままだった。点の色で揚げ色を付けた生地は、XPU でも揚げ色だった。"
            f"冬の海の空（点の色で光らせた空の球）も、XPU では真っ白に飛んだ（差 {s('ocean_winter', 'diff'):.0f}、"
            f"画の明るさの平均 {s('ocean_winter', 'cpu_mean'):.0f} → {s('ocean_winter', 'xpu_mean'):.0f}）。どちらも原因は確かめていない。\n\n"
            f"**ガラスの場面は、全体が明るく飛んだ。**グラスの水は背景の幕が白く飛び、ガラスの輪郭が見えにくくなった（差 {s('glasscup', 'diff'):.0f}、明るさ {s('glasscup', 'cpu_mean'):.0f} → {s('glasscup', 'xpu_mean'):.0f}）。"
            "原因は確かめていない。\n\n"
            f"**雪（SSS）と炎（Pyro）は、ほぼ同じ絵。**差は雪だるま {s('snowman', 'diff'):.0f}、焚き火 {s('campfire', 'diff'):.0f}、ネオン管 {s('neon', 'diff'):.0f}。"
            "どれも XPU の方が少し明るかった。\n\n"
            "**決め方: 試し撮りは XPU で速く回し、仕上げの前に必ず CPU の画と並べて確かめる。**色が変わる所（この実験ではアイシング・光る空）があれば、その場面は CPU で撮る。\n\n"
            "**追記（実験242・243）: 色が白くなった原因が分かった。**XPU では、形に点の色 Cd があると、principledshader の色が Cd に置き換わる"
            "（Use Point Color を切っていても）。ドーナツは揚げ色の Cd を持つ生地とアイシングを 1 つの形にまとめていたので、アイシングにも白の Cd が付いて白くなった。"
            "MaterialX の材質（mtlxstandard_surface）なら、Cd があっても CPU と同じ色になった。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "CPU と XPU（640×360・32 サンプル、ノイズ除去なし）",
             "images": [{"path": "232_grid.png", "caption": "左が CPU、右が XPU。ドーナツのアイシングと海の空は色が出ずに白くなり、グラスは明るく飛んだ。"}],
             "per_row": 1, "columns": ["場面", "CPU（秒）", "XPU（秒）", "速さの比", "画の差（0〜255）", "明るさの平均 CPU → XPU"], "rows": table},
        ],
        "notes": [
            f"<strong>XPU は多くの場面で CPU の数倍〜十数倍速い。</strong>グラスの水 {s('glasscup', 'cpu_sec'):.0f} → {s('glasscup', 'xpu_sec'):.0f} 秒。",
            "<strong>ドーナツのアイシングと海の空は、XPU では色が出ずに白くなった。</strong>原因は確かめていない。",
            "<strong>ガラスの場面は明るく飛んだ。雪（SSS）と炎（Pyro）はほぼ同じ絵。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "232_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
