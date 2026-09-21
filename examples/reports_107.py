# -*- coding: utf-8 -*-
"""実験107 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font  # noqa: E402

METHOD = {"com": "Center of Mass", "bbox": "Bounding Box Center",
          "convexhull": "Convex Hull Center"}
SHAPE = {"L": "L字の板（開いた面1枚）", "pyramid": "四角錐（閉じている）",
         "open_pyramid": "底の無い四角錐（開いている）", "L_prism": "L字の柱（閉じている）"}
ANSWER = {"point_avg": "点の平均", "bbox": "箱の中心", "area": "面積の中心",
          "volume": "体積の中心", "hull_volume": "凸包の体積の中心"}


def draw_top_view(path, rows):
    """L字の柱を上から見て、3つの Method の答えを置く。"""
    size, pad, unit = (1000, 620), 90, 220
    img = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(img)
    ox, oy = pad + 40, size[1] - pad

    def xy(x, z):
        return ox + x * unit, oy - z * unit

    hull = [(0, 0), (2, 0), (2, 1), (1, 2), (0, 2)]
    d.polygon([xy(*p) for p in hull], outline=(170, 170, 178), fill=(244, 244, 247))
    lshape = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)]
    d.polygon([xy(*p) for p in lshape], outline=(60, 60, 70), fill=(222, 232, 245))
    font, small = _font(26), _font(20)
    d.text((pad, 24), "L字の柱を上から見た図。3つの Method で、中心の置き場所がちがう", fill=(30, 30, 30), font=font)
    d.text(xy(1.35, 1.72), "凸包は灰色の所まで", fill=(120, 120, 128), font=small)
    got = {r["method"]: r["got"] for r in rows if r["shape"] == "L_prism" and r["class"] == "prim"}
    colors = {"com": PALETTE[0], "bbox": PALETTE[1], "convexhull": PALETTE[2]}
    legend_y = 110
    for method, pos in got.items():
        cx, cy = xy(pos[0], pos[2])
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=colors[method])
        lx = 640
        d.ellipse([lx, legend_y + 6, lx + 16, legend_y + 22], fill=colors[method])
        d.text((lx + 26, legend_y), f"{METHOD[method]}", fill=(30, 30, 30), font=small)
        d.text((lx + 26, legend_y + 26), f"({pos[0]:.6f}, {pos[2]:.6f})", fill=(90, 90, 96), font=small)
        legend_y += 70
    for v in (0, 1, 2):
        d.text((xy(v, 0)[0] - 6, oy + 10), str(v), fill=(90, 90, 96), font=small)
        d.text((ox - 30, xy(0, v)[1] - 12), str(v), fill=(90, 90, 96), font=small)
    img.save(path)


def main():
    with open(os.path.join(OUT, "107_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows = data["rows"]
    prim_rows = [r for r in rows if r["class"] == "prim"]
    same_class = all(
        r["got"] == next(x["got"] for x in rows if x["shape"] == r["shape"]
                         and x["method"] == r["method"] and x["class"] == "point")
        for r in prim_rows)
    draw_top_view(os.path.join(OUT, "107_centroid.png"), rows)
    print("107_centroid.png")

    def got(shape, method):
        return next(r["got"] for r in prim_rows if r["shape"] == shape and r["method"] == method)

    payload = {
        "title": "extractcentroid の Center of Mass は、閉じていれば体積・開いていれば面積の中心",
        "summary":
            "「中心」には何通りもある。点の平均、囲む箱の中心、面積の中心、体積の中心。"
            "形によっては全部ちがう値になる。答えが計算で出る4つの形を作り、"
            "extractcentroid の Method ごとに出てくる値を式と突き合わせた。\n\n"
            "**Center of Mass は、閉じた形なら体積の中心、開いた形なら面積の中心。** "
            f"四角錐（閉じている）では y={got('pyramid', 'com')[1]:g}（体積の中心 3/4）、"
            f"底を抜くと y={got('open_pyramid', 'com')[1]:g}（側面の面積の中心）。"
            f"L字の板では ({got('L', 'com')[0]:.6f}, {got('L', 'com')[2]:.6f})"
            "（面積の中心 5/6）。点の平均ではない。\n\n"
            "**Bounding Box Center は、囲む箱の真ん中。** 四角錐なら y=1.5 で、"
            "形の重さのある所からいちばん離れる。\n\n"
            "**Convex Hull Center は、凸包（へこみを埋めた外形）の体積の中心。** "
            f"L字の柱では ({got('L_prism', 'convexhull')[0]:.6f}, …) で、式 19/21 と一致。"
            "底を抜いた四角錐でも、凸包は底をふさいだ形になるので y=0.75。"
            "平らな L字の板では凸包に体積が無く、(1, 1) が出た"
            "（点の平均とも箱の中心とも同じ値なので、どちらに倒れたのかは確かめていない）。\n\n"
            f"Piece Elements を Primitive にしても Point にしても、結果は{'同じ' if same_class else '違った'}。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "形と Method ごとの中心（式と一致したものを右に書く）",
             "note": "Run Over = Detail（形全体で1つ）、Output = Points。"
                     "四角錐は底 2×2・高さ3、L字は 2×2 から 1×1 の角を欠いたもの、柱は高さ1。",
             "images": [{"path": "107_centroid.png",
                         "caption": "L字の柱を上から。Center of Mass（青）は本当の体積の中心、"
                                    "Convex Hull（緑）は灰色まで含めた外形の中心、Bounding Box（橙）は箱の真ん中。"}],
             "per_row": 1,
             "columns": ["形", "Method", "出た中心", "一致した式"],
             "rows": [[SHAPE[r["shape"]], METHOD[r["method"]],
                       "(" + ", ".join(f"{v:g}" for v in r["got"]) + ")",
                       "・".join(ANSWER[m] for m in r["match"]) or "—"]
                      for r in prim_rows]},
        ],
        "notes": [
            "<strong>Center of Mass は「形の中身」の中心。</strong>閉じていれば体積、"
            "開いていれば面積で重みを付ける。点の平均ではない"
            "（点が片寄った形では試していない）。",
            "<strong>Bounding Box Center は、先が尖った形ほど外れる。</strong>四角錐で y=1.5"
            "（体積の中心 0.75 の2倍の高さ）。",
            "<strong>Convex Hull Center は、へこみを埋めた形の中心。</strong>L字の柱で 19/21≒0.905。"
            "開いた形でもふさいだ形として扱う。",
            "<strong>Primitive / Point の切り替えは、Detail で回すときは結果を変えない。</strong>",
        ],
        "next": [
            "点がかたよった形（片側だけ細かく割った箱）でも Center of Mass が動かないか",
            "Run Over = Pieces で、破片ごとの中心が1つずつ正しく出るか",
            "RBD の重心（center of mass）と extractcentroid の値が一致するか",
        ],
    }
    with open(os.path.join(OUT, "107_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 107_report.json")


if __name__ == "__main__":
    main()
