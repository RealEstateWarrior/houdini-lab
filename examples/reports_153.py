# -*- coding: utf-8 -*-
"""実験153 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "153_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    keys = sorted({int(k) for r in rows for k in r["hist"]})
    line_chart(os.path.join(OUT, "153_hist.png"),
               [{"label": r["shape"], "points": [(k, r["hist"].get(str(k), 0)) for k in keys if k <= 6], "color": PALETTE[i % 5],
                 "dash": i >= 5} for i, r in enumerate(rows)],
               title="neighbourcount() の分布（隣の点が 2〜6 個の点の数。球の極 16 個は表に）",
               x_label="隣の点の数", y_label="点の数")
    ok_e = all(r["E_from_nb"] == r["E_from_prims"] for r in rows)
    ok_x = all(r["euler"] == r["want"] for r in rows)
    first = rows[0]["sec"]
    rest = max(r["sec"] for r in rows[1:])
    payload = {
        "title": "neighbourcount() の合計の半分は辺の数 — そこから出した V − E + F は、板 1・球と箱 2・トーラスと筒 0",
        "summary":
            "grid・box・sphere・torus・tube（蓋なし）に attribwrangle で i@nb = neighbourcount(0, @ptnum) を入れ、"
            "隣の点の数を数えた。辺の数 E を「隣の数の合計 ÷ 2」で出し、面から数え直した辺の数とも比べた。\n\n"
            f"**隣の数の合計 ÷ 2 は、辺の数と5通り{'すべて一致' if ok_e else 'で一致しないものがあった'}。**"
            "neighbourcount は「辺でつながった点」を数えている。\n\n"
            f"**V − E + F（オイラー標数）は、板 1・球と箱 2・トーラスと蓋なしの筒 0 と{'すべて一致' if ok_x else '一致しないものがあった'}。**"
            "形の穴や縁を、点と面の数だけで見分けられる。\n\n"
            "**分布で形の場所が分かる。**grid の角は 2、縁は 3、内側は 4。box の角（8点）は 3。"
            "sphere の極は Columns の数（16）だけ隣を持ち、残りは 4。torus は全部 4。\n\n"
            f"**最初の1回だけ遅い。**1つ目の wrangle は {first:.4f} 秒、2つ目からは {rest:.4f} 秒以下。VEX を最初に組み立てる時間とみられるが、確かめていない。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "形ごとの点・辺・面と、V − E + F",
            "images": [{"path": "153_hist.png", "caption": "grid だけ 2 と 3 が出る（角と縁）。torus は 4 だけ。"}],
            "per_row": 1,
            "columns": ["形", "V（点）", "Σ neighbourcount", "E = Σ/2", "E（面から）", "F（面）", "V − E + F", "答え", "分布（隣の数: 点の数）", "秒"],
            "rows": [[r["shape"], r["V"], r["sum_nb"], f"{r['E_from_nb']:g}", r["E_from_prims"], r["F"], f"{r['euler']:g}", r["want"],
                      " / ".join(f"{k}: {v}" for k, v in r["hist"].items()), f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>neighbourcount の合計 = 辺の数 × 2。</strong>辺の数を出す別の数え方として使える。",
            "<strong>V − E + F が 2 でなければ、閉じた1つの塊ではない。</strong>穴・縁・離れた塊の見つけ方になる。",
            "<strong>極の点は隣が多い。</strong>sphere の極は Columns 個。ぼかしや平滑化で極だけ効き方が変わる理由になる。",
        ],
        "next": ["neighbours() の並び順（時計回りか）", "fuse 前後で V − E + F がどう変わるか"],
    }
    with open(os.path.join(OUT, "153_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 153_report.json", ok_e, ok_x)


if __name__ == "__main__":
    main()
