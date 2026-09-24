# -*- coding: utf-8 -*-
"""実験238 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font, line_chart  # noqa: E402


def main():
    with open(os.path.join(OUT, "238_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["color_limit"]: r for r in d["rows"]}
    ks = sorted(t)
    line_chart(os.path.join(OUT, "238_curve.png"),
               [{"label": "光の道の明るさ（128 サンプル）", "points": [(k, t[k]["path_mean"]) for k in ks]}],
               "Color Limit と光の道の明るさ（1 を超えると画では白く飛ぶ）", "Color Limit", "明るさの平均")
    font = _font(15)
    shots = (1, 3, 10, 1000)
    sheet = Image.new("RGB", (320 * 4, 160 + 26), (236, 236, 238))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(shots):
        sheet.paste(Image.open(os.path.join(OUT, f"238_cl{k}.png")).convert("RGB").crop((160, 170, 480, 330)), (i * 320, 26))
        dr.text((i * 320 + 6, 4), f"Color Limit {k}{'（既定）' if k == 10 else ''}", fill=(30, 30, 30), font=font)
    sheet.save(os.path.join(OUT, "238_grid.png"))
    table = [[str(k) + ("（既定）" if k == 10 else ""), f"{t[k]['sec']:.1f}", f"{t[k]['path_mean']:.2f}", f"{t[k]['hot_px']:,}", f"{t[k]['noise'] * 100:.0f}"] for k in ks]
    g = lambda k, f: t[k][f]  # noqa: E731
    payload = {
        "title": f"水面に映る太陽のきらめきは、Karma の Color Limit（既定 10）で明るさが切り詰められている。1000 にすると光の道は {g(1000, 'path_mean') / g(10, 'path_mean'):.1f} 倍明るく、"
                 f"16 サンプルのざらつきも {g(10, 'noise') * 100:.0f}% → {g(1000, 'noise') * 100:.0f}% に増える。1 に下げるときらめきが鈍る",
        "summary":
            "**課題: 水面やガラスに太陽が映る場面では、ぽつぽつと白い点（ファイアフライ）が出やすい。Karma の Color Limit は、明るすぎる光を上限で切り詰めて、それを抑える。"
            "上げ下げすると、きらめきの明るさとざらつきはどう変わるか。**\n\n"
            "実践「冬の朝の七里ヶ浜」の場面で、Color Limit を 1・3・10（既定）・30・100・1000 にし（Indirect Color Limit は既定どおり同じ値）、"
            "640×360・16 サンプル（ノイズ除去なし）で撮った。光の道（太陽の下の水面）の明るさの平均は同じ Color Limit の 128 サンプルの画で測り、"
            "16 サンプルとの差をざらつき（明るさに対する割合）とした。\n\n"
            f"**Color Limit を上げるほど、光の道は明るくなり続ける。**明るさの平均は 1・3・10・30・100・1000 で {g(1, 'path_mean'):.2f}・{g(3, 'path_mean'):.2f}・{g(10, 'path_mean'):.2f}・"
            f"{g(30, 'path_mean'):.2f}・{g(100, 'path_mean'):.2f}・{g(1000, 'path_mean'):.2f}。太陽を映した光はとても明るいので、既定の 10 では大きく切り詰められていた。\n\n"
            f"**上げると、ざらつきも増える。**16 サンプルでのざらつきは {g(1, 'noise') * 100:.0f}・{g(3, 'noise') * 100:.0f}・{g(10, 'noise') * 100:.0f}・{g(30, 'noise') * 100:.0f}・"
            f"{g(100, 'noise') * 100:.0f}・{g(1000, 'noise') * 100:.0f}%。明るさ 5 を超える画素（画全体）は {g(1, 'hot_px')}・{g(3, 'hot_px')}・{g(10, 'hot_px')}・{g(30, 'hot_px')}・{g(100, 'hot_px')}・{g(1000, 'hot_px')} 個。"
            f"撮る時間はほとんど変わらない（{g(1, 'sec'):.1f}〜{max(r['sec'] for r in t.values()):.1f} 秒）。\n\n"
            "**画（0〜1 に切った PNG）で見える違いは、1〜3 の間だけ。**1 ではきらめきが鈍い灰白になり、10 以上は白く飛んで同じに見えた。"
            "10 を超える明るさは、あとで露出を下げたり、光のにじみ（グロー）を足したりするときにだけ効く。\n\n"
            "**決め方: そのまま画にするなら既定の 10 でよい。**あとでにじみを足す・露出を下げるなら上げるが、ざらつきが増えるのでサンプルを増やすかノイズ除去を入れる。"
            "1〜3 に下げると、ざらつきは減るがきらめきが鈍る。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Color Limit と光の道（640×360・16 サンプル、光の道のまわりを切り出し）",
             "images": [{"path": "238_grid.png", "caption": "左から 1・3・10（既定）・1000。1 はきらめきが鈍く、10 以上は画では同じに白く飛ぶ。"},
                        {"path": "238_curve.png", "caption": "明るさは 1000 まで上がり続ける。"}],
             "per_row": 1, "columns": ["Color Limit", "撮る時間（秒）", "光の道の明るさ", "明るさ 5 超の画素", "ざらつき（%）"], "rows": table},
        ],
        "notes": [
            f"<strong>太陽のきらめきは、既定の Color Limit 10 で明るさが切り詰められている。</strong>1000 で {g(1000, 'path_mean') / g(10, 'path_mean'):.1f} 倍。",
            f"<strong>上げるとざらつきが増える（16 サンプルで {g(10, 'noise') * 100:.0f}% → {g(1000, 'noise') * 100:.0f}%）。</strong>",
            "<strong>そのまま画にするなら 10 でよい。</strong>画で見える違いは 1〜3 の間だけ。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "238_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])


if __name__ == "__main__":
    main()
