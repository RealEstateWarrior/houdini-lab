# -*- coding: utf-8 -*-
"""実験220 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart  # noqa: E402

LAB = {"base": "揺らぎなし", "ctrl": "Turbulence 1（revertToDefaults のまま）", "free": "Turbulence 1・Use Control Field 切り",
       "ctrl_on": "Turbulence 1・Use Control Field 入り"}


def main():
    with open(os.path.join(OUT, "220_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    with open(os.path.join(OUT, "220_density.json"), encoding="utf-8") as fp:
        dens = json.load(fp)
    t = {(r["case"], r["rep"]): r for r in d["rows"]}
    same = {c: t[(c, 1)]["heights"] == t[(c, 2)]["heights"] for c in LAB}
    eq = lambda a, b: t[(a, 1)]["heights"] == t[(b, 1)]["heights"]  # noqa: E731
    m = lambda c: t[(c, 1)]["height_mean"]  # noqa: E731
    series = [{"label": LAB[c], "points": [(i + 1, h) for i, h in enumerate(t[(c, 1)]["heights"])]} for c in ("base", "free", "ctrl_on")]
    line_chart(os.path.join(OUT, "220_heights.png"), series, "炎の高さ（フレームごと）", "フレーム", "高さ（m）")
    table = [[LAB[c], ("入り" if t[(c, 1)]["turb_parms"]["turbulence_usecontrol"] else "切り"), f"{m(c):.3f}", "同じ" if same[c] else "違う"] for c in LAB]
    payload = {
        "title": f"焚き火の Turbulence は、Use Control Field を入れると効かない（揺らぎなしと全フレーム同じ）。切ると炎の高さ {m('free'):.2f} m（なし {m('base'):.2f} m）。"
                 "実験201 の結論は正しく、点検で合わなかったのは revertToDefaults が Use Control Field を「切り」に戻したため",
        "summary":
            "**課題: pyrosolver の Turbulence は、Use Control Field を入れたままでも効くのか。実験201 の結論（切らないと効かない）は正しいか。点検（実験210）で 201 の 2 条件が記録と合わなかったのはなぜか。**\n\n"
            "実験201 と同じ焚き火（実験202 の組み立て、Voxel Size 0.04、72 フレーム、寿命 0.25・浮力 0.25・冷め方 1）で、"
            "揺らぎなし・Turbulence 1 を revertToDefaults のまま・Use Control Field を切り・Use Control Field を入り、の 4 条件を、"
            "それぞれ別の Houdini で 2 回ずつ回した。36〜72 フレームの炎の高さの平均で比べた。\n\n"
            f"**毎回同じに回る。**4 条件とも、1 回目と 2 回目のフレームごとの高さがすべて一致した。\n\n"
            f"**Use Control Field を入れると、Turbulence は効かない。**入れた条件は、揺らぎなしとすべてのフレームで同じ値（平均 {m('ctrl_on'):.3f} m）だった"
            f"（{'一致' if eq('ctrl_on', 'base') else '不一致'}）。切ると {m('free'):.3f} m で、揺らぎなし（{m('base'):.3f} m）より高くなった。実験201 の結論は正しかった。\n\n"
            "**点検で合わなかった原因: 「既定」が 2 つあった。**pyrosolver を作った直後、Use Control Field は「入り」になっている。"
            "ところが、つまみの既定値（revertToDefaults で戻る値）は「切り」だった（hython で確かめた。作った直後の値は既定値と違う、と出る）。"
            f"点検で 201 の台本を直したとき、借りた組み立ての設定を revertToDefaults で戻したので、Use Control Field も「切り」になった。"
            f"そのため「入り」のつもりの 2 条件で Turbulence が効き、炎が高く出た（revertToDefaults のまま: {m('ctrl'):.3f} m。切りと"
            f"{'全フレーム同じ' if eq('ctrl', 'free') else '違う'}）。"
            "201 の台本を「作った直後と同じく入り」に直して 2 条件を流し直すと、記録と全フレーム一致した。\n\n"
            f"**なぜ入りだと効かないのかは、確かめきれなかった。**Control Field は既定で density、範囲は 0〜1。焚き火の density の最大は "
            f"フレーム 24・48 とも {dens['24']['density']}（範囲の中）で、「煙が無いから 0 になる」わけではなかった。\n\n"
            "**決め方: 焚き火を Turbulence で揺らすなら、Use Control Field を切る。**台本で設定を戻すときは、revertToDefaults ではなく、作った直後の値で戻す。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "条件ごとの炎の高さ（36〜72 フレームの平均）",
             "images": [{"path": "220_heights.png", "caption": "Use Control Field 入りの線は、揺らぎなしの線と重なる。"}],
             "per_row": 1, "columns": ["条件", "Use Control Field", "高さの平均（m）", "2 回目と"], "rows": table},
        ],
        "notes": [
            "<strong>Use Control Field を入れると、Turbulence は効かない。</strong>揺らぎなしと全フレーム同じ。実験201 の結論は正しかった。",
            f"<strong>切ると効く。</strong>炎の高さ {m('base'):.2f} → {m('free'):.2f} m。",
            "<strong>pyrosolver を作った直後の Use Control Field は「入り」、revertToDefaults で戻る値は「切り」。</strong>点検で合わなかったのはこのため。",
            "<strong>毎回同じに回る。</strong>2 回回して全フレーム一致。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "220_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])
    print(same, eq("ctrl_on", "base"), eq("ctrl", "free"))


if __name__ == "__main__":
    main()
