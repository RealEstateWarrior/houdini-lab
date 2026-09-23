# -*- coding: utf-8 -*-
"""実験200 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "200_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, short, nores = d["rows"], d["short"], d["noreseed"]
    with open(os.path.join(OUT, "200_trap.json"), encoding="utf-8") as fp:
        trap = json.load(fp)
    cling = [json.loads(line) for line in open(os.path.join(OUT, "200_cling.jsonl"), encoding="utf-8")]
    water = d["water_volume"]
    with open(os.path.join(OUT, "200_threads.json"), encoding="utf-8") as fp:
        th = json.load(fp)

    def arrive(r):
        return next(x["f"] for x in r["per_frame"] if x["front"] > 1.4)

    def depth_vol(r, f="60"):
        prof = r["frames"][f]["profile"]
        return sum(v + 0.75 for v in prof) / len(prof) * 3.0 * 1.0

    def keep(r):
        return r["per_frame"][-1]["count"] / r["per_frame"][0]["count"]

    by = {r["sep"]: r for r in rows}
    line_chart(os.path.join(OUT, "200_volume.png"),
               [{"label": f"粒の間隔 {r['sep']:.2f}", "points": [(f, r[f"surface_volume_f{f}"] if f != 60 else r["surface_volume"]) for f in (1, 24, 36, 48, 60) if f != 36 or "surface_volume_f36" in r],
                 "color": PALETTE[i % 5]} for i, r in enumerate(rows)]
               + [{"label": "最初に入れた水 0.54", "points": [(1, water), (60, water)], "color": PALETTE[4], "dash": True}],
               title="FLIP ダムブレイク: 面にした水の体積（particlefluidsurface・多角形）",
               x_label="フレーム", y_label="体積")
    line_chart(os.path.join(OUT, "200_cost.png"),
               [{"label": "60 フレームの計算時間（秒）", "points": [(r["sep"], r["sim_sec"]) for r in rows], "color": PALETTE[0]},
                {"label": "落ち着いた液面の形の差 × 100（フレーム60、0.02 と比べて）", "points": [(r["sep"], r["frames"]["60"]["profile_rms"] * 100) for r in rows], "color": PALETTE[1]}],
               title="FLIP ダムブレイク: 粒の間隔と、時間・形の差",
               x_label="Particle Separation", y_label="秒 ／ 形の差 × 100")

    ref, s04, s08 = by[0.02], by[0.04], by[0.08]
    n06 = [r for r in nores if r["sep"] == 0.06][0]
    c06 = [c for c in cling if c["sep"] == 0.06 and c["wall"] == 0.2 and c["gap"] == 0.0][0]
    c06t = [c for c in cling if c["sep"] == 0.06 and c["wall"] == 0.6 and c["gap"] == 0.0][0]
    c06g = [c for c in cling if c["sep"] == 0.06 and c["wall"] == 0.2 and c["gap"] == 0.1][0]
    c04 = [c for c in cling if c["sep"] == 0.04][0]
    pct = lambda v: f"{(v / water - 1) * 100:+.0f}%"

    payload = {
        "title": "FLIP のダムブレイクは Particle Separation 0.04 で足りる — 0.06 より粗いと壁ぎわの数粒が大きな塊に見え、水も 1〜2 割増える",
        "summary":
            "**課題: 水の柱が崩れて流れる場面で、FLIP の粒の間隔（Particle Separation）をどこまで粗くしても見た目が保てるか。時間はどれだけ減るか。**\n\n"
            "幅 3 × 高さ 1.5 × 奥行き 1 の水槽の左端に、幅 0.6 × 高さ 0.9 の水（体積 0.54）を置いて崩した。"
            "粒の間隔を 0.02（基準）・0.03・0.04・0.06・0.08 と変えて 60 フレーム（24 fps で 2.5 秒）回し、"
            "波の到着・液面の形・面にしたときの体積・時間を測り、同じカメラで撮った。\n\n"
            "**結論: この大きさなら 0.04。**"
            f"波が右の壁に届くのは 0.02〜0.06 でどれもフレーム {arrive(ref)}（0.08 だけ {arrive(s08)}）。"
            f"落ち着いた液面（フレーム60）の形の差は、0.02 と比べて 0.03 で {by[0.03]['frames']['60']['profile_rms']:.3f}、0.04 で {s04['frames']['60']['profile_rms']:.3f}、"
            f"0.06 で {by[0.06]['frames']['60']['profile_rms']:.3f}、0.08 で {s08['frames']['60']['profile_rms']:.3f}（高さの二乗平均の差、単位は水槽と同じ）。"
            f"面にした水の体積はフレーム60で 0.02 {ref['surface_volume']:.3f}（{pct(ref['surface_volume'])}）、0.04 {s04['surface_volume']:.3f}（{pct(s04['surface_volume'])}）、"
            f"0.06 {by[0.06]['surface_volume']:.3f}（{pct(by[0.06]['surface_volume'])}）、0.08 {s08['surface_volume']:.3f}（{pct(s08['surface_volume'])}）。\n\n"
            "**0.02 で面の体積が 13% 少ないのは、面にする段階で痩せているため。**"
            f"粒の液面の高さ（区間ごとの粒の y の 99 パーセンタイル）の平均から出した水の量は、0.02 のフレーム60で {depth_vol(ref):.3f} と、入れた 0.54 に合っていた。"
            "粒は水を保っていて、particlefluidsurface（既定の設定）が細かい間隔で水を薄く面にしている。\n\n"
            f"**粗くしても時間はあまり減らない。**60 フレームで 0.02 が {ref['sim_sec']:.1f} 秒、0.04 が {s04['sim_sec']:.1f} 秒、0.08 が {s08['sim_sec']:.1f} 秒。"
            f"粒は {ref['per_frame'][0]['count']:,} 個から {s08['per_frame'][0]['count']:,} 個へ約 {ref['per_frame'][0]['count'] / s08['per_frame'][0]['count']:.0f} 分の 1 になるのに、時間は {ref['sim_sec'] / s08['sim_sec']:.1f} 分の 1 にしかならない。"
            f"理由を切り分けた。水を入れない空の水槽でも {th['empty_tank']['0.08']:.1f}〜{th['empty_tank']['0.02']:.1f} 秒かかる。"
            f"さらに、1 スレッドに絞る（hython -j 1）と 0.02 は {th['single']['0.02']:.1f} 秒、0.08 は {th['single']['0.08']:.1f} 秒で、差は {th['single']['0.02'] / th['single']['0.08']:.1f} 倍に開いた。"
            f"この機械（{th['cpu_threads']} スレッド）では、粒の多い細かい間隔ほど並列で速くなり、粗い間隔は並列の恩恵をほとんど受けない。"
            "時間の差が縮むのはこのため。\n\n"
            "**0.06 より粗いと、左の壁に水の柱が残ったように見える。**原因を切り分けた。"
            f"壁ぎわの高い所（x < −1.3、y > −0.45）にいる粒は、0.06 のフレーム60で全体の {c06['cling']['60'] * 100:.1f}%（約 {round(c06['cling']['60'] * n06['per_frame'][0]['count'])} 個）だけ。"
            f"0.04 では {c04['cling']['36'] * 100:.1f}%（フレーム36）。"
            f"壁を 0.2 から 0.6 に厚くしても変わらず（{c06t['cling']['36'] * 100:.2f}%）、最初の水を壁から 0.1 離すと減った（フレーム36で {c06g['cling']['36'] * 100:.2f}%）。"
            "壁の衝突が効いていないのではなく、壁ぎわに残った数粒が、粒の間隔が粗いぶん大きな半径で面になり、塊に見えている。\n\n"
            "**粒の数が減るのは、水が消えたからではない。**0.06 では粒が 60 フレームで "
            f"{by[0.06]['per_frame'][0]['count']:,} → {by[0.06]['per_frame'][-1]['count']:,} 個（{keep(by[0.06]) * 100:.0f}%）に減った。"
            f"壁を 0.85 から 1.45 に高くしても同じ減り方（{keep([r for r in short if r['sep'] == 0.06][0]) * 100:.0f}%）で、壁を越えて外へ出たのではない。"
            f"既定で入っている Reseeding を切ると {n06['per_frame'][0]['count']:,} 個のまま変わらず、面の体積は {n06['surface_volume']:.3f}（入れたままは {by[0.06]['surface_volume']:.3f}）。"
            "Reseeding が混んだ所の粒を間引いているだけで、見た目の水の量はほぼ同じ。\n\n"
            "**しぶきの高さは、どの間隔でも揃わない。**右の壁を駆け上がるいちばん高い所は "
            + "・".join(f"{r['sep']:.2f} で {max(x['runup'] for x in r['per_frame'] if x['runup'] is not None):.2f}" for r in rows)
            + "。細かくするほど一方向に近づくのではなく、行ったり来たりする。しぶきの先端は、間隔を変えるたびに別物になると考えてよい。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "同じカメラで撮った水（上から 0.02・0.03・0.04・0.06・0.08）",
             "images": [{"path": "200_grid.png", "caption": "0.06・0.08 は左の壁ぎわに塊が残る。0.04 までは平らに広がる。"}],
             "per_row": 1, "columns": [], "rows": []},
            {"label": "粒の間隔と、時間・形・体積",
             "images": [{"path": "200_cost.png", "caption": "時間（青）は粗くしてもゆっくりしか減らない。形の差（橙）は 0.06 で跳ね上がる。"},
                        {"path": "200_volume.png", "caption": "粗いほど面にした水が増える（点線が入れた水 0.54）。"}],
             "per_row": 2,
             "columns": ["粒の間隔", "粒の数（最初）", "粒の数（F60）", "壁に届くフレーム", "形の差（F48）", "形の差（F60）", "体積（F60）", "計算 秒", "面にする 秒"],
             "rows": [[f"{r['sep']:.2f}", f"{r['per_frame'][0]['count']:,}", f"{r['per_frame'][-1]['count']:,}", arrive(r),
                       f"{r['frames']['48']['profile_rms']:.3f}", f"{r['frames']['60']['profile_rms']:.3f}",
                       f"{r['surface_volume']:.3f}", f"{r['sim_sec']:.2f}", f"{r['surface_sec']:.2f}"] for r in rows]},
            {"label": "原因の切り分け（粒の間隔 0.06 など）",
             "images": [], "per_row": 1,
             "columns": ["条件", "粒の数 F1 → F60", "壁ぎわの粒の割合 F36", "体積（F60）"],
             "rows": [["0.06・壁の上端 1.45（基準）", f"{by[0.06]['per_frame'][0]['count']:,} → {by[0.06]['per_frame'][-1]['count']:,}", f"{c06['cling']['36'] * 100:.2f}%", f"{by[0.06]['surface_volume']:.3f}"],
                      ["0.06・壁の上端 0.85", f"{[r for r in short if r['sep'] == 0.06][0]['per_frame'][0]['count']:,} → {[r for r in short if r['sep'] == 0.06][0]['per_frame'][-1]['count']:,}", "—", f"{[r for r in short if r['sep'] == 0.06][0]['surface_volume']:.3f}"],
                      ["0.06・Reseeding 切", f"{n06['per_frame'][0]['count']:,} → {n06['per_frame'][-1]['count']:,}", "—", f"{n06['surface_volume']:.3f}"],
                      ["0.06・壁の厚み 0.6", "—", f"{c06t['cling']['36'] * 100:.2f}%", "—"],
                      ["0.06・水を壁から 0.1 離す", "—", f"{c06g['cling']['36'] * 100:.2f}%", "—"],
                      ["0.04（基準）", "—", f"{c04['cling']['36'] * 100:.2f}%", f"{s04['surface_volume']:.3f}"]]},
        ],
        "notes": [
            "<strong>水槽 3 m・水 0.5 m³ くらいの場面なら、Particle Separation は 0.04。</strong>流れと落ち着いた形は 0.02 とほぼ同じで、時間は 1.5 分の 1。",
            "<strong>0.06 より粗くしても時間はあまり減らない（多コアの機械では特に）。</strong>代わりに、壁ぎわの数粒が塊になり、水が 1〜2 割増えて見える。プレビューでも 0.04 で回したほうが得。",
            "<strong>粒の数が減っても、水が消えたとは限らない。</strong>Reseeding（既定で入）が間引いているだけ。水の量は粒の液面の高さか、面にした体積で見る。",
            "<strong>細かい間隔（0.02）では、面にすると水が 1 割ほど痩せる。</strong>粒は水を保っている。面の厚みが足りなく見えたら particlefluidsurface の設定を疑う。",
            "<strong>しぶきの先端の形は、間隔を変えると別物になる。</strong>プレビューのしぶきを本番でそのまま再現しようとしない。",
            f"<strong>SOP の FLIP を一から組むときの落とし穴 4 つ。</strong>(1) 容器（flipcontainer）は壁の無い開いた箱で、外に出た粒は消える。床と壁は flipcollide の 4 番目の入力につなぐ。"
            f"(2) flipsource で Add pscale を入れないと「{trap['missing_pscale_error']}」で止まる。"
            "(3) Volume Name を既定の surface のままにすると水がソルバーに入らなかった（粒 5 個）。source にし、最初のフレームだけ湧かせる。"
            f"(4) その入れ方で Narrow Band（既定で入）のままだと、内側の粒が消えていく（0.08 で 12 フレームに {trap['narrowband_on_counts'][0]} → {trap['narrowband_on_counts'][-1]} 個）。",
            "<strong>訂正: 実験019 の「落ちる水」は、床の無い容器を落ち抜けていただけだった。</strong>今回と同じ組み方（flipcollide で床を足す）でないと、水は溜まらない。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "200_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 200_report.json")


if __name__ == "__main__":
    main()
