# -*- coding: utf-8 -*-
"""実験101・102 の図とレポートを、測った値から組み立てる。

    python examples/reports_101_102.py
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


def do_101():
    data = stats("101")
    rows = data["rows"]
    grid_rows = data["grid_rows"]
    exact = data["exact_sphere"]
    ratios = [r["short_ratio"] for r in rows if r.get("short_ratio")]
    worst_grid = max(abs(r["diff"]) for r in grid_rows)

    line_chart(
        os.path.join(OUT, "101_area.png"),
        [{"label": "足りない分（真の球との差）",
          "points": [(r["divs"], r["short"]) for r in rows],
          "color": PALETTE[0]}],
        title="分割を倍にすると、足りない分は4分の1になる",
        x_label="分割の数（rows = cols）", y_label="真の球に足りない面積")
    line_chart(
        os.path.join(OUT, "101_ratio.png"),
        [{"label": "1段ごとに何分の1になったか（実測）",
          "points": [(i + 1, r) for i, r in enumerate(ratios)],
          "color": PALETTE[0]},
         {"label": "分割の2乗で減るなら 4",
          "points": [(1, 4.0), (len(ratios), 4.0)],
          "color": PALETTE[2], "dash": True}],
        title="誤差は分割の2乗で減る（実測は4の前後）",
        x_label="分割を倍にした回数", y_label="足りない分の減り方",
        y_range=(0, 6))
    print("101_area.png 101_ratio.png")

    write("101", {
        "title": f"面積の測りは、平らな面ならぴったり合う — 球の足りない分は分割の2乗で減る",
        "summary":
            "面積は「測るための道具」としてよく使う。散らす濃さを決めたり、"
            "重さを面積から出したり。その道具そのものの精度を、"
            "答えの分かっている形で確かめた。\n\n"
            f"1辺 {data['side'] if 'side' in data else 2.0} の平らな板は、面積 "
            f"{data['exact_grid']} がぴったり出る。分割を 2 から 201 まで"
            f"変えても差は最大 {worst_grid:.9f}（小数の丸めの範囲）。"
            "**分割の数は面積に影響しない。**\n\n"
            f"球は違う。半径 1.0 の球の答えは {exact} だが、多角形なので必ず"
            f"小さく出る。分割 8 では {rows[0]['area']}（{rows[0]['short_pct']}% 足りない）、"
            f"分割 240 で {rows[-1]['area']}（{rows[-1]['short_pct']}% 足りない）。\n\n"
            "足りない分の減り方は " + " / ".join(str(r) for r in ratios)
            + " で、**分割を倍にすると4分の1**になる。誤差が分割の2乗で減る"
            "ということで、細かくする効きは良い。\n\n"
            f"実用の目安として、分割 60（{rows[3]['prims']:,}面）で足りない分は "
            f"{rows[3]['short_pct']}%。面積を使って何かを決めるぶんには十分だが、"
            "答えとして出すなら、多角形のぶん小さく出ていることを覚えておく。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "平らな板（1辺 2.0、答えは 4.000000）",
             "note": "grid の分割を変えた。差は小数の丸めの範囲に収まる。",
             "images": [],
             "per_row": 1,
             "columns": ["分割", "面", "面積", "答えとの差", "秒"],
             "rows": [[str(r["divs"]), f"{r['prims']:,}", f"{r['area']:.6f}",
                       f"{r['diff']:+.9f}", f"{r['seconds']:.3f}"]
                      for r in grid_rows]},
            {"label": f"球（半径 1.0、答えは {exact}）",
             "note": "polymesh の球。rows と cols を同じ数にした。"
                     "「何分の1」は、前の段の足りない分をこの段の足りない分で割った値。",
             "images": [{"path": "101_area.png",
                         "caption": "分割を倍にすると、足りない分は4分の1になる。"},
                        {"path": "101_ratio.png",
                         "caption": "減り方は4の前後。誤差は分割の2乗で減っている。"}],
             "per_row": 2,
             "columns": ["分割", "面", "面積", "足りない分", "％", "何分の1", "秒"],
             "rows": [[str(r["divs"]), f"{r['prims']:,}", f"{r['area']:.6f}",
                       f"{r['short']:.6f}", f"{r['short_pct']}%",
                       str(r["short_ratio"] or "—"), f"{r['seconds']:.3f}"]
                      for r in rows]},
        ],
        "notes": [
            f"<strong>平らな面はぴったり。</strong>1辺2.0の板は、分割 2 から 201 まで"
            f"どれも 4.000000。差は最大 {worst_grid:.9f} で、小数の丸めの範囲。",
            "<strong>球は必ず小さく出る。</strong>多角形が球の内側を通るので、"
            f"分割 8 で {rows[0]['short_pct']}%、分割 60 で {rows[3]['short_pct']}%、"
            f"分割 240 で {rows[-1]['short_pct']}% 足りない。",
            "<strong>足りない分は分割の2乗で減る。</strong>実測 "
            + " / ".join(str(r) for r in ratios)
            + "。分割を倍にすると4分の1になるので、細かくする効きは良い。",
        ],
        "next": [
            "曲率の測り（Curvature）も同じように収束するか",
            "体積の測りは、面積と同じ減り方をするか",
        ],
    })


def do_102():
    data = stats("102")
    rows = data["rows"]
    inset_rows = data["inset_rows"]
    worst = max(abs(r["diff"]) for r in rows)
    worst_inset = max(abs(r["diff"]) for r in inset_rows)

    line_chart(
        os.path.join(OUT, "102_extrude.png"),
        [{"label": "測った体積",
          "points": [(r["dist"], r["volume"]) for r in rows],
          "color": PALETTE[0]},
         {"label": "面積 × 距離 の式",
          "points": [(r["dist"], r["want"]) for r in rows],
          "color": PALETTE[2], "dash": True}],
        title="押し出した体積は、面積×距離とぴったり重なる",
        x_label="押し出す距離", y_label="体積")
    line_chart(
        os.path.join(OUT, "102_inset.png"),
        [{"label": "測った体積",
          "points": [(r["inset"], r["volume"]) for r in inset_rows],
          "color": PALETTE[0]},
         {"label": "四角錐台の式",
          "points": [(r["inset"], r["want"]) for r in inset_rows],
          "color": PALETTE[2], "dash": True}],
        title="Inset を入れても、四角錐台の式に合う",
        x_label="Inset（内側に寄せる幅）", y_label="体積")
    print("102_extrude.png 102_inset.png")

    write("102", {
        "title": "押し出した体積は式どおり — 面積×距離、Inset を入れても四角錐台の式に6桁一致",
        "summary":
            "polyextrude で平らな板を厚くすると、できる立体の体積は"
            "「元の面積 × 押し出した距離」になるはず。答えの分かっている形で"
            "突き合わせた。\n\n"
            f"1辺 {data['side']} の板（面積 {data['area']}）を 0.1 から 2.0 まで"
            f"押し出した。5通りすべてで差は {worst:.6f}。**式どおり。**\n\n"
            "Inset を入れると上の面が小さくなり、立体は四角錐台になる。"
            "1辺 L の正方形を i だけ内側に寄せると、上の1辺は L-2i。"
            "四角錐台の体積は d/3 × (L² + (L-2i)² + L(L-2i)) になる。\n\n"
            f"Inset を 0 から 0.9 まで（上の1辺 {inset_rows[0]['top_side']} から "
            f"{inset_rows[-1]['top_side']} まで）変えて測ったところ、"
            f"5通りすべてで差は {worst_inset:.6f}。**こちらも式どおり。**\n\n"
            f"Inset 0.9 では体積が {inset_rows[-1]['volume']} で、"
            f"Inset なしの {inset_rows[0]['volume']} に対して "
            f"{inset_rows[-1]['volume'] / inset_rows[0]['volume'] * 100:.1f}%。"
            "上の面をほとんど潰しても、体積は3分の1までしか減らない"
            "（錐に近づくので、底のぶんが残る）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": f"押し出す距離を変える（1辺 {data['side']}、面積 {data['area']}）",
             "note": "grid（1面）に polyextrude をかけ、前・後・側面のすべてを出した。"
                     "体積は measure の Volume を面ごとに足した値の絶対値。",
             "images": [{"path": "102_extrude.png",
                         "caption": "2本の線が完全に重なっている。"}],
             "per_row": 1,
             "columns": ["距離", "面", "体積", "面積×距離", "差", "秒"],
             "rows": [[f"{r['dist']:g}", str(r["prims"]), f"{r['volume']:.6f}",
                       f"{r['want']:.6f}", f"{r['diff']:+.6f}",
                       f"{r['seconds']:.3f}"] for r in rows]},
            {"label": f"Inset を変える（距離は {data['inset_dist']} で揃える）",
             "note": "上の1辺は 2.0 - 2×Inset。"
                     "四角錐台の式は d/3 × (L² + 上² + L×上)。",
             "images": [{"path": "102_inset.png",
                         "caption": "Inset を入れても、四角錐台の式の線に重なる。"}],
             "per_row": 1,
             "columns": ["Inset", "上の1辺", "体積", "四角錐台の式", "差",
                         "Insetなしとの差"],
             "rows": [[f"{r['inset']:g}", f"{r['top_side']:.2f}",
                       f"{r['volume']:.6f}", f"{r['want']:.6f}",
                       f"{r['diff']:+.6f}", f"{r['vs_prism']:+.6f}"]
                      for r in inset_rows]},
        ],
        "notes": [
            f"<strong>面積×距離で合う。</strong>5通りすべてで差は {worst:.6f}。"
            "押し出した体積を式で見積もれるので、重さや量の計算にそのまま使える。",
            f"<strong>Inset も四角錐台の式で合う。</strong>5通りすべてで差は "
            f"{worst_inset:.6f}。上の面が小さくなるぶんは、式のとおりに減る。",
            f"<strong>上の面を潰しても、体積は3分の1までしか減らない。</strong>"
            f"Inset 0.9（上の1辺 {inset_rows[-1]['top_side']}）で "
            f"{inset_rows[-1]['volume']}、Inset なしの "
            f"{inset_rows[-1]['volume'] / inset_rows[0]['volume'] * 100:.1f}%。"
            "錐に近づくので、底の面のぶんが残る。",
            "<strong>実験100と合わせて。</strong>peak は法線の向きに動かすので、"
            "角のある形では式が変わる（立方体は 1+2d/√3）。"
            "polyextrude は面の向きに押し出すので、面積×距離で素直に効く。"
            "厚みを付けたいだけなら polyextrude のほうが読みやすい。",
        ],
        "next": [
            "曲面（球の一部）を押し出したときは、どの式に合うか",
            "Divisions を入れて段を作ったとき、体積は変わらないか",
        ],
    })


if __name__ == "__main__":
    do_101()
    do_102()
