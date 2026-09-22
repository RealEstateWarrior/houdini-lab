# -*- coding: utf-8 -*-
"""実験156 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "156_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, joints, r = d["rows"], d["joints"], d["radius"]
    for x in rows:
        x["want_area"] = x["want_side"] + x["want_caps"]
    line_chart(os.path.join(OUT, "156_wire.png"),
               [{"label": "側面＋蓋の面積 ÷ 円柱の 2πrL + 2πr²", "points": [(math.log2(x["div"]), x["area"] / (2 * math.pi * r * 2 + 2 * math.pi * r * r)) for x in rows], "color": PALETTE[0]},
                {"label": "体積 ÷ 円柱の πr²L", "points": [(math.log2(x["div"]), x["volume"] / (math.pi * r * r * 2)) for x in rows], "color": PALETTE[1]}],
               title="polywire（長さ 2・Wire Radius 0.1）: 円柱に対する比（横は log2 Divisions）",
               x_label="log2（Divisions）", y_label="円柱に対する比")
    wa = max(abs(x["area"] - x["want_area"]) for x in rows)
    wv = max(abs(x["volume"] - x["want_volume"]) for x in rows)
    on, off = joints[0], joints[1]
    payload = {
        "title": "polywire の管は Wire Radius に内接する正 n 角柱で両端に蓋 — 折れ目は Prevent Joint Buckling で r/cos(θ/2) に広がる",
        "summary":
            "長さ 2 のまっすぐな線と、90° に折れた線に polywire（Wire Radius r = 0.1）をかけ、点の位置・面積・体積を測った。\n\n"
            "**まっすぐな線では、管は半径 r の円に内接する正 n 角柱。**点はどれも軸からちょうど 0.1。"
            "面の数は Divisions + 2 で、両端に n 角形の蓋が付く（閉じた形）。"
            f"面積は 側面 L·2n·r·sin(π/n) ＋ 蓋 2·(n/2)r²·sin(2π/n)、体積は L·(n/2)r²·sin(2π/n) と、6通りとも合った（差は最大 {max(wa, wv):.0e}）。\n\n"
            "**折れ目では、Prevent Joint Buckling（既定で入）が輪を曲がりの面の中だけ広げる。**90° の折れ目の輪は、"
            f"曲がりの面の中で {on['inplane_max']:g}（= r/cos 45° = {on['want_inplane']:g}）、面に垂直な向きは {on['dist_min']:g} のまま。"
            "輪は2本の線の間の、ちょうど半分の角度の面に乗っている。管の太さが折れ目でも変わらないようにする仕組み。\n\n"
            f"**切ると、折れ目の輪は半径 r の円のまま（{off['inplane_max']:g}）。**曲がりの内側で管が細くくびれる。"
            f"面積は {on['area']:.6f} → {off['area']:.6f} に減った。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "まっすぐな線（長さ 2）",
             "images": [{"path": "156_wire.png", "caption": "内接多角形なので、どちらも 1 より下から近づく。"}],
             "per_row": 1,
             "columns": ["Divisions", "点", "面", "軸からの距離", "面積", "側面＋蓋の式", "体積", "式", "秒"],
             "rows": [[x["div"], x["points"], x["prims"], f"{x['rmin']:g}〜{x['rmax']:g}", f"{x['area']:.6f}", f"{x['want_area']:.6f}",
                       f"{x['volume']:.6f}", f"{x['want_volume']:.6f}", f"{x['sec']:.4f}"] for x in rows]},
            {"label": "90° の折れ目の輪（Divisions 16）",
             "columns": ["Prevent Joint Buckling", "輪の点", "折れ目からの距離（最小〜最大）", "曲がりの面の中の広がり", "r/cos 45°", "二等分面からのずれ", "全体の面積"],
             "rows": [["入" if j["jointcorrect"] else "切", j["ring_points"], f"{j['dist_min']:g}〜{j['dist_max']:g}", f"{j['inplane_max']:g}",
                       f"{j['want_inplane']:g}", f"{j['off_bisector']:g}", f"{j['area']:.6f}"] for j in joints]},
        ],
        "notes": [
            "<strong>polywire の管は内接多角形。</strong>Divisions 4 だと断面積は円の 64%。",
            "<strong>両端には蓋が付く。</strong>体積をそのまま measure で測れる。",
            "<strong>折れ目で細くなるなら、Prevent Joint Buckling が切れていないか。</strong>入れると r/cos(θ/2) に広がって太さを保つ。",
        ],
        "next": ["急な折れ目（150° など）で Max Joint Scale が効くところ", "Segments を増やしたときの点の数"],
    }
    with open(os.path.join(OUT, "156_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 156_report.json", wa, wv)


if __name__ == "__main__":
    main()
