"""Generate the site twice: once for Artifacts, once for GitHub Pages.

Two JSON files are the single sources of truth:
  glossary.json … 用語。用語集タブ・本文のポップアップ・Notebook用PDFの3つを生成する
  nodes.json    … ノード解説タブ

実験ポップアップの中身は out/*_report.json から組み立てる。PDFとサイトで
説明が食い違わないように、同じファイルを読んでいる。

Pages can't fetch these at runtime — the Artifact CSP blocks XHR — so the
build inlines what each page needs.

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
NODES = os.path.join(HERE, "nodes.json")

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

# ロゴ。ノード2つをワイヤーでつないだ形。押すとハブに戻る。
LOGO_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<rect x="1.1" y="1.1" width="21.8" height="21.8" rx="6.4"'
    ' stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M7.9 10.5V13.6a2.2 2.2 0 0 0 2.2 2.2h3"'
    ' stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
    '<circle cx="7.9" cy="8.1" r="2.2" fill="currentColor"/>'
    '<circle cx="15.9" cy="15.8" r="2.2" fill="currentColor"/>'
    "</svg>"
)
BRAND = "Houdini 研究ハブ"

SEARCH_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8"/>'
    '<path d="M15.4 15.4L20 20" stroke="currentColor" stroke-width="1.8"'
    ' stroke-linecap="round"/></svg>'
)
BURGER_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<path d="M4 9h16M4 15h16" stroke="currentColor" stroke-width="1.8"'
    ' stroke-linecap="round"/></svg>'
)


# ハブ内のタブ。読み込みなしで切り替わる。子ページでは同じ並びがリンクになる。
TABS = [
    ("overview", "概要"),
    ("experiments", "実験"),
    ("nodes", "ノード解説"),
    ("glossary", "用語集"),
    ("links", "参考リンク"),
]

DONE = [
    {"no": "001", "anchor": "exp001", "thumb": "box_mountain.png",
     "report": "box_mountain_report.json",
     "shots": ["box_mountain.png", "box_mountain_graph.png"],
     "title": "Box を山にして細分割し、位置で色を付ける",
     "note": "最小構成。mountain は点を増やさないと分かった"},
    {"no": "002", "anchor": "exp002", "thumb": "002_subdiv_3.png",
     "shots": ["002_subdiv_0.png", "002_subdiv_3.png"],
     "title": "subdivide の回数で、形と数はどう変わるか",
     "note": "面数は正確に4倍、点数は常に面数+2。縮む原因は分割ではなく平滑化"},
    {"no": "003", "anchor": "exp003", "thumb": "003_D.png",
     "shots": ["003_C.png", "003_D.png"],
     "title": "mountain と subdivide は、順序を変えると何が変わるか",
     "note": "点数は解像度を決め、凹凸の大きさは elementsize が決める"},
    {"no": "004", "anchor": "exp004", "thumb": "004_rough_10.png",
     "shots": ["004_rough_00.png", "004_rough_10.png"],
     "title": "mountain のノイズパラメータは、それぞれ何に効くのか",
     "note": "rough が形の性質を決める。oct は点数が足りないと効かない"},
    {"no": "005", "anchor": "exp005", "thumb": "005_mworleyFA.png",
     "shots": ["005_perlin.png", "005_mworleyFA.png"],
     "title": "basis 14通りで、形はどこまで変わるか",
     "note": "振幅も性質も変わる。外向きに押すか内向きに削るかが種類で決まる"},
    {"no": "006", "anchor": "exp006", "thumb": "006_bias_075.png",
     "shots": ["006_bias_025.png", "006_bias_075.png"],
     "title": "height は純粋な倍率か。gain と bias は何に効くか",
     "note": "005の「上限がある」は誤りだった。bias で突起と窪みを連続的に制御できる"},
    {"no": "007", "anchor": "exp007", "thumb": "007_frac_fBm.png",
     "shots": ["007_flat.png", "007_frac_fBm.png"],
     "title": "平面で地形を作り、指標を作り直す",
     "note": "勾配が止まる点が「足りている解像度」を教えてくれる。fractal は平面で差が出る"},
    {"no": "008", "anchor": "exp008", "thumb": "008_z_axis.png",
     "shots": ["008_plain.png", "008_z_axis.png"],
     "title": "scatter と copy to points — 地面に物を生やす",
     "note": "N はテンプレートのZ軸に対応する。Y軸のまま複製すると必ず横倒しになる"},
    {"no": "009", "anchor": "exp009", "thumb": "009_wave.png",
     "shots": ["009_wave.png"],
     "title": "attribute wrangle で VEX を書く",
     "note": "実行対象でアトリビュートの置き場所が変わる。処理時間の計測は3回目で本物になった"},
    {"no": "010", "anchor": "exp010", "thumb": "010_ui_network.png",
     "shots": ["010_ui_network.png"],
     "title": "for-each ループと VEX を比べる",
     "note": "3,969面で85.9倍の差。ただし置き換え可能とは限らず、点の共有が鍵だった"},
    {"no": "011", "anchor": "exp011", "thumb": "011_w3_0.png",
     "shots": ["011_w0_0.png", "011_w3_0.png"],
     "title": "crease で角を残す — どれだけの重みが要るのか",
     "note": "分割回数と同じ重みで完全に角が残る。一辺だけ見ていると誤判定する"},
    {"no": "012", "anchor": "exp012", "thumb": "012_bool_subtract.png",
     "shots": ["012_bool_union.png", "012_bool_subtract.png"],
     "title": "polyextrude と boolean — 硬い形を作る",
     "note": "押し出しは寸法が指定どおり。boolean は体積の関係式で正しさを検算できる"},
    {"no": "013", "anchor": "exp013", "thumb": "013_sheet.png",
     "shots": ["013_wave.gif", "013_sheet.png"],
     "title": "時間軸への対応 — フレームを進めて記録する",
     "note": "連番・コンタクトシート・GIF。パーティクルはSOPに0種でDOPに67種と判明"},
    {"no": "014", "anchor": "exp014", "thumb": "014_sheet.png",
     "shots": ["014_rbd.gif", "014_sheet.png"],
     "title": "RBD 破壊 — 最初の本物のシミュレーション",
     "note": "体積が全フレームで完全に保存。落下中は砕けず、着地して2.8倍に散らばる"},
    {"no": "015", "anchor": "exp015", "thumb": "015_sheet.png",
     "shots": ["015_cloth.gif", "015_sheet.png"],
     "title": "Vellum クロス — 布で保存されるべき量は何か",
     "note": "かたさは「値 × 10の指数乗」。既定の指数10のせいで値を触っても効かない"},
    {"no": "016", "anchor": "exp016", "thumb": "016_sheet.png",
     "shots": ["016_sheet.png"],
     "title": "Pyro 煙 — dissipation の正体を式で突き止める",
     "note": "毎フレーム (1−d) 倍に減らす仕組み。立てた式と実測が4桁一致した"},
    {"no": "017", "anchor": "exp017", "thumb": "017_graph.png",
     "shots": ["017_graph.png"],
     "title": "FLIP 液体 — 組み方が分からず保留",
     "note": "4通りの配線を試して全部同じエラー。他のソルバと作法が違うと判明"},
    {"no": "018", "anchor": "exp018", "thumb": "018_karma.png",
     "shots": ["018_noise_strip.png", "018_opengl.png", "018_karma.png"],
     "title": "Karma でのレンダリング — ノイズはサンプル数で本当に減るのか",
     "note": "サンプル数は上限であって指定ではない。頭打ちの犯人は varianceaa_thresh"},
    {"no": "019", "anchor": "exp019", "thumb": "019_sheet.png",
     "shots": ["019_pool.gif", "019_sheet.png"],
     "title": "FLIP 液体 — 配線が解けた。そして粒の数は体積ではなかった",
     "note": "017の保留を解決。コンテナは3チャンネルの中継点で、VDBの名前が役割を決める"},
    {"no": "020", "anchor": "exp020", "thumb": "020_sheet.png",
     "shots": ["020_pop.gif", "020_graph.png"],
     "title": "POP パーティクル — 生まれる数と落ち方を式で確かめる",
     "note": "生まれる数は指定どおり。落ち方のずれは計算の刻み1.3個ぶんの遅れだった"},
]

PLANNED = []

PLANNED_FX = [
    {"no": "021", "title": "構造のある煙を作る",
     "note": "018で判明。いまの煙は一様な球で、レンダラーの差を見せる題材として弱い"},
    {"no": "022", "title": "液体に表面を張る",
     "note": "019の粒のままでは液体に見えない。particlefluidsurface を使う"},
]

PAGES = [
    # template, site出力, docs出力, ナビの現在位置, タブ形式か
    ("home_template.html", "home.html", "index.html", "home", True),
    ("template.html", "index.html", "log.html", "log", False),
    ("glossary_template.html", "glossary.html", "glossary.html", "glossary", False),
    ("links_template.html", "links.html", "links.html", "links", False),
]


def render_nav(active, tabs, urls):
    """上部のバー。どのページでも同じ並びにする。

    ハブではタブがボタン（読み込みなしで切り替わる）、子ページでは
    ハブの該当タブへのリンクになる。ロゴは常にハブへ戻る。
    """
    logo_href = "#overview" if tabs else urls["home"]
    out = [
        '  <nav class="sidenav" aria-label="サイト内の移動">',
        '    <div class="nav-inner">',
        f'      <a class="logo" href="{logo_href}" aria-label="{BRAND}（ハブに戻る）">',
        f"        {LOGO_SVG}",
        f'        <span class="logo-text">{BRAND}</span>',
        "      </a>",
        '      <ul role="tablist">' if tabs else "      <ul>",
    ]

    for panel, label in TABS:
        if tabs:
            out.append(f'        <li><button type="button" class="nav-tab" role="tab"'
                       f' id="tab-{panel}" data-panel="{panel}"'
                       f' aria-controls="panel-{panel}" aria-selected="false">'
                       f"{html.escape(label)}</button></li>")
        else:
            current = ""
            if (active == "glossary" and panel == "glossary") or \
               (active == "links" and panel == "links"):
                current = ' aria-current="page"'
            out.append(f'        <li><a href="{urls["home"]}#{panel}"{current}>'
                       f"{html.escape(label)}</a></li>")

    log_current = ' aria-current="page"' if active == "log" else ""
    out.append(f'        <li><a href="{urls["log"]}"{log_current}>実験ログ</a></li>')
    out.append(f'        <li><a href="{NOTEBOOK_URL}" class="nav-ext">Notebook</a></li>')
    out.append("      </ul>")
    out.append('      <button type="button" class="nav-icon" id="search-open"'
               ' aria-label="サイト内を検索">' + SEARCH_SVG + "</button>")
    out.append('      <button type="button" class="nav-icon nav-burger" id="menu-open"'
               ' aria-label="メニューを開く" aria-expanded="false">'
               + BURGER_SVG + "</button>")
    out.append("    </div>")
    out.append("  </nav>")
    return "\n".join(out)


def render_thumbs(urls):
    """実験の一覧。カードはリンクではなくボタンで、押すとポップアップが開く。"""
    out = ['      <div class="stage"><h3>完了した実験</h3>'
           "<p>カードを押すと要点が開く。全文のログへはそこから進める。</p></div>",
           '      <div class="thumbs">']
    for item in DONE:
        out.append(f'        <button type="button" class="thumb" data-exp="{item["no"]}">')
        out.append(f'          <span class="thumb-img"><img src="{item["thumb"]}"'
                   f' alt="実験{item["no"]}の結果のレンダリング"></span>')
        out.append('          <span class="thumb-body">')
        out.append(f'            <span class="thumb-no">実験 {item["no"]}</span>')
        out.append(f'            <h4>{html.escape(item["title"])}</h4>')
        out.append(f'            <p>{html.escape(item["note"])}</p>')
        out.append("          </span>")
        out.append("        </button>")
    out.append("      </div>")

    for label, items in (("予定 — プロシージャルモデリング", PLANNED),
                         ("予定 — エフェクト", PLANNED_FX)):
        if not items:
            continue
        out.append(f'      <div class="stage"><h3>{html.escape(label)}</h3></div>')
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
    return "\n".join(out)


def render_exp_data(urls):
    """実験ポップアップの中身。out/*_report.json をそのまま流用する。"""
    payload = {}
    for item in DONE:
        entry = {
            "title": item["title"],
            "href": f'{urls["log"]}#{item["anchor"]}',
            "shots": item.get("shots") or [item["thumb"]],
            "summary": [html.escape(item["note"])],
            "points": [],
            "next": [],
        }
        path = os.path.join(OUT, item.get("report", f'{item["no"]}_report.json'))
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fp:
                rep = json.load(fp)
            entry["title"] = rep.get("title", entry["title"])
            summary = [p.strip() for p in rep.get("summary", "").split("\n\n")]
            entry["summary"] = [p for p in summary if p] or entry["summary"]
            entry["points"] = rep.get("notes", [])
            entry["next"] = rep.get("next", [])
        payload[item["no"]] = entry

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # </script> がJSON中に現れてもタグが閉じないようにする（\/ は正しいJSON）
    body = body.replace("</", "<\\/")
    return f'<script type="application/json" id="experiment-data">{body}</script>'


# ---------- ノード解説 ----------

def render_node_nav(nodes):
    return "\n".join(
        f'      <a href="#{g["id"]}">{html.escape(g["label"])}</a>'
        for g in nodes["groups"]
    )


def render_nodes(nodes, urls):
    anchors = {item["no"]: item["anchor"] for item in DONE}
    out = []
    node_index = -1
    for group in nodes["groups"]:
        out.append(f'      <div class="stage" id="{group["id"]}">')
        out.append(f'        <h3>{html.escape(group["label"])}</h3>')
        if group.get("note"):
            out.append(f'        <p>{html.escape(group["note"])}</p>')
        out.append("      </div>")
        out.append('      <div class="nodegrid">')
        for node in group["nodes"]:
            node_index += 1
            klass = "nodecard" if node.get("img") else "nodecard nodecard--noimg"
            out.append(f'        <article class="{klass}" id="node-{node_index}">')
            out.append('          <div class="node-main">')
            out.append('            <div class="node-head">')
            out.append(f'              <h4>{html.escape(node["name"])}</h4>')
            out.append(f'              <span class="node-kind">{html.escape(node["kind"])}</span>')
            out.append("            </div>")
            out.append(f'            <p class="node-one">{html.escape(node["one"])}</p>')
            out.append(f'            <p class="node-what">{html.escape(node["what"])}</p>')
            if node.get("params"):
                out.append('            <ul class="node-parms">')
                for name, desc in node["params"]:
                    out.append(f"              <li><code>{html.escape(name)}</code>"
                               f"{html.escape(desc)}</li>")
                out.append("            </ul>")
            if node.get("extra"):
                out.append(f'            <p class="node-extra">{html.escape(node["extra"])}</p>')
            if node.get("gotcha"):
                out.append('            <div class="gotcha">'
                           '<span class="gotcha-tag">つまずいた点</span>'
                           f'{html.escape(node["gotcha"])}</div>')
            if node.get("exps"):
                out.append('            <div class="node-exps">')
                for no in node["exps"]:
                    anchor = anchors.get(no, "")
                    out.append(f'              <a href="{urls["log"]}#{anchor}">実験 {no}</a>')
                out.append("            </div>")
            out.append("          </div>")
            if node.get("img"):
                out.append('          <div class="node-shot">')
                out.append(f'            <img src="{node["img"]}"'
                           f' alt="{html.escape(node["name"])}の結果">')
                if node.get("cap"):
                    out.append(f'            <span>{html.escape(node["cap"])}</span>')
                out.append("          </div>")
            out.append("        </article>")
        out.append("      </div>")
    return "\n".join(out)


def render_search_data(data, nodes, urls, tabs):
    """検索の索引。実験・ノード・用語をまとめて1つのJSONに入れる。

    ページの中で開ける行き先（タブ + 要素のid）と、別ページへのリンクを
    どちらも持たせる。ハブではタブを切り替えて飛び、子ページではリンクで飛ぶ。
    """
    items = []

    for item in DONE:
        items.append({
            "kind": "実験",
            "label": f'実験{item["no"]} {item["title"]}',
            "note": item["note"],
            "href": f'{urls["log"]}#{item["anchor"]}',
            "exp": item["no"],
        })

    index = -1
    for group in nodes["groups"]:
        for node in group["nodes"]:
            index += 1
            items.append({
                "kind": "ノード",
                "label": node["name"],
                "note": node["one"],
                "href": f'{urls["home"]}#nodes',
                "tab": "nodes",
                "anchor": f"node-{index}",
            })

    index = -1
    for cat in data["categories"]:
        for entry in cat["terms"]:
            index += 1
            items.append({
                "kind": "用語",
                "label": entry["term"],
                "note": entry["def"][:70],
                "href": f'{urls["glossary"]}#{cat["id"]}',
                "tab": "glossary",
                "anchor": f"gloss-{index}",
                "reading": entry.get("reading", ""),
            })

    for panel, label in TABS:
        items.append({"kind": "ページ", "label": label,
                      "note": "タブを開く", "href": f'{urls["home"]}#{panel}',
                      "tab": panel})
    items.append({"kind": "ページ", "label": "実験ログ（全文）",
                  "note": "すべての実験の記録", "href": urls["log"]})

    body = json.dumps({"tabs": bool(tabs), "items": items},
                      ensure_ascii=False, separators=(",", ":"))
    body = body.replace("</", "<\\/")
    return f'<script type="application/json" id="search-data">{body}</script>'

# ---------- 用語集 ----------

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
    term_index = -1
    for cat in data["categories"]:
        out.append(f'    <section class="gloss-cat" id="{cat["id"]}">')
        out.append(f'      <h3>{html.escape(cat["label"])}</h3>')
        if cat.get("note"):
            out.append(f'      <p class="gloss-note">{html.escape(cat["note"])}</p>')
        out.append('      <dl class="gloss-list">')
        for entry in cat["terms"]:
            term_index += 1
            meta = [html.escape(v) for v in
                    (entry.get("reading"), entry.get("expand")) if v]
            out.append(f'        <div class="gloss-item" id="gloss-{term_index}">')
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


def count_terms(data):
    return sum(len(cat["terms"]) for cat in data["categories"])


def count_nodes(nodes):
    return sum(len(g["nodes"]) for g in nodes["groups"])


def render(template_name, out_dir, out_name, active, tabs, urls,
           data, nodes, css, links_body, popover, chrome):
    with open(os.path.join(SITE, template_name), encoding="utf-8") as fp:
        page = fp.read()

    for needle, value in (
        ("<!--CSS-->", css),
        ("<!--NAV-->", render_nav(active, tabs, urls)),
        ("<!--THUMBS-->", render_thumbs(urls)),
        ("<!--EXP_DATA-->", render_exp_data(urls)),
        ("<!--NODES-->", render_nodes(nodes, urls)),
        ("<!--NODE_NAV-->", render_node_nav(nodes)),
        ("<!--LINKS_BODY-->", links_body),
        ("<!--GLOSSARY_SECTION-->", render_section(data)),
        ("<!--GLOSSARY_NAV-->", render_gloss_nav(data)),
        ("<!--GLOSSARY_DATA-->", render_data(data)),
        ("<!--POPOVER-->", popover),
        ("<!--CHROME-->", chrome),
        ("<!--SEARCH_DATA-->", render_search_data(data, nodes, urls, tabs)),
        ("<!--EXP_COUNT-->", str(len(DONE))),
        ("<!--EXP_TOTAL-->", str(len(DONE) + len(PLANNED) + len(PLANNED_FX))),
        ("<!--NODE_COUNT-->", str(count_nodes(nodes))),
        ("<!--TERM_COUNT-->", str(count_terms(data))),
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

    if out_dir == DOCS:
        page = as_document(page)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, out_name)
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(page)
    return out_path


def as_document(page):
    """docs/ 用に完全なHTMLに包む。

    Artifact 側は発行時に doctype と charset を付けてくれるが、GitHub Pages は
    ファイルをそのまま配る。charset が無いと日本語が化け、doctype が無いと
    ブラウザが互換モードになってレイアウトが崩れる。
    """
    split = page.find('<div class="layout">')
    if split == -1:
        raise SystemExit("レイアウトの開始位置が見つからない")
    head, body = page[:split].strip(), page[split:]
    return (
        "<!doctype html>\n"
        '<html lang="ja">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"{head}\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )


def copy_images():
    """out/ の画像を site/ と docs/ に配る。

    <img src="…"> だけでなく、ポップアップ用のJSONに入っているファイル名も拾う。
    """
    names = set()
    for page_html in os.listdir(SITE):
        if not page_html.endswith(".html"):
            continue
        with open(os.path.join(SITE, page_html), encoding="utf-8") as fp:
            names |= set(re.findall(r'"([\w.\-]+\.(?:png|gif))"', fp.read()))

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
    with open(NODES, encoding="utf-8") as fp:
        nodes = json.load(fp)
    with open(os.path.join(SITE, "base.css"), encoding="utf-8") as fp:
        css = fp.read()
    with open(os.path.join(SITE, "partial_links.html"), encoding="utf-8") as fp:
        links_body = fp.read()
    with open(os.path.join(SITE, "partial_popover.html"), encoding="utf-8") as fp:
        popover = fp.read()
    with open(os.path.join(SITE, "partial_chrome.html"), encoding="utf-8") as fp:
        chrome = fp.read()

    for template_name, site_out, docs_out, active, tabs in PAGES:
        render(template_name, SITE, site_out, active, tabs,
               ARTIFACT_URLS, data, nodes, css, links_body, popover, chrome)
        render(template_name, DOCS, docs_out, active, tabs,
               PAGES_URLS, data, nodes, css, links_body, popover, chrome)

    # GitHub Pages に Jekyll 処理をさせない
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fp:
        fp.write("")

    total, copied = copy_images()
    print(f"site/ と docs/ に {len(PAGES)} ページずつ生成")
    print(f"ノード {count_nodes(nodes)} 件 / 用語 {count_terms(data)} 件")
    print(f"画像 {total} 件（うち {copied} 件をコピー）")


if __name__ == "__main__":
    main()
