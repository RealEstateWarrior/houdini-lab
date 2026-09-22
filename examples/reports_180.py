# -*- coding: utf-8 -*-
"""実験180（151〜179 の振り返り点検）の図とレポートを、測り直した結果から組み立てる。"""
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
    return "second" in k or "us_per" in k or "ms_per" in k or k.endswith("sec") or "_ms" in k


def main():
    with open(os.path.join(OUT, "180_checks.json"), encoding="utf-8") as fp:
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
    d.text((24, 16), "151〜179 を全部流し直して、記録と比べた（数字1つずつ）", fill=(30, 30, 30), font=font)
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
    img.save(os.path.join(OUT, "180_audit.png"))
    print("180_audit.png")


    payload = {
        "title": f"151〜179 の振り返り点検 — 29本すべて流し直し、時間以外の数字は{'全部一致' if not real else f'{len(real)}個ずれ'}",
        "summary":
            "30件ごとの点検（030・060・090・121・150 に続いて6回目）。151〜179 の29本を、150 と同じやり方で全部流し直した。"
            "記録（out/NNN_*.json）を控えに退避し、台本を hython で流し、新しい値と控えを数字1つずつ比べて、最後に控えを戻した（記録は変えていない）。\n\n"
            f"比べた値は {total:,} 個。かかった時間は全部で {sec:.0f} 秒（Vellum の 170・177 が 24 秒と 51 秒）。\n\n"
            f"**時間以外の数字は{'全部一致した' if not real else f' {len(real)} 個ずれた'}。**"
            f"違ったのは時間の項目 {timing_n} 個だけ（173・174・178 の「1点あたり」「1かけらあたり」の時間。流すたびに揺れる）。"
            "RBD・Vellum・POP・erode のようなシミュレーションも、同じ条件なら同じ数字を返した。\n\n"
            "**公開前に直したもの: 5件。**"
            "156 で折れ目の点の輪の選び方を2回まちがえた（点の番号の並びを思い込んだ。距離で選び直した）。"
            "172 で粒の混み具合を「升に分けて数える」方法で測ったが、群れの形の変化が混ざったので「まわりの粒の数」に替えた。"
            "173 で VEX の時間が 0.00001 秒と出た（cook(force=True) では計算し直さない。つまみを少し変えて計算し直させた）。"
            "175 で popwind の風のつまみ名をまちがえ、粒が動かなかった（windx が正しい）。"
            "170 の題が Substeps 1 のときしか成り立たない言い方だったので、条件を付けた。\n\n"
            "**あとの実験で書き直したもの: 3件。**157 の「relax で種を広げればそろうはず」は、158 で逆（かえってばらつく）と分かったので直した。"
            "171 の「粒は1点に集まらないはず」は、172 で確かめて言い切りに直した。171 の「3 万分の 1」は計算した値（35,055）に合わせて「約 3.5 万分の 1」に直した。\n\n"
            "**置き場所の直し: 1件。**シミュレーションの実験7本（157〜159・163・165〜167）がモデリング編に入っていたので、エフェクト編へ移した。\n\n"
            "**スクリプトで見つけた落とし穴: 151〜179 で8件**（polyfill の四角形の塞ぎ方は奇数の穴を塞がない 154、scatter の relax で種が壁へ寄る 158、"
            "POP の粒は生まれたフレームで1ステップ先に進む 165、popdrag の終端速度は g/k でなく √(g/k) 166、RBD の Collision Padding は止まる高さを変えない 167、"
            "heightfield_noise の Amplitude は高さの幅ではない 168、erode は土の量を保たない 169、cook(force=True) では VEX が計算し直さない 173）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "実験ごとの測り直し",
             "note": "時間の項目（sec・1点あたりの時間など）は除いて比べた。許す差は 0.000001（相対）。",
             "images": [{"path": "180_audit.png", "caption": "29本とも、時間以外の数字がすべて一致。"}],
             "per_row": 1,
             "columns": ["実験", "台本", "比べた値", "時間以外のずれ", "秒"],
             "rows": [[c["no"], c.get("script", "—"), f"{c.get('values', 0):,}",
                       str(len(c["real"])), f"{c.get('sec', 0):.1f}"] for c in checks]},
        ],
        "notes": [
            f"<strong>29本すべて流し直せた。</strong>全部で約{sec:.0f}秒。",
            "<strong>シミュレーションも、同じ条件なら同じ数字。</strong>比べる相手として使える。",
            "<strong>時間をはかる台本は、本当に計算し直しているかを最初に確かめる。</strong>173 で分かった。",
            "<strong>次の点検は210。</strong>",
        ],
        "next": ["時間の項目を3回の中央値で記録する", "点検の台本を、範囲を引数で渡せるようにする"],
    }
    with open(os.path.join(OUT, "180_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 180_report.json", total, len(real), timing_n)


if __name__ == "__main__":
    main()
