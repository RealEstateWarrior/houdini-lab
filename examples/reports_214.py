# -*- coding: utf-8 -*-
"""実験214 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font, line_chart  # noqa: E402


def main():
    with open(os.path.join(OUT, "214_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows = d["rows"]
    f, s, dist, ap, resx = d["focal_mm"], d["focus_m"] * 1000, d["dist_m"] * 1000, d["aperture_mm"], d["res"][0]
    blur = [r for r in rows if r["tag"] != "sharp"]
    for r in blur:
        r["s_form_px"] = round(f * f * (dist - s) / (r["fstop"] * dist * s) / ap * resx, 2)
    worst_s = max(abs(r["blur_diameter_px"] / r["s_form_px"] - 1) for r in blur)
    ratio_thin = [r["blur_diameter_px"] / r["formula_px"] for r in blur]
    # 図 1: ぼけた球（真ん中を切り出して 2 倍）
    font = _font(15)
    tags = ["sharp"] + [r["tag"] for r in blur]
    size = 220
    im = Image.new("RGB", (size * len(tags), size + 26), (10, 10, 12))
    dr = ImageDraw.Draw(im)
    for i, tg in enumerate(tags):
        p = Image.open(os.path.join(OUT, f"214_{tg}.png")).convert("RGB").crop((265, 125, 375, 235)).resize((size, size), Image.NEAREST)
        im.paste(p, (i * size, 26))
        lab = "ピントを球に" if tg == "sharp" else f"F-Stop {tg[1:]}"
        dr.text((i * size + 8, 4), lab, fill=(230, 230, 230), font=font)
    im.save(os.path.join(OUT, "214_blur.png"))
    line_chart(os.path.join(OUT, "214_chart.png"),
               [{"label": "測ったぼけの直径", "points": [(r["fstop"], r["blur_diameter_px"]) for r in blur], "color": PALETTE[0]},
                {"label": "写真の薄いレンズの式", "points": [(r["fstop"], r["formula_px"]) for r in blur], "color": PALETTE[1]},
                {"label": "f²(d−s)/(N·d·s) の式", "points": [(r["fstop"], r["s_form_px"]) for r in blur], "color": PALETTE[2]}],
               title="F-Stop と、背景のぼけの直径（640 画素の画）", x_label="F-Stop", y_label="直径（画素）")
    table = [[f"{r['fstop']:g}", f"{r['blur_diameter_px']:.2f}", f"{r['formula_px']:.2f}", f"{r['blur_diameter_px'] / r['formula_px']:.3f}",
              f"{r['s_form_px']:.2f}", f"{r['blur_diameter_px'] / r['s_form_px']:.3f}", f"{r['total']:.0f}"] for r in blur]
    sharp = rows[0]
    ex = 50 * 50 / (2.8 * 5000 * ap) * 1920
    payload = {
        "title": f"Karma のぼけの大きさは f²(d−s)/(N·d·s) に {worst_s:.1%} 以内で一致 — F を半分にすると直径は倍。写真の薄いレンズの式より約 {1 - sum(ratio_thin) / len(ratio_thin):.0%} 小さい",
        "summary":
            "**課題: 実験205 で、F-Stop 0.7 でも背景があまりぼけなかった。狙った大きさのぼけにするには、F-Stop・焦点距離・ピントの距離をどう決めればよいのか。Houdini のカメラの数字は、写真のレンズの式どおりに効くのか。**\n\n"
            f"真っ暗な中に光る球（半径 {d['ball_radius_m'] * 100:.0f} cm）を置き、焦点距離 {f:g} mm・Aperture {ap:.4f} mm のカメラを {d['dist_m']:g} m 手前に置いた。"
            f"ピントは {d['focus_m']:g} m で、球はピントより {d['dist_m'] - d['focus_m']:g} m 奥にある。F-Stop を 1〜16 にして {d['res'][0]}×{d['res'][1]} で撮り（Enable Depth of Field）、"
            "EXR を OpenImageIO で読んで、ぼけた円盤の大きさを測った。測り方は、明るさで重みを付けた中心からの距離の二乗平均（一様な円盤なら直径 = 2√2 × この値）。"
            "ピントを球に合わせた画も撮り、球そのものの大きさの分を差し引いた（広がりは二乗で足し算になる）。\n\n"
            f"**ぼけの直径は F-Stop に反比例する。**F 1・2・4・8・16 で {' ・'.join(f'{r['blur_diameter_px']:.1f}' for r in blur)} 画素。F を倍にすると、ちょうど半分になった。\n\n"
            f"**写真の薄いレンズの式（(f/N)·f·(d−s)/(d·(s−f))）より、どれも約 {1 - sum(ratio_thin) / len(ratio_thin):.0%} 小さい**（比 {min(ratio_thin):.3f}〜{max(ratio_thin):.3f}）。"
            f"式の (s − f) を s に替えた f²(d−s)/(N·d·s) とは、{worst_s:.1%} 以内で一致した。ピントの距離 {d['focus_m']:g} m に対して焦点距離 {f / 1000:g} m の分（5%）の違いで、"
            "ピントが遠いほど、2 つの式の差は小さくなる。\n\n"
            f"**ぼけても、光の量は変わらない。**窓の中の明るさの合計は {min(r['total'] for r in rows):.0f}〜{max(r['total'] for r in rows):.0f} で、ぼけた分だけ円盤は暗くなる"
            f"（いちばん明るい画素は、ピントが合うと {sharp['peak']:.1f}、F 1 で {blur[0]['peak']:.2f}）。\n\n"
            "**目安の式: 遠くの背景のぼけの直径（画素）≒ 焦点距離² ÷ (F-Stop × ピントの距離 × Aperture) × 画の横の画素数**（長さは mm でそろえる。背景がピントよりずっと遠いとき）。"
            f"たとえば焦点距離 50 mm・ピント 5 m・F 2.8・1920 画素なら、この式で約 {ex:.1f} 画素（式から出した値。撮っては確かめていない）。"
            "式からは、ぼけを大きくするには焦点距離を上げる（2 乗で効く）かピントを近づけるのが効くと言える（この実験で変えたのは F-Stop だけ）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "F-Stop を変えたぼけ（真ん中を 2 倍に拡大）",
             "images": [{"path": "214_blur.png", "caption": "左端はピントを球に合わせた画。F を上げるほど円盤が小さく、明るくなる。"},
                        {"path": "214_chart.png", "caption": "測った直径（青）は、f²(d−s)/(N·d·s)（緑）とほぼ重なる。薄いレンズの式（橙）より少し小さい。"}],
             "per_row": 1,
             "columns": ["F-Stop", "測った直径（画素）", "薄いレンズの式", "比", "f²(d−s)/(N·d·s)", "比", "明るさの合計"], "rows": table},
        ],
        "notes": [
            "<strong>ぼけの直径は F-Stop に反比例する。</strong>F を半分にすると直径は倍。",
            f"<strong>Karma のぼけは f²(d−s)/(N·d·s) の式どおり（{worst_s:.1%} 以内）。</strong>写真の薄いレンズの式より約 5% 小さい（ピント 2 m・焦点距離 100 mm のとき）。",
            "<strong>式からは、焦点距離が 2 乗で効く。</strong>ぼけを大きくしたいなら焦点距離かピントの距離を変える（この実験で変えたのは F-Stop だけ）。",
            "<strong>ぼけても光の量は変わらない。</strong>円盤が広がるぶん暗くなる。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "214_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 214_report.json")
    print(payload["title"], [r["s_form_px"] for r in blur], ex)


if __name__ == "__main__":
    main()
