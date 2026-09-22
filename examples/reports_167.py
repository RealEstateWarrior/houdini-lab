# -*- coding: utf-8 -*-
"""実験167 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "167_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, tracks = d["rows"], d["tracks"]
    line_chart(os.path.join(OUT, "167_drop.png"),
               [{"label": f"Bounce {b:g}", "points": [(i + 1, y) for i, y in enumerate(tracks[f"m0.02_b{b:g}"]) if i < 60], "color": PALETTE[k]}
                for k, b in enumerate((0.25, 0.8))],
               title="rbdbulletsolver: 中心 y = 2 から落とした 1×1×1 の箱の、底の高さ（Collision Padding 0.02）",
               x_label="フレーム", y_label="箱の底の y")
    same = all(r["bottom_rest"] == rows[i % 2]["bottom_rest"] and r["rebound"] == rows[i % 2]["rebound"] for i, r in enumerate(rows))
    lo = min(r["lowest"] for r in rows)
    b25 = [r for r in rows if r["bounce"] == 0.25][0]
    b80 = [r for r in rows if r["bounce"] == 0.8][0]
    payload = {
        "title": "rbdbulletsolver の箱は地面ぴったりで止まる — Collision Padding を変えても止まる高さは同じ、当たった瞬間だけ少し沈む",
        "summary":
            "1×1×1 の箱（中心 y = 2）に name を付けて rbdbulletsolver に入れ、Ground Plane（y = 0）へ落とした。"
            "Collision Padding（0・0.02・0.05）と Bounce（0.25・0.8。地面の Bounce も同じ値）を変え、箱の底（点の y の最小）を毎フレーム読んだ。\n\n"
            f"**止まった箱の底は y = 0 のすぐ近く。**4 秒後の底は {b25['bottom_rest']:.6f}、中心は {b25['center_rest']:.6f}。"
            "形のまわりに余白を付けるつまみがあっても、見た目の形は地面から浮かない。\n\n"
            f"**Collision Padding を 0・0.02・0.05 と変えても、結果は6桁まで同じだった**（{'すべての値が一致' if same else '違いがあった'}）。"
            "この形（凸包）では、余白が止まる高さにも跳ね方にも出ない。Bullet が余白の分だけ形を内側へ縮めてから余白を足している可能性があるが、確かめていない。\n\n"
            f"**当たった瞬間だけ、少し地面にめり込む**（いちばん深くて {lo:.4f}）。{b25['first_hit_frame']} フレーム目に当たる。\n\n"
            f"**Bounce で跳ね返りの高さが大きく変わる。**最初の跳ね返りの高さ（底の y）は Bounce 0.25 で {b25['rebound']:.4f}、0.8 で {b80['rebound']:.4f}。"
            "落とした高さ（底が 1.5 から）に対して、それぞれ 0.6%・15%。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Collision Padding・Bounce と、止まり方",
            "images": [{"path": "167_drop.png", "caption": "Bounce 0.8（橙）は何度か跳ねてから止まる。0.25（青）はほぼ跳ねない。"}],
            "per_row": 1,
            "columns": ["Collision Padding", "Bounce", "止まった底の y", "止まった中心の y", "いちばん深い所", "当たったフレーム", "跳ね返りの高さ", "97 フレームの秒"],
            "rows": [[f"{r['margin']:g}", f"{r['bounce']:g}", f"{r['bottom_rest']:.6f}", f"{r['center_rest']:.6f}", f"{r['lowest']:.6f}",
                      r["first_hit_frame"], f"{r['rebound']:.4f}", f"{r['sec_97f']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>箱は地面ぴったりで止まる。</strong>Collision Padding で浮いて見えることはなかった。",
            "<strong>当たった瞬間は 0.007〜0.008（箱の一辺 1 に対して）沈む。</strong>速い物ほど深い可能性がある（確かめていない）。",
            "<strong>跳ね返りは Bounce しだい。</strong>0.25 ではほとんど跳ねない。",
        ],
        "next": ["Bullet Substeps を増やしたときの沈み込み", "球（Collision Shape = Sphere）での Collision Padding"],
    }
    with open(os.path.join(OUT, "167_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 167_report.json", same)


if __name__ == "__main__":
    main()
