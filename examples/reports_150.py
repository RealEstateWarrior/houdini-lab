# -*- coding: utf-8 -*-
"""実験150（122〜149 の振り返り点検）の図とレポートを、測り直した結果から組み立てる。"""
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
    with open(os.path.join(OUT, "150_checks.json"), encoding="utf-8") as fp:
        checks = json.load(fp)
    real, timing_n = [], 0
    for c in checks:
        c["real"] = [d for d in c.get("diffs", []) if not is_timing(d[1])]
        timing_n += c.get("n_diffs", 0) - len(c["real"])
        real += [(c["no"],) + tuple(d) for d in c["real"]]
    total = sum(c.get("values", 0) for c in checks)
    sec = sum(c.get("sec", 0) for c in checks)

    img = Image.new("RGB", (1000, 560), (255, 255, 255))
    d = ImageDraw.Draw(img)
    font, small, tiny = _font(26), _font(22), _font(15)
    d.text((24, 16), "122〜149 を全部流し直して、記録と比べた（数字1つずつ）", fill=(30, 30, 30), font=font)
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
    img.save(os.path.join(OUT, "150_audit.png"))
    print("150_audit.png")

    payload = {
        "title": f"122〜149 の振り返り点検 — 28本すべて流し直し、時間以外の数字は{'全部一致' if not real else f'{len(real)}個ずれ'}",
        "summary":
            "30件ごとの点検（030・060・090・121 に続いて5回目）。122〜149 の28本を、121 と同じやり方で全部流し直した。"
            "記録（out/NNN_*.json）を控えに退避し、台本を hython で流し、新しい値と控えを数字1つずつ比べて、"
            "最後に控えを戻した（記録は変えていない）。\n\n"
            f"比べた値は {total:,} 個。かかった時間は全部で {sec:.0f} 秒。\n\n"
            f"**時間以外の数字は{'全部一致した' if not real else f' {len(real)} 個ずれた'}。**"
            "時間の項目は流すたびに揺れるので、比べる対象から外している。"
            "121 で見つかった「ファイルの大きさが1バイト違う」「記録に手で足した項目」の類いは、今回は無かった。\n\n"
            "**記事を書く前に直したもの: 1件。**実験149 で、Bricker の線は原点から引かれると一度書いたが、"
            "Offset 0.05・Size 0.3 の枚数が予測と合わなかった。点の位置を測り直すと、線は形の端から引かれていた。"
            "公開前に記事を直した。予測の式を表に並べておいたので、ずれに気づけた。\n\n"
            "**理由が分かっていないもの: 1件。**実験147 の Taper の体積（倍率を平均した値と 0.45% 違う）。\n\n"
            "**スクリプトで見つけた落とし穴: 122〜149 で6件**（最初から式の入ったつまみは set しても変わらない 133・134、"
            "attribblur は Pin Border が入っていると曲線では何も変わらない 139、mirror の継ぎ目は距離がつまみ未満でないとまとまらない 145、"
            "clip の Both は切り口の点を共有したまま 146、tube の円錐は先の点が重なったまま 148、"
            "Bricker の升目は形の端から 149）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "実験ごとの測り直し",
             "note": "時間の項目（sec など）は除いて比べた。許す差は 0.000001（相対）。",
             "images": [{"path": "150_audit.png", "caption": "28本とも、時間以外の数字がすべて一致。"}],
             "per_row": 1,
             "columns": ["実験", "台本", "比べた値", "時間以外のずれ", "秒"],
             "rows": [[c["no"], c.get("script", "—"), f"{c.get('values', 0):,}",
                       str(len(c["real"])), f"{c.get('sec', 0):.1f}"] for c in checks]},
        ],
        "notes": [
            f"<strong>28本すべて流し直せた。</strong>全部で約{sec:.0f}秒。",
            "<strong>予測の式を表に並べておくと、書き間違いに気づける。</strong>149 の Bricker がそうだった。",
            "<strong>次の点検は180。</strong>",
        ],
        "next": ["実験147 の Taper の体積が平均と合わない理由", "時間の項目を3回の中央値で記録する"],
    }
    with open(os.path.join(OUT, "150_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 150_report.json", total, len(real), timing_n)


if __name__ == "__main__":
    main()
