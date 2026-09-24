# -*- coding: utf-8 -*-
"""実験210（181〜209 の点検）のレポートを、out/210_checks.json から組み立てる。

ずれを 4 つに分ける:
  時間      … 名前に us_ / per_ms / _ms / sec を含む（同時に回した処理で変わる）
  ファイル  … 書き出したファイルの大きさ（sizes・vdbfile・per_frame の中のバイト数）
  項目の追加 … 記録に無かった項目（台本にあとから足した）
  値        … それ以外（本当に結果が変わったもの）
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")


def kind(no, key, old, new):
    k = key.lower()
    if old is None or new is None:
        return "add"
    if any(s in k for s in ("us_per", "_ms", "per_ms", "sec", "time", "first")):
        return "time"
    if no in ("204", "209") and any(s in k for s in ("sizes", "vdbfile", "per_frame", "inproc_sizes")):
        return "file"
    return "value"


def main():
    with open(os.path.join(OUT, "210_checks.json"), encoding="utf-8") as fp:
        checks = json.load(fp)
    rows, detail = [], {}
    for c in checks:
        no = c["no"]
        counts = {"time": 0, "file": 0, "add": 0, "value": 0}
        worst = {"file": 0.0, "value": 0.0}
        for _f, key, old, new in c.get("diffs_all", c.get("diffs", [])):
            kd = kind(no, key, old, new)
            counts[kd] += 1
            if kd in worst and isinstance(old, (int, float)) and isinstance(new, (int, float)) and old:
                worst[kd] = max(worst[kd], abs(new / old - 1))
        # diffs は 40 件で切ってあるので、件数は n_diffs を使い、分け方は見本から
        if c.get("kinds"):                      # 点検の台本が全部のずれを数えてあればそちらを使う
            counts, worst = c["kinds"], c["worst"]
        detail[no] = {"counts": counts, "worst": worst, "n": c.get("n_diffs", 0), "values": c.get("values", 0),
                      "errors": c.get("errors", []), "sec": c.get("sec"), "full": bool(c.get("kinds")),
                      "per_file": c.get("per_file", {})}
    return checks, detail


def write_report():
    checks, detail = main()
    nos = sorted(detail)
    total_values = sum(v["values"] for v in detail.values())
    clean = [no for no in nos if detail[no]["n"] == 0]
    table = []
    for no in nos:
        v = detail[no]
        c = v["counts"]
        if v["n"] == 0:
            verdict = "一致"
        elif c["value"] == 0 and c["add"] == 0 and c["file"] == 0:
            verdict = "時間だけ違う"
        elif c["value"] == 0 and c["file"] and not c["add"]:
            verdict = f"ファイルの大きさが最大 {v['worst']['file']:.2%} 揺れた"
        elif c["value"] == 0 and c["add"]:
            verdict = "あとから足した項目だけ"
        elif no == "201":
            bad = [k.replace("201_part_", "").replace(".json", "") for k, n in v.get("per_file", {}).items() if n and "part" in k]
            verdict = f"23 条件のうち {len(bad)} 条件が合わない（{'・'.join(bad)}）"
        else:
            verdict = f"値が違う（最大 {v['worst']['value']:.1%}）"
        table.append([no, str(v["values"]), str(v["n"]), verdict])
    payload = {
        "title": f"181〜209 の点検 — {len(nos)} 本を流し直して {total_values:,} 個の値を突き合わせた。{len(clean)} 本は完全に一致。201 は台本が 202 の変更に引きずられていたので直したが、Turbulence の 2 条件はまだ合わない",
        "summary":
            "**課題: 実験181〜209 の台本を今のまま流し直すと、記事に書いた値が同じように出るか。**\n\n"
            "30 件ごとの点検（030・060・090・121・150・180 に続いて 7 回目）。記録（out/NNN_*.json）を控えに退避し、台本を流し直して、"
            "数字を 1 つずつ比べた（時間の項目は除く）。比べたあと記録は元に戻した。200 番台は条件ごとに 1 プロセスで回す台本なので、条件の一覧を記録の部分ファイルの名前から作った"
            "（examples/210_audit.py）。\n\n"
            f"**{len(clean)} 本は、時間以外のすべての値が一致した。**\n\n"
            "**ずれの出たものは 4 種類に分けられた。**"
            "時間の項目（名前に us_per などが付いていて、飛ばす一覧から漏れていたもの。点検と同時に別の実験を回していた）、"
            "書き出したファイルの大きさの揺れ（数十バイト。圧縮の結果がわずかに変わる）、あとから台本に足した項目（古い記録に無い）、そして本当に値が変わったもの。\n\n"
            "**本当に値が変わったのは 201 だけ。はじめの原因は台本の外にあった。**201 は、火の組み立てを 202 の台本から借りている。"
            "202 を作ったときに、その組み立てに焚き火の設定（Flame Lifespan 0.25・Buoyancy 0.25・Cooling Rate 1・Turbulence 3 など）を足したため、"
            "201 を今流すと、既定値のつもりの条件がすべて焚き火の設定になっていた（23 条件でずれ 5,870 か所）。"
            "201 の台本で、借りた組み立てのあとにこの 6 つを Houdini の既定値に戻すようにして、流し直した。\n\n"
            f"**直したあとも、23 条件のうち 2 条件が合わなかった。**{'・'.join(k.replace('201_part_', '').replace('.json', '') for k, n in detail.get('201', {}).get('per_file', {}).items() if n and 'part' in k)}。"
            "どちらも Turbulence を Use Control Field 入り（既定）で効かせた条件で、流し直すと炎が高く出た（フレーム 10 の高さ 0.66 → 0.94 など）。"
            "201 の記事の「Use Control Field を切らないと Turbulence は効かない」は、この 2 条件の記録から出した結論なので、確かめ直しが要る。原因はまだ確かめていない（やることメモに残した）。"
            "ほかの 21 条件は、時間以外のすべての値が一致した。\n\n"
            "**学んだこと: ほかの実験の台本から組み立てを借りるときは、借りた先をあとで変えると、借りた側の結果が黙って変わる。**点検で流し直すまで気づけない。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "1 本ずつの結果", "images": [], "per_row": 1,
             "columns": ["実験", "比べた値", "ずれた値", "判定"], "rows": table},
        ],
        "notes": [
            f"<strong>{len(clean)} / {len(nos)} 本は完全に一致。</strong>",
            "<strong>201 の台本が、202 で足した焚き火の設定を借りていた。</strong>借りたあと既定値に戻すよう直した。",
            "<strong>201 の 2 条件（Turbulence を Use Control Field 入りで効かせたもの）は、直しても合わなかった。</strong>記事の結論は確かめ直しが要る。",
            "<strong>ファイルの大きさは、同じ中身でも数十バイト揺れる。</strong>容量の比べ方には影響しない大きさ（204・209）。",
            "<strong>時間の項目の名前がばらばらだと、点検で飛ばしきれない。</strong>us_per_point（181）のような名前も飛ばす一覧に入れる。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "210_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 210_report.json")
    print(payload["title"])
    return detail


if __name__ == "__main__":
    write_report()
    ch, de = main()
    for no, v in de.items():
        print(no, v["values"], v["n"], v["counts"], {k: round(x, 5) for k, x in v["worst"].items()}, v["errors"][:1])
