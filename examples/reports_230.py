# -*- coding: utf-8 -*-
"""実験230 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

LAB = {"obj_rot_2": "オブジェクトで回す・Rotation Blur・2", "obj_lin_2": "オブジェクト・Linear Blur・2", "obj_lin_8": "オブジェクト・Linear Blur・8",
       "sop_2": "SOP で回す・Geometry 2", "sop_4": "SOP・Geometry 4", "sop_8": "SOP・Geometry 8", "sop_16": "SOP・Geometry 16"}


def main():
    with open(os.path.join(OUT, "230_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    font = _font(14)
    shots = ["obj_rot_2", "obj_lin_2", "sop_2", "sop_8"]
    sheet = Image.new("RGB", (400 * 4, 400 + 44), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(shots):
        sheet.paste(Image.open(os.path.join(OUT, f"230_{k}.png")).convert("RGB"), (i * 400, 44))
        dr.text((i * 400 + 6, 4), LAB[k], fill=(30, 30, 30), font=font)
        dr.text((i * 400 + 6, 22), f"内側 {t[k]['r_p5']:.2f} m・平均 {t[k]['r_mean']:.2f} m", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "230_grid.png"))
    table = [[LAB[k], str(r["xformsamples"]), r["blurstyle"], str(r["geosamples"]), f"{r['r_mean']:.3f}", f"{r['r_p5']:.3f}", f"{r['span_deg']:.1f}", f"{r['sec']:.2f}"]
             for k, r in t.items()]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": "速く回る物のブレは、オブジェクトごと回すなら既定（Rotation Blur・2 サンプル）で弧になる。"
                 "SOP で形を回すと既定の Geometry Time Samples 2 ではまっすぐな線になり、8 で弧になる。時間はほぼ同じ",
        "summary":
            "**課題: 扇風機の羽や車輪のように速く回る物をモーションブラーで撮ると、ブレが弧ではなく、まっすぐな線になることがある。"
            "Karma の Transform Time Samples（既定 2）・Motion Blur Style（既定 Rotation Blur）・Geometry Time Samples（既定 2）の、どれをいくつにすればよいか。**\n\n"
            "中心から 1 m の所に半径 5 cm の光る球を置き、1 フレームで 180° 回した。カメラのシャッターは既定の 0.5 フレームなので、本物なら 90° の弧のブレになる。"
            "真正面から平行投影（幅 3 m）で 400×400・64 サンプルで撮り、ブレの筋の画素が中心からどれだけ離れているかを測った（右下の透かしは除いた）。"
            "弧ならどこも 1 m。まっすぐな線（弦）なら、真ん中が 0.71 m まで内側に寄る。\n\n"
            f"**オブジェクトごと回すなら、既定のままで弧になる。**Transform Time Samples 2・Rotation Blur で、筋の中心からの距離は平均 {g('obj_rot_2', 'r_mean'):.2f} m、"
            f"いちばん内側（5 パーセンタイル）{g('obj_rot_2', 'r_p5'):.2f} m。Linear Blur にすると平均 {g('obj_lin_2', 'r_mean'):.2f} m・内側 {g('obj_lin_2', 'r_p5'):.2f} m で弦になり、"
            f"Transform Time Samples を 8 にすると {g('obj_lin_8', 'r_mean'):.2f} m・{g('obj_lin_8', 'r_p5'):.2f} m で弧に戻った。\n\n"
            f"**SOP で形を回すと、既定では弦になる。**オブジェクトは止めて、中の transform（SOP）で回すと、Rotation Blur は効かない。"
            f"Geometry Time Samples 2・4・8・16 で、いちばん内側は {g('sop_2', 'r_p5'):.2f}・{g('sop_4', 'r_p5'):.2f}・{g('sop_8', 'r_p5'):.2f}・{g('sop_16', 'r_p5'):.2f} m。"
            "4 でほぼ弧、8 で弧（オブジェクトで回したときと同じ）になった。シャッターの間の回転 90° を 7 区間に分けると、1 区間 13° になる。\n\n"
            f"**時間はほとんど変わらない。**どの条件も {min(r['sec'] for r in t.values()):.1f}〜{max(r['sec'] for r in t.values()):.1f} 秒。\n\n"
            "**決め方: 回る物は、できればオブジェクトの回転で動かす（既定で弧になる）。**SOP やシミュレーションで回すなら、Geometry Time Samples を、"
            "シャッターの間の回転を 15° 以下の区間に分けられる数にする（この例の 90° なら 8）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "回し方とサンプル数と、ブレの形（90° の弧になるはず）",
             "images": [{"path": "230_grid.png", "caption": "左から: オブジェクト・Rotation Blur 2（弧）、Linear Blur 2（弦）、SOP・Geometry 2（弦）、SOP・Geometry 8（弧）。"}],
             "per_row": 1, "columns": ["回し方", "Transform Samples", "Blur Style", "Geometry Samples", "距離 平均（m）", "いちばん内側（m）", "広がり（°）", "時間（秒）"],
             "rows": table},
        ],
        "notes": [
            "<strong>オブジェクトごと回すなら、既定（Rotation Blur・2 サンプル）で弧になる。</strong>",
            f"<strong>SOP で回すと、Geometry Time Samples 2 ではまっすぐな線（内側 {g('sop_2', 'r_p5'):.2f} m）。8 で弧。</strong>",
            "<strong>サンプル数を上げても、時間はほとんど変わらない。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "230_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
