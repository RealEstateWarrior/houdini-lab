# -*- coding: utf-8 -*-
"""実験246 の図とレポートを、測った値から組み立てる。"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart  # noqa: E402

LAB = {"r80_g06_all": "強さ 0.6・ふつう", "r80_g06_t1": "強さ 0.6・1 スレッド", "r80_g05_all": "強さ 0.5・ふつう", "r80_g05_t1": "強さ 0.5・1 スレッド"}


def main():
    with open(os.path.join(OUT, "246_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    line_chart(os.path.join(OUT, "246_runs.png"),
               [{"label": LAB[k], "points": [(i + 1, v) for i, v in enumerate(t[k]["moved"])]} for k in LAB],
               "同じ設定で 5 回回したときの、動いた破片の数", "何回目", "動いた破片の数")
    f = lambda v: "・".join(map(str, v))  # noqa: E731
    table = [[LAB[k], f(t[k]["moved"]), f"{statistics.fmean(t[k]['sim_sec']):.2f}"] for k in LAB]
    m = lambda k: statistics.fmean(t[k]["sim_sec"])  # noqa: E731
    payload = {
        "title": "ガラスの割れ方が回ごとに揺れたのは、計算を何本も並べて走らせていた（マルチスレッド）ため。1 スレッドにすると 5 回とも同じ割れ方になった。"
                 f"ただし Bullet の計算は約 {m('r80_g06_t1') / m('r80_g06_all'):.0f} 倍遅くなる",
        "summary":
            "**課題: 実験226 で、つながりを弱めたガラスは、同じ設定で回しても割れ方が毎回違った（強さ 0.6 で動いた破片 54〜116 個）。"
            "同じ設定なら同じ結果になってほしい。計算を 1 本（1 スレッド）にすると揃うのか。**\n\n"
            "実験226 の台本で、「ひび 80 本・強さ 0.6」と「ひび 80 本・強さ 0.5」だけを、ふつう（Houdini が使えるだけのスレッド）と、"
            "環境変数 HOUDINI_MAXTHREADS=1（1 スレッド）で、5 回ずつ別の hython で回した。48 フレーム目までに 5 cm 以上動いた破片を数えた。\n\n"
            f"**1 スレッドなら、5 回とも同じ。**強さ 0.6: {f(t['r80_g06_t1']['moved'])}、強さ 0.5: {f(t['r80_g05_t1']['moved'])}。\n\n"
            f"**ふつう（マルチスレッド）では揺れる。**強さ 0.6: {f(t['r80_g06_all']['moved'])}、強さ 0.5: {f(t['r80_g05_all']['moved'])}。"
            "1 スレッドのときの値（88・100）がいちばん多く出たが、ときどき大きく違う割れ方になった。"
            "計算を並べて走らせると、足し算の順番が回ごとに変わってごくわずかな差が生まれ、割れるか割れないかの境目では、その差でつながりが切れるかどうかが変わると考えられる。\n\n"
            f"**1 スレッドは遅い。**Bullet の 48 フレームの時間は、強さ 0.6 で {m('r80_g06_all'):.2f} → {m('r80_g06_t1'):.2f} 秒、強さ 0.5 で {m('r80_g05_all'):.2f} → {m('r80_g05_t1'):.2f} 秒。\n\n"
            "**決め方: 割れ方を毎回同じにしたいなら、決まった割れ方をキャッシュに書き出して、それを読む。**"
            "1 スレッドで回せば毎回同じになるが、3 倍遅い。形を詰める間は 1 スレッドで回し、決まったらキャッシュに書き出すのがよい。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "同じ設定で 5 回回した結果",
             "images": [{"path": "246_runs.png", "caption": "1 スレッド（平らな線）は毎回同じ。ふつう（ぎざぎざの線）はときどき大きく違う。"}],
             "per_row": 1, "columns": ["条件", "動いた破片の数（5 回）", "Bullet 48 フレームの平均（秒）"], "rows": table},
        ],
        "notes": [
            "<strong>1 スレッド（HOUDINI_MAXTHREADS=1）なら、Bullet の割れ方は 5 回とも同じ。</strong>",
            "<strong>ふつう（マルチスレッド）では、境目の強さで割れ方がときどき大きく変わる。</strong>",
            f"<strong>1 スレッドは約 {m('r80_g06_t1') / m('r80_g06_all'):.0f} 倍遅い。</strong>決まった割れ方はキャッシュで固定する。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "246_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
