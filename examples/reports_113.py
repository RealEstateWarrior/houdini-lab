# -*- coding: utf-8 -*-
"""実験113 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "113_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows, fps = data["rows"], data["fps"]
    lin_ok = max(abs(r["blend"] - r["linear"]) for r in rows)
    v_err = max(abs(r["blend_v"] - r["true"]) for r in rows)
    lin_err = max(abs(r["blend"] - r["true"]) for r in rows)
    wrong_err = max(abs(r["blend_wrongv"] - r["true"]) for r in rows)

    line_chart(
        os.path.join(OUT, "113_blend.png"),
        [{"label": "速度なし（直線でつなぐ）",
          "points": [(r["frame"], r["blend"] - r["true"]) for r in rows], "color": PALETTE[1]},
         {"label": "速度あり（1秒あたりの v）",
          "points": [(r["frame"], r["blend_v"] - r["true"]) for r in rows], "color": PALETTE[0]},
         {"label": "速度あり（v を1フレームあたりで入れた）",
          "points": [(r["frame"], r["blend_wrongv"] - r["true"]) for r in rows],
          "color": PALETTE[3], "dash": True}],
        title="y = F² の点を timeblend でつないだときの、本当の値とのずれ",
        x_label="フレーム", y_label="ずれ（timeblend − F²）")
    print("113_blend.png")

    payload = {
        "title": "timeblend は速度が無ければ直線、あれば F² を誤差0でつなぐ — v は「1秒あたり」",
        "summary":
            "点を1つ、高さ y = F²（F はフレーム）で動かし、timeblend で整数フレームの間"
            "（1.25・1.5・3.3 など）を作らせた。整数フレームの形だけから直線でつなぐなら、"
            "1.5 フレームでは (1+4)/2 = 2.5 になる（本当は 2.25）。\n\n"
            f"**速度が無いと、直線でつなぐ。** 8通りすべてで直線の式と一致（差 {lin_ok:.6f}）。"
            f"本当の値からは最大 {lin_err:.3f} ずれた。\n\n"
            "**速度 v を持たせて Use Velocity When Interpolating Position を入れると、"
            f"F² をぴったり再現した**（ずれ最大 {v_err:.6f}）。"
            "両端の位置と速度を使う3次のつなぎ方（エルミート補間）なら2次式は誤差0になるので、"
            "それと合う。\n\n"
            f"**v は1秒あたりの速さとして読まれる。** 2F×{fps:g}（fps）を入れたときに合った。"
            "fps を掛け忘れて1フレームあたりの値（2F）を入れると、"
            f"ずれは最大 {wrong_err:.3f} で、速度なし（{lin_err:.3f}）より悪くなることもある。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "フレームと高さ（y = F²）",
             "note": f"fps = {fps:g}。v は attribwrangle で毎フレーム入れた。"
                     "Hold First Frame は切った。",
             "images": [{"path": "113_blend.png",
                         "caption": "青（1秒あたりの v）はずれ0。橙（速度なし）は整数フレームの間でふくらむ。"}],
             "per_row": 1,
             "columns": ["フレーム", "本当の値 F²", "速度なし", "直線の式",
                         "速度あり", "v を1フレームあたり"],
             "rows": [[f"{r['frame']:g}", f"{r['true']:.6f}", f"{r['blend']:.6f}",
                       f"{r['linear']:.6f}", f"{r['blend_v']:.6f}",
                       f"{r['blend_wrongv']:.6f}"] for r in rows]},
        ],
        "notes": [
            "<strong>速度が無ければ直線。</strong>曲がって動くものは、フレームの間で近道する"
            f"（F² では最大 {lin_err:.2f}）。",
            "<strong>速度を渡せば、2次の動きは誤差0。</strong>Use Velocity When Interpolating Position を入れる。",
            f"<strong>v は1秒あたり。</strong>{fps:g} fps なら、1フレームあたりの動き×{fps:g}。"
            "間違えると、速度なしより悪くなる。",
            "<strong>今回は点に id=0 を入れた。</strong>id が無い場合は試していない。",
        ],
        "next": [
            "id が無い／点の数がフレームで変わるとき、timeblend はどうするか",
            "回転（orient）を Smoothly Interpolate で補うと、角度はどうつながるか",
            "モーションブラー（サブフレームのレンダ）に timeblend を挟んだときの見た目",
        ],
    }
    with open(os.path.join(OUT, "113_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 113_report.json")


if __name__ == "__main__":
    main()
