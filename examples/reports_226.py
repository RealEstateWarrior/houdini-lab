# -*- coding: utf-8 -*-
"""実験226 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"r8": "ひび 8 本", "r20": "ひび 20 本（既定）", "r40": "ひび 40 本", "r80": "ひび 80 本", "r20_smooth": "20 本・縁なめらか",
       "r80_smooth": "80 本・縁なめらか", "r80_g06": "80 本・強さ 0.6", "r80_g05": "80 本・強さ 0.5", "r80_g04": "80 本・強さ 0.4",
       "r80_g02": "80 本・強さ 0.2", "r80_g01": "80 本・強さ 0.1"}


def main():
    with open(os.path.join(OUT, "226_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(15)
    shots = ["r20", "r80", "r80_smooth", "r80_g06", "r80_g04", "r80_g01"]
    sheet = Image.new("RGB", (400 * 3, (400 + 26) * 2), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(shots):
        x, y = (i % 3) * 400, (i // 3) * 426
        im = Image.open(os.path.join(OUT, f"226_{k}.png")).convert("RGBA").resize((400, 400))
        bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (x, y + 26))
        r = t[k]
        dr.text((x + 6, y + 4), f"{LAB[k]}・強さ {r['glue']:g}  動いた {r['moved']}/{r['pieces']}", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "226_grid.png"))
    table = [[LAB[k], str(r["radial_cracks"]), "入り" if r["edge_noise"] else "切り", f"{r['glue']:g}", str(r["pieces"]), f"{r['polys']:,}",
              f"{r['fracture_sec']:.2f}", f"{r['sim_sec']:.2f}", f"{r['moved']}（{r['moved'] / r['pieces'] * 100:.0f}%）"] for k, r in t.items()]
    g = lambda k, f: t[k][f]  # noqa: E731
    pct = lambda k: g(k, "moved") / g(k, "pieces") * 100  # noqa: E731
    with open(os.path.join(OUT, "226_runs.json"), encoding="utf-8") as fp:
        runs = json.load(fp)["runs"]
    fmt = lambda v: "・".join(map(str, v))  # noqa: E731
    payload = {
        "title": f"ガラスのひびを増やすと、同じつながりの強さでは割れにくくなる（20 本で破片の {pct('r20'):.0f}% が動いたのが、80 本では {pct('r80'):.0f}%）。"
                 f"80 本なら強さを 0.6 前後に下げる。ただし弱めた条件は、流すたびに割れ方が大きく揺れた（0.6 で 54〜116 個）。計算はどれも 3 秒以内",
        "summary":
            "**課題: 窓ガラスを割る場面で、破片をもっと細かくしたい。rbdmaterialfracture（Glass）の Radial Crack Number（放射状のひびの数、既定 20）を上げると、"
            "計算の時間はどれだけ増えるか。見た目はどう変わるか。**\n\n"
            "実践「窓ガラスを割る」と同じ場面（1 × 1.4 m・厚さ 8 mm の板に、半径 6 cm の球を秒速 14 m で当てる。枠に触れる破片は止め、破片どうしのつながりの強さ 0.8）を"
            "48 フレーム回した。ひびを 8・20・40・80 本にし、Enable Edge Noise（破片の縁のでこぼこ）を切ったものも比べた。48 フレーム目までに 5 cm 以上動いた破片を数えた。\n\n"
            f"**計算の時間は、どれも小さい。**ひび 8・20・40・80 本で、破片は {g('r8', 'pieces')}・{g('r20', 'pieces')}・{g('r40', 'pieces')}・{g('r80', 'pieces')} 個、"
            f"割る計算は {g('r8', 'fracture_sec'):.2f}・{g('r20', 'fracture_sec'):.2f}・{g('r40', 'fracture_sec'):.2f}・{g('r80', 'fracture_sec'):.2f} 秒"
            "（8 本は 1 回目の作成の分を含む）、"
            f"Bullet の 48 フレームは {g('r8', 'sim_sec'):.2f}・{g('r20', 'sim_sec'):.2f}・{g('r40', 'sim_sec'):.2f}・{g('r80', 'sim_sec'):.2f} 秒。"
            f"縁のでこぼこを切ると、面の数が {g('r20', 'polys'):,} → {g('r20_smooth', 'polys'):,}（20 本）に減り、割る計算は {g('r20', 'fracture_sec'):.2f} → {g('r20_smooth', 'fracture_sec'):.2f} 秒になった。\n\n"
            f"**ひびを増やすと、割れにくくなる。**同じ強さ 0.8 で、動いた破片は 20 本で {g('r20', 'moved')} / {g('r20', 'pieces')} 個（{pct('r20'):.0f}%）、"
            f"80 本で {g('r80', 'moved')} / {g('r80', 'pieces')} 個（{pct('r80'):.0f}%）。画でも、80 本は球が小さな穴を開けただけだった。"
            f"縁をなめらかにした 80 本は {g('r80_smooth', 'moved')} 個しか動かず、ほとんど割れなかった。"
            "破片が増えると、破片どうしのつながりの数も増えて、全体として割れにくくなると考えられる。\n\n"
            f"**80 本なら、つながりの強さを下げる。**強さ 0.6・0.5・0.4・0.2・0.1 で、動いた破片は {pct('r80_g06'):.0f}・{pct('r80_g05'):.0f}・{pct('r80_g04'):.0f}・"
            f"{pct('r80_g02'):.0f}・{pct('r80_g01'):.0f}%（1 回目の記録）。0.6 で 20 本・0.8 と同じくらい（{pct('r80_g06'):.0f}% と {pct('r20'):.0f}%）割れ、穴の縁の破片がずっと細かくなった。"
            "0.1 では、ガラスの大半が崩れ落ちた。\n\n"
            f"**弱めた条件は、流すたびに割れ方が揺れる。**同じ設定のまま 5 回流すと、動いた破片の数は、強さ 0.8 の条件では毎回ほぼ同じ"
            f"（20 本: {fmt(runs['r20'])}、80 本: {fmt(runs['r80'])}）だったが、弱めた条件は大きく揺れた"
            f"（0.6: {fmt(runs['r80_g06'])}、0.5: {fmt(runs['r80_g05'])}、0.4: {fmt(runs['r80_g04'])}）。"
            "割れるか割れないかの境目の強さでは、Bullet の計算のわずかな違いで、つながりが切れる破片の数が変わると考えられる。"
            "点検（実験240）で流し直したとき、0.6 の条件が記録の 88 個に対して 54 個になって気づいた。"
            "実験246 で、1 スレッド（HOUDINI_MAXTHREADS=1）で回すと 5 回とも同じ割れ方になることを確かめた（ただし約 3 倍遅い）。\n\n"
            "**決め方: ひびを増やしたら、つながりの強さを下げる（20 → 80 本で 0.6 前後）。**境目の強さでは割れ方が回ごとに変わるので、"
            "何度か回して見た目で選び、決めたらキャッシュに書き出して固定する。計算の時間は気にしなくてよい。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "ひびの数とつながりの強さ（48 フレーム目）",
             "images": [{"path": "226_grid.png", "caption": "上: 20 本・80 本・80 本縁なめらか（強さ 0.8）。下: 80 本で強さ 0.6・0.4・0.1。"}],
             "per_row": 1, "columns": ["条件", "ひび", "縁のでこぼこ", "つながりの強さ", "破片", "面の数", "割る計算（秒）", "Bullet（秒）", "動いた破片"],
             "rows": table},
        ],
        "notes": [
            f"<strong>ひびを増やすと、同じつながりの強さでは割れにくくなる。</strong>20 本 {pct('r20'):.0f}% → 80 本 {pct('r80'):.0f}% の破片が動いた。",
            "<strong>80 本なら強さ 0.6 前後で、20 本・0.8 と同じくらい割れる。</strong>",
            f"<strong>弱めた条件は、流すたびに割れ方が揺れる（0.6 で {min(runs['r80_g06'])}〜{max(runs['r80_g06'])} 個）。</strong>決めたらキャッシュで固定する。",
            "<strong>計算の時間はどれも 3 秒以内。</strong>縁のでこぼこを切ると面の数と割る時間が減る。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "226_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
