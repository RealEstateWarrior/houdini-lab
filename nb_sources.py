# -*- coding: utf-8 -*-
"""Gemini Notebook「Houdini 操作ガイド」に入れるソースを、題材ごとに作る（2026-09-24）。

SOURCE_STRATEGY.md の方針（実験1本1ソースにせず、テーマ単位で束ねて差し替える）どおりにする。
それまでは全実験が「実験ログ A」1つ（30MB）に入っていて、広く薄い1文書になっていた。

    python nb_sources.py          → out/nb/ に PDF と Markdown を作る
作ったあとの差し替え（古いソースの削除・追加）は Claude が notebooklm の道具で行う。
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
NB = os.path.join(OUT, "nb")
sys.path.insert(0, HERE)

# 上から順に見て、最初に当たった題材に入れる
THEMES = [
    ("rbd", "実験ログ: 剛体と破壊（RBD）", ["RBD", "剛体", "破壊"]),
    ("vellum", "実験ログ: 布とやわらかい物（Vellum）", ["Vellum", "布", "ソフトボディ"]),
    ("pyro", "実験ログ: 煙と炎（Pyro・ボリューム）", ["煙", "炎", "Pyro", "ボリューム"]),
    ("fluid", "実験ログ: 液体と MPM（FLIP・砂・雪）", ["液体", "FLIP", "MPM", "海"]),
    ("pop", "実験ログ: 粒（POP）", ["パーティクル", "POP", "粒"]),
    ("look", "実験ログ: 見た目（Karma・材質・テクスチャ）", ["レンダリング", "Karma", "テクスチャ", "COP", "材質"]),
    ("terrain", "実験ログ: 地形（HeightField）", ["地形", "HeightField"]),
    ("groom", "実験ログ: 毛とリグ（グルーム・APEX）", ["グルーム", "毛", "APEX", "リグ"]),
    ("tools", "実験ログ: VEX・道具・速さ", ["VEX", "ツール", "速度", "効率化", "書き出し", "USD", "点検"]),
]
MODEL_SPLIT = 120   # モデリングは本数が多いので2つに分ける


def theme_of(tags):
    for key, _, words in THEMES:
        if any(w in tags for w in words):
            return key
    return None


def report_path(no):
    name = "box_mountain_report.json" if no == "001" else f"{no}_report.json"
    path = os.path.join(OUT, name)
    return path if os.path.exists(path) else None


def plain(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text or ""))


def main():
    import build_site
    import report_pdf
    os.makedirs(NB, exist_ok=True)
    groups = {}
    for item in build_site.DONE:
        key = theme_of(item["tags"])
        if key is None:
            key = "model1" if int(item["no"]) <= MODEL_SPLIT else "model2"
        path = report_path(item["no"])
        if path:
            groups.setdefault(key, []).append(path)
    titles = {k: t for k, t, _ in THEMES}
    titles["model1"] = f"実験ログ: プロシージャルモデリング（001〜{MODEL_SPLIT}）"
    titles["model2"] = f"実験ログ: プロシージャルモデリング（{MODEL_SPLIT + 1}〜）"
    made = []
    for key, paths in groups.items():
        out = os.path.join(NB, f"exp_{key}.pdf")
        report_pdf.build_bundle(paths, out, titles[key],
                                intro="Houdini 研究部で、hython で実際に測った実験の記録。数字はどれも測った値。")
        made.append((titles[key], out, len(paths)))

    # 実践（作り方の手順）は Markdown 1つに
    with open(os.path.join(HERE, "guides.json"), encoding="utf-8") as fp:
        guides = json.load(fp)["guides"]
    lines = ["# 実践: Houdini で作る手順（Houdini 研究部）", "",
             "どの実践も hython で組んで確かめた手順。数字は測った値。hip はサイトから開ける。", ""]
    for i, g in enumerate(guides, 1):
        lines += [f"## 実践{i:02d} {g['title']}", "", plain(g["lede"]), ""]
        for label, value in g.get("facts") or []:
            lines.append(f"- {label}: {value}")
        lines.append("")
        for j, s in enumerate(g["steps"], 1):
            lines += [f"### 手順{j} {s['title']}（{s['node']}）", "", plain(s["body"]), ""]
        if g.get("traps"):
            lines += ["### 落とし穴", ""]
            for t in g["traps"]:
                lines.append(f"- **{plain(t['title'])}**: {plain(t['body'])}")
            lines.append("")
    path = os.path.join(NB, "practice.md")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    made.append(("実践: Houdini で作る手順", path, len(guides)))

    # ノード解説も Markdown 1つに
    with open(os.path.join(HERE, "nodes.json"), encoding="utf-8") as fp:
        nodes = json.load(fp)
    lines = ["# ノード解説（Houdini 研究部）", "",
             "つまみの名前は Houdini 21.0 の実物から取ったもの。", ""]
    count = 0
    for group in nodes["groups"]:
        lines += [f"## {group['label']}", ""]
        for n in group["nodes"]:
            count += 1
            lines += [f"### {n['name']}（{n.get('kind', '')}）", "", plain(n.get("one")), "", plain(n.get("what")), ""]
            for p in n.get("params") or []:
                lines.append(f"- `{p[0]}`: {plain(p[1])}")
            if n.get("gotcha"):
                lines += ["", "注意: " + plain(n["gotcha"])]
            lines.append("")
    path = os.path.join(NB, "nodes.md")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    made.append(("ノード解説", path, count))

    with open(os.path.join(NB, "_made.json"), "w", encoding="utf-8") as fp:
        json.dump(made, fp, ensure_ascii=False, indent=1)
    for title, path, n in made:
        print(f"{n:4d}  {os.path.getsize(path) // 1024:6d}KB  {title}")


if __name__ == "__main__":
    main()
