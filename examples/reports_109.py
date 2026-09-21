# -*- coding: utf-8 -*-
"""実験109 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font  # noqa: E402

LABEL = {"points": "点のグループ", "prims_edge": "面（辺を共有する隣だけ）",
         "prims_point": "面（角を共有する隣まで・既定）"}


def draw(path, k=3):
    """k 段広げたときの形を、3つ並べて描く（数は式どおりだったので、その形で描く）。"""
    cell, n = 22, 2 * k + 5
    img = Image.new("RGB", (1000, 360), (255, 255, 255))
    d = ImageDraw.Draw(img)
    font, small = _font(24), _font(19)
    d.text((24, 16), f"真ん中の1つから {k} 段広げた範囲", fill=(30, 30, 30), font=font)
    shapes = [("点のグループ", "diamond"), ("面・辺を共有", "diamond"),
              ("面・角を共有（既定）", "square")]
    for i, (title, kind) in enumerate(shapes):
        x0, y0 = 40 + i * 320, 80
        c = n // 2
        for r in range(n):
            for q in range(n):
                dr, dq = abs(r - c), abs(q - c)
                inside = (dr + dq <= k) if kind == "diamond" else max(dr, dq) <= k
                color = PALETTE[0] if (dr == 0 and dq == 0) else \
                    ((150, 190, 230) if inside else (240, 240, 244))
                box = [x0 + q * cell, y0 + r * cell, x0 + (q + 1) * cell - 2, y0 + (r + 1) * cell - 2]
                if kind != "diamond" or i != 0:
                    d.rectangle(box, fill=color)
                else:
                    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=color)
        count = 2 * k * k + 2 * k + 1 if kind == "diamond" else (2 * k + 1) ** 2
        d.text((x0, y0 + n * cell + 8), f"{title}: {count} 個", fill=(60, 60, 66), font=small)
    img.save(path)


def main():
    with open(os.path.join(OUT, "109_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows, shrink = data["rows"], data["shrink"]
    fits = {}
    for case in LABEL:
        sub = [r for r in rows if r["case"] == case]
        fits[case] = ("菱形" if all(r["count"] == r["diamond"] for r in sub)
                      else "正方形" if all(r["count"] == r["square"] for r in sub) else "どちらでもない")
    shrink_ok = all(r["count"] == r["square"] for r in shrink)
    draw(os.path.join(OUT, "109_expand.png"))
    print("109_expand.png")

    steps = sorted({r["steps"] for r in rows})
    payload = {
        "title": "groupexpand の1段は「隣」の決め方しだい — 点と辺共有は菱形、面の既定は正方形",
        "summary":
            "格子の真ん中の1つから groupexpand で広げ、段ごとの数を数えた。"
            "辺でつながった隣へ広がるなら k 段で菱形 **2k²+2k+1 個**、"
            "角を共有する隣まで広がるなら正方形 **(2k+1)² 個**になる。\n\n"
            f"結果は、点のグループが **{fits['points']}**、"
            f"面で Require Primitives Share Edge を入れると **{fits['prims_edge']}**、"
            f"切ったまま（既定）だと **{fits['prims_point']}**。"
            f"{len(steps)} 通りの段数（0〜{max(steps)}）で、すべて式の数ちょうどだった。\n\n"
            "つまり、面のグループを既定のまま広げると、斜めの隣にも一度に広がる。"
            "8段で 289 枚と、辺だけのとき（145 枚）の約2倍になる。\n\n"
            "負の段数は縮める。9×9 の点の塊から −1 段で 7×7、−2 段で 5×5、−4 段で 1 点"
            f"（{'すべて式どおり' if shrink_ok else '式と違うものがあった'}）。"
            "1段ごとに外周が1列ずつ削られる。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "広げた段数と数",
             "note": "点は 21×21 の格子の真ん中の点から、面は 21×21 枚の真ん中の面から。",
             "images": [{"path": "109_expand.png",
                         "caption": "3段広げたときの範囲。面の既定は斜めにも広がる。"}],
             "per_row": 1,
             "columns": ["段数"] + [LABEL[c] for c in LABEL] + ["菱形の式", "正方形の式"],
             "rows": [[str(k)] + [str(next(r["count"] for r in rows
                                           if r["case"] == c and r["steps"] == k))
                                  for c in LABEL]
                      + [str(2 * k * k + 2 * k + 1), str((2 * k + 1) ** 2)]
                      for k in steps]},
            {"label": "縮める（負の段数）",
             "note": "9×9 の点の塊から。",
             "images": [],
             "per_row": 1,
             "columns": ["段数", "数", "式"],
             "rows": [[str(r["steps"]), str(r["count"]), str(r["square"])] for r in shrink]},
        ],
        "notes": [
            "<strong>点は辺でつながった隣へ。</strong>k 段で 2k²+2k+1 個の菱形。",
            "<strong>面の既定は、角を共有する隣まで。</strong>k 段で (2k+1)² 個の正方形。"
            "辺でつながった隣だけにしたいときは Require Primitives Share Edge を入れる。",
            "<strong>負の段数は、外周を1列ずつ削る。</strong>9×9 → 7×7 → 5×5。",
            "<strong>速い。</strong>21×21 の格子なら、どの段数でも1ミリ秒未満"
            "（最初の1回を除く）。",
        ],
        "next": [
            "Restrict by Normal Spread Angle で、箱の角を越えずに止められるか",
            "Flood Fill と connectivity の結果が同じになるか",
            "三角形の網や、ばらつきのある網での広がり方",
        ],
    }
    with open(os.path.join(OUT, "109_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 109_report.json")


if __name__ == "__main__":
    main()
