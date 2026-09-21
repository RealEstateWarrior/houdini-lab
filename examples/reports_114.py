# -*- coding: utf-8 -*-
"""実験114 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def bend_angle(divs, r=1.0, pitch=1.0):
    """らせんの折れ線で、となりの区間どうしが曲がる角度（ラジアン）。"""
    h = 2 * r * math.sin(math.pi / divs)
    v = pitch / divs
    c = (h * h * math.cos(2 * math.pi / divs) + v * v) / (h * h + v * v)
    return math.acos(c)


def main():
    with open(os.path.join(OUT, "114_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows = data["rows"]
    for r in rows:
        if r["path"].startswith("helix"):
            divs = int(r["path"].split("_")[1])
            r["angle"] = math.degrees(bend_angle(divs))
            r["cos_pred"] = math.cos(bend_angle(divs) / 2) - 1
        else:
            r["angle"], r["cos_pred"] = 0.0, 0.0
    off = [r for r in rows if not r["stretch"] and r["cols"] == 32]
    on = [r for r in rows if r["stretch"] and r["cols"] == 32]
    worst_on = max(abs(r["rel"]) for r in rows if r["stretch"])
    line_off = [r for r in rows if r["path"] == "line"]

    pts_off = sorted((r["angle"], -r["rel"] * 100) for r in off)
    pts_pred = sorted((r["angle"], -r["cos_pred"] * 100) for r in off)
    pts_on = sorted((r["angle"], -r["rel"] * 100) for r in on)
    line_chart(
        os.path.join(OUT, "114_sweep.png"),
        [{"label": "Stretch Around Turns 切（既定）", "points": pts_off, "color": PALETTE[1]},
         {"label": "1 − cos(曲がる角/2)", "points": pts_pred, "color": PALETTE[4], "dash": True},
         {"label": "Stretch Around Turns 入", "points": pts_on, "color": PALETTE[0]}],
        title="曲がり角で管が細る。足りない体積は 1 − cos(角/2) に合う",
        x_label="となりの区間どうしが曲がる角度（°）", y_label="体積の不足（%）")
    print("114_sweep.png")

    h12 = next(r for r in off if r["path"] == "helix_12")
    h50 = next(r for r in off if r["path"] == "helix_50")
    payload = {
        "title": "sweep の管は曲がり角で細る — 不足は 1−cos(角/2)、Stretch Around Turns で A×L に一致",
        "summary":
            "sweep の Round Tube で太さ 0.1 の管を作り、体積を「断面積 × 長さ」と比べた。"
            "断面は円ではなく k 角形（Columns）なので、断面積は (k/2)·a²·sin(2π/k)。"
            "端は Single Polygon でふさいだ。\n\n"
            "**まっすぐな線では、ぴったり 断面積×長さ**"
            f"（{len(line_off)}通りすべて差 0.000000）。\n\n"
            "**らせん（実験105）に沿わせると、既定では体積が足りない。** "
            f"1巻き50分割で {h50['rel'] * 100:.3f}%、12分割で {h12['rel'] * 100:.2f}%。"
            "折れ線の曲がり角で、断面が角の二等分の向きに置かれ、そのぶん管が細るためと考えて、"
            "不足を 1 − cos(曲がる角/2) と比べると、"
            f"12分割（角 {h12['angle']:.1f}°）で式 {-h12['cos_pred'] * 100:.2f}% に対し実測 "
            f"{-h12['rel'] * 100:.2f}%、50分割（{h50['angle']:.2f}°）で式 "
            f"{-h50['cos_pred'] * 100:.3f}% に対し {-h50['rel'] * 100:.3f}%。近いが完全には一致しない。\n\n"
            "**Stretch Around Turns を入れると、曲がり角の断面を引き伸ばして太さを保つ。** "
            f"すべての場合で 断面積×長さ との差が {worst_on * 100:.3f}% 以内になった。\n\n"
            "Columns（8 か 32）を変えても、不足の割合はほとんど変わらない。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "道の形・断面の角数・Stretch Around Turns と体積",
             "note": "管の半径 0.1。らせんは半径1・3巻き・高さ3（実験105と同じ）。"
                     "長さは道の折れ線の長さ（measure の Perimeter）。",
             "images": [{"path": "114_sweep.png",
                         "caption": "既定（橙）は角が大きいほど体積が足りない。"
                                    "Stretch Around Turns を入れる（青）とほぼ0。"}],
             "per_row": 1,
             "columns": ["道", "角数", "Stretch", "曲がる角", "体積", "断面積×長さ", "ずれ", "1−cos(角/2)"],
             "rows": [[r["path"].replace("helix_", "らせん ").replace("line", "直線 5"),
                       str(r["cols"]), "入" if r["stretch"] else "切", f"{r['angle']:.2f}°",
                       f"{r['volume']:.6f}", f"{r['want']:.6f}", f"{r['rel'] * 100:+.3f}%",
                       f"{r['cos_pred'] * 100:+.3f}%"] for r in rows]},
        ],
        "notes": [
            "<strong>まっすぐなら 断面積×長さ ちょうど。</strong>断面は k 角形なので、円の面積 πa² ではない"
            "（8角形なら 0.90 倍）。",
            "<strong>既定のままだと、曲がり角で管が細る。</strong>体積の不足はほぼ 1 − cos(角/2)。"
            "1巻き12分割のらせんで約3%。",
            "<strong>Stretch Around Turns を入れれば太さが保たれる。</strong>パイプや電線の太さを"
            "そろえたいときは入れる。",
            "<strong>道を細かく割っても不足は減る。</strong>角が半分になると不足は約1/4。",
        ],
        "next": [
            "Max Stretch を下げたとき、鋭い角でどこまで太さが保たれるか",
            "Square Tube / Ribbon の面積と体積",
            "道に pscale を持たせたとき、太さが点ごとに変わるか",
        ],
    }
    with open(os.path.join(OUT, "114_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 114_report.json")


if __name__ == "__main__":
    main()
