# -*- coding: utf-8 -*-
"""実験を1本しまう: 記事を差し込み、build_site.py の DONE に1行足す。

    python examples/finish_exp.py 105 "タグ1,タグ2" "カードの一言" 図1.png 図2.png …

記事の題は out/NNN_report.json の title を使う。1枚目の図がサムネイルになる。
DONE にすでに同じ番号があれば足さない。ログは log_pm（モデリング編）に入れる。
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    no, tags, note = sys.argv[1:4]
    shots = sys.argv[4:]
    with io.open(os.path.join(HERE, "out", f"{no}_report.json"), encoding="utf-8") as fp:
        report = json.load(fp)
    script = [n for n in os.listdir(os.path.join(HERE, "examples"))
              if n.startswith(no + "_") and n.endswith(".py")][0]
    subprocess.check_call([sys.executable, os.path.join(HERE, "examples", "make_entry.py"),
                           no, "log_pm", "モデリング", f"examples/{script}", note])
    path = os.path.join(HERE, "build_site.py")
    s = io.open(path, encoding="utf-8").read()
    if f'{{"no": "{no}"' in s:
        print("DONE にはもうある")
        return
    tag_list = ", ".join(json.dumps(t, ensure_ascii=False) for t in tags.split(","))
    shot_list = ", ".join(json.dumps(x) for x in shots)
    entry = (f'    {{"no": "{no}", "anchor": "exp{no}",\n'
             f'     "tags": [{tag_list}],\n'
             f'     "log": "log_pm", "thumb": "{shots[0]}",\n'
             f'     "shots": [{shot_list}],\n'
             f'     "title": {json.dumps(report["title"], ensure_ascii=False)},\n'
             f'     "note": {json.dumps(note, ensure_ascii=False)}}},\n')
    anchor = "]\n\nPLANNED = []"
    assert s.count(anchor) == 1
    s = s.replace(anchor, entry + anchor, 1)
    io.open(path, "w", encoding="utf-8").write(s)
    print("DONE に足した:", no)


if __name__ == "__main__":
    main()
