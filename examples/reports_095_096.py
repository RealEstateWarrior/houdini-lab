# -*- coding: utf-8 -*-
"""実験095・096 の図とレポートを、測った値から組み立てる。

    python examples/reports_095_096.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def stats(no):
    with open(os.path.join(OUT, f"{no}_stats.json"), encoding="utf-8") as fp:
        return json.load(fp)


def write(no, payload):
    with open(os.path.join(OUT, f"{no}_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた:", f"{no}_report.json")


def num(value, digits=6):
    return "—" if value is None else f"{value:.{digits}f}"


def do_095():
    data = stats("095")
    gap_rows = data["rows"]
    mesh_rows = data["mesh_rows"]
    gap = data["gap"]
    closed = [r for r in gap_rows if r["merged"] > 0]
    open_rows = [r for r in gap_rows if r["merged"] == 0]
    threshold = closed[0]["dist"]
    last_open = open_rows[-1]["dist"]

    line_chart(
        os.path.join(OUT, "095_fuse.png"),
        [{"label": "残った点の数（元 2,402点の球）",
          "points": [(r["dist"], r["points"]) for r in mesh_rows],
          "color": PALETTE[0]},
         {"label": "元の形からのずれ 平均 ×100万",
          "points": [(r["dist"], (r["gap_mean"] or 0) * 1e6) for r in mesh_rows],
          "color": PALETTE[1], "dash": True}],
        title=f"距離を上げると点は減る。形が動き出すのは 0.04 を超えてから",
        x_label="Snap Distance", y_label="点の数 ／ ずれ×100万")
    print("095_fuse.png")

    write("095", {
        "title": f"隙間 {gap} の継ぎ目は、Snap Distance が {threshold} になって初めて閉じる"
                 f" — {last_open} では閉じない",
        "summary":
            f"fuse は Snap Distance より近い点をひとつにまとめる。では「より近い」の"
            "境目はどこなのか。そして距離を上げていくと、狙った継ぎ目だけが閉じるのか、"
            "細かい所まで潰れてしまうのか。2つの場面で測った。\n\n"
            f"ひとつ目は、板を2枚ちょうど {gap} だけ離して並べた形（{data['base_points']}点）。"
            f"Snap Distance を 0 から上げていくと、{last_open} までは1点も合わさらず、"
            f"{threshold} でいきなり 11点（継ぎ目の1列ぶん）が合わさった。"
            "**距離が隙間と同じ値になったところで閉じる。** それより手前では、"
            "どれだけ近くても閉じない。\n\n"
            f"ふたつ目は、球（50×50、{data['mesh_base_points']}点）にそのまま fuse をかけた場合。"
            f"距離 0.01 で 50点、0.02 で 118点が減るが、**形は動かない**"
            f"（ずれ 0.0）。極のあたりに同じ位置の点が重なっていて、それが掃除されている。\n\n"
            f"形が動き出すのは 0.04 を超えてから。0.08 では点が元の "
            f"{[r for r in mesh_rows if r['dist'] == 0.08][0]['kept_pct']}% まで減り、"
            f"ずれは {num([r for r in mesh_rows if r['dist'] == 0.08][0]['gap_mean'])}。"
            f"0.16 では {[r for r in mesh_rows if r['dist'] == 0.16][0]['kept_pct']}% まで減り、"
            f"ずれは {num(mesh_rows[-1]['gap_mean'])} で、形そのものが崩れる。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": f"板2枚（隙間 {gap}）の継ぎ目が閉じる境目",
             "note": f"1辺1.0の板を11×11で2枚、x方向に {gap} 離して並べた。"
                     "継ぎ目に向き合う点は左右で11個ずつ。",
             "images": [],
             "per_row": 1,
             "columns": ["Snap Distance", "残った点", "合わさった点"],
             "rows": [[f"{r['dist']:g}", str(r["points"]), str(r["merged"])]
                      for r in gap_rows]},
            {"label": "球にそのままかけたとき",
             "note": "球（50×50）の 2,402点。ずれは各点から元の面までの最短距離の平均。"
                     "距離 0.01・0.02 では点が減ってもずれが 0 のままで、"
                     "重なっていた点だけが掃除されたことが分かる。",
             "images": [{"path": "095_fuse.png",
                         "caption": "点は早い段階から減るが、形が動き出すのは 0.04 を超えてから。"}],
             "per_row": 1,
             "columns": ["Snap Distance", "点", "元の%", "面", "ずれ 平均"],
             "rows": [[f"{r['dist']:g}", str(r["points"]), f"{r['kept_pct']}%",
                       str(r["prims"]), num(r["gap_mean"])] for r in mesh_rows]},
        ],
        "notes": [
            f"<strong>境目は隙間と同じ値。</strong>隙間 {gap} の継ぎ目は、"
            f"Snap Distance {last_open} では閉じず、{threshold} で閉じた。"
            "「より近い」は、距離がちょうど同じときも含む。",
            "<strong>点が減っても形が変わらないことがある。</strong>"
            "球では距離 0.01 で 50点、0.02 で 118点が減るが、ずれは 0.0 のまま。"
            "同じ位置に重なっていた点が掃除されただけ。",
            "<strong>形が崩れ始めるのは 0.04 より上。</strong>0.04 でずれ 0.000002、"
            f"0.08 で {num([r for r in mesh_rows if r['dist'] == 0.08][0]['gap_mean'])}、"
            f"0.16 で {num(mesh_rows[-1]['gap_mean'])}。"
            "掃除のつもりで大きな値を入れると、形まで持っていかれる。",
        ],
        "next": [
            "隙間が斜めのときも、境目は同じ値になるか",
            "Snap To（どこへ寄せるか）を変えると位置がどうずれるか",
        ],
    })


def do_096():
    data = stats("096")
    rows = data["rows"]
    seeds = data["seeds"]
    flat = [r for r in rows if r["shape"].startswith("平ら")]
    bumpy = [r for r in rows if not r["shape"].startswith("平ら")]
    diffs = {r["diff"] for r in rows}

    line_chart(
        os.path.join(OUT, "096_scatter.png"),
        [{"label": "平らな板（1面）",
          "points": [(r["got"], r["seconds"]) for r in flat],
          "color": PALETTE[0]},
         {"label": "凹凸のある球（3,540面）",
          "points": [(r["got"], r["seconds"]) for r in bumpy[1:]],
          "color": PALETTE[1], "dash": True}],
        title="点の数と、かかる時間（100万点で約1秒）",
        x_label="出た点の数", y_label="秒")
    line_chart(
        os.path.join(OUT, "096_per.png"),
        [{"label": "平らな板（1面）",
          "points": [(r["got"], r["us_per_point"]) for r in flat],
          "color": PALETTE[0]},
         {"label": "凹凸のある球（3,540面）",
          "points": [(r["got"], r["us_per_point"]) for r in bumpy[1:]],
          "color": PALETTE[1], "dash": True}],
        title="1点あたりの時間は、数が増えるほど下がる（準備の分が薄まる）",
        x_label="出た点の数", y_label="1点あたりのマイクロ秒")
    print("096_scatter.png 096_per.png")

    write("096", {
        "title": "Force Total Count はぴったり合う — 10通り試して差は1つも出なかった",
        "summary":
            "scatter の「Force Total Count」は、指定した数をそのまま出すという意味の"
            "つまみ。面の大きさが場所によって違う形でも、本当にぴったりになるのか。"
            "100点から100万点まで、2つの形で測った。\n\n"
            f"結果は、**10通りすべてで差が {sorted(diffs)[0]:+d}**。"
            "平らな板（1面）でも、凹凸のある球（3,540面）でも、指定した数がそのまま出た。"
            "種を変えても数は変わらない（1万点で3回、いずれも 10,000点）。\n\n"
            "時間は点の数にほぼ比例する。板では 1万点で "
            f"{[r for r in flat if r['asked'] == 10000][0]['seconds']}秒、"
            f"100万点で {flat[-1]['seconds']}秒。100倍の点で "
            f"{round(flat[-1]['seconds'] / [r for r in flat if r['asked'] == 10000][0]['seconds'], 1)}倍。\n\n"
            "1点あたりで見ると、数が少ないうちは割高になる。板では100点で "
            f"{flat[0]['us_per_point']}マイクロ秒、100万点で {flat[-1]['us_per_point']}マイクロ秒。"
            "準備にかかる固定の分が、点の数で薄まっていく。\n\n"
            "面の数が多いほうがわずかに遅い。1万点で板が "
            f"{[r for r in flat if r['asked'] == 10000][0]['seconds']}秒、"
            f"球が {[r for r in bumpy if r['asked'] == 10000][0]['seconds']}秒。"
            "ただし差は小さく、点の数のほうがずっと効く。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "指定した数と、実際に出た数・時間",
             "note": "Force Total Count を入れ、Total Count に左の数を指定した。"
                     f"球の100点だけ {bumpy[0]['seconds']}秒と外れて見えるが、"
                     "これは上流の mountain を初めて計算した分が乗っているため。"
                     "この行だけは時間の比べ物にならない。",
             "images": [{"path": "096_scatter.png",
                         "caption": "時間は点の数にほぼ比例する。100万点で約1秒。"},
                        {"path": "096_per.png",
                         "caption": "1点あたりの時間は、数が増えるほど下がっていく。"}],
             "per_row": 2,
             "columns": ["形", "指定", "出た数", "差", "秒", "1点あたりμ秒"],
             "rows": [[r["shape"], f"{r['asked']:,}", f"{r['got']:,}",
                       f"{r['diff']:+d}", f"{r['seconds']:.3f}",
                       str(r["us_per_point"])] for r in rows]},
            {"label": "種を変えても数は変わらない（1万点）",
             "note": "Seed だけを変えて3回。位置は変わるが数は同じ。",
             "images": [],
             "per_row": 1,
             "columns": ["Seed", "出た数", "秒"],
             "rows": [[str(s["seed"]), f"{s['got']:,}", f"{s['seconds']:.3f}"]
                      for s in seeds]},
        ],
        "notes": [
            f"<strong>数はぴったり合う。</strong>10通り試して、差はすべて "
            f"{sorted(diffs)[0]:+d}。面の大きさがばらついた形でも、"
            "指定した数がそのまま出た。",
            "<strong>時間は点の数に比例する。</strong>板では1万点 "
            f"{[r for r in flat if r['asked'] == 10000][0]['seconds']}秒 → 100万点 "
            f"{flat[-1]['seconds']}秒。100倍の点で "
            f"{round(flat[-1]['seconds'] / [r for r in flat if r['asked'] == 10000][0]['seconds'], 1)}倍。",
            "<strong>少ない点ほど割高。</strong>1点あたりは板の100点で "
            f"{flat[0]['us_per_point']}マイクロ秒、100万点で {flat[-1]['us_per_point']}"
            "マイクロ秒。準備の固定分が薄まっていく。少しだけ散らすのを何度も繰り返すより、"
            "一度にまとめて散らすほうが得。",
        ],
        "next": [
            "Density Scale やアトリビュートで濃さを変えても、合計はぴったり合うか",
            "Force Total Count を切ったときは、どれだけずれるか",
        ],
    })


if __name__ == "__main__":
    do_095()
    do_096()
