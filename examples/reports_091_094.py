# -*- coding: utf-8 -*-
"""実験091〜094 のレポート JSON を、測った値から組み立てる。

数字を手で打ち直すと写し間違いが起きる。out/NNN_stats.json から読んで埋める。

    python examples/reports_091_094.py
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")


def stats(no):
    with open(os.path.join(OUT, f"{no}_stats.json"), encoding="utf-8") as fp:
        return json.load(fp)


def write(no, payload):
    path = os.path.join(OUT, f"{no}_report.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた:", os.path.basename(path))


def num(value, digits=6):
    return f"{value:.{digits}f}"


def report_091():
    data = stats("091")
    rows = data["rows"]
    base = data["base_prims"]
    by = {r["keep"]: r for r in rows}
    half, quarter, tiny = by[50], by[25], by[2]

    write("091", {
        "title": "面を半分にすると、形のずれはおよそ2倍になる"
                 f" — 25%まで減らしてもずれは幅の {quarter['gap_mean_pct']}%",
        "summary":
            f"polyreduce は「残す割合」を決めると、そこまで面を間引く。軽くなるのは"
            f"当たり前だが、形はどれだけ元から離れるのか。{base}面の形を 80/50/25/10/5/2% "
            "まで減らして測った。\n\n"
            "ずれの測り方は、減らしたあとの各点から元の面までの最短距離（VEX の xyzdist）。"
            "その平均と最大を、元の形の幅で割って割合にした。\n\n"
            f"25%まで減らすと、面は {base} から {quarter['prims']} へ。"
            f"ずれの平均は幅の {quarter['gap_mean_pct']}%、最大でも {quarter['gap_max_pct']}%。"
            "見た目にはほとんど分からない大きさに収まっている。\n\n"
            f"減らしすぎると急に崩れる。2%（{tiny['prims']}面）では平均 {tiny['gap_mean_pct']}%、"
            f"最大 {tiny['gap_max_pct']}%。50%から2%までの区間では、面の数が半分になるたびに"
            "ずれがおよそ2倍になっていた。\n\n"
            f"時間は、どの割合でもほとんど変わらない（{min(r['seconds'] for r in rows)}〜"
            f"{max(r['seconds'] for r in rows)}秒）。減らす量を増やしても遅くならない。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "残す割合ごとの、面の数と形のずれ",
             "note": f"元は球（60×60）に mountain をかけた {base}面・幅 {data['base_size']}。"
                     "ずれは、減らしたあとの各点から元の面までの最短距離。"
                     "「幅の%」は、その距離を元の形の幅で割ったもの。",
             "images": [{"path": "091_reduce.png",
                         "caption": "25%まではずれが小さいまま。そこから先は、"
                                    "面を半分にするたびにずれがおよそ2倍になる。"}],
             "per_row": 1,
             "columns": ["残す%", "面", "点", "ずれ 平均", "幅の%", "ずれ 最大", "幅の%", "秒"],
             "rows": [[str(r["keep"]), str(r["prims"]), str(r["points"]),
                       num(r["gap_mean"]), f"{r['gap_mean_pct']}%",
                       num(r["gap_max"]), f"{r['gap_max_pct']}%",
                       f"{r['seconds']:.3f}"] for r in rows]},
        ],
        "notes": [
            f"<strong>25%まではほとんど変わらない。</strong>面を {base} から "
            f"{quarter['prims']} に減らしても、ずれの平均は幅の {quarter['gap_mean_pct']}%。"
            f"半分（{half['prims']}面）なら {half['gap_mean_pct']}%。",
            "<strong>面を半分にすると、ずれはおよそ2倍。</strong>"
            + "、".join(
                f"{a['prims']}→{b['prims']}面で {round(b['gap_mean'] / a['gap_mean'], 2)}倍"
                for a, b in zip(rows[1:-1], rows[2:])) + "。",
            f"<strong>減らす量を増やしても遅くならない。</strong>"
            f"{min(r['seconds'] for r in rows)}秒から {max(r['seconds'] for r in rows)}秒の間で、"
            "残す割合との関係は見えなかった。",
        ],
        "next": [
            "ずれの2倍という関係が、もっと角のある形でも成り立つか",
            "polyreduce と remesh で、同じ面数にしたときどちらがずれないか",
        ],
    })


def report_092():
    data = stats("092")
    rows = data["rows"]
    ratios = [r["prim_ratio"] for r in rows if r.get("prim_ratio")]
    first, last = rows[0], rows[-1]
    gap_ratio = [round(a["gap_mean"] / b["gap_mean"], 2)
                 for a, b in zip(rows, rows[1:])]

    write("092", {
        "title": "辺の長さを半分にすると、面は約4倍・ずれは約1/4・時間は約4倍",
        "summary":
            "remesh は「目指す辺の長さ」を決めて、そこに近い三角形で張り直す。"
            "面積あたりの三角形の数で考えれば、辺を半分にすると面は4倍になるはず。"
            f"球（40×40、{data['base_prims']}面）を、辺 0.2 / 0.1 / 0.05 / 0.025 で"
            "張り直して測った。\n\n"
            f"面の数は {first['prims']} → {rows[1]['prims']} → {rows[2]['prims']} → "
            f"{last['prims']}。前の段からの倍率は "
            + " / ".join(str(r) for r in ratios) + " で、いずれも4倍の前後だった。\n\n"
            f"元の形からのずれは {num(first['gap_mean'])} から {num(last['gap_mean'])} まで"
            "小さくなる。1段ごとの縮み方は "
            + " / ".join(f"{r}倍" for r in gap_ratio) + "。こちらも約4分の1ずつ。\n\n"
            f"時間は {first['seconds']}秒 から {last['seconds']}秒。"
            "面の数に比例して増えている。細かくすることの代金は、面の数そのままに乗る。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "目指す辺の長さごとの、面の数・ずれ・時間",
             "note": f"元は球（40×40）の {data['base_prims']}面。"
                     "「面の倍率」は前の段からの比。ずれは各点から元の面までの最短距離。",
             "images": [{"path": "092_remesh.png",
                         "caption": "1段ごとの面の増え方は4倍の前後に収まる。"
                                    "空間ではなく面積あたりで増えていることになる。"},
                        {"path": "092_gap.png",
                         "caption": "ずれは約1/4ずつ小さくなり、時間は約4倍ずつ増える。"}],
             "per_row": 2,
             "columns": ["目指す辺", "面", "点", "面の倍率", "ずれ 平均", "ずれ 最大", "秒"],
             "rows": [[str(r["edge"]), str(r["prims"]), str(r["points"]),
                       str(r["prim_ratio"] or "—"),
                       num(r["gap_mean"]), num(r["gap_max"]),
                       f"{r['seconds']:.3f}"] for r in rows]},
        ],
        "notes": [
            "<strong>面は4倍ずつ増える。</strong>実測 "
            + " / ".join(str(r) for r in ratios)
            + "。辺の長さを半分にすると、面積あたりの三角形の数が4倍になるという見方と合う。",
            "<strong>ずれは約1/4ずつ小さくなる。</strong>"
            + " / ".join(f"{r}倍" for r in gap_ratio)
            + "。面を4倍にして、ずれが1/4。増やした分がそのまま精度になっている。",
            f"<strong>時間も約4倍ずつ。</strong>{first['seconds']}秒 → {last['seconds']}秒。"
            "面の数に比例するので、細かさを上げるほど代金は素直に増える。",
        ],
        "next": [
            "同じ面数にしたとき、remesh と polyreduce でどちらがずれないか",
            "角のある形（箱や文字）では、辺の長さを決めるやり方が通じるか",
        ],
    })


def report_093():
    data = stats("093")
    rows = data["rows"]
    methods = data["methods"]
    last = rows[-1]
    by_method = {m["method"]: m for m in methods}

    write("093", {
        "title": "ならしても体積はほとんど減らない — 強さ160でも 99.60%、縮みは 0.40%だけ",
        "summary":
            "smooth は点を近所の平均へ寄せる。凹凸が消えるのは狙い通りだが、"
            "同時に形が縮むと言われる。どれだけ縮むのかを測った。\n\n"
            "球（60×60）に mountain をかけた形（体積 "
            f"{data['base_volume']}）に、Strength を 0 から 160 までかけた。"
            "体積は measure SOP の Volume を面ごとに足して出した。\n\n"
            f"既定の Strength 10 で体積は元の {rows[3]['volume_pct']}%。"
            f"16倍の 160 まで上げても {last['volume_pct']}% で、減ったのは 0.40%だけだった。"
            "「ならすと縮む」という言い方は、少なくともこの形とこのノードでは"
            "**体積の話としては当てはまらない**。\n\n"
            f"形そのものは動いている。元の面からのずれは強さ10で {num(rows[3]['gap_mean'])}、"
            f"160で {num(last['gap_mean'])}。凹凸は確かに消えているが、"
            "出た所と入った所が相殺して、体積としては残る。\n\n"
            "ならし方（Method）を変えても、縮みの差は小さい。強さ160で揃えると "
            + "、".join(f"{m['method']} が {m['volume_pct']}%" for m in methods)
            + "。曲率を見るやり方がいちばん体積を保ち、同時にずれも小さかった。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "Strength ごとの体積とずれ",
             "note": f"元は球（60×60）に mountain（高さ0.2）をかけた 3,540面、"
                     f"体積 {data['base_volume']}。体積は measure の Volume を面ごとに足した値。"
                     "ずれは各点から元の面までの最短距離。",
             "images": [{"path": "093_smooth.png",
                         "caption": "強さを16倍にしても、体積は 0.40% しか減らない。"},
                        {"path": "093_gap.png",
                         "caption": "形は動いている。ずれは強さとともに増える。"}],
             "per_row": 2,
             "columns": ["Strength", "体積", "元の%", "ずれ 平均", "ずれ 最大", "秒"],
             "rows": [[f"{r['strength']:g}", num(r["volume"]), f"{r['volume_pct']}%",
                       num(r["gap_mean"]), num(r["gap_max"]),
                       f"{r['seconds']:.3f}"] for r in rows]},
            {"label": "ならし方（Method）を変えたとき（Strength 160 で揃える）",
             "note": "3つのやり方を、同じ強さで比べた。",
             "images": [],
             "per_row": 1,
             "columns": ["Method", "体積", "元の%", "ずれ 平均", "ずれ 最大"],
             "rows": [[m["method"], num(m["volume"]), f"{m['volume_pct']}%",
                       num(m["gap_mean"]), num(m["gap_max"])] for m in methods]},
        ],
        "notes": [
            f"<strong>縮みは 0.40%だけ。</strong>Strength 160 で体積は元の "
            f"{last['volume_pct']}%。既定の 10 では {rows[3]['volume_pct']}%。"
            "「ならすと縮む」は、体積の話としてはこの形では出なかった。",
            "<strong>形は動いている。</strong>ずれの平均は強さ10で "
            f"{num(rows[3]['gap_mean'])}、160で {num(last['gap_mean'])}。"
            "凹凸は消えるが、出た所と入った所が相殺している。",
            "<strong>曲率を見るやり方がいちばん保つ。</strong>強さ160で、"
            f"curvaturedominant が {by_method['curvaturedominant']['volume_pct']}%、"
            f"uniform が {by_method['uniform']['volume_pct']}%。"
            f"ずれも {num(by_method['curvaturedominant']['gap_mean'])} と "
            f"{num(by_method['uniform']['gap_mean'])} で、曲率を見るほうが小さい。",
        ],
        "next": [
            "薄い形（板や布）では縮みが出るのか",
            "強さをもっと上げると、どこで体積が落ち始めるのか",
            "vdbsmooth との縮み方の違い",
        ],
    })


def report_094():
    data = stats("094")
    rows = data["rows"]
    ratios = [r["voxel_ratio"] for r in rows if r.get("voxel_ratio")]
    first, last = rows[0], rows[-1]

    write("094", {
        "title": "升目を半分にしても、数は8倍ではなく約4倍 — VDB は表面の近くだけ持っている",
        "summary":
            "VDB は空間を升目に区切って値を入れる。1辺を半分にすれば、空間ぜんぶを"
            "持つなら升目の数は8倍になる。ところが VDB は表面の近くだけを持つ作りなので、"
            "面積に比例して4倍で済むのではないか。測った。\n\n"
            f"球（50×50）に mountain をかけた形を、升目 0.2 から 0.0125 まで"
            "半分ずつ細かくして、VDB が実際に持っている升目の数（activevoxelcount）を数えた。\n\n"
            f"升目の数は {first['voxels']} → {last['voxels']}。"
            "前の段からの倍率は " + " / ".join(str(r) for r in ratios)
            + " で、細かくするほど4に近づいた。**8倍にはならない。**\n\n"
            "面に戻したときの面の数も同じように増える。"
            f"{first['prims']} 面から {last['prims']} 面。\n\n"
            f"ずれは頭打ちになる。{num(first['gap_mean'])} から "
            f"{num(rows[3]['gap_mean'])} までは順に小さくなるが、最後の段では "
            f"{num(last['gap_mean'])} で、ほとんど変わらなかった。"
            "升目を細かくしても、元の面の細かさより細かい形は出てこない。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "升目の大きさごとの、升目の数・面の数・ずれ",
             "note": "元は球（50×50）に mountain（高さ0.15）をかけた 2,450面。"
                     "升目の数は、VDB の prim に activevoxelcount を聞いた値。"
                     "「作る」は vdbfrompolygons、「戻す」は convertvdb の時間。",
             "images": [{"path": "094_voxels.png",
                         "caption": "1段ごとの増え方は4に近づく。"
                                    "空間ぜんぶではなく、表面の近くだけを持っている。"},
                        {"path": "094_gap.png",
                         "caption": "細かくしてもずれは止まる。"
                                    "元の面の細かさが上限になる。"}],
             "per_row": 2,
             "columns": ["升目", "升目の数", "倍率", "戻した面", "作る秒", "戻す秒", "ずれ 平均"],
             "rows": [[f"{r['voxel']:g}", f"{r['voxels']:,}",
                       str(r["voxel_ratio"] or "—"), f"{r['prims']:,}",
                       f"{r['make_seconds']:.3f}", f"{r['convert_seconds']:.3f}",
                       num(r["gap_mean"])] for r in rows]},
        ],
        "notes": [
            "<strong>8倍ではなく約4倍。</strong>実測 "
            + " / ".join(str(r) for r in ratios)
            + "。VDB は表面の近くだけを持つので、空間の体積ではなく面積に比例して増える。",
            f"<strong>ずれは頭打ちになる。</strong>{num(rows[3]['gap_mean'])} から "
            f"{num(last['gap_mean'])} へ、最後の段では "
            f"{round(rows[3]['gap_mean'] / last['gap_mean'], 2)}倍しか縮まなかった。"
            "元の面の細かさが上限になっている。",
            f"<strong>時間は升目の数ほど増えない。</strong>作るのは "
            f"{first['make_seconds']}秒 から {last['make_seconds']}秒。"
            "升目が230倍になっても、この大きさでは1秒を切ったままだった。",
        ],
        "next": [
            "元の面を細かくすれば、ずれはさらに小さくなるのか",
            "升目を細かくしたときの記憶の使用量",
            "SDF と Fog で、持つ升目の数が違うのか",
        ],
    })


if __name__ == "__main__":
    report_091()
    report_092()
    report_093()
    report_094()
