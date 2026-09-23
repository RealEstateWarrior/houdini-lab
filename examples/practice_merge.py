# -*- coding: utf-8 -*-
"""out/pr_<id>.json（practice_kit.py が書いた実践1本分）を guides.json に混ぜる。

同じ id がすでにあれば置き換え、無ければ最後に足す。書き方（字下げ2）は元の guides.json に合わせる。

    python examples/practice_merge.py rock neon gems
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
GUIDES = os.path.join(HERE, "guides.json")


def main():
    with open(GUIDES, encoding="utf-8") as fp:
        data = json.load(fp)
    by_id = {g["id"]: i for i, g in enumerate(data["guides"])}
    for gid in sys.argv[1:]:
        with open(os.path.join(OUT, f"pr_{gid}.json"), encoding="utf-8") as fp:
            entry = json.load(fp)
        if gid in by_id:
            data["guides"][by_id[gid]] = entry
            print("置き換え:", gid)
        else:
            data["guides"].append(entry)
            by_id[gid] = len(data["guides"]) - 1
            print("足した:", gid)
    # 後から撮った動き（pr_anim_add.py）のキャプションも、ここでまとめて混ぜる
    caps_path = os.path.join(OUT, "_anim_caps.json")
    if os.path.exists(caps_path):
        with open(caps_path, encoding="utf-8") as fp:
            caps = json.load(fp)
        for g in data["guides"]:
            if g["id"] in caps:
                g["anim_cap"] = caps[g["id"]]
    # 作り直した実践の改訂の記録（revisions.json、id → 記録の並び）も混ぜる。台本の出力で消えないよう別に持つ
    rev_path = os.path.join(HERE, "revisions.json")
    if os.path.exists(rev_path):
        with open(rev_path, encoding="utf-8") as fp:
            revs = json.load(fp)
        for g in data["guides"]:
            if g["id"] in revs:
                g["revisions"] = revs[g["id"]]
    with open(GUIDES, "w", encoding="utf-8", newline="") as fp:
        fp.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("実践", len(data["guides"]), "本")


if __name__ == "__main__":
    main()
