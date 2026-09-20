# -*- coding: utf-8 -*-
"""実験099・100 の図とレポートを、測った値から組み立てる。

    python examples/reports_099_100.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def stats(no):
    with open(os.path.join(OUT, f"{no}_stats.json"), encoding="utf-8") as fp:
        return json.load(fp)


def write(no, payload):
    with open(os.path.join(OUT, f"{no}_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた:", f"{no}_report.json")


def do_099():
    data = stats("099")
    rows = data["rows"]
    algos = data["algorithms"]
    steps = [r["step"] for r in rows[1:]]
    ratios = [round(a / b, 2) for a, b in zip(steps, steps[1:])]
    # 1段ごとの減りが約1/4なので、残りを等比で足して極限を見積もる
    last = rows[-1]
    tail = last["step"] / 4.0 / (1.0 - 0.25)
    limit = last["volume"] + tail
    by_algo = {a["algorithm"]: a for a in algos}

    line_chart(
        os.path.join(OUT, "099_subdiv.png"),
        [{"label": "体積（元の立方体の%）",
          "points": [(r["depth"], r["volume_pct"]) for r in rows],
          "color": PALETTE[0]},
         {"label": f"見積もった行き先 {limit / data['base_volume'] * 100:.2f}%",
          "points": [(rows[0]["depth"], limit / data["base_volume"] * 100),
                     (rows[-1]["depth"], limit / data["base_volume"] * 100)],
          "color": PALETTE[4], "dash": True}],
        title="立方体を割り続けると、体積は約32.76%に落ち着く",
        x_label="深さ（Depth）", y_label="体積（元の%）")
    line_chart(
        os.path.join(OUT, "099_step.png"),
        [{"label": "1段ごとの減り（絶対値）",
          "points": [(r["depth"], abs(r["step"])) for r in rows[1:]],
          "color": PALETTE[1]}],
        title="1段ごとの減りは、約4分の1ずつ小さくなる",
        x_label="深さ（Depth）", y_label="前の段からの減り")
    print("099_subdiv.png 099_step.png")

    write("099", {
        "title": "立方体を割り続けると、体積は約32.76%に落ち着く"
                 " — bilinear だけはちょうど1.000000のまま",
        "summary":
            "subdivide（Catmull-Clark）は、割るたびに形を滑らかにする。"
            "立方体を割り続けると、どこまで縮んで、どこで止まるのか。"
            "1辺 1.0 の立方体（体積 1.000000）を深さ 0 から 6 まで割って測った。\n\n"
            f"深さ1で {rows[1]['volume_pct']}%、深さ2で {rows[2]['volume_pct']}%、"
            f"深さ6で {rows[-1]['volume_pct']}%。"
            "1段ごとの減りは " + " / ".join(f"{abs(s):.6f}" for s in steps)
            + " で、**前の段の約4分の1ずつ**小さくなる（比は "
            + " / ".join(str(r) for r in ratios) + "）。\n\n"
            f"この比が 1/4 のまま続くとして残りを足すと、行き先は約 {limit:.6f}"
            f"（元の {limit / data['base_volume'] * 100:.2f}%）。"
            "ここは測った値ではなく見積もり。深さ6の実測は "
            f"{rows[-1]['volume']} で、見積もりとの差は {last['volume'] - limit:+.6f}。\n\n"
            "測り方が正しいことは、割り方を変えると確かめられる。"
            f"**osdbilinear は深さ3でも体積 {by_algo['osdbilinear']['volume']}** で、"
            "元のまま1ミリも変わらない。滑らかにせず、ただ割るだけの方式なので"
            "体積が変わらないのが正しい。ここが 1.000000 で出たので、"
            "他の数字も信じられる。\n\n"
            f"houdini と osdcc は同じ値（どちらも {by_algo['osdcc']['volume']}）。"
            f"mantra は少し小さく {by_algo['mantra']['volume']}。"
            f"osdloop は三角形に割るので面の数が倍（{by_algo['osdloop']['prims']}面）で、"
            f"体積は {by_algo['osdloop']['volume']} と大きめに残る。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "深さごとの面の数と体積（osdcc）",
             "note": "元は poly の立方体（6面・体積 1.000000）。"
                     "体積は measure の Volume を面ごとに足した値。"
                     "「前の段から」は、ひとつ浅い深さとの差。",
             "images": [{"path": "099_subdiv.png",
                         "caption": "深さ3でほぼ落ち着き、そこからはほとんど動かない。"},
                        {"path": "099_step.png",
                         "caption": "1段ごとの減りは約4分の1ずつ。等比で残りを足すと行き先が出る。"}],
             "per_row": 2,
             "columns": ["深さ", "面", "点", "秒", "体積", "元の%", "前の段から"],
             "rows": [[str(r["depth"]), f"{r['prims']:,}", f"{r['points']:,}",
                       f"{r['seconds']:.3f}", f"{r['volume']:.6f}",
                       f"{r['volume_pct']}%", f"{r['step']:+.6f}"]
                      for r in rows]},
            {"label": "割り方（Algorithm）を5通り（深さ3で揃える）",
             "note": "osdbilinear は滑らかにせず割るだけなので、"
                     "体積が変わらないのが正しい。測り方の裏付けになる。",
             "images": [],
             "per_row": 1,
             "columns": ["Algorithm", "面", "点", "秒", "体積", "元の%"],
             "rows": [[a["algorithm"], f"{a['prims']:,}", f"{a['points']:,}",
                       f"{a['seconds']:.3f}", f"{a['volume']:.6f}",
                       f"{a['volume_pct']}%"] for a in algos]},
        ],
        "notes": [
            f"<strong>行き先は元の約 {limit / data['base_volume'] * 100:.2f}%。</strong>"
            f"深さ6の実測は {rows[-1]['volume_pct']}%。"
            "1段ごとの減りが約1/4ずつなので、残りを等比で足して見積もった"
            "（この行き先の値は実測ではない）。",
            f"<strong>深さ3でほぼ決まる。</strong>深さ3で {rows[3]['volume_pct']}%、"
            f"深さ6で {rows[-1]['volume_pct']}%。差は "
            f"{rows[3]['volume_pct'] - rows[-1]['volume_pct']:.2f}ポイントしかない。"
            f"面の数は {rows[3]['prims']:,} から {rows[-1]['prims']:,} へ64倍になる。"
            "深さを上げても形はほとんど変わらないのに、重さだけが増える。",
            "<strong>osdbilinear はちょうど 1.000000 だった。</strong>"
            "滑らかにせず割るだけなので、体積が変わらないのが正しい。"
            "測り方（measure の Volume を面ごとに足す）が正しいことの裏付けになる。",
            f"<strong>houdini と osdcc は同じ値。</strong>どちらも "
            f"{by_algo['osdcc']['volume']}。mantra は "
            f"{by_algo['mantra']['volume']} で少し小さく、osdloop は三角形に割るため"
            f"面が倍（{by_algo['osdloop']['prims']}面）で "
            f"{by_algo['osdloop']['volume']} と大きめに残る。",
        ],
        "next": [
            "Catmull-Clark の極限体積は、計算で求められる値と一致するか",
            "球や円柱では、深さいくつで落ち着くか",
            "Crease Weight を入れると、どこまで縮みを止められるか",
        ],
    })


def do_100():
    data = stats("100")
    rows = data["rows"]
    box_rows = data["box_rows"]
    worst = max(abs(r["diff"]) for r in rows)
    worst_box = max(abs(r["diff_real"]) for r in box_rows)
    coarse = [r for r in rows if r["rows"] == 20]
    fine = [r for r in rows if r["rows"] == 120]
    big = [r for r in box_rows if r["dist"] == 1.0][0]

    line_chart(
        os.path.join(OUT, "100_peak.png"),
        [{"label": "球（20×20）で測った倍率",
          "points": [(r["dist"], r["ratio"]) for r in coarse],
          "color": PALETTE[0]},
         {"label": "球（120×120）で測った倍率",
          "points": [(r["dist"], r["ratio"]) for r in fine],
          "color": PALETTE[2]},
         {"label": "((r+d)/r)³ の式",
          "points": [(r["dist"], r["want_ratio"]) for r in coarse],
          "color": PALETTE[1], "dash": True}],
        title="球では、粗くても細かくても倍率は式とぴったり重なる",
        x_label="Distance", y_label="体積の倍率")
    line_chart(
        os.path.join(OUT, "100_box.png"),
        [{"label": "立方体で測った倍率",
          "points": [(r["dist"], r["ratio"]) for r in box_rows],
          "color": PALETTE[0]},
         {"label": "(1 + 2d/√3)³ の式",
          "points": [(r["dist"], r["want_real"]) for r in box_rows],
          "color": PALETTE[2], "dash": True},
         {"label": "(1 + 2d)³ と思っていたら",
          "points": [(r["dist"], r["want_cube_ratio"]) for r in box_rows],
          "color": PALETTE[1], "dash": True}],
        title="立方体は 1+2d ではなく 1+2d/√3 だけ大きくなる",
        x_label="Distance", y_label="体積の倍率")
    print("100_peak.png 100_box.png")

    write("100", {
        "title": "peak は式どおりに動く — 球は ((r+d)/r)³、立方体は (1+2d/√3)³ に6桁一致",
        "summary":
            "peak は点を、その点の法線の向きへ Distance だけ動かす。"
            "球なら半径が r から r+d になるだけなので、体積は ((r+d)/r)³ 倍に"
            "なるはず。球は多角形なので体積そのものは真の球より小さいが、"
            "**倍率なら分割の粗さに関係なく式に合う**はず。\n\n"
            f"3つの粗さ（20×20 / 60×60 / 120×120）× 6つの距離 = 18通りを測った。"
            f"差はすべて 0.000000 台で、いちばん大きい差でも {worst:.6f}。"
            f"20×20 の球は真の球の {round(coarse[0]['volume'] / data['true_sphere'] * 100, 3)}% "
            f"しかない粗さだが、倍率は d=1.0 で {coarse[-1]['ratio']}（式は "
            f"{coarse[-1]['want_ratio']}）。**粗さは倍率に影響しない。**\n\n"
            "立方体では話が変わる。立方体の点の法線は、隣り合う3面の平均で "
            "(1,1,1)/√3 を向く。だから角は各軸に d/√3 しか動かず、"
            "1辺は 1+2d ではなく **1 + 2d/√3** になる。\n\n"
            f"d=1.0 のとき、1辺が 1+2d になったつもりだと 27倍を期待するが、"
            f"実測は {big['ratio']}。1 + 2d/√3 の式では {big['want_real']} で、"
            f"差は {big['diff_real']:+.6f}。**思い違いのほうが 16.99 もずれていた。**\n\n"
            "peak が「法線の向きに動かす」と書かれているとき、その法線は"
            "面の向きではなく点の向き。角のある形では、そこが効いてくる。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "球：測った倍率と ((r+d)/r)³",
             "note": f"半径 1.0 の球に normal を通してから peak をかけた。"
                     f"真の球の体積は {data['true_sphere']}。"
                     "倍率は、同じ粗さの d=0 の体積で割った値。",
             "images": [{"path": "100_peak.png",
                         "caption": "3つの粗さの線が、式の線と完全に重なっている。"}],
             "per_row": 1,
             "columns": ["球の粗さ", "Distance", "体積", "倍率", "式", "差"],
             "rows": [[f"{r['rows']}×{r['rows']}", f"{r['dist']:g}",
                       f"{r['volume']:.6f}", f"{r['ratio']:.6f}",
                       f"{r['want_ratio']:.6f}", f"{r['diff']:+.6f}"]
                      for r in rows]},
            {"label": "立方体：1+2d ではなく 1+2d/√3",
             "note": "立方体の点の法線は3面の平均で (1,1,1)/√3 を向く。"
                     "角は各軸に d/√3 だけ動く。",
             "images": [{"path": "100_box.png",
                         "caption": "1+2d だと思っていると大きく外す。"
                                    "実測は 1+2d/√3 の線に重なる。"}],
             "per_row": 1,
             "columns": ["Distance", "1辺", "体積", "1+2d/√3 の式", "差",
                         "1+2d の式", "その差"],
             "rows": [[f"{r['dist']:g}", f"{r['side']:.6f}",
                       f"{r['volume']:.6f}", f"{r['want_real']:.6f}",
                       f"{r['diff_real']:+.6f}",
                       f"{r['want_cube_ratio']:.6f}",
                       f"{r['diff_naive']:+.6f}"] for r in box_rows]},
        ],
        "notes": [
            f"<strong>球では18通りすべて式に一致した。</strong>"
            f"いちばん大きい差でも {worst:.6f}。"
            f"20×20 の粗い球（真の球の "
            f"{round(coarse[0]['volume'] / data['true_sphere'] * 100, 3)}%）でも、"
            "倍率は細かい球とまったく同じだった。",
            "<strong>倍率で見ると、分割の粗さは消える。</strong>"
            "体積そのものは粗さで変わるが、同じ形の d=0 で割れば粗さの分が打ち消える。"
            "「答えと突き合わせる」ときに使える手。",
            f"<strong>立方体は 1+2d/√3。</strong>d=1.0 で実測 {big['ratio']}、"
            f"式 {big['want_real']}（差 {big['diff_real']:+.6f}）。"
            f"1+2d だと思っていると 27倍を期待して {abs(big['diff_naive']):.2f} も外す。",
            "<strong>法線は面の向きではなく点の向き。</strong>"
            "立方体の角の点は3面の平均を向くので、斜めに出る。"
            "角のある形を peak で厚くすると、面は動かず角だけが出っぱる。",
        ],
        "next": [
            "polyextrude で厚みを付けたときは、どの式に合うか",
            "法線を面ごとに持たせた（頂点法線）状態で peak をかけるとどうなるか",
            "Mask で効きを弱めたとき、倍率はどう崩れるか",
        ],
    })


if __name__ == "__main__":
    do_099()
    do_100()
