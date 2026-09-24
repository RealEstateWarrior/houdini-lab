# -*- coding: utf-8 -*-
"""実験215 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402

MODE = {0: "パックしたまま", 1: "パックを解く", 2: "ポイントインスタンサー"}
SHOW = ["packed_1e4", "flat_1e4", "inst_1e5", "inst_1e5_wide"]


def main():
    with open(os.path.join(OUT, "215_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    font = _font(16)
    w, h = 640, 360
    sheet = Image.new("RGB", (w * 2, (h + 30) * 2), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(SHOW):
        r = t[k]
        x, y = (i % 2) * w, (i // 2) * (h + 30)
        sheet.paste(Image.open(os.path.join(OUT, f"215_{k}.png")).convert("RGB"), (x, y + 30))
        dr.text((x + 8, y + 6), f"{r['count']:,} 本・{MODE[r['mode']]}・地面 {r['ground']:g} m 四方  {r['sec']:.1f} 秒", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "215_grid.png"))
    s = lambda k: t[k]["sec"]  # noqa: E731
    table = [[f"{t[k]['count']:,}", MODE[t[k]["mode"]], f"{t[k]['ground']:g}", f"{t[k]['prims']:,}", f"{s(k):.1f}"] for k in t]
    payload = {
        "title": f"草を Karma で撮るならパックしたまま（1 万本 {s('packed_1e4'):.0f} 秒、解くと {s('flat_1e4'):.0f} 秒）。"
                 f"ただし 10 万本は、ポイントインスタンサーにしても、地面を広げて混み具合を 1 万本と同じにしても {s('inst_1e5_wide') / 60:.0f} 分かかった",
        "summary":
            "**課題: 草原を作ると、同じ草を何万本も並べる。Karma で何本まで撮れるか。copytopoints の Pack and Instance は入れたままがよいのか。**\n\n"
            "草 1 本は細い三角の葉 3 枚（面 15 枚）。地面に scatter で点をまき、copytopoints で並べて、向き・大きさ・色を VEX でばらつかせた。"
            "同じカメラで 640×360・8 サンプル＋ノイズ除去で撮り、時間を測った。並べ方は 3 つ: パックしたまま・パックを解く・パックして "
            "<code>usdinstancerpath</code> を付ける（Karma へは「形 1 つ＋置く点の並び」のポイントインスタンサーとして渡る）。"
            "昼の 1 回目（960×540・16 サンプル）では、パックしたまま 10 万本が 10 分を超えても終わらず、止めていた。\n\n"
            f"**パックは入れたままにする。**1 万本で、パックしたまま {s('packed_1e4'):.1f} 秒、パックを解くと {s('flat_1e4'):.1f} 秒（{s('flat_1e4') / s('packed_1e4'):.1f} 倍）。"
            f"解くと面が {t['flat_1e4']['prims']:,} 枚になる。\n\n"
            f"**ポイントインスタンサーにしても、速くならなかった。**1 万本で {s('inst_1e4'):.1f} 秒（パックしたまま {s('packed_1e4'):.1f} 秒）。\n\n"
            f"**本数が 1 万本を超えると、時間が急に延びる。**1,000 本 {s('packed_1e3'):.1f} 秒、1 万本 {s('packed_1e4'):.1f} 秒、"
            f"10 万本（ポイントインスタンサー）{s('inst_1e5'):.0f} 秒。本数 10 倍で時間は {s('inst_1e5') / s('inst_1e4'):.0f} 倍。\n\n"
            f"**混み具合のせいではなかった。**10 万本を 31.6 m 四方（1 m² あたりの本数が 1 万本のときと同じ）にまいても {s('inst_1e5_wide'):.0f} 秒で、"
            f"10 m 四方（{s('inst_1e5'):.0f} 秒）とほとんど変わらなかった。なぜ本数でこれほど延びるのかは、確かめきれなかった"
            "（撮るたびに「vblur はインスタンスごとに指定できない」という注意が出ていた）。100 万本と、パックを解いた 10 万本は、時間がかかるので撮らなかった。\n\n"
            "**決め方: この組み方（SOP の copytopoints を /out の Karma で撮る）では、1 万本前後までにする。**"
            "それより多い草原は、Solaris（LOP）で並べるなど、別の撮り方を試す必要がある（まだ測っていない）。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "本数と並べ方を変えた草（640×360・8 サンプル）",
             "images": [{"path": "215_grid.png", "caption": "上: 1 万本（パックしたまま・解く）。下: 10 万本（ポイントインスタンサー、10 m 四方・31.6 m 四方）。"}],
             "per_row": 1, "columns": ["本数", "並べ方", "地面（m 四方）", "面（またはパック）の数", "撮る時間（秒）"], "rows": table},
        ],
        "notes": [
            f"<strong>パックは入れたままにする。</strong>1 万本で {s('packed_1e4'):.0f} 秒、解くと {s('flat_1e4'):.0f} 秒。",
            "<strong>ポイントインスタンサー（usdinstancerpath）にしても速くならなかった。</strong>",
            f"<strong>10 万本は {s('inst_1e5') / 60:.0f} 分かかった。</strong>地面を広げて混み具合を下げても同じ。原因は確かめきれていない。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "215_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
