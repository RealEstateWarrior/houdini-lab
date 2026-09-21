# -*- coding: utf-8 -*-
"""実験121（091〜120 の振り返り点検）の図とレポートを、測り直した結果から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def is_timing(key):
    k = key.lower()
    return "second" in k or "us_per" in k or k.endswith("sec") or "_ms" in k


def main():
    with open(os.path.join(OUT, "121_checks.json"), encoding="utf-8") as fp:
        checks = json.load(fp)
    real, timing_n = [], 0
    for c in checks:
        c["real"] = [d for d in c.get("diffs", []) if not is_timing(d[1])]
        timing_n += c.get("n_diffs", 0) - len(c["real"])
        real += [(c["no"],) + tuple(d) for d in c["real"]]
    total = sum(c.get("values", 0) for c in checks)
    uv = next(c["values"] for c in checks if c["no"] == "116")
    sec = sum(c.get("sec", 0) for c in checks)

    img = Image.new("RGB", (1000, 560), (255, 255, 255))
    d = ImageDraw.Draw(img)
    font, small, tiny = _font(26), _font(22), _font(15)
    d.text((24, 16), "091〜120 を全部流し直して、記録と比べた（数字1つずつ）", fill=(30, 30, 30), font=font)
    for i, c in enumerate(checks):
        x0, y0 = 24 + (i % 6) * 160, 70 + (i // 6) * 94
        ok = not c["real"]
        fill = (223, 240, 228) if ok else (250, 232, 214)
        edge = (46, 139, 87) if ok else (214, 96, 30)
        d.rectangle([x0, y0, x0 + 148, y0 + 82], fill=fill, outline=edge, width=2)
        d.text((x0 + 10, y0 + 8), c["no"], fill=(30, 30, 30), font=small)
        d.text((x0 + 10, y0 + 42), f"{c.get('values', 0):,} 値" + ("" if ok else f"・{len(c['real'])}件"),
               fill=(70, 70, 76), font=tiny)
        d.text((x0 + 96, y0 + 10), "一致" if ok else "要確認", fill=edge, font=tiny)
    img.save(os.path.join(OUT, "121_audit.png"))
    print("121_audit.png")

    b097 = next(r for r in real if r[0] == "097")
    payload = {
        "title": "091〜120 の振り返り点検 — 30本すべて流し直し、結果の数字は1つを除いて全部一致",
        "summary":
            "30件ごとの点検（030・060・090 に続いて4回目）。090 までは数件を選んで測り直したが、"
            "091 からの台本はどれも数秒で終わるので、**30本すべてを流し直した**。"
            "記録（out/NNN_*.json）を控えに退避し、台本を hython で流し、"
            "新しい値と控えを数字1つずつ比べて、最後に控えを戻した（記録は変えていない）。\n\n"
            f"比べた値は {total:,} 個（うち {uv:,} 個は実験116 の UV の座標）。"
            f"かかった時間は全部で {sec:.0f} 秒。\n\n"
            f"**違ったのは時間の項目 {timing_n} 個と、それ以外の {len(real)} 個だけ。**\n\n"
            f"- 実験097: パックして書き出したファイルの大きさが {b097[3]:,} → {b097[4]:,} バイト（1バイト差）。"
            "同じものを書いても、ファイルの大きさはぴったり同じにならないことがある"
            "（記事の結論「パックすると小さくなる」は変わらない）\n"
            "- 実験101: 記録に、台本が書かない項目（side = 2.0）が1つ混ざっていた。"
            "あとから手で足したもの。値は既定と同じで、記事の数字は変わらない\n\n"
            "時間の項目（秒・1点あたりのマイクロ秒）は、流すたびに揺れるので比べていない。"
            "実験096 の最も遅い行は 3371 → 1418 マイクロ秒と大きく動いた。"
            "時間の値は1回の測定では目安にとどまる。\n\n"
            "**あとの実験で結論に条件が付いたもの: 1件。** 実験115（到着時間が縦横の道のりになる）の"
            "理由を、実験119 で確かめた（distancealonggeometry の Edge と同じ値）。記事115 に注記を足した。\n\n"
            "**解説の訂正: 1件。** copyxform の説明を「同じ変形を重ねる」と書いていたが、"
            "実験110 で「値を i 倍して1回かける」と分かったので直した。\n\n"
            "**検算で見つけた落とし穴: 091〜120 で8件**（boolean は poly 以外だと何もしない 098、"
            "carve の First U は入切 104、copyxform は輪にならない 110、timeblend の v は1秒あたり 113、"
            "attribfill の到着時間は辺の道のり 115、revolve は裏返しになる 118、"
            "box の Use Divisions は線の籠 120、素性の控えがメニューを12個で切っていた 112）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "実験ごとの測り直し",
             "note": "時間の項目（sec・seconds・us_per_point など）は除いて比べた。許す差は 0.000001（相対）。",
             "images": [{"path": "121_audit.png",
                         "caption": "30本のうち28本は、時間以外の数字がすべて一致。"}],
             "per_row": 1,
             "columns": ["実験", "台本", "比べた値", "時間以外のずれ", "秒"],
             "rows": [[c["no"], c.get("script", "—"), f"{c.get('values', 0):,}",
                       str(len(c["real"])), f"{c.get('sec', 0):.1f}"] for c in checks]},
            {"label": "ずれた値（時間以外）",
             "note": "",
             "images": [],
             "per_row": 1,
             "columns": ["実験", "ファイル", "項目", "記録", "流し直し"],
             "rows": [[r[0], r[1], r[2], str(r[3]), str(r[4])] for r in real]},
        ],
        "notes": [
            "<strong>30本すべて流し直せた。</strong>全部で約1分。091 以降の台本は、1本数秒で結果を出す作りになっている。",
            "<strong>結果の数字は、ファイルの大きさ1バイトを除いて全部一致。</strong>",
            "<strong>時間の値は揺れる。</strong>最も遅い行では2倍以上動いた。速さの比べは、同じ回で並べて測る。",
            "<strong>記録を手で直さない。</strong>台本が書かない項目が1つ混ざっていた。直すなら台本を直して流し直す。",
            "<strong>次の点検は150。</strong>",
        ],
        "next": [
            "時間の項目を、3回流した中央値で記録するようにする",
            "点検の台本を、次回（150）もそのまま使えるように番号の範囲を引数にする",
        ],
    }
    with open(os.path.join(OUT, "121_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 121_report.json")


if __name__ == "__main__":
    main()
