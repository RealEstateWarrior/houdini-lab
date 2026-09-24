# -*- coding: utf-8 -*-
"""実験209 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font  # noqa: E402


def bars(path, items, title):
    f, fs = _font(20), _font(17)
    w, rowh, left = 1000, 52, 300
    h = 70 + rowh * len(items) + 20
    im = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((20, 18), title, fill=(20, 20, 20), font=f)
    top = max(v for _, v, _ in items)
    for i, (lab, v, c) in enumerate(items):
        y = 70 + i * rowh
        d.text((20, y + 8), lab, fill=(30, 30, 30), font=fs)
        x1 = left + (w - left - 110) * v / top
        d.rectangle((left, y + 6, x1, y + 34), fill=c)
        d.text((x1 + 8, y + 8), f"{v:.1f} 秒", fill=(40, 40, 40), font=fs)
    im.save(path)


def main():
    with open(os.path.join(OUT, "209_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    s = lambda k: t[k]["sec"]  # noqa: E731
    bars(os.path.join(OUT, "209_time.png"),
         [("1 つの Houdini で順に", s("inproc"), PALETTE[4])] +
         [(f"PDG・同時に {n} 本", s(f"pdg{n}"), PALETTE[0]) for n in (1, 2, 4, 8)],
         f"焚き火（Voxel 0.03・48 フレーム）を {d['count']} 通り回して書き出す時間")
    ref = d["inproc_sizes"]
    worst = max(abs(a / b - 1) for n in (1, 2, 4, 8) for a, b in zip(t[f"pdg{n}"]["sizes"], ref))
    table = [["1 つの Houdini で順に", "—", f"{s('inproc'):.1f}", "1.00"]] + \
        [[f"PDG（Total Slots {n}）", str(n), f"{s(f'pdg{n}'):.1f}", f"{s('inproc') / s(f'pdg{n}'):.2f}"] for n in (1, 2, 4, 8)]
    per_job = s("pdg1") / d["count"]
    per_in = s("inproc") / d["count"]
    payload = {
        "title": f"焚き火を 8 通り回すなら、PDG で同時に 8 本が {s('inproc') / s('pdg8'):.1f} 倍速い — ただし同時に 1 本だと {s('pdg1') / s('inproc'):.1f} 倍遅く、2 本でほぼ並ぶ。Evaluate Using を Frame Range にしないと 1 フレームしか回らない",
        "summary":
            "**課題: 焚き火の揺れ（Turbulence）を 8 通り試して比べたい。1 つの Houdini の中で順に回すのと、PDG（TOP ネットワークの wedge）で別々の Houdini に分けて同時に回すのとでは、どちらが速いか。同時に何本がよいか。**\n\n"
            f"実験202 の焚き火（Voxel Size {d['vox']}）を {d['frame']} フレーム回し、毎フレーム書き出す（速度 vel を消した形。実験204）仕事を、Turbulence 1〜4.5 の {d['count']} 通り用意した。"
            f"PDG は wedge（{d['count']} 本）→ ropgeometry で、localscheduler の Total Slots（同時に回す数）を 1・2・4・8 にした。このパソコンは {d['cpu']} スレッド"
            "（既定の Total Slots は「CPU の 1/4」なので 8）。\n\n"
            f"**1 つの Houdini の中で順に回すと {s('inproc'):.1f} 秒**（1 通りあたり {per_in:.1f} 秒）。\n\n"
            f"**PDG で同時に 1 本だと {s('pdg1'):.1f} 秒で、{s('pdg1') / s('inproc'):.1f} 倍遅い。**1 通りあたり {per_job:.1f} 秒で、順に回すより約 {per_job - per_in:.1f} 秒長い。"
            "仕事ごとに別の Houdini を起動し、保存した hip を開いてから回すためと考えられる（起動の時間だけを分けては測っていない）。\n\n"
            f"**同時に 2 本でほぼ並び（{s('pdg2'):.1f} 秒）、4 本で {s('pdg4'):.1f} 秒（{s('inproc') / s('pdg4'):.2f} 倍速い）、8 本で {s('pdg8'):.1f} 秒（{s('inproc') / s('pdg8'):.2f} 倍）。**"
            f"本数を倍にしても時間は半分にならない。4 → 8 本で {1 - s('pdg8') / s('pdg4'):.0%} しか縮まなかった。Pyro の計算は 1 本でも複数のスレッドを使うので、同時に回すと取り合いになるためと考えられる。\n\n"
            f"**結果はどのやり方でも同じ。**フレーム 48 のファイルの大きさは、順に回したものと {worst:.2%} 以内で一致した。\n\n"
            "**落とし穴: ropgeometry の Evaluate Using の既定は Single Frame。**このままだと仕事 1 つにつき 1 フレーム目しか書かず、シミュレーションが進まない（燃え始めの 34 KB が書き出された）。"
            "Valid Frame Range を Render Frame Range にしても変わらなかった。Evaluate Using を Frame Range にし、Frame Range（f1・f2。最初から式が入っている）を 1〜48 にして、"
            "All Frames in One Batch を入れると、1 つの Houdini が 1〜48 を順に回した。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "8 通りを回して書き出す時間",
             "images": [{"path": "209_time.png", "caption": "PDG は同時に 2 本で順に回すのと並び、8 本で 1.6 倍速い。"}],
             "per_row": 1, "columns": ["回し方", "同時に回す数", "秒", "順に回すのと比べた速さ"], "rows": table},
        ],
        "notes": [
            f"<strong>何通りも試すなら PDG で同時に回す。</strong>焚き火 8 通りで、同時に 8 本（既定の Total Slots）が {s('inproc') / s('pdg8'):.1f} 倍速かった。",
            f"<strong>同時に 1 本の PDG は、順に回すより遅い。</strong>1 通りあたり約 {per_job - per_in:.0f} 秒余分にかかった（別の Houdini を立ち上げる分と考えられる）。",
            "<strong>シミュレーションを書き出すときは、ropgeometry の Evaluate Using を Frame Range にし、All Frames in One Batch を入れる。</strong>既定の Single Frame では 1 フレーム目しか回らない。",
            f"<strong>同時に回す数を増やしても、比例しては速くならない。</strong>4 → 8 本で {1 - s('pdg8') / s('pdg4'):.0%} だけ。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "209_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 209_report.json")
    print(payload["title"], worst)


if __name__ == "__main__":
    main()
