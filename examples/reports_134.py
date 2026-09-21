# -*- coding: utf-8 -*-
"""実験134 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def kind_of(expr):
    if expr.startswith("$F") or expr in ("$T", "$TSTART", "$TEND", "$FPS", "1/$FPS", "$FF-1"):
        return "時間（$F・$T など）"
    if expr.startswith("@"):
        return "属性（@N など）"
    if "ch(" in expr or "chs(" in expr or "chsraw(" in expr:
        return "ほかのつまみの参照（ch）"
    return "その他"


def main():
    with open(os.path.join(OUT, "134_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    with open(os.path.join(HERE, "nodes.json"), encoding="utf-8") as fp:
        nodes = json.load(fp)
    def base(name):
        """版の番号（::2.0 など）だけを外す。kinefx:: のような名前空間は残す。"""
        head, _, tail = name.rpartition("::")
        return head if head and tail.replace(".", "").isdigit() else name

    documented = {base(n["name"]) for g in nodes["groups"] for n in g["nodes"]}
    found = d["found"]
    kinds = Counter(kind_of(f["expr"]) for f in found)
    seen = set()
    ours = []
    for f in found:
        key = (base(f["node"]), f["parm"])
        if base(f["node"]) in documented and key not in seen:
            seen.add(key)
            ours.append(f)
    ours_attr = [f for f in found if kind_of(f["expr"]) == "属性（@N など）"]

    ks = list(kinds.most_common())
    line_chart(os.path.join(OUT, "134_expr.png"),
               [{"label": "式の入ったつまみの数", "points": [(i, c) for i, (_, c) in enumerate(ks)],
                 "color": PALETTE[0]}],
               title="最初から式が入っているつまみ（SOP 全体）: " + "・".join(f"{i}={k}" for i, (k, _) in enumerate(ks)),
               x_label="式の種類", y_label="つまみの数")
    print("134_expr.png")

    sp = d["set_probe"]
    payload = {
        "title": "最初から式が入っているつまみは SOP 全体で488個 — set しても式が残り、値は変わらない",
        "summary":
            "実験133 で、ray の Direction に最初から式が入っていて、Python の set が効かないと分かった。"
            f"同じ落とし穴がどれだけあるかを、SOP の全ノード {d['nodes_made']:,} 種類を1つずつ作って数えた"
            f"（{d['sec']:g} 秒）。\n\n"
            f"**最初から式が入っているつまみは {d['parms_with_expr']} 個、{d['nodes_with_expr']} 種類のノードにあった。** "
            "式の中身は、" + "、".join(f"{k} {v} 個" for k, v in kinds.most_common()) + "。"
            "多いのは $FSTART・$FEND（フレーム範囲）で、キャッシュや読み込みの箱に集まっている。\n\n"
            f"このサイトで解説しているノードでは {len(ours)} 個。"
            f"属性を読む式（@N など）は SOP 全体で {len(ours_attr)} 個で、ray の Direction がその代表。\n\n"
            "**式の入ったつまみに set すると、式は残り、値は変わらない。** ray の diry で、"
            f"set(−1) の前は 式 {sp['before'][0]}・値 {sp['before'][1]:g}、後も 式 {sp['after_set'][0]}・値 "
            f"{sp['after_set'][1]:g}。deleteAllKeyframes() で式を消してから set すると、値 {sp['after_delete'][1]:g} になった。\n\n"
            "スクリプトでつまみを入れるときは、keyframes() で式の有無を確かめ、あれば消してから入れる。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "このサイトで解説しているノードの、式の入ったつまみ",
             "note": "式は最初の80文字まで。",
             "images": [{"path": "134_expr.png", "caption": "式の種類ごとの数。時間の式が大半。"}],
             "per_row": 1,
             "columns": ["ノード", "つまみ", "画面の名前", "式"],
             "rows": [[f["node"], f["parm"], f["label"], f["expr"].replace("\n", " ")] for f in ours]},
        ],
        "notes": [
            f"<strong>式の入ったつまみは {d['parms_with_expr']} 個。</strong>大半はフレーム範囲（$FSTART・$FEND）。",
            "<strong>set は式を消さない。</strong>値を入れたいときは deleteAllKeyframes() が先。",
            "<strong>@N などの属性の式は要注意。</strong>入力に属性が無いと 0 になり、黙って効かない（ray が動かなかった）。",
        ],
        "next": [
            "DOP・LOP でも同じように数える",
            "hou.Parm.set ではなく setExpression / 値の上書き（lock）の振る舞いを比べる",
        ],
    }
    with open(os.path.join(OUT, "134_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 134_report.json", len(ours))


if __name__ == "__main__":
    main()
