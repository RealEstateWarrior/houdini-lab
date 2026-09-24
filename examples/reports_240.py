# -*- coding: utf-8 -*-
"""実験240（211〜239 の点検）のレポートを、out/240_checks.json から組み立てる。"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
NOTES = json.load(open(os.path.join(OUT, "240_notes.json"), encoding="utf-8")) if os.path.exists(os.path.join(OUT, "240_notes.json")) else {}


def main():
    with open(os.path.join(OUT, "240_checks.json"), encoding="utf-8") as fp:
        checks = json.load(fp)
    table, clean, value_bad = [], [], []
    total = 0
    for c in checks:
        no = c["no"]
        k = c.get("kinds", {})
        total += c.get("values", 0)
        if c.get("n_diffs", 0) == 0:
            verdict = "一致"
            clean.append(no)
        elif k.get("value", 0) == 0 and k.get("add", 0) == 0:
            verdict = "時間だけ違う"
            clean.append(no)
        elif k.get("value", 0) == 0:
            verdict = "あとから足した項目だけ"
            clean.append(no)
        else:
            verdict = f"値が {k['value']} か所違う（最大 {c['worst']['value']:.1%}）"
            value_bad.append(no)
        if no in NOTES:
            verdict += "。" + NOTES[no]
        table.append([no, str(c.get("values", 0)), str(c.get("n_diffs", 0)), verdict])
    table.append(["215", "—", "—", "流し直さなかった（1 条件で 13 分かかる条件を含む）"])
    n = len(checks)
    payload = {
        "title": f"211〜239 の点検 — {n} 本を流し直して {total:,} 個の値を突き合わせた。{len(clean)} 本は一致（時間・足した項目を除く）"
                 + (f"。値が違ったのは {'・'.join(value_bad)}" if value_bad else "。値が違ったものは無い"),
        "summary":
            "**課題: 実験211〜239 の台本を今のまま流し直すと、記事に書いた値が同じように出るか。**\n\n"
            "30 件ごとの点検（030・060・090・121・150・180・210 に続いて 8 回目）。記録（out/NNN_*.json）を控えに退避し、台本を流し直して、"
            "数字を 1 つずつ比べた。時間の項目と、時間から出した値（倍率・百万画素あたりの秒など）は「時間」として分けた。比べたあと記録は元に戻した"
            "（examples/240_audit.py）。215（草の本数と Karma）は、1 条件で 13 分かかる条件を含むので流し直さなかった。\n\n"
            + NOTES.get("_summary", ""),
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "1 本ずつの結果", "images": [], "per_row": 1, "columns": ["実験", "比べた値", "ずれた値", "判定"], "rows": table},
        ],
        "notes": NOTES.get("_notes", []),
        "next": [],
    }
    with open(os.path.join(OUT, "240_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print(payload["title"])
    for row in table:
        print(row)


if __name__ == "__main__":
    main()
