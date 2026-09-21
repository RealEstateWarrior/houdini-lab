# -*- coding: utf-8 -*-
"""実験133 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "133_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows = d["point"]
    proj = [r for r in rows if r["method"] == "project"]
    mini = [r for r in rows if r["method"] == "minimum"]
    line_chart(os.path.join(OUT, "133_ray.png"),
               [{"label": "Project（真下へ）: 式とのずれの最大", "points": [(r["res"], r["err_max"]) for r in proj],
                 "color": PALETTE[0]},
                {"label": "Minimum Distance: 放射状の点とのずれの最大", "points": [(r["res"], r["err_max"]) for r in mini],
                 "color": PALETTE[1]}],
               title="球を細かくすると、落とした点は式の位置に近づく",
               x_label="球の段数", y_label="ずれ（最大）")
    print("133_ray.png")
    p96, m96 = proj[-1], mini[-1]
    payload = {
        "title": "ray の Direction には最初から @N の式が入っている — Python で set しても変わらず、真下に落ちなかった",
        "summary":
            "半径1の球の上に格子（31×31点、高さ2）を置き、ray で球に落とした。"
            "真下へ落とせば、当たった点は y = √(1 − x² − z²) に来るはず。\n\n"
            "**最初は1点も動かなかった。** 調べると、ray の Direction（dirx・diry・dirz）には最初から "
            f"{', '.join(d['dir_expressions'])} という式が入っていた。Python で "
            "parmTuple(\"dir\").set((0, −1, 0)) としても、式が残ったままで値は "
            f"{tuple(d['dir_after_plain_set'])} のまま。格子には法線が無いので、光線は格子の向き（上）へ飛び、"
            "下の球には当たらなかった。**式を消してから（deleteAllKeyframes）入れると、正しく真下へ落ちた。** "
            "（画面で値を打ち込んだときに式が置き換わるかは、確かめていない。"
            "格子を球の下に置くと、同じ設定のまま下の面に当たったので、光線が上へ飛んでいたことは確か）\n\n"
            f"**真下へ落とした点は、式の位置と一致した**（段数96でずれ最大 {p96['err_max']:.4f}、平均 {p96['err_mean']:.5f}）。"
            "ずれは球が多角形である分で、段数24では最大 "
            f"{proj[0]['err_max']:.4f}。球の外側を通る光線の点（{p96['missed_stayed']} 点）は、元の高さのまま残った。\n\n"
            "**Minimum Distance は、いちばん近い面の上へ動かす。** 中心から放射状に落とした位置とのずれは、"
            f"段数96で最大 {m96['err_max']:.4f}。多角形の平らな面の上では「いちばん近い点」と「放射状の点」が"
            "少し違うため、Project より大きい。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "落とし方と、式とのずれ",
             "note": "Project の式は y = √(1 − x² − z²)。Minimum Distance は 点 ÷ 中心からの距離（放射状）と比べた。"
                     "当たった点の中心からの距離も出した（1 なら球の上）。",
             "images": [{"path": "133_ray.png", "caption": "どちらも、球を細かくするとずれが減る。"}],
             "per_row": 1,
             "columns": ["球の段数", "落とし方", "当たった点", "外れて残った点", "ずれの最大", "ずれの平均",
                         "中心からの距離（最小）"],
             "rows": [[str(r["res"]), "Project（真下）" if r["method"] == "project" else "Minimum Distance",
                       str(r["hits"]), str(r["missed_stayed"]), f"{r['err_max']:.6f}", f"{r['err_mean']:.6f}",
                       f"{r['r_min']:.6f}"] for r in rows]},
        ],
        "notes": [
            "<strong>ray の Direction は、最初は @N の式。</strong>スクリプトで向きを入れるときは、"
            "先に deleteAllKeyframes() で式を消す。",
            "<strong>法線の無い形から飛ばすと、面の向き（格子なら上）へ飛ぶ。</strong>落としたい向きを必ず決める。",
            "<strong>外れた点は動かない。</strong>外れた点を消したいときは、別に選んで消す。",
        ],
        "next": [
            "Scale と Lift で、当たった位置から少し戻す・浮かせるときの距離",
            "ほかにも「最初から式が入っている」つまみがどれだけあるか（node_dump で数える）",
        ],
    }
    with open(os.path.join(OUT, "133_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 133_report.json")


if __name__ == "__main__":
    main()
