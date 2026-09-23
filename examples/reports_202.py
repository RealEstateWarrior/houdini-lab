# -*- coding: utf-8 -*-
"""実験202 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LABELS = {"vox020": "0.02（基準）", "vox030": "Voxel 0.03", "vox040": "Voxel 0.04", "vox060": "Voxel 0.06",
          "veldiv2": "速度の升 2倍", "sub2": "Substeps 2"}


def fire_image(case, f):
    fl = np.load(os.path.join(OUT, f"202_{case}_flame_{f}.npy"))
    sm = np.load(os.path.join(OUT, f"202_{case}_smoke_{f}.npy"))
    h, w = fl.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)
    s = np.clip(sm, 0, 1)[..., None] * np.array([0.35, 0.35, 0.38])
    f_ = np.clip(fl, 0, 1)[..., None]
    rgb = s * (1 - f_) + f_ * np.array([1.0, 0.55, 0.12]) + (np.clip(fl - 0.6, 0, 1)[..., None] * np.array([0, 0.4, 0.5]))
    img = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(img)


def main():
    with open(os.path.join(OUT, "202_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    by = {r["case"]: r for r in d["rows"]}
    order = list(LABELS)
    # 正面に投影した炎（上段フレーム 36、下段 48）
    tiles = [[fire_image(c, f) for c in order] for f in (36, 48)]
    tw, th = tiles[0][0].size
    if np.asarray(tiles[1][0])[: th // 4].mean() > np.asarray(tiles[1][0])[-th // 4:].mean():
        tiles = [[t.transpose(Image.FLIP_TOP_BOTTOM) for t in row] for row in tiles]   # 地面が下にくるようにそろえる
    tw2, th2 = tw, int(th * 0.75)
    tiles = [[t.crop((0, th - th2, tw, th)) for t in row] for row in tiles]   # 上の何もない所を切る
    font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 13)
    sheet = Image.new("RGB", (tw2 * len(order), th2 * 2 + 28), (16, 16, 18))
    draw = ImageDraw.Draw(sheet)
    for j, c in enumerate(order):
        draw.text((j * tw2 + 6, 5), LABELS[c], fill=(230, 230, 230), font=font)
        for i in range(2):
            sheet.paste(tiles[i][j].resize((tw2, th2)), (j * tw2, 28 + i * th2))
    sheet.save(os.path.join(OUT, "202_grid.png"))
    line_chart(os.path.join(OUT, "202_height.png"),
               [{"label": LABELS[c], "points": [(x["f"], x["flame"]["height"]) for x in by[c]["per_frame"]], "color": (PALETTE + [(200, 160, 0)])[i]}
                for i, c in enumerate(order)],
               title="焚き火の炎の高さ（上から 1% の点）", x_label="フレーム", y_label="高さ（m）")
    ref = by["vox020"]
    sp = lambda c: ref["sec"] / by[c]["sec"]
    hh = lambda c: by[c]["flame_height_mean"]
    iou = lambda c: min(v["flame_iou"] for v in by[c]["image_diff"].values())
    iou_max = lambda c: max(v["flame_iou"] for v in by[c]["image_diff"].values())
    payload = {
        "title": f"焚き火の Pyro を速く回すなら Voxel Size を 0.02 → 0.04 に — {sp('vox040'):.1f} 倍速く、炎の高さの差は {abs(hh('vox040') / hh('vox020') - 1):.0%}。速度の升だけ粗くするのと Substeps 2 は、かえって遅い",
        "summary":
            "**課題: Pyro の焚き火（高さ 1.5 m 前後、実験201 の設定）を短い時間で回したい。どのつまみを下げればよく、見た目はどれだけ変わるか。**\n\n"
            "平たい球（半径 0.3・厚み 0.18）を pyrosource の Source Burn で燃やし、pyrosolver（SOP）に実験201 の焚き火の設定"
            "（Flame Lifespan 0.25・Buoyancy 0.25・Cooling 1・Turbulence 3・Use Control Field 切）を入れて 48 フレーム（2 秒）回した。"
            "Voxel Size を 0.02（基準）・0.03・0.04・0.06 に変えたもの、0.02 のまま Velocity Voxel Scale を 2 にしたもの、Max Substeps を 2 にしたものを、1 プロセスずつ測った。"
            "毎フレーム、炎（flame > 0.1）の上から 1% の点の高さを出し、フレーム 24〜48 の平均を「炎の高さ」とした。"
            "フレーム 24・36・48 の炎を正面に投影し、基準との重なり（IoU）も出した。\n\n"
            f"**Voxel Size がいちばん効く。**0.02 の {ref['sec']:.1f} 秒に対し、0.03 で {by['vox030']['sec']:.1f} 秒（{sp('vox030'):.1f} 倍速い）、"
            f"0.04 で {by['vox040']['sec']:.1f} 秒（{sp('vox040'):.1f} 倍）、0.06 で {by['vox060']['sec']:.1f} 秒（{sp('vox060'):.1f} 倍）。"
            f"炎の高さは {hh('vox020'):.2f}・{hh('vox030'):.2f}・{hh('vox040'):.2f}・{hh('vox060'):.2f} m で、0.04 までは 3% 以内、0.06 で {1 - hh('vox060') / hh('vox020'):.0%} 低くなった。\n\n"
            f"**速度の升だけ粗くする（Velocity Voxel Scale 2）は速くならなかった。**{by['veldiv2']['sec']:.1f} 秒で、基準より遅い。"
            f"最後のフレームの升の数は {by['veldiv2']['per_frame'][-1]['res']}（基準は {ref['per_frame'][-1]['res']}）と、計算する範囲のほうが広がっていた。\n\n"
            f"**Max Substeps 2 も遅い（{by['sub2']['sec']:.1f} 秒）。**高さは {hh('sub2'):.2f} m で、揺らぎ（高さの標準偏差）は {by['sub2']['flame_height_std']:.3f} m と、"
            f"基準の {ref['flame_height_std']:.3f} m より大きい。速くするための設定ではない。\n\n"
            f"**形の重なり（IoU）は、どの条件も 0.72〜0.89。**高さがほぼ同じ Voxel 0.03 でも {iou('vox030'):.2f}〜{iou_max('vox030'):.2f}、速度の升 2倍でも {iou('veldiv2'):.2f}〜{iou_max('veldiv2'):.2f}。"
            "炎の細かい形はどの変更でもずれるので、形を1画素ずつ合わせる比べ方では差が出すぎる。ここでは高さで判断した。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "炎と煙を正面に投影した画（上がフレーム36、下がフレーム48）",
             "images": [{"path": "202_grid.png", "caption": "左から Voxel 0.02・0.03・0.04・0.06・速度の升 2倍・Substeps 2。炎は橙、煙は灰色。"}],
             "per_row": 1, "columns": [], "rows": []},
            {"label": "条件ごとの時間と炎",
             "images": [{"path": "202_height.png", "caption": "炎の高さの移り変わり。0.06 だけが目に見えて低い。"}],
             "per_row": 1,
             "columns": ["条件", "48 フレームの計算（秒）", "基準より何倍速い", "炎の高さ（m）", "高さの揺らぎ（m）", "形の重なり（IoU）"],
             "rows": [[LABELS[c], f"{by[c]['sec']:.1f}", f"{sp(c):.1f}", f"{hh(c):.2f}", f"{by[c]['flame_height_std']:.3f}",
                       f"{iou(c):.2f}〜{iou_max(c):.2f}"] for c in order]},
        ],
        "notes": [
            f"<strong>焚き火を速く回すなら Voxel Size を上げる。</strong>0.02 → 0.04 で {sp('vox040'):.1f} 倍速く、炎の高さの差は 3% 以内。形を決めるうちは 0.04、仕上げで 0.02 に戻す。",
            f"<strong>0.06 まで上げると炎が {1 - hh('vox060') / hh('vox020'):.0%} 低くなる。</strong>速さは {sp('vox060'):.0f} 倍だが、高さを合わせたい段階では使わない。",
            "<strong>Velocity Voxel Scale 2 と Max Substeps 2 は、この焚き火では遅くなった。</strong>速くする目的で触るつまみではない。",
            "<strong>炎の細かい形は、どの設定を変えてもずれる（重なり 0.72〜0.89）。</strong>速さの設定を選ぶときは、形の重なりより高さを見る。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "202_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 202_report.json")


if __name__ == "__main__":
    main()
