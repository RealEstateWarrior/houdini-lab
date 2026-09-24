# -*- coding: utf-8 -*-
"""実験222 の図とレポートを、測った値から組み立てる（前半 222_stats.json、後半 222_lop.json）。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font, line_chart  # noqa: E402


def main():
    with open(os.path.join(OUT, "222_stats.json"), encoding="utf-8") as fp:
        a = {r["case"]: r for r in json.load(fp)["rows"]}
    with open(os.path.join(OUT, "222_lop.json"), encoding="utf-8") as fp:
        b = {r["case"]: r for r in json.load(fp)["rows"]}
    with open(os.path.join(OUT, "215_stats.json"), encoding="utf-8") as fp:
        c = {r["case"]: r for r in json.load(fp)["rows"]}
    s = lambda d, k: d[k]["sec"]  # noqa: E731
    # 図 1: 本数と時間（/obj の Karma と、LOP のポイントインスタンサー）
    obj_pts = [(1, s(c, "packed_1e3")), (10, s(a, "big_packed_10k")), (30, s(a, "big_packed_30k")), (100, s(c, "inst_1e5"))]
    lop_pts = [(10, s(b, "lop_pointinstancer_10k")), (30, s(b, "lop_pointinstancer_30k")), (100, s(b, "lop_pointinstancer_100k")),
               (1000, s(b, "lop_pointinstancer_1000k"))]
    line_chart(os.path.join(OUT, "222_time.png"),
               [{"label": "/obj の Karma（10 万本の点だけ usdinstancerpath 付き）", "points": obj_pts}, {"label": "LOP の sopimport（ポイントインスタンサー）", "points": lop_pts}],
               "草の本数と撮る時間（640×360・8 サンプル）", "本数（千本）", "撮る時間（秒）")
    # 図 2: 画を並べる
    font = _font(16)
    w, h = 640, 360
    shots = [("222_big_packed_30k.png", f"/obj の Karma・3 万本  {s(a, 'big_packed_30k'):.1f} 秒"),
             ("222_lop_pointinstancer_30k.png", f"LOP・ポイントインスタンサー・3 万本  {s(b, 'lop_pointinstancer_30k'):.1f} 秒"),
             ("222_lop_pointinstancer_100k.png", f"LOP・10 万本  {s(b, 'lop_pointinstancer_100k'):.1f} 秒"),
             ("222_lop_pointinstancer_1000k.png", f"LOP・100 万本  {s(b, 'lop_pointinstancer_1000k'):.1f} 秒")]
    sheet = Image.new("RGB", (w * 2, (h + 30) * 2), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (f, cap) in enumerate(shots):
        x, y = (i % 2) * w, (i // 2) * (h + 30)
        im = Image.open(os.path.join(OUT, f)).convert("RGBA")
        bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
        sheet.paste(Image.alpha_composite(bg, im).convert("RGB"), (x, y + 30))
        dr.text((x + 8, y + 6), cap, fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "222_grid.png"))
    table = [["/obj の Karma", "パックしたまま", "1 万", f"{s(a, 'big_packed_10k'):.1f}", f"{s(a, 'tiny_packed_10k'):.1f}"],
             ["/obj の Karma", "パックしたまま", "3 万", f"{s(a, 'big_packed_30k'):.1f}", f"{s(a, 'tiny_packed_30k'):.1f}"],
             ["/obj の Karma", "usdinstancerpath", "3 万", f"{s(a, 'big_inst_30k'):.1f}", f"{s(a, 'tiny_inst_30k'):.1f}"],
             ["/obj の Karma", "パックしたまま（色 Cd を消す）", "3 万", f"{s(a, 'big_nocd_packed_30k'):.1f}", "—"],
             ["/obj の Karma", "usdinstancerpath（実験215）", "10 万", f"{s(c, 'inst_1e5'):.1f}", "—"],
             ["LOP の sopimport", "Create Point Instancer", "1 万", f"{s(b, 'lop_pointinstancer_10k'):.1f}", "—"],
             ["LOP の sopimport", "Create Point Instancer", "3 万", f"{s(b, 'lop_pointinstancer_30k'):.1f}", "—"],
             ["LOP の sopimport", "Create Point Instancer", "10 万", f"{s(b, 'lop_pointinstancer_100k'):.1f}", "—"],
             ["LOP の sopimport", "Create Point Instancer", "100 万", f"{s(b, 'lop_pointinstancer_1000k'):.1f}", "—"],
             ["LOP の sopimport", "Create Native Instances（既定）", "3 万", f"{s(b, 'lop_nativeinstances_30k'):.1f}", "—"],
             ["LOP の sopimport", "Create Xforms", "3 万", f"{s(b, 'lop_xforms_30k'):.1f}", "—"]]
    tiny_share = s(a, "tiny_packed_30k") / s(a, "big_packed_30k") * 100
    payload = {
        "title": f"草を何万本も Karma で撮るなら、Solaris（LOP）の sopimport で「Create Point Instancer」にして撮る。"
                 f"10 万本が {s(c, 'inst_1e5'):.0f} 秒 → {s(b, 'lop_pointinstancer_100k'):.0f} 秒、100 万本も {s(b, 'lop_pointinstancer_1000k'):.0f} 秒",
        "summary":
            f"**課題: 実験215 で、パックした草は 1 万本 17 秒なのに 10 万本は {s(c, 'inst_1e5') / 60:.0f} 分かかった。時間はどこでかかっているのか。どう撮れば速いのか。**\n\n"
            "実験215 の場面（草 1 本 = 細い葉 3 枚・面 15 枚。10 m 四方にまいて copytopoints でパックして並べる）を使った。"
            "はじめに小さく 1 枚撮って捨て（Karma の立ち上がり）、1 通りずつ、ほかの重い処理は回さずに測った。\n\n"
            f"**/obj の Karma では、時間の 9 割が「場面を Karma に渡す」段階だった。**3 万本を 640×360・8 サンプル＋ノイズ除去で撮ると {s(a, 'big_packed_30k'):.1f} 秒。"
            f"画を 64×36・1 サンプル（光の計算がほぼ無い）にしても {s(a, 'tiny_packed_30k'):.1f} 秒で、{tiny_share:.0f}% が残った。"
            f"本数を 1 万 → 3 万にすると、時間は {s(a, 'big_packed_10k'):.1f} → {s(a, 'big_packed_30k'):.1f} 秒（{s(a, 'big_packed_30k') / s(a, 'big_packed_10k'):.1f} 倍）と、本数より速く延びた。"
            f"usdinstancerpath を付けても（{s(a, 'big_inst_30k'):.1f} 秒）、草ごとの色 Cd を消しても（{s(a, 'big_nocd_packed_30k'):.1f} 秒）変わらなかった。\n\n"
            "**Solaris（LOP）で読むと、段違いに速い。**LOP の sopimport で同じ草を読み、Packed Primitives を「Create Point Instancer」にして、"
            "カメラとライトは sceneimport で /obj から読み、karmarendersettings で 8 サンプルにして usdrender で撮った（ノイズ除去は入れていないので、条件は少し違う）。"
            f"1 万・3 万・10 万・100 万本で {s(b, 'lop_pointinstancer_10k'):.1f}・{s(b, 'lop_pointinstancer_30k'):.1f}・{s(b, 'lop_pointinstancer_100k'):.1f}・{s(b, 'lop_pointinstancer_1000k'):.1f} 秒。"
            f"10 万本は /obj の {s(c, 'inst_1e5'):.0f} 秒に比べて約 {s(c, 'inst_1e5') / s(b, 'lop_pointinstancer_100k'):.0f} 分の 1。\n\n"
            f"**LOP でも、渡し方で 5 倍ちがう。**3 万本で、Create Point Instancer {s(b, 'lop_pointinstancer_30k'):.1f} 秒、"
            f"Create Native Instances（既定）{s(b, 'lop_nativeinstances_30k'):.1f} 秒、Create Xforms {s(b, 'lop_xforms_30k'):.1f} 秒。"
            "1 本ずつ別の物として渡すと、本数に応じて重くなる。\n\n"
            "**決め方: 同じ形を何万も並べる場面（草原・森・群衆）は、LOP の sopimport で Create Point Instancer にして撮る。**"
            "/obj の Karma で撮るのは、数千本までにする。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "撮り方と本数と時間",
             "images": [{"path": "222_time.png", "caption": "/obj の Karma は 10 万本で 13 分。LOP のポイントインスタンサーは 100 万本でも 37 秒。"},
                        {"path": "222_grid.png", "caption": "同じ草原。LOP で撮っても見た目は同じ（ノイズ除去の有無の違いだけ）。"},
                        {"path": "222_lop_graph.png", "caption": "LOP のつなぎ方: sceneimport（カメラとライト）→ sopimport（草。Create Point Instancer）→ karmarendersettings。"}],
             "per_row": 1, "columns": ["撮り方", "渡し方", "本数", "撮る時間（秒）", "極小の画で（秒）"], "rows": table},
        ],
        "notes": [
            f"<strong>/obj の Karma で草を撮ると、時間の {tiny_share:.0f}% が「場面を渡す」段階。</strong>本数より速く延びる。",
            f"<strong>LOP の sopimport で Create Point Instancer にすると、10 万本 {s(b, 'lop_pointinstancer_100k'):.0f} 秒、100 万本 {s(b, 'lop_pointinstancer_1000k'):.0f} 秒。</strong>",
            f"<strong>LOP でも、既定の Create Native Instances は 3 万本 {s(b, 'lop_nativeinstances_30k'):.0f} 秒、Xforms は {s(b, 'lop_xforms_30k'):.0f} 秒。</strong>",
            "<strong>草ごとの色（Cd）や usdinstancerpath は、/obj の Karma では時間に効かなかった。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "222_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
