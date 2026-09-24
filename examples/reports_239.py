# -*- coding: utf-8 -*-
"""実験239 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart  # noqa: E402

SIZES = ((640, 360), (1280, 720), (1920, 1080))
LAB = {"donut": "ドーナツ", "ocean_winter": "冬の朝の七里ヶ浜（224 万点の海）"}


def main():
    with open(os.path.join(OUT, "239_stats.json"), encoding="utf-8") as fp:
        t = {r["case"]: r for r in json.load(fp)["rows"]}
    line_chart(os.path.join(OUT, "239_time.png"),
               [{"label": LAB[g], "points": [(w * h / 1e6, t[g]["times"][f"{w}x{h}"]) for w, h in SIZES]} for g in t],
               "画の大きさと撮る時間（16 サンプル、ノイズ除去なし）", "画素の数（百万）", "撮る時間（秒）")
    table = [[LAB[g]] + [f"{t[g]['times'][f'{w}x{h}']:.1f}" for w, h in SIZES] + [f"{t[g]['fixed_sec']:.1f}", f"{t[g]['per_mpx_sec']:.1f}", f"{t[g]['ratio_1080_to_360']:.1f}"]
             for g in t]
    d, o = t["donut"], t["ocean_winter"]
    payload = {
        "title": f"画を 640×360 → 1920×1080（画素 9 倍）にすると、ドーナツは撮る時間が {d['ratio_1080_to_360']:.1f} 倍、海は {o['ratio_1080_to_360']:.1f} 倍。"
                 f"海は 1 枚あたり {o['fixed_sec']:.0f} 秒が画の大きさによらない分",
        "summary":
            "**課題: 試し撮りは 640×360 で、仕上げは 1920×1080 で撮りたい。画素の数は 9 倍になるが、時間も 9 倍になるのか。場面によって違うのか。**\n\n"
            "実践 2 本（ドーナツ＝ふつうの材質、冬の朝の七里ヶ浜＝224 万点の海と空）の hip を読み、同じ設定（16 サンプル・ノイズ除去なし・CPU）で "
            "640×360・1280×720・1920×1080 に撮った。はじめに小さく 1 枚撮って捨てた。"
            "3 つの時間を「時間 = 画の大きさによらない分 a ＋ 画素に比例する分 b × 画素数」に当てはめた。\n\n"
            f"**ドーナツは、ほぼ画素の数に比例する。**{d['times']['640x360']:.1f}・{d['times']['1280x720']:.1f}・{d['times']['1920x1080']:.1f} 秒で、640×360 → 1920×1080 は {d['ratio_1080_to_360']:.1f} 倍。"
            f"画の大きさによらない分は {d['fixed_sec']:.1f} 秒、百万画素あたり {d['per_mpx_sec']:.0f} 秒。\n\n"
            f"**海は、画の大きさによらない分が大きい。**{o['times']['640x360']:.1f}・{o['times']['1280x720']:.1f}・{o['times']['1920x1080']:.1f} 秒で {o['ratio_1080_to_360']:.1f} 倍。"
            f"画の大きさによらない分が {o['fixed_sec']:.1f} 秒、百万画素あたり {o['per_mpx_sec']:.0f} 秒。"
            "224 万点の海と大きな空の球を Karma に渡す時間が、毎回かかると考えられる（実験221 で、サンプル数や解像度を下げても 2 割しか速くならなかったのと合う）。\n\n"
            "**決め方: 仕上げの時間は、試し撮りを 2 つの大きさで撮って見積もる。**2 点から a と b が出るので、1920×1080 の時間は a ＋ b × 207 万で求まる。"
            "形が重い場面は a が大きく、解像度を下げても速くならない。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "画の大きさと撮る時間",
             "images": [{"path": "239_time.png", "caption": "ドーナツはほぼ原点を通る直線、海は画の大きさによらない分（a）が大きい。"}],
             "per_row": 1, "columns": ["場面", "640×360（秒）", "1280×720（秒）", "1920×1080（秒）", "大きさによらない分 a（秒）", "百万画素あたり b（秒）", "9 倍の画素で何倍"],
             "rows": table},
        ],
        "notes": [
            f"<strong>ドーナツは、画素 9 倍で時間 {d['ratio_1080_to_360']:.1f} 倍。</strong>ほぼ画素に比例する。",
            f"<strong>海は {o['ratio_1080_to_360']:.1f} 倍。</strong>1 枚あたり {o['fixed_sec']:.0f} 秒が画の大きさによらない。",
            "<strong>仕上げの時間は、2 つの大きさの試し撮りから a ＋ b × 画素数で見積もる。</strong>",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "239_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
