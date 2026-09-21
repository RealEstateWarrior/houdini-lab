# -*- coding: utf-8 -*-
"""gloss_add_*.py の用語を glossary.json に混ぜる。

    python gloss_merge.py

同じ見出しが二重にならないよう、既にある語は足さない。
related は本文ではなく「関連: 」の一行として出るだけなので、
用語集に無い語（ノード名など）を書いても構わない。数だけ数えて出す。
"""
import io
import json
import os

import gloss_add_1
import gloss_add_2
import gloss_add_3
import gloss_add_4
import gloss_add_5
import gloss_add_6

HERE = os.path.dirname(os.path.abspath(__file__))

ORDER = ["network", "geometry", "operations", "vex", "math", "simulation",
         "render", "usd", "files", "houdini"]


def keys_of(term):
    """見出しから、リンクに使える語を切り出す（「ノード / Node」→ 2語）。"""
    out = {term["term"]}
    for part in term["term"].split("/"):
        part = part.strip()
        if part:
            out.add(part)
    return out


def main():
    path = os.path.join(HERE, "glossary.json")
    with io.open(path, encoding="utf-8") as fp:
        data = json.load(fp)

    cats = {c["id"]: c for c in data["categories"]}
    added = 0

    for module in (gloss_add_1, gloss_add_2, gloss_add_3, gloss_add_4,
                   gloss_add_5, gloss_add_6):
        for cid, label, note in getattr(module, "CATEGORIES_NEW", []):
            if cid not in cats:
                cats[cid] = {"id": cid, "label": label, "note": note,
                             "terms": []}
        for cid, terms in module.ADD.items():
            if cid not in cats:
                raise SystemExit(f"分類 {cid} が無い")
            have = {t["term"] for t in cats[cid]["terms"]}
            for term in terms:
                if term["term"] in have:
                    continue
                cats[cid]["terms"].append(term)
                added += 1

    data["categories"] = [cats[cid] for cid in ORDER if cid in cats]

    # related のつなぎ先が在るかを確かめる
    known = set()
    for cat in data["categories"]:
        for term in cat["terms"]:
            known |= keys_of(term)
    missing = []
    for cat in data["categories"]:
        for term in cat["terms"]:
            for name in (term.get("related") or "").split(","):
                name = name.strip()
                if name and name not in known:
                    missing.append((term["term"], name))

    with io.open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)

    total = sum(len(c["terms"]) for c in data["categories"])
    print(f"{added} 語を足して、合計 {total} 語")
    for cat in data["categories"]:
        print(f"  {cat['id']}: {len(cat['terms'])}")
    if missing:
        print(f"related に用語集の外の語が {len(missing)} 件（ノード名などは想定どおり）")


if __name__ == "__main__":
    main()
