"""実験レポート（out/NNN_report.json）から、実験ログの記事を組み立てて差し込む。

記事の数字をレポートと別に手で打つと、写し間違いが起きる。
同じ JSON から PDF と記事の両方を作れば、食い違いようがない。

    python examples/make_entry.py 071 log_fx MPM "/obj/spin" "一言"

同じ番号の記事がすでにあれば置き換える。
"""

import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
SITE = os.path.join(HERE, "site")


def link_exps(text):
    """「実験070」を記事内リンクにする（すでにリンクになっているものは触らない）。
    レポートの **太字** もここで <strong> にする（しないと記号のまま出る）。"""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<!>)実験(\d{3})(?![^<]*</a>)",
                  lambda m: f'<a href="#exp{m.group(1)}">実験{m.group(1)}</a>', text)


def cell(value):
    text = html.escape(str(value))
    numeric = re.fullmatch(r"[−\-+]?[\d,.]+(〜[\d,.]+)?", str(value)) is not None
    if str(value) in ("—", "-"):
        return '<td class="num muted">—</td>'
    return f'<td class="num">{text}</td>' if numeric else f"<td>{text}</td>"


def article(no, chip, path, lesson, report, log="log_fx"):
    tone = "chip--pm" if log == "log_pm" else "chip--fx"     # モデリング編とエフェクト編で色が違う
    out = [f"    <!-- ===================== {no} ===================== -->",
           f'    <article class="entry entry--current" id="exp{no}">',
           f'      <div class="badge">{no}</div>',
           '      <div class="body">',
           f'        <span class="chip {tone}">{html.escape(chip)}</span>',
           f"        <h2>{html.escape(report['title'])}</h2>",
           f'        <p class="path">{html.escape(path)} &nbsp;·&nbsp; {html.escape(lesson)}</p>',
           ""]
    if report.get("callout"):
        # あとの実験で結論に条件が付いたり、訂正したりしたときの注記
        out += ['        <p class="callout">', f"          {link_exps(report['callout'])}",
                "        </p>", ""]
    out += ['        <div class="prose">']
    for para in report["summary"].split("\n\n"):
        out.append(f"          <p>{link_exps(html.escape(para))}</p>")
    out.append("        </div>")

    for comp in report.get("comparisons", []):
        out.append("")
        out.append(f'        <p class="label">{html.escape(comp["label"])}</p>')
        if comp.get("images"):
            wide = " figs--wide" if comp.get("per_row", 2) == 1 else ""
            out.append(f'        <div class="figs{wide}">')
            for img in comp["images"]:
                out.append("          <figure>")
                out.append(f'            <div class="frame-light"><img src="{img["path"]}"'
                           f' alt="{html.escape(img["caption"][:40])}" loading="lazy" decoding="async"></div>')
                out.append(f"            <figcaption>{link_exps(html.escape(img['caption']))}</figcaption>")
                out.append("          </figure>")
            out.append("        </div>")
        if comp.get("columns") and comp.get("rows"):
            out.append('        <div class="scroll">')
            out.append("          <table>")
            head = "".join(f"<th>{html.escape(c)}</th>" for c in comp["columns"])
            out.append(f"            <thead><tr>{head}</tr></thead>")
            out.append("            <tbody>")
            for row in comp["rows"]:
                out.append("              <tr>" + "".join(cell(v) for v in row) + "</tr>")
            out.append("            </tbody>")
            out.append("          </table>")
            out.append("        </div>")
        if comp.get("note"):
            out.append(f'        <p class="hint">{link_exps(html.escape(comp["note"]))}</p>')

    out.append("")
    out.append('        <p class="label">わかったこと</p>')
    out.append('        <ul class="findings">')
    for note in report["notes"]:
        out.append(f"          <li>{link_exps(note)}</li>")
    out.append("        </ul>")
    out.append("      </div>")
    out.append("    </article>")
    return "\n".join(out) + "\n"


def main():
    no, log, chip, path, lesson = sys.argv[1:6]
    with open(os.path.join(OUT, f"{no}_report.json"), encoding="utf-8") as fp:
        report = json.load(fp)
    template = os.path.join(SITE, f"{log}_template.html")
    with open(template, encoding="utf-8") as fp:
        page = fp.read()
    block = article(no, chip, path, lesson, report, log)
    pattern = re.compile(
        rf"    <!-- =+ {no} =+ -->\n    <article .*?</article>\n", re.S)
    if pattern.search(page):
        page = pattern.sub(lambda m: block, page)
        print(f"実験{no} の記事を置き換えた")
    else:
        anchor = "\n  </div>\n\n  <footer>"
        if anchor not in page:
            raise SystemExit("差し込み位置が見つからない")
        page = page.replace(anchor, "\n\n" + block + anchor, 1)
        print(f"実験{no} の記事を足した")
    with open(template, "w", encoding="utf-8") as fp:
        fp.write(page)


if __name__ == "__main__":
    main()
