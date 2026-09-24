# -*- coding: utf-8 -*-
"""実験206 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def grid(rows):
    font = _font(16)
    ims = [Image.open(os.path.join(OUT, f"206_r{r['rows']}.png")).convert("RGBA") for r in rows]
    w, h = ims[0].size
    cols = 3
    out = Image.new("RGB", (w * cols, (h + 28) * 2), (236, 236, 238))
    d = ImageDraw.Draw(out)
    for i, (im, r) in enumerate(zip(ims, rows)):
        x, y = (i % cols) * w, (i // cols) * (h + 28)
        bg = Image.new("RGBA", im.size, (236, 236, 238, 255))
        out.paste(Image.alpha_composite(bg, im).convert("RGB"), (x, y + 28))
        d.text((x + 8, y + 5), f"{r['rows']}×{r['cols']}（点 {r['points']:,}）{r['sec']:.0f} 秒", fill=(30, 30, 30), font=font)
    out.save(os.path.join(OUT, "206_grid.png"))


def main():
    with open(os.path.join(OUT, "206_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows = d["rows"]
    grid(rows)
    by = {r["rows"]: r for r in rows}
    fine, prac = by[165], by[110]
    cm = lambda v: v * 100  # noqa: E731
    hem = lambda r: sum(r["hem"].values()) / 4  # noqa: E731
    table = []
    for r in rows:
        tf = r.get("to_finest")
        table.append([f"{r['rows']}×{r['cols']}", f"{r['points']:,}", f"{r['sec']:.1f}",
                      f"{cm(tf['mean']):.1f}" if tf else "—", f"{cm(tf['max']):.1f}" if tf else "—",
                      f"{hem(r):.3f}", f"{r['lowest']:.3f}", f"{r['top_std_mm']:.1f}"])
    c44, c22, c66 = by[44], by[22], by[66]
    tf = lambda r: r["to_finest"]  # noqa: E731
    payload = {
        "title": f"テーブルクロスを粗い布で試すなら 44×56 まで — 落ち方の差は平均 {cm(tf(c44)['mean']):.1f} cm で、計算は {c44['sec']:.0f} 秒（実践の細かさの {c44['sec'] / prac['sec']:.0%}）。ただし粗いほど角の垂れが短く、22×28 では {cm(c22['lowest'] - fine['lowest']):.0f} cm 高い",
        "summary":
            "**課題: 実践「テーブルクロスを掛ける」では「粗いうちに落ち方を決めて、最後に細かくする」と書いた。粗い布で決めた落ち方は、細かい布でも同じになるのか。どこまで粗くしてよいか。**\n\n"
            "実践と同じ机（天板 1.2 × 0.8 m、高さ 0.74 m）と布（1.9 × 1.45 m を天板の 12 cm 上に置き、4° 回す）を、布の分割だけ変えて "
            f"vellumsolver（Substeps 5、地面あり）で {d['last']} フレーム（3 秒）落とした。Rows × Columns は 22×28・44×56・66×84・110×140（実践の値）・165×210。"
            "いちばん細かい 165×210 を答えとして、その各点から粗い布の面までの距離を測った。\n\n"
            f"**計算の時間は、点の数ほどには増えない。**点 {c22['points']:,} 個で {c22['sec']:.0f} 秒、{c44['points']:,} 個で {c44['sec']:.0f} 秒、{c66['points']:,} 個で {c66['sec']:.0f} 秒、"
            f"{prac['points']:,} 個で {prac['sec']:.0f} 秒、{fine['points']:,} 個で {fine['sec']:.0f} 秒。点が 56 倍でも時間は {fine['sec'] / c22['sec']:.0f} 倍だった。\n\n"
            f"**形の差は、細かくするほど縮む。**いちばん細かい布との距離の平均は、22×28 で {cm(tf(c22)['mean']):.1f} cm、44×56 で {cm(tf(c44)['mean']):.1f} cm、"
            f"66×84 で {cm(tf(c66)['mean']):.1f} cm、110×140 で {cm(tf(prac)['mean']):.1f} cm。最大（ひだの先など）は {cm(tf(c22)['max']):.0f}・{cm(tf(c44)['max']):.0f}・{cm(tf(c66)['max']):.0f}・{cm(tf(prac)['max']):.0f} cm。\n\n"
            f"**粗い布は、角が短く垂れる。**布のいちばん低い点（角の先）は、22×28 で {c22['lowest']:.2f} m、44×56 で {c44['lowest']:.2f} m、66×84 で {c66['lowest']:.2f} m、"
            f"110×140 で {prac['lowest']:.2f} m、165×210 で {fine['lowest']:.2f} m。四辺の真ん中の裾の高さ（平均）も {hem(c22):.3f} → {hem(fine):.3f} m と、細かいほど下がった。"
            "粗い布は折れ曲がれる所が少ないためと考えられるが、確かめていない。\n\n"
            f"**天板の上の平らさは、44×56 から目に見えて変わる。**天板の上にある点の高さのばらつきは、{c22['top_std_mm']:.1f}・{c44['top_std_mm']:.1f}・{c66['top_std_mm']:.1f}・"
            f"{prac['top_std_mm']:.2f}・{fine['top_std_mm']:.2f} mm。22×28 では天板の上に波が残った。\n\n"
            f"**決め方: 落とす位置・向き・机との当たり方は 44×56 で決めてよい。**差は平均 {cm(tf(c44)['mean']):.1f} cm で、時間は実践の細かさの {c44['sec'] / prac['sec']:.0%}。"
            f"ただし角の垂れの長さは細かくすると {cm(c44['lowest'] - prac['lowest']):.0f} cm 伸びるので、裾の長さ（床からの高さ）は最後の細かさで確かめる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "落ちる様子（左が 44×56、右が実践の 110×140）",
             "images": [{"path": "206_anim.gif", "caption": "72 フレーム（3 秒）を 2 フレームおきに。粗い布も同じように落ちるが、角の垂れが短い。"}],
             "per_row": 1, "columns": [], "rows": []},
            {"label": "72 フレーム目の形",
             "images": [{"path": "206_grid.png", "caption": "かっこは点の数、右は 72 フレームの計算時間。66×84 までは網目を重ねて見せた。"}],
             "per_row": 1,
             "columns": ["Rows×Columns", "点", "秒", "細かい布との差 平均 cm", "最大 cm", "裾の高さ m", "いちばん低い点 m", "天板の上のばらつき mm"],
             "rows": table},
        ],
        "notes": [
            f"<strong>落ち方の試しは 44×56 で足りる。</strong>いちばん細かい布との差は平均 {cm(tf(c44)['mean']):.1f} cm、時間は実践の細かさの {c44['sec'] / prac['sec']:.0%}（{c44['sec']:.0f} 秒）。",
            f"<strong>粗い布ほど、角が短く垂れる。</strong>22×28 は 165×210 より {cm(c22['lowest'] - fine['lowest']):.0f} cm 高い所で止まった。裾の長さは最後の細かさで決める。",
            f"<strong>点を増やしても、時間はそれほど増えない。</strong>点 56 倍で時間 {fine['sec'] / c22['sec']:.0f} 倍。",
            "<strong>22×28 は粗すぎる。</strong>天板の上に波が残り、形の差も平均 3 cm を超えた。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "206_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 206_report.json")
    print(payload["title"])


if __name__ == "__main__":
    main()
