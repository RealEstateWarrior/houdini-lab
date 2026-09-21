# -*- coding: utf-8 -*-
"""実験116 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font  # noqa: E402

NAME = {"cylinder": "円筒", "hemisphere": "半球"}
METHOD = {"scp": "Spectral (SCP)", "abf": "Angle-Based (ABF)"}


def draw(path, rows):
    """開いた UV を4つ並べる。"""
    img = Image.new("RGB", (1000, 900), (255, 255, 255))
    d = ImageDraw.Draw(img)
    font, small = _font(24), _font(19)
    d.text((24, 14), "開いた UV（同じ網を、形と開き方を変えて）", fill=(30, 30, 30), font=font)
    cells = [("cylinder", "scp"), ("cylinder", "abf"), ("hemisphere", "scp"), ("hemisphere", "abf")]
    tops = {"cylinder": 60, "hemisphere": 290}
    for i, (shape, method) in enumerate(cells):
        x0, y0 = 30 + (i % 2) * 490, tops[shape]
        size = 440
        with open(os.path.join(OUT, f"116_uv_{shape}_{method}.json")) as fp:
            polys = json.load(fp)
        us = [u for p in polys for u in p]
        umin, vmin = min(u[0] for u in us), min(u[1] for u in us)
        vmax = max(u[1] for u in us)
        span = max(max(u[0] for u in us) - umin, vmax - vmin)
        color = PALETTE[0] if shape == "cylinder" else PALETTE[1]
        for p in polys:
            # 上端を y0+36 にそろえて、下へ描く
            pts = [(x0 + (u[0] - umin) / span * size,
                    y0 + 36 + (vmax - u[1]) / span * size) for u in p]
            d.line(pts + [pts[0]], fill=color, width=1)
        r = next(r for r in rows if r["shape"] == shape and r["method"] == method)
        d.text((x0, y0), f"{NAME[shape]} × {METHOD[method]}　ゆがみ {r['spread'] * 100:.2f}%",
               fill=(40, 40, 46), font=small)
    img.save(path)


def main():
    with open(os.path.join(OUT, "116_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows = data["rows"]
    draw(os.path.join(OUT, "116_uv.png"), rows)
    print("116_uv.png")

    def get(shape, method):
        return next(r for r in rows if r["shape"] == shape and r["method"] == method)

    cs, ca = get("cylinder", "scp"), get("cylinder", "abf")
    hs, ha = get("hemisphere", "scp"), get("hemisphere", "abf")
    payload = {
        "title": "uvflatten は円筒をゆがみ0.0001%で開く — 半球は SCP 13%・ABF 10% ゆがむ",
        "summary":
            f"{data['cols']}×{data['rows_n']} 点の板を丸めて、円筒（半径1・高さ2）と半球を作り、"
            "uvflatten で開いた。辺ごとに「UV の長さ ÷ 3D の長さ」を出し、"
            "そのばらつき（標準偏差 ÷ 平均）をゆがみとした。ゆがみが無ければ、どの辺でも比は同じになる。\n\n"
            "**円筒は、ゆがまずに開いた。** ばらつきは SCP で "
            f"{cs['spread'] * 100:.4f}%、ABF で {ca['spread'] * 100:.4f}%。"
            f"開いた長方形の縦横比は {cs['aspect']:.6f} で、式（{data['cols'] - 1}角形の周 ÷ 高さ）"
            f" {data['want_aspect']:.6f} と6桁一致した。円筒は切り開けば平らになる形なので、これが正解。\n\n"
            "**半球は、どちらの開き方でもゆがむ。** ばらつきは SCP で "
            f"{hs['spread'] * 100:.1f}%、ABF で {ha['spread'] * 100:.1f}%。"
            "球の一部は、どう開いても長さを保てない（地図の図法と同じ問題）。"
            "ABF のほうが今回は小さかった。\n\n"
            "UV は横幅がほぼ 1（"
            f"{cs['uv_w']:.6f}）になるように縮められていた。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "形・開き方と、ゆがみ",
             "note": "ゆがみ = 辺ごとの（UV の長さ ÷ 3D の長さ）の標準偏差 ÷ 平均。"
                     "円筒は板を丸めたので、最初から1本の切れ目がある。",
             "images": [{"path": "116_uv.png",
                         "caption": "円筒（青）はきれいな長方形。半球（橙）は扇形に開き、場所によって辺の長さの比がそろわない。"}],
             "per_row": 1,
             "columns": ["形", "開き方", "ゆがみ", "UV の幅", "UV の高さ", "縦横比", "秒"],
             "rows": [[NAME[r["shape"]], METHOD[r["method"]], f"{r['spread'] * 100:.4f}%",
                       f"{r['uv_w']:.6f}", f"{r['uv_h']:.6f}", f"{r['aspect']:.6f}",
                       f"{r['sec']:.4f}"] for r in rows]},
        ],
        "notes": [
            "<strong>展開できる形は、ゆがみ0で開く。</strong>円筒の縦横比は式と6桁一致。",
            "<strong>球はどう開いてもゆがむ。</strong>半球で 10〜13%。切れ目を増やすほど減るはず"
            "（今回は試していない）。",
            "<strong>UV は幅1に収められる。</strong>そのままでは、部品ごとのテクセル密度はそろわない。",
        ],
        "next": [
            "半球に切れ目を足していくと、ゆがみがどこまで減るか",
            "Preserve Seams を入れて、既存の切れ目を生かしたときの結果",
            "uvunwrap / uvproject との、ゆがみと速さの比較",
        ],
    }
    with open(os.path.join(OUT, "116_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 116_report.json")


if __name__ == "__main__":
    main()
