# -*- coding: utf-8 -*-
"""実験179 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "179_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    fall, ws = d["rows"], d["windspeed"]
    with open(os.path.join(OUT, "166_stats.json"), encoding="utf-8") as fp:
        conv166 = json.load(fp)["convergence"]
    ref = {(c["k"], c["substeps"]): c["vy_2s"] for c in conv166}
    for r in fall:
        r["gap"] = (1 - r["vy_2s"] / r["sqrt_g_over_k"]) * 100
        r["popdrag"] = ref.get((r["k"], r["substeps"]))
    line_chart(os.path.join(OUT, "179_speed.png"),
               [{"label": "4 秒後の v.x", "points": [(x["windspeed"], x["vx_4s"]) for x in ws], "color": PALETTE[0]},
                {"label": "Wind Velocity × Wind Speed", "points": [(x["windspeed"], x["product"]) for x in ws], "color": PALETTE[4], "dash": True}],
               title="popwind（Wind Velocity 5・重力なし）: Wind Speed と、4 秒後の粒の速さ",
               x_label="Wind Speed", y_label="v.x")
    same166 = [r for r in fall if r["popdrag"] is not None]
    match = all(abs(r["vy_2s"] - r["popdrag"]) < 1e-5 for r in same166)
    wq = max(abs(x["vx_4s"] - x["quad_4s"]) for x in ws)
    k1s1 = [r for r in fall if r["k"] == 1.0 and r["substeps"] == 1][0]
    payload = {
        "title": "止まった空気の popwind と重力は、popdrag とぴったり同じ落ち方 — Substeps で差が出るのは重力と組み合わせたとき。Wind Speed は掛け算",
        "summary":
            "実験166・175 の続き。1 粒に popwind（風 0 = 止まった空気）と重力（−9.80665）をかけ、Air Resistance k = 1・4、Substeps 1・8 で 2 秒後の v.y を読んだ。"
            "また、重力なしで Wind Velocity (5, 0, 0) のまま Wind Speed を変え、4 秒後の v.x を読んだ。\n\n"
            f"**popwind（風 0）＋重力の落ち方は、実験166 の popdrag と6桁まで同じ**（{f'比べた {len(same166)} 通りすべて一致' if match else '違いがあった'}。"
            f"k = 1・Substeps 1 でどちらも {k1s1['vy_2s']:.6f}）。popdrag は、止まった空気に対する popwind と同じ抵抗とみられる。\n\n"
            "**Substeps で結果が変わるのは、重力と組み合わせたとき。**風だけ（実験175）なら Substeps 1 と 8 で同じだったが、重力を足すと "
            + "、".join(f"k = {k:g} で Substeps 1 → 8 が {' → '.join(f'{r['gap']:.1f}%' for r in fall if r['k'] == k)} 遅い" for k in (1.0, 4.0))
            + "（√(g/k) に対して）。抵抗は1ステップの中でぴったり解いても、重力と交互に足すところで誤差が出るとみられる。\n\n"
            f"**Wind Speed は Wind Velocity への掛け算。**Wind Speed 0.5・1・2 で、行き着く速さは 2.5・5・10 に向かい、4 秒後の v.x は "
            f"差の2乗の式（5·s − 5·s/(1 + 5·s·k·t)）と最大 {wq:.0e} の差で合った。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "止まった空気＋重力の落下（2 秒後）",
             "columns": ["Air Resistance k", "Substeps", "v.y（popwind）", "v.y（実験166 の popdrag）", "−√(g/k)", "足りない割合", "秒"],
             "rows": [[f"{r['k']:g}", r["substeps"], f"{r['vy_2s']:.6f}", f"{r['popdrag']:.6f}" if r["popdrag"] is not None else "—",
                       f"{r['sqrt_g_over_k']:.6f}", f"{r['gap']:.2f}%", f"{r['sec']:.3f}"] for r in fall]},
            {"label": "Wind Speed（重力なし・k = 1）",
             "images": [{"path": "179_speed.png", "caption": "4 秒後の速さは、点線（Wind Velocity × Wind Speed）の少し下。"}],
             "per_row": 1,
             "columns": ["Wind Speed", "4 秒後の v.x", "行き着く速さ（5 × Wind Speed）", "差の2乗の式"],
             "rows": [[f"{x['windspeed']:g}", f"{x['vx_4s']:.6f}", f"{x['product']:g}", f"{x['quad_4s']:.6f}"] for x in ws]},
        ],
        "notes": [
            "<strong>popdrag と popwind（風 0）は同じ抵抗。</strong>どちらを使っても落ち方は変わらない。",
            "<strong>重力と一緒に使うなら Substeps を上げる。</strong>Substeps 1 では終端速度が 6〜12% 遅い。",
            "<strong>Wind Speed は Wind Velocity の倍率。</strong>向きは Wind Velocity、強さの調整は Wind Speed で。",
        ],
        "next": ["粒の mass を変え、Ignore Mass を切ったとき", "popwind の Amplitude（乱れ）で速さがどれだけ揺れるか"],
    }
    with open(os.path.join(OUT, "179_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 179_report.json", match, wq)


if __name__ == "__main__":
    main()
