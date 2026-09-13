"""Generate the site twice: once for Artifacts, once for GitHub Pages.

glossary.json is the single source of truth for terms. It feeds three outputs:
the glossary PDF (a Gemini Notebook source), the glossary page, and the popups
inside the experiment log. Pages can't fetch it at runtime — the Artifact CSP
blocks XHR — so the build inlines what each page needs.

The two outputs differ only in how pages link to each other:
  site/  … absolute Artifact URLs (each page is its own Artifact)
  docs/  … relative paths, served by GitHub Pages from this folder

Usage:
    python build_site.py
"""

import html
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
DOCS = os.path.join(HERE, "docs")
OUT = os.path.join(HERE, "out")
GLOSSARY = os.path.join(HERE, "glossary.json")

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/9e4a30fe-e11f-455d-8179-df0765435022"

# 発行済みArtifactのURL。新規発行したらここを更新して再ビルドする。
ARTIFACT_URLS = {
    "home": "https://claude.ai/code/artifact/e6fa0709-06ab-4ab9-9591-ed52742a88fa",
    "log": "https://claude.ai/code/artifact/f9b31321-23e5-4e7c-b6bc-ad2bcf9c1129",
    "glossary": "https://claude.ai/code/artifact/5236e98a-7bc1-4fd0-b523-856c80513868",
    "links": "https://claude.ai/code/artifact/0085c322-cc2d-4d35-ac08-f39eb4e63f4f",
}

# GitHub Pages 版。ルートがハブになるよう index.html をハブに割り当てる。
PAGES_URLS = {
    "home": "index.html",
    "log": "log.html",
    "glossary": "glossary.html",
    "links": "links.html",
}

# ハブ内のタブ。読み込みなしで切り替わる。
TABS = [
    ("overview", "概要"),
    ("experiments", "実験"),
    ("glossary", "用語集"),
    ("links", "参考リンク"),
]

CHILD_NAV = [
    ("group", "Houdini"),
    ("home", "研究ハブ"),
    ("log", "実験ログ"),
    ("glossary", "用語辞典"),
    ("links", "参考リンク集"),
    ("group", "外部"),
    ("notebook", "Gemini Notebook"),
]

DONE = [
    {"no": "001", "anchor": "exp001", "thumb": "box_mountain.png",
     "title": "Box を山にして細分割し、位置で色を付ける",
     "note": "最小構成。mountain は点を増やさないと分かった"},
    {"no": "002", "anchor": "exp002", "thumb": "002_subdiv_3.png",
     "title": "subdivide の回数で、形と数はどう変わるか",
     "note": "面数は正確に4倍、点数は常に面数+2。縮む原因は分割ではなく平滑化"},
    {"no": "003", "anchor": "exp003", "thumb": "003_D.png",
     "title": "mountain と subdivide は、順序を変えると何が変わるか",
     "note": "点数は解像度を決め、凹凸の大きさは elementsize が決める"},
    {"no": "004", "anchor": "exp004", "thumb": "004_rough_10.png",
     "title": "mountain のノイズパラメータは、それぞれ何に効くのか",
     "note": "rough が形の性質を決める。oct は点数が足りないと効かない"},
    {"no": "005", "anchor": "exp005", "thumb": "005_mworleyFA.png",
     "title": "basis 14通りで、形はどこまで変わるか",
     "note": "振幅も性質も変わる。外向きに押すか内向きに削るかが種類で決まる"},
    {"no": "006", "anchor": "exp006", "thumb": "006_bias_075.png",
     "title": "height は純粋な倍率か。gain と bias は何に効くか",
     "note": "005の「上限がある」は誤りだった。bias で突起と窪みを連続的に制御できる"},
    {"no": "007", "anchor": "exp007", "thumb": "007_frac_fBm.png",
     "title": "平面で地形を作り、指標を作り直す",
     "note": "勾配が止まる点が「足りている解像度」を教えてくれる。fractal は平面で差が出る"},
    {"no": "008", "anchor": "exp008", "thumb": "008_z_axis.png",
     "title": "scatter と copy to points — 地面に物を生やす",
     "note": "N はテンプレートのZ軸に対応する。Y軸のまま複製すると必ず横倒しになる"},
    {"no": "009", "anchor": "exp009", "thumb": "009_wave.png",
     "title": "attribute wrangle で VEX を書く",
     "note": "実行対象でアトリビュートの置き場所が変わる。処理時間の計測は3回目で本物になった"},
]

PLANNED = [
    {"no": "010", "title": "for-each ループ",
     "note": "プリミティブ単位の繰り返し。VEXとの使い分け"},
    {"no": "011", "title": "crease で角を保持する",
     "note": "分割しても立方体らしさを残せるか"},
    {"no": "012", "title": "polyextrude と boolean", "note": "押し出しとブーリアン"},
]

PLANNED_FX = [
    {"no": "013", "title": "POP パーティクル基本", "note": "source と solver。重力と寿命"},
    {"no": "014", "title": "RBD 破壊", "note": "voronoi fracture からの剛体シミュレーション"},
    {"no": "015", "title": "Vellum クロス", "note": "布のシミュレーション"},
    {"no": "016", "title": "Pyro と FLIP", "note": "ボリュームと液体"},
]

PAGES = [
    # template, site出力, docs出力, ナビの現在位置, タブ形式か
    ("home_template.html", "home.html", "index.html", "home", True),
    ("template.html", "index.html", "log.html", "log", False),
    ("glossary_template.html", "glossary.html", "glossary.html", "glossary", False),
    ("links_template.html", "links.html", "links.html", "links", False),
]


def render_nav(active, tabs, urls):
    out = ['  <nav class="sidenav" aria-label="サイト内の移動">',
           '    <p class="brand">Houdini 研究ハブ</p>',
           '    <p class="brand-note">measured, not guessed</p>',
           '    <ul role="tablist">' if tabs else "    <ul>"]

    if tabs:
        out.append('      <li class="nav-group">Houdini</li>')
        for panel, label in TABS:
            out.append(f'      <li><button type="button" class="nav-tab" role="tab"'
                       f' id="tab-{panel}" data-panel="{panel}"'
                       f' aria-controls="panel-{panel}" aria-selected="false">'
                       f"{html.escape(label)}</button></li>")
        out.append('      <li class="nav-group">外部</li>')
        out.append(f'      <li><a href="{urls["log"]}">実験ログ（全文）</a></li>')
        out.append(f'      <li><a href="{NOTEBOOK_URL}" class="nav-ext">'
                   "Gemini Notebook</a></li>")
    else:
        for key, label in CHILD_NAV:
            if key == "group":
                out.append(f'      <li class="nav-group">{html.escape(label)}</li>')
                continue
            url = NOTEBOOK_URL if key == "notebook" else urls[key]
            current = ' aria-current="page"' if key == active else ""
            klass = ' class="nav-ext"' if key == "notebook" else ""
            out.append(f'      <li><a href="{url}"{current}{klass}>'
                       f"{html.escape(label)}</a></li>")

    out.append("    </ul>")
    out.append("  </nav>")
    return "\n".join(out)


def render_thumbs(urls):
    out = ['      <div class="stage" style="margin-top: 40px;"><h3>完了</h3></div>',
           '      <div class="thumbs">']
    for item in DONE:
        out.append(f'        <a class="thumb" href="{urls["log"]}#{item["anchor"]}">')
        out.append(f'          <span class="thumb-img"><img src="{item["thumb"]}"'
                   f' alt="実験{item["no"]}の結果のレンダリング"></span>')
        out.append('          <span class="thumb-body">')
        out.append(f'            <span class="thumb-no">実験 {item["no"]}</span>')
        out.append(f'            <h4>{html.escape(item["title"])}</h4>')
        out.append(f'            <p>{html.escape(item["note"])}</p>')
        out.append("          </span>")
        out.append("        </a>")
    out.append("      </div>")

    for label, items in (("予定 — プロシージャルモデリング", PLANNED),
                         ("予定 — エフェクト", PLANNED_FX)):
        out.append(f'      <div class="stage" style="margin-top: 40px;">'
                   f"<h3>{html.escape(label)}</h3></div>")
        out.append('      <div class="thumbs">')
        for item in items:
            out.append('        <div class="thumb thumb--planned">')
            out.append('          <span class="thumb-img">未実施</span>')
            out.append('          <span class="thumb-body">')
            out.append(f'            <span class="thumb-no">実験 {item["no"]}</span>')
            out.append(f'            <h4>{html.escape(item["title"])}</h4>')
            out.append(f'            <p>{html.escape(item["note"])}</p>')
            out.append("          </span>")
            out.append("        </div>")
        out.append("      </div>")

    out.append('      <p class="hint" style="margin-top: 30px;">'
               "エフェクトに入る前に、ツール側で複数フレームの書き出しと"
               "シミュレーションのキャッシュに対応する必要がある。</p>")
    return "\n".join(out)


def aliases(term):
    """"プリミティブ / Primitive" is addressable as either half, or in full."""
    keys = {term.strip()}
    for part in term.split("/"):
        part = part.strip()
        if part:
            keys.add(part)
    return keys


def all_keys(data):
    keys = set()
    for cat in data["categories"]:
        for entry in cat["terms"]:
            keys |= aliases(entry["term"])
    return keys


def render_gloss_nav(data):
    return "\n".join(
        f'      <a href="#{cat["id"]}">{html.escape(cat["label"])}</a>'
        for cat in data["categories"]
    )


def render_section(data):
    out = []
    for cat in data["categories"]:
        out.append(f'    <section class="gloss-cat" id="{cat["id"]}">')
        out.append(f'      <h3>{html.escape(cat["label"])}</h3>')
        if cat.get("note"):
            out.append(f'      <p class="gloss-note">{html.escape(cat["note"])}</p>')
        out.append('      <dl class="gloss-list">')
        for entry in cat["terms"]:
            meta = [html.escape(v) for v in
                    (entry.get("reading"), entry.get("expand")) if v]
            out.append('        <div class="gloss-item">')
            out.append(f'          <dt>{html.escape(entry["term"])}'
                       + (f'<span class="gloss-meta">{" · ".join(meta)}</span>' if meta else "")
                       + "</dt>")
            rel = (f'<span class="gloss-rel">関連: {html.escape(entry["related"])}</span>'
                   if entry.get("related") else "")
            out.append(f'          <dd>{html.escape(entry["def"])}{rel}</dd>')
            out.append("        </div>")
        out.append("      </dl>")
        out.append("    </section>")
    return "\n".join(out)


def render_data(data):
    lookup = {}
    for cat in data["categories"]:
        for entry in cat["terms"]:
            payload = {
                "term": entry["term"],
                "reading": entry.get("reading", ""),
                "expand": entry.get("expand", ""),
                "def": entry["def"],
                "related": entry.get("related", ""),
            }
            for key in aliases(entry["term"]):
                lookup[key] = payload
    body = json.dumps(lookup, ensure_ascii=False, separators=(",", ":"))
    return f'<script type="application/json" id="glossary-data">{body}</script>'


def render(template_name, out_dir, out_name, active, tabs, urls, data, css, links_body):
    with open(os.path.join(SITE, template_name), encoding="utf-8") as fp:
        page = fp.read()

    for needle, value in (
        ("<!--CSS-->", css),
        ("<!--NAV-->", render_nav(active, tabs, urls)),
        ("<!--THUMBS-->", render_thumbs(urls)),
        ("<!--LINKS_BODY-->", links_body),
        ("<!--GLOSSARY_SECTION-->", render_section(data)),
        ("<!--GLOSSARY_NAV-->", render_gloss_nav(data)),
        ("<!--GLOSSARY_DATA-->", render_data(data)),
        ("<!--HOME_URL-->", urls["home"]),
        ("<!--LOG_URL-->", urls["log"]),
        ("<!--GLOSSARY_URL-->", urls["glossary"]),
        ("<!--LINKS_URL-->", urls["links"]),
        ("<!--NOTEBOOK_URL-->", NOTEBOOK_URL),
    ):
        page = page.replace(needle, value)

    leftover = re.findall(r"<!--[A-Z_]+-->", page)
    if leftover:
        raise SystemExit(f"{template_name}: placeholder left unfilled: {leftover}")

    unknown = sorted(set(re.findall(r'data-term="([^"]+)"', page)) - all_keys(data))
    if unknown:
        raise SystemExit(f"{template_name}: 用語集に存在しない用語: {unknown}")

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, out_name)
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(page)
    return out_path


def copy_images():
    """out/ のPNGを site/ と docs/ に配る。ページが参照するのはファイル名だけ。"""
    names = set()
    for page_html in os.listdir(SITE):
        if not page_html.endswith(".html"):
            continue
        with open(os.path.join(SITE, page_html), encoding="utf-8") as fp:
            names |= set(re.findall(r'<img src="([^"/]+\.png)"', fp.read()))

    os.makedirs(DOCS, exist_ok=True)
    copied = 0
    for name in sorted(names):
        source = os.path.join(OUT, name)
        if not os.path.exists(source):
            raise SystemExit(f"画像が out/ にない: {name}")
        for target_dir in (SITE, DOCS):
            target = os.path.join(target_dir, name)
            if not os.path.exists(target) or \
                    os.path.getmtime(source) > os.path.getmtime(target):
                shutil.copy2(source, target)
                copied += 1
    return len(names), copied


def main():
    with open(GLOSSARY, encoding="utf-8") as fp:
        data = json.load(fp)
    with open(os.path.join(SITE, "base.css"), encoding="utf-8") as fp:
        css = fp.read()
    with open(os.path.join(SITE, "partial_links.html"), encoding="utf-8") as fp:
        links_body = fp.read()

    for template_name, site_out, docs_out, active, tabs in PAGES:
        render(template_name, SITE, site_out, active, tabs,
               ARTIFACT_URLS, data, css, links_body)
        render(template_name, DOCS, docs_out, active, tabs,
               PAGES_URLS, data, css, links_body)

    # GitHub Pages に Jekyll 処理をさせない
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fp:
        fp.write("")

    total, copied = copy_images()
    print(f"site/ と docs/ に {len(PAGES)} ページずつ生成")
    print(f"画像 {total} 件（うち {copied} 件をコピー）")


if __name__ == "__main__":
    main()
