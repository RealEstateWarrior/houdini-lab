# -*- coding: utf-8 -*-
"""実験201 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "201_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    with open(os.path.join(OUT, "201_shape.json"), encoding="utf-8") as fp:
        shape = json.load(fp)
    by = {r["case"]: r for r in d["rows"]}
    line_chart(os.path.join(OUT, "201_height.png"),
               [{"label": lab, "points": [(x["f"], x["flame"]["height"]) for x in by[c]["per_frame"]], "color": PALETTE[i]}
                for i, (c, lab) in enumerate((("life2", "既定（Lifespan 2）"), ("life05", "Lifespan 0.5"), ("life025", "Lifespan 0.25"),
                                              ("l025b025c1", "0.25＋Buoyancy 0.25＋Cooling 1"), ("fire_turb3", "↑＋Turbulence 3")))],
               title="Pyro の焚き火（薪の幅 0.6）: 炎の高さ（上から 1% の点）", x_label="フレーム", y_label="高さ（m）")
    h = lambda c: by[c]["height_mean"]
    io = lambda c: shape[c]["iou_48_72"]
    payload = {
        "title": "Pyro で焚き火の炎（高さ 1.2 m）を作るなら Flame Lifespan 0.25・Buoyancy 0.25・Cooling Rate 1 — 揺らすのは Turbulence で、Use Control Field を切る",
        "summary":
            "**課題: 焚き火くらいの炎（高さ 1 m 前後で揺れる）にするには、Pyro のどのつまみを動かすか。**\n\n"
            "幅 0.6・厚み 0.18 の薪（平たい球）を pyrosource の Initialize = Source Burn で燃やし、pyrosolver（SOP、Voxel Size 0.04）で 72 フレーム（3 秒）回した。"
            "炎（flame > 0.1）の上から 1% の点の高さを毎フレーム測り、フレーム 36〜72 の平均を「落ち着いた高さ」とした。"
            "炎を正面に投影した画から、輪郭の入り組み具合（縁の長さ ÷ 面積の平方根）と、フレーム 48 と 72 の形の重なり（IoU、低いほどよく動く）も出した。\n\n"
            f"**既定のままでは焚き火にならない。**炎は 1 秒に約 {by['life2']['rise_speed']:.0f} m で伸び、3 秒たっても平均 {h('life2'):.1f} m の柱のまま。\n\n"
            "**高さは3つのつまみで決まる。1つずつ変えた結果:**"
            f" Flame Lifespan（既定 2 秒）を 1・0.5・0.25 にすると {h('life1'):.1f}・{h('life05'):.1f}・{h('life025'):.1f} m。"
            f" Lifespan 0.5 のまま Buoyancy Scale を 0.5・0.25 にすると {h('buoy05'):.1f}・{h('buoy025'):.1f} m。"
            f" Cooling Rate を 0.75・1 にすると {h('cool075'):.1f}・{h('cool1'):.2f} m で、1.5・2 も {h('cool15'):.2f}・{h('cool2'):.2f} m と 1 と同じ（1 以上は効かない）。\n\n"
            f"**組み合わせると 1 m 前後になる。**Lifespan 0.25・Buoyancy 0.25・Cooling 1 で {h('l025b025c1'):.2f} m、Buoyancy を 0.1 にすると {h('l025b01c1'):.2f} m。\n\n"
            f"**ただしそのままでは炎が止まって見える。**形の重なり（IoU）は {io('l025b025c1'):.3f}（既定の柱でも {io('life2'):.3f}）。揺らす仕組みを入れて比べた:"
            f" Disturbance（既定の強さ・5）で {io('l025b025c1_dist'):.3f}・{io('fire_dist5'):.3f}、Shredding 2 で {io('fire_shred2'):.3f}、"
            f"Turbulence 1・3（Use Control Field を切る）で {io('fire_turb1'):.3f}・{io('fire_turb3'):.3f}。"
            f"輪郭の入り組み具合も Turbulence 3 が {shape['fire_turb3']['rough48']:.2f} と一番大きい（揺らす前は {shape['l025b025c1']['rough48']:.2f}）。"
            f"Turbulence 3 を入れても高さは {h('fire_turb3'):.2f} m にとどまった。\n\n"
            "**Turbulence を入れても効かなかったのは、Use Control Field のせい。**"
            f"既定（Use Control Field 入、制御する場は density）のまま Turbulence を 1 にしても、高さ {h('fire_turb1_ctrl'):.3f} m・IoU {io('fire_turb1_ctrl'):.3f} と、入れる前と小数 3 桁まで同じ。"
            f"切ると {h('fire_turb1'):.3f} m・IoU {io('fire_turb1'):.3f} に変わった。\n\n"
            f"**時間は炎が小さいほど短い。**既定 {by['life2']['sec']:.1f} 秒に対し、焚き火の設定は {by['l025b025c1']['sec']:.1f} 秒、Turbulence 3 を足して {by['fire_turb3']['sec']:.1f} 秒（72 フレーム）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "炎を正面に投影した画（上がフレーム48、下がフレーム72）",
             "images": [{"path": "201_grid.png", "caption": "左から 既定・Lifespan 0.25・焚き火の設定・＋Disturbance 5・＋Turbulence 3・＋3つとも。"}],
             "per_row": 1, "columns": [], "rows": []},
            {"label": "条件と、炎の高さ・動き",
             "images": [{"path": "201_height.png", "caption": "既定は伸び続ける。Lifespan と Buoyancy・Cooling で 1 m 台に収まる。"}],
             "per_row": 1,
             "columns": ["条件", "落ち着いた高さ（m）", "高さの揺らぎ（m）", "伸びる速さ（m/秒）", "形の重なり F48–72", "輪郭の入り組み", "秒"],
             "rows": [[c, f"{by[c]['height_mean']:.2f}", f"{by[c]['height_std']:.3f}", f"{by[c]['rise_speed']:.1f}",
                       f"{shape[c]['iou_48_72']:.3f}", f"{shape[c]['rough48']:.2f}", f"{by[c]['sec']:.1f}"] for c in by]},
        ],
        "notes": [
            "<strong>焚き火の高さ（1 m 台）は Flame Lifespan 0.25・Buoyancy Scale 0.25・Cooling Rate 1。</strong>既定の Lifespan 2 秒では、炎が柱になって伸び続ける。",
            "<strong>Cooling Rate は 1 より上げても変わらない。</strong>",
            "<strong>炎を揺らすのは Turbulence（1〜3）。</strong>Disturbance と Shredding は輪郭を少し乱すだけで、炎全体はあまり動かない。",
            "<strong>Turbulence が効かないときは Use Control Field を切る。</strong>既定のまま（制御する場 density）だと、強さを上げても何も変わらなかった。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "201_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 201_report.json")


if __name__ == "__main__":
    main()
