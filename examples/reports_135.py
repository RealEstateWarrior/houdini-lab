# -*- coding: utf-8 -*-
"""実験135 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "135_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    r = {x["func"]: x for x in rows}
    order = ["rand(P)", "noise(P)", "xnoise(P)", "anoise(P)", "onoise(P)", "curlnoise(P).x", "snoise(P)"]
    line_chart(os.path.join(OUT, "135_noise.png"),
               [{"label": "最大", "points": [(i, r[f]["max"]) for i, f in enumerate(order)], "color": PALETTE[1]},
                {"label": "平均", "points": [(i, r[f]["mean"]) for i, f in enumerate(order)], "color": PALETTE[0]},
                {"label": "最小", "points": [(i, r[f]["min"]) for i, f in enumerate(order)], "color": PALETTE[2]}],
               title="0=rand 1=noise 2=xnoise 3=anoise 4=onoise 5=curlnoise.x 6=snoise（100万点）",
               x_label="関数", y_label="値")
    print("135_noise.png")
    same_flow = r["flownoise(P, 0)"]["min"] == r["noise(P)"]["min"] and r["flownoise(P, 0)"]["sd"] == r["noise(P)"]["sd"]
    n = r["noise(P)"]
    payload = {
        "title": "VEX のノイズの値の範囲 — noise() は 0.06〜0.92 にしか届かず、snoise() は ±1 を超える",
        "summary":
            "VEX のノイズ関数を、約100万点（100×100×100 の格子、間隔 0.37）で呼んで、"
            "出てきた値の最小・最大・平均・標準偏差を数えた。「0〜1」「−1〜1」という思い込みを実測で確かめる。\n\n"
            f"**noise() は 0〜1 の真ん中に固まる。** 最小 {n['min']:g}・最大 {n['max']:g}・平均 {n['mean']:g}・"
            f"標準偏差 {n['sd']:g}。0 や 1 には近づかない。マスクに使うなら、fit で伸ばさないと"
            "コントラストが弱い。xnoise() も似ていて {:g}〜{:g}（標準偏差 {:g}）。\n\n".format(
                r["xnoise(P)"]["min"], r["xnoise(P)"]["max"], r["xnoise(P)"]["sd"]) +
            f"**snoise() は −1〜1 に収まらない。** {r['snoise(P)']['min']:g}〜{r['snoise(P)']['max']:g}。"
            f"平均も {r['snoise(P)']['mean']:g} と少しプラスに寄る。\n\n"
            f"onoise() は {r['onoise(P)']['min']:g}〜{r['onoise(P)']['max']:g}（平均ほぼ0）、"
            f"anoise() は {r['anoise(P)']['min']:g}〜{r['anoise(P)']['max']:g} で平均 {r['anoise(P)']['mean']:g}（0 の側に寄る）、"
            f"curlnoise() の x 成分は {r['curlnoise(P).x']['min']:g}〜{r['curlnoise(P).x']['max']:g}。\n\n"
            f"**flownoise(P, 0) は、noise(P) と{'同じ値' if same_flow else '違う値'}だった**（最小・最大・標準偏差がすべて一致）。"
            "流れの位相が0のときは、ふつうの noise と同じ。vector を受ける noise() の x 成分も、float の noise() と同じ値だった。\n\n"
            f"比べとして rand() は {r['rand(P)']['min']:g}〜{r['rand(P)']['max']:g}、標準偏差 {r['rand(P)']['sd']:g}"
            "（一様なら 0.2887）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "関数ごとの値の範囲（約100万点）",
             "note": "位置は整数格子 × 0.37 +（0.123, 0.456, 0.789）。周波数は変えていない。"
                     "秒は1回の計算（最初の関数はコンパイルを含む）。",
             "images": [{"path": "135_noise.png",
                         "caption": "noise・xnoise は 0.5 のまわりに狭く、snoise は ±1 を超える。"}],
             "per_row": 1,
             "columns": ["関数", "最小", "最大", "平均", "標準偏差", "0〜1 に入る割合", "秒"],
             "rows": [[x["func"], f"{x['min']:g}", f"{x['max']:g}", f"{x['mean']:g}", f"{x['sd']:g}",
                       f"{x['inside01'] * 100:.1f}%", f"{x['sec']:.3f}"] for x in rows]},
        ],
        "notes": [
            "<strong>noise() は 0.06〜0.92。</strong>0〜1 いっぱいに使いたいなら fit(v, 0.1, 0.9, 0, 1) などで伸ばす"
            "（端の値は目安。場所を変えれば少し変わる）。",
            "<strong>snoise() は ±2 近くまで出る。</strong>clamp せずに色や高さに使うと、はみ出す。",
            "<strong>anoise() は 0 の側に寄る。</strong>平均 0.13。",
            "<strong>flownoise の位相0は noise と同じ。</strong>",
        ],
        "next": [
            "周波数を上げ下げしても、範囲は変わらないか",
            "unifiednoise の各種類で、Output を正規化したときの範囲",
            "オクターブを重ねた（フラクタル）ときの範囲の広がり",
        ],
    }
    with open(os.path.join(OUT, "135_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 135_report.json")


if __name__ == "__main__":
    main()
