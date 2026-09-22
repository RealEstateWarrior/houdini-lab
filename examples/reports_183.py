# -*- coding: utf-8 -*-
"""実験183 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "183_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, tracks = d["rows"], d["tracks"]
    line_chart(os.path.join(OUT, "183_substeps.png"),
               [{"label": f"Bullet Substeps {s}", "points": [(i + 1, y) for i, y in enumerate(tracks[f'b0.5_s{s}']) if 10 <= i < 40], "color": PALETTE[k]}
                for k, s in enumerate((1, 10, 50))],
               title="rbdbulletsolver（Bounce 0.5）: 当たる前後の箱の底の y",
               x_label="フレーム", y_label="箱の底の y")
    by = {(r["bounce"], r["bullet_substeps"]): r for r in rows}
    s1, s10, s50 = by[(0.5, 1)], by[(0.5, 10)], by[(0.5, 50)]
    b1 = by[(1.0, 10)]
    payload = {
        "title": "rbdbulletsolver の沈み込みは Bullet Substeps で決まる — 1 だと 0.38 めり込んで沈んだまま、50 でほぼ 0",
        "summary":
            "実験167 の続き。1×1×1 の箱（底は y = 1.5 から）を Ground Plane に落とし、Bounce（箱と地面の両方）と Bullet Substeps（既定 10）を変えて、"
            "箱の底の y を毎フレーム読んだ。\n\n"
            f"**Bullet Substeps 1 では、当たった瞬間に {abs(s1['lowest']):.3f} めり込み、止まっても {abs(s1['bottom_rest']):.3f} 沈んだまま**だった。"
            f"既定の 10 で {abs(s10['lowest']):.4f}、50 で {abs(s50['lowest']):.6f}（止まった底は {s50['bottom_rest']:g}）。"
            "Substeps を減らして軽くすると、地面の中に沈んだ絵になる。\n\n"
            "**跳ね返りの高さは、Bounce から想像するよりずっと低い。**落とした高さ 1.5 に対して、Bounce 0・0.25・0.5・0.75 で "
            + "・".join(f"{by[(b, 10)]['rebound']:.4f}" for b in (0.0, 0.25, 0.5, 0.75))
            + "（1.5 × Bounce² なら 0・0.094・0.375・0.84）。ただしフレームごとに読んだ値なので、跳ね返りのいちばん高い所を逃している可能性がある。\n\n"
            f"**Bounce 1 だと、4 秒たっても跳ね続けた**（4 秒後の底が {b1['bottom_rest']:.2f}）。エネルギーがほとんど減らない。\n\n"
            f"**時間はどれも 97 フレームで 0.3〜0.6 秒。**Substeps 50 でも {s50['sec_97f']:.2f} 秒。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Bounce・Bullet Substeps と、沈み込み・跳ね返り",
            "images": [{"path": "183_substeps.png", "caption": "Substeps 1（青）だけが、当たったあと 0 より下に沈む。"}],
            "per_row": 1,
            "columns": ["Bounce", "Bullet Substeps", "いちばん深い所", "止まった底の y", "跳ね返りの高さ", "当たったフレーム", "97 フレームの秒"],
            "rows": [[f"{r['bounce']:g}", r["bullet_substeps"], f"{r['lowest']:.6f}", f"{r['bottom_rest']:.6f}", f"{r['rebound']:.4f}",
                      r["first_hit_frame"], f"{r['sec_97f']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>RBD が地面に沈むなら、まず Bullet Substeps。</strong>1 では 0.38 めり込み、そのまま 0.06 沈む。",
            "<strong>既定の 10 でも、当たった瞬間は 0.005 沈む。</strong>アップで見せるなら 50。時間はほぼ変わらない。",
            "<strong>Bounce 1 は止まらない。</strong>跳ね続けてほしくないなら 1 未満に。",
        ],
        "next": ["跳ね返りの高さを 1 フレームより細かく読む", "球（回らない形）での Bounce と跳ね返りの関係"],
    }
    with open(os.path.join(OUT, "183_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 183_report.json")


if __name__ == "__main__":
    main()
