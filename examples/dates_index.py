# -*- coding: utf-8 -*-
"""実験と実践が最初に公開された日を、git の履歴から取って out/dates.json に書く。

実験は実験ログのひな形に id="expNNN" が初めて現れた日、実践は guides.json に "id" が初めて現れた日。
すでに分かっている日は変えない（公開日は動かない）。新しいものだけ足す。

    python examples/dates_index.py
"""
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out", "dates.json")
SOURCES = {
    "exp": (["site/log_pm_template.html", "site/log_fx_template.html", "site/index.html"],
            re.compile(r'id="exp(\d{3})"')),
    "guide": (["guides.json"], re.compile(r'"id":\s*"([\w\-]+)"')),
}


def git(*args):
    return subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def first_seen(paths, pattern):
    seen = {}
    for path in paths:
        log = git("log", "--reverse", "--format=%H %ad", "--date=short", "--", path)
        for line in log.splitlines():
            commit, day = line.split()
            body = git("show", f"{commit}:{path}")
            for key in set(pattern.findall(body)):
                if key not in seen or day < seen[key]:
                    seen[key] = day
    return seen


def main():
    dates = {"exp": {}, "guide": {}}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as fp:
            dates.update(json.load(fp))
    for kind, (paths, pattern) in SOURCES.items():
        found = first_seen(paths, pattern)
        for key, day in found.items():
            dates[kind].setdefault(key, day)
    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(dates, fp, ensure_ascii=False, indent=1, sort_keys=True)
    print("実験", len(dates["exp"]), "本 / 実践", len(dates["guide"]), "本")


if __name__ == "__main__":
    main()
