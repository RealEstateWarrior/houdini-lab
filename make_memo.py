# -*- coding: utf-8 -*-
"""memo.json から、右パネルに置くメモページ（out/memo.html）を組み立てる。

中身を直すのは memo.json だけ。ここは並べ方と見た目だけを持つ。
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

TONE_LABEL = {
    "wait": "あなた待ち",
    "todo": "私がやる",
    "open": "未解決",
    "rule": "決めごと",
}

HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Houdini 研究部 やることメモ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Zen+Old+Mincho:wght@600;700&display=swap">
<style>
:root{
  --paper:#f7f6f3;
  --card:#fffefb;
  --ink:#23262b;
  --ink-soft:#5c626c;
  --ink-faint:#8b919b;
  --rule:#e2e0da;
  --rule-soft:#edebe5;
  --accent:#b4531b;
  --wait:#b4531b;
  --todo:#2f6b87;
  --open:#7a4a8c;
  --rule-tone:#4a7350;
  --wait-bg:#f6e7dc;
  --todo-bg:#e0edf3;
  --open-bg:#eee4f3;
  --rule-bg:#e3eee4;
  --shadow:0 1px 2px rgba(35,38,43,.06);
  --serif:"Zen Old Mincho",'Hiragino Mincho ProN','Yu Mincho',serif;
  --sans:"Zen Kaku Gothic New",'Hiragino Sans','Yu Gothic',sans-serif;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#191b1f;
    --card:#212429;
    --ink:#e8e6e1;
    --ink-soft:#a8adb5;
    --ink-faint:#787e87;
    --rule:#33373d;
    --rule-soft:#2a2e33;
    --accent:#e08a4e;
    --wait:#e08a4e;
    --todo:#6fb3d2;
    --open:#bd94d4;
    --rule-tone:#85b98e;
    --wait-bg:#3a2a1c;
    --todo-bg:#1e3340;
    --open-bg:#31253a;
    --rule-bg:#22331f;
    --shadow:0 1px 2px rgba(0,0,0,.3);
  }
}
:root[data-theme="dark"]{
  --paper:#191b1f;
  --card:#212429;
  --ink:#e8e6e1;
  --ink-soft:#a8adb5;
  --ink-faint:#787e87;
  --rule:#33373d;
  --rule-soft:#2a2e33;
  --accent:#e08a4e;
  --wait:#e08a4e;
  --todo:#6fb3d2;
  --open:#bd94d4;
  --rule-tone:#85b98e;
  --wait-bg:#3a2a1c;
  --todo-bg:#1e3340;
  --open-bg:#31253a;
  --rule-bg:#22331f;
  --shadow:0 1px 2px rgba(0,0,0,.3);
}
*{box-sizing:border-box}
body{
  margin:0;
  padding:28px 16px 56px;
  background:var(--paper);
  color:var(--ink);
  font-family:var(--sans);
  font-size:15px;
  line-height:1.75;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:720px;margin:0 auto;display:flex;flex-direction:column;gap:26px}
header{display:flex;flex-direction:column;gap:10px}
h1{
  margin:0;
  font-family:var(--serif);
  font-size:26px;
  font-weight:700;
  letter-spacing:.04em;
  text-wrap:balance;
}
.sub{margin:0;color:var(--ink-soft);font-size:13px}
.tally{display:flex;flex-wrap:wrap;gap:8px}
.tally span{
  display:inline-flex;align-items:baseline;gap:6px;
  padding:4px 10px;border-radius:999px;
  font-size:12px;letter-spacing:.02em;
  border:1px solid var(--rule);
  background:var(--card);
}
.tally b{font-size:14px;font-variant-numeric:tabular-nums}
.n-wait{color:var(--wait)}
.n-todo{color:var(--todo)}
.n-open{color:var(--open)}
.n-rule{color:var(--rule-tone)}
section{display:flex;flex-direction:column;gap:12px}
.head{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2{
  margin:0;
  font-family:var(--serif);
  font-size:17px;font-weight:600;letter-spacing:.03em;
}
.tag{
  font-size:11px;letter-spacing:.08em;
  padding:2px 8px;border-radius:4px;
  background:var(--rule-soft);color:var(--ink-soft);
}
.g-wait .tag{background:var(--wait-bg);color:var(--wait)}
.g-todo .tag{background:var(--todo-bg);color:var(--todo)}
.g-open .tag{background:var(--open-bg);color:var(--open)}
.g-rule .tag{background:var(--rule-bg);color:var(--rule-tone)}
ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}
li{
  background:var(--card);
  border:1px solid var(--rule);
  border-left:3px solid var(--ink-faint);
  border-radius:3px;
  padding:12px 14px;
  box-shadow:var(--shadow);
  display:flex;flex-direction:column;gap:5px;
}
.g-wait li{border-left-color:var(--wait)}
.g-todo li{border-left-color:var(--todo)}
.g-open li{border-left-color:var(--open)}
.g-rule li{border-left-color:var(--rule-tone);box-shadow:none;background:transparent}
.t{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.t strong{font-weight:700;font-size:14.5px;line-height:1.6}
.state{
  margin-left:auto;
  font-size:11px;letter-spacing:.04em;white-space:nowrap;
  padding:2px 8px;border-radius:999px;
  background:var(--rule-soft);color:var(--ink-soft);
}
.g-wait .state{background:var(--wait-bg);color:var(--wait)}
.g-todo .state{background:var(--todo-bg);color:var(--todo)}
.d{margin:0;color:var(--ink-soft);font-size:13px;line-height:1.7}
code{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:.92em;
  background:var(--rule-soft);
  padding:1px 5px;border-radius:3px;
}
.links{
  display:flex;flex-direction:column;gap:11px;
  background:var(--card);
  border:1px solid var(--rule);
  border-radius:3px;
  padding:13px 15px;
  box-shadow:var(--shadow);
}
.band{display:grid;grid-template-columns:104px 1fr;gap:10px;align-items:baseline}
.band h3{
  margin:0;font-family:var(--sans);
  font-size:11px;font-weight:500;letter-spacing:.06em;
  color:var(--ink-faint);
}
.row{display:flex;flex-wrap:wrap;gap:6px}
.row a{
  display:inline-block;
  padding:3px 10px;border-radius:999px;
  border:1px solid var(--rule);
  color:var(--ink);text-decoration:none;
  font-size:12.5px;line-height:1.5;
  transition:border-color .12s,color .12s;
}
.row a:hover{border-color:var(--accent);color:var(--accent)}
.row a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.log{border-top:1px solid var(--rule);padding-top:16px}
.log h2{font-size:15px}
.log ol{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.log li{
  background:transparent;border:0;box-shadow:none;padding:0;
  display:grid;grid-template-columns:86px 1fr;gap:12px;align-items:baseline;
}
.log time{color:var(--ink-faint);font-size:12px;font-variant-numeric:tabular-nums}
.log p{margin:0;font-size:13px;color:var(--ink-soft)}
footer{color:var(--ink-faint);font-size:12px;border-top:1px solid var(--rule);padding-top:14px}
@media (max-width:520px){
  .state{margin-left:0}
  .log li{grid-template-columns:1fr;gap:2px}
  .band{grid-template-columns:1fr;gap:5px}
}
</style>
</head>
<body>
<div class="wrap">
"""

FOOT = """</div>
</body>
</html>
"""


def esc(text):
    """記号を安全な形に直し、バッククォートで囲んだ所をコードの見た目にする。"""
    out = html.escape(text)
    parts = out.split("`")
    if len(parts) % 2 == 1:
        for i in range(1, len(parts), 2):
            parts[i] = "<code>" + parts[i] + "</code>"
        out = "".join(parts)
    return out


def build(data):
    rows = [HEAD]
    groups = data["groups"]
    counts = {g["id"]: len(g["items"]) for g in groups}

    rows.append('<header>\n')
    rows.append('<h1>Houdini 研究部 やることメモ</h1>\n')
    rows.append('<p class="sub">%s 現在。中身は <code>memo.json</code> を直して組み直す。</p>\n'
                % esc(data["updated"]))
    rows.append('<div class="tally">')
    for g in groups:
        rows.append('<span><b class="n-%s">%d</b>%s</span>'
                    % (g["tone"], counts[g["id"]], esc(g["label"])))
    rows.append('</div>\n</header>\n')

    bands = data.get("links", [])
    if bands:
        rows.append('<div class="links">\n')
        for band in bands:
            rows.append('<div class="band"><h3>%s</h3><div class="row">'
                        % esc(band["label"]))
            for link in band["items"]:
                rows.append('<a href="%s" target="_blank" rel="noopener">%s</a>'
                            % (html.escape(link["url"], quote=True), esc(link["label"])))
            rows.append('</div></div>\n')
        rows.append('</div>\n')

    for g in groups:
        rows.append('<section class="g-%s">\n<div class="head"><h2>%s</h2>'
                    '<span class="tag">%s</span></div>\n<ul>\n'
                    % (g["tone"], esc(g["label"]), esc(TONE_LABEL.get(g["tone"], ""))))
        for item in g["items"]:
            state = item.get("state")
            rows.append('<li>\n<div class="t"><strong>%s</strong>%s</div>\n'
                        '<p class="d">%s</p>\n</li>\n' % (
                            esc(item["title"]),
                            ('<span class="state">%s</span>' % esc(state)) if state else "",
                            esc(item["detail"]),
                        ))
        rows.append('</ul>\n</section>\n')

    rows.append('<section class="log">\n<div class="head"><h2>直近やったこと</h2></div>\n<ol>\n')
    for entry in data.get("recent", []):
        rows.append('<li><time>%s</time><p>%s</p></li>\n' % (esc(entry["when"]), esc(entry["what"])))
    rows.append('</ol>\n</section>\n')

    rows.append('<footer>%s</footer>\n' % esc(data.get("note", "")))
    rows.append(FOOT)
    return "".join(rows)


def main():
    with open(os.path.join(HERE, "memo.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    page = build(data)
    path = os.path.join(OUT, "memo.html")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(page)
    print("書き出し:", path, len(page), "文字")


if __name__ == "__main__":
    main()
