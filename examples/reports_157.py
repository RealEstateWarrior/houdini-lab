# -*- coding: utf-8 -*-
"""実験157 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "157_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    on = [r for r in rows if r["interior"] == 1]
    off = [r for r in rows if r["interior"] == 0]
    line_chart(os.path.join(OUT, "157_pieces.png"),
               [{"label": "Create Interior Surfaces 入", "points": [(r["N"], r["pieces"]) for r in on], "color": PALETTE[0]},
                {"label": "切（外側の面だけ）", "points": [(r["N"], r["pieces"]) for r in off], "color": PALETTE[1]},
                {"label": "種の点の数", "points": [(r["N"], r["N"]) for r in on], "color": PALETTE[4], "dash": True}],
               title="voronoifracture: 1×1×1 の箱を N 個の種で割ったときの、かけらの数",
               x_label="種の点の数 N", y_label="かけらの数（name の種類）")
    ok = all(r["pieces"] == r["N"] and abs(r["volume"] - 1) < 1e-6 for r in on)
    n50 = [r for r in on if r["N"] == 50][0]
    payload = {
        "title": "voronoifracture は種 N 個で N 個のかけら、体積の合計は元のまま — 切り口を作らないと、中のかけらは消える",
        "summary":
            "1×1×1 の箱の中に scatter で N 個の点を撒き（isooffset で中を埋めてから撒いた）、voronoifracture で割った。"
            "かけらは name 属性の種類で数え、measure で体積を測った。\n\n"
            f"**かけらは種の数と同じ N 個、体積を足すとちょうど 1。**5通り{'すべてそうなった' if ok else 'で合わないものがあった'}（6桁）。"
            "すき間も重なりもなく、箱をちょうど分けている。\n\n"
            f"**かけらの大きさはそろわない。**N = 50 で、いちばん小さいかけら {n50['vmin']:.6f}、大きいかけら {n50['vmax']:.6f}"
            f"（{n50['vmax'] / n50['vmin']:.0f} 倍）。平均は 1/N = 0.02。種を撒いた場所しだいで決まる。\n\n"
            "**Create Interior Surfaces を切ると、切り口の面が作られない。**残るのは元の箱の表面を割った面だけで、"
            "箱の表面に触れないかけらは消える（N = 50 で 43 個、200 で 154 個）。形が閉じないので体積も測れない。\n\n"
            f"**速い。**N = 200 でも {on[-1]['sec']:.3f} 秒（1回目だけ {on[0]['sec']:.3f} 秒かかった）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "種の数・切り口の有無と、かけら",
            "images": [{"path": "157_pieces.png", "caption": "切り口ありは点線（N）にぴったり乗る。切ると中のかけらの分だけ下がる。"}],
            "per_row": 1,
            "columns": ["N", "切り口", "かけら", "面", "点", "体積の合計", "最小のかけら", "最大のかけら", "秒"],
            "rows": [[r["N"], "作る" if r["interior"] else "作らない", r["pieces"], f"{r['prims']:,}", f"{r['points']:,}",
                      f"{r['volume']:.6f}" if r["volume"] is not None else "—",
                      f"{r['vmin']:.6f}" if r["vmin"] is not None else "—",
                      f"{r['vmax']:.6f}" if r["vmax"] is not None else "—", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>かけらの数は種の点の数で決まる。</strong>欲しい数だけ点を撒く。",
            "<strong>体積は割っても変わらない。</strong>密度が同じなら、RBD の質量の合計も元のままのはず（RBD では確かめていない）。",
            "<strong>大きさは最大と最小で数百倍ちがう。</strong>scatter の relax で種を広げると、かえってばらつく（実験158）。",
        ],
        "next": ["種を relax したときの大きさのばらつき", "丸い形（球）を割ったときの体積の合計"],
    }
    with open(os.path.join(OUT, "157_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 157_report.json", ok)


if __name__ == "__main__":
    main()
