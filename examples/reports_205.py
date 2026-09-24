# -*- coding: utf-8 -*-
"""実験205 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import _font  # noqa: E402


def sheet(path, items, crop=None, scale=1.0, contrast=1.0, cols=None):
    """画を横に並べ、上に題を書く。items = [(tag, 題), ...]"""
    font = _font(17)
    ims = []
    for tag, _ in items:
        im = Image.open(os.path.join(OUT, f"205_{tag}.png")).convert("RGB")
        if crop:
            im = im.crop(crop)
        if scale != 1.0:
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.NEAREST if scale > 1 else Image.LANCZOS)
        if contrast != 1.0:
            im = ImageEnhance.Contrast(im).enhance(contrast)
        ims.append(im)
    cols = cols or len(ims)
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    out = Image.new("RGB", (w * cols, (h + 30) * rows), (24, 24, 26))
    d = ImageDraw.Draw(out)
    for i, (im, (_, lab)) in enumerate(zip(ims, items)):
        x, y = (i % cols) * w, (i // cols) * (h + 30)
        out.paste(im, (x, y + 30))
        d.text((x + 8, y + 5), lab, fill=(235, 235, 235), font=font)
    out.save(path)


def main():
    with open(os.path.join(OUT, "205_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["tag"]: r for r in d["rows"]}
    sec = lambda k: t[k]["sec"]  # noqa: E731
    gr = lambda k: t[k]["grain"]  # noqa: E731
    # 図 1: ぼけ・ぶれの見た目（16 サンプル）
    sheet(os.path.join(OUT, "205_look.png"),
          [("base_16", "ぼけ・ぶれ無し"), ("both_16", "両方（F-Stop 0.7・Shutter 0.5）"),
           ("s_both_16", "両方を強く（F-Stop 0.2・Shutter 1）")], scale=0.5)
    # 図 2: ざらつき（背景の一部を 2 倍に拡大し、コントラストを 4 倍にした）
    sheet(os.path.join(OUT, "205_grain.png"),
          [("both_16", f"16 サンプル（{sec('both_16'):.0f} 秒）"), ("both_256", f"256 サンプル（{sec('both_256'):.0f} 秒）"),
           ("both_64_n0.0025", f"64・Noise Level 0.0025（{sec('both_64_n0.0025'):.0f} 秒）"),
           ("tune_both_16_oidn", f"16＋ノイズ除去（{sec('tune_both_16_oidn'):.0f} 秒）")],
          crop=(560, 110, 760, 230), scale=2.0, contrast=4.0, cols=2)
    gb = lambda k: t[k]["grain_box"]  # noqa: E731
    order = [("base_16", "ぼけ・ぶれ無し・16"), ("base_64", "ぼけ・ぶれ無し・64"), ("base_256", "ぼけ・ぶれ無し・256"),
             ("mblur_16", "ぶれ・16"), ("dof_16", "ぼけ・16"), ("both_16", "両方・16"), ("both_64", "両方・64"), ("both_256", "両方・256"),
             ("s_both_16", "両方を強く・16"), ("s_both_64", "両方を強く・64"), ("s_both_256", "両方を強く・256"),
             ("tune_both_16_n0.005", "両方・16・Noise Level 0.005"), ("tune_both_16_n0.0025", "両方・16・Noise Level 0.0025"),
             ("both_64_n0.005", "両方・64・Noise Level 0.005"), ("both_64_n0.0025", "両方・64・Noise Level 0.0025"),
             ("tune_both_16_oidn", "両方・16・ノイズ除去"), ("tune_both_64_oidn", "両方・64・ノイズ除去")]
    table = [[lab, f"{sec(k):.1f}", f"{gr(k):.2f}", f"{gb(k):.2f}", f"{t[k]['grain_near']:.2f}"] for k, lab in order]
    add = lambda a, b: (sec(a) / sec(b) - 1)  # noqa: E731
    payload = {
        "title": f"Karma のぼけ（被写界深度）とぶれ（モーションブラー）は、時間を +{add('both_16', 'base_16'):.0%}〜{add('s_both_64', 'base_64'):.0%} しか増やさない — ざらつきを消すのはサンプル数ではなくノイズ除去。16 サンプル＋OIDN で {sec('tune_both_16_oidn'):.0f} 秒",
        "summary":
            "**課題: 映像らしく見せるために、ぼけ（被写界深度）とぶれ（モーションブラー）を入れたい。入れると何倍重くなるのか。ぼけ・ぶれた所のざらつきを消すには、何を上げればよいのか。**\n\n"
            "奥へ並んだ球 7 つと、画面を横切る箱（秒速 12 m）を、960×540 で撮った。Karma の決め方は既定のまま（Convergence Mode = Variance、Noise Level 0.01）で、"
            "Primary Samples と Max Secondary Samples を同じ数（16・64・256）にした。ぼけは F-Stop 0.7（ピントは 4 番目の球）、ぶれはカメラの Shutter Time 0.5 フレーム（既定）。"
            "強くした組は F-Stop 0.2・Shutter Time 1。ざらつきの目安は、画を 3×3 の中央値でならした画との差（画素の値 0〜255 の二乗平均の平方根）で、"
            "画全体・動く箱のまわり・手前の球のまわりで測った。"
            "（はじめは Noise Level 0.001 の画を答えにしようとしたが、1 枚 8 分を超えても終わらなかったのでやめた）\n\n"
            f"**ぼけ・ぶれを入れても、時間はほとんど増えない。**16 サンプルで、無し {sec('base_16'):.1f} 秒・ぶれ {sec('mblur_16'):.1f} 秒・ぼけ {sec('dof_16'):.1f} 秒・両方 {sec('both_16'):.1f} 秒。"
            f"強くしても {sec('s_both_16'):.1f} 秒。64 サンプルでも 無し {sec('base_64'):.1f} 秒 → 強い両方 {sec('s_both_64'):.1f} 秒（+{add('s_both_64', 'base_64'):.0%}）。\n\n"
            f"**ぶれた所は少しざらつく。**16 サンプルの箱のまわりのざらつきは、無し {gb('base_16'):.2f}・両方 {gb('both_16'):.2f}・強い両方 {gb('s_both_16'):.2f}。"
            "画全体では差がほとんど出ない（ぼけ・ぶれの所が画の一部だけのため）。\n\n"
            f"**サンプル数を上げても、ざらつきは減らなかった。**両方入れた画で、16・64・256 サンプルは {sec('both_16'):.0f}・{sec('both_64'):.0f}・{sec('both_256'):.0f} 秒と延びたのに、"
            f"ざらつきは {gr('both_16'):.2f}・{gr('both_64'):.2f}・{gr('both_256'):.2f} と、むしろ増えた（拡大図でも 256 の方が粗い）。"
            "Noise Level 0.01 に届いた所でサンプルを打ち切る決め方なので、上限を上げても仕上がりのざらつきは Noise Level で決まると考えられるが、増える理由は確かめていない。\n\n"
            f"**Noise Level を下げると減るが、時間が大きく延びる。**64 サンプルで 0.01・0.005・0.0025 は {sec('both_64'):.0f}・{sec('both_64_n0.005'):.0f}・{sec('both_64_n0.0025'):.0f} 秒、"
            f"ざらつきは {gr('both_64'):.2f}・{gr('both_64_n0.005'):.2f}・{gr('both_64_n0.0025'):.2f}。16 サンプルのままだと 0.0025 でも {gr('tune_both_16_n0.0025'):.2f}（{sec('tune_both_16_n0.0025'):.0f} 秒）までしか下がらない。\n\n"
            f"**いちばん効いたのはノイズ除去（Denoiser = OIDN）。**16 サンプル＋ノイズ除去は {sec('tune_both_16_oidn'):.1f} 秒（入れない {sec('both_16'):.1f} 秒とほぼ同じ）で、"
            f"ざらつきは画全体 {gr('tune_both_16_oidn'):.2f}・箱のまわり {gb('tune_both_16_oidn'):.2f}。Noise Level 0.0025 の {sec('both_64_n0.0025'):.0f} 秒（箱のまわり {gb('both_64_n0.0025'):.2f}）より、短い時間で滑らかになった。"
            "コントラストを 4 倍にして拡大すると、ノイズ除去の画には大きなむらが少し見える。細かい模様のある物まで一緒にならしてしまうかは、この場面（模様が無い）では確かめていない。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "ぼけ・ぶれの見た目（16 サンプル）",
             "images": [{"path": "205_look.png", "caption": "左から 無し・両方（F-Stop 0.7、Shutter 0.5）・強い両方（F-Stop 0.2、Shutter 1）。箱は右へ秒速 12 m で動いている。"}],
             "per_row": 1, "columns": [], "rows": []},
            {"label": "ざらつき（背景の一部を 2 倍に拡大し、コントラストを 4 倍にした）",
             "images": [{"path": "205_grain.png", "caption": "サンプルを 256 に上げると、かえって粗い。Noise Level を下げるか、ノイズ除去を入れると滑らかになる。"}],
             "per_row": 1, "columns": ["条件（サンプル数）", "秒", "ざらつき（全体）", "箱のまわり", "手前の球"], "rows": table},
        ],
        "notes": [
            f"<strong>ぼけ・ぶれは遠慮なく入れてよい。</strong>時間は +{add('both_16', 'base_16'):.0%}〜{add('s_both_64', 'base_64'):.0%} しか増えなかった。",
            "<strong>ざらつきが気になっても、サンプル数を上げない。</strong>既定の Noise Level 0.01 のままでは、256 にしても滑らかにならず、時間だけ 3.3 倍になった。",
            f"<strong>仕上げは 16 サンプル＋ノイズ除去（OIDN）。</strong>{sec('tune_both_16_oidn'):.0f} 秒で、Noise Level 0.0025（{sec('both_64_n0.0025'):.0f} 秒）より滑らかだった。",
            "<strong>ノイズ除去が使えない場面では Noise Level を下げる。</strong>0.005 で約 2 倍、0.0025 で約 6 倍の時間。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "205_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 205_report.json")
    print(payload["title"])


if __name__ == "__main__":
    main()
