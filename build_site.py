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

import datetime
import hashlib
import html
import json
import os
import re
import shutil
import urllib.parse

import link_terms

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
DOCS = os.path.join(HERE, "docs")
# 親ページ（Saito Production）の置き場。リポジトリ RealEstateWarrior.github.io を
# ここへクローンしてあるときだけ、index.html を書き出す。
ROOT = os.path.join(os.path.dirname(HERE), "sp")
OUT = os.path.join(HERE, "out")
GLOSSARY = os.path.join(HERE, "glossary.json")
NODES = os.path.join(HERE, "nodes.json")
GUIDES = os.path.join(HERE, "guides.json")
WORKS = os.path.join(HERE, "works.json")
REQUESTS = os.path.join(HERE, "requests.json")
SYNONYMS = os.path.join(HERE, "search_synonyms.json")
SPEED = os.path.join(HERE, "speed_tips.json")

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/9e4a30fe-e11f-455d-8179-df0765435022"
# ノードの名前とつまみを確認した Houdini の版
HOU_VERSION = "Houdini 21.0.700"
GITHUB_RAW = ("https://github.com/RealEstateWarrior/houdini-lab/raw/main/out/")
# 要望の受け皿。書いた中身を入れた投稿画面をここで開く。
ISSUE_NEW = "https://github.com/RealEstateWarrior/houdini-lab/issues/new"

# 発行済みArtifactのURL。新規発行したらここを更新して再ビルドする。
ARTIFACT_URLS = {
    "home": "https://claude.ai/artifact/VXGxKiAvNg9hcq3kFM99pu",
    "log": "https://claude.ai/artifact/XqNSd943n6cguxcULeHxBz",
    "log_pm": "https://claude.ai/artifact/XqNSd943n6cguxcULeHxBz",
    "log_fx": "https://claude.ai/artifact/23aXF1hG3G5oCZaaeZ5BAT",
    "glossary": "https://claude.ai/artifact/B9pzUkXod3G6acw2ZF9aLP",
    "links": "https://claude.ai/artifact/14k3waBngc76XEj2JhUusL",
    "parent": "https://claude.ai/artifact/1ayTdyUEY1avfBfUARaiLo",
    # ハブを3つに分けたので、実践と解説は別のArtifactになる（2026-09-20 発行）
    "guides": "https://claude.ai/artifact/WthDFVCMFYPpKBXrgkwWzs",
    "ref": "https://claude.ai/artifact/GbMG66nTbwbAYRBRCg6Le7",
    # VEX 解説は GitHub 版だけ（2026-09-24 新設。Artifact の写しは出していない）
    "vex": "https://realestatewarrior.github.io/houdini-lab/vex.html",
}

# GitHub Pages 版。ルートがハブになるよう index.html をハブに割り当てる。
PAGES_URLS = {
    "home": "index.html",
    "log": "log.html",
    "log_pm": "log.html",
    "log_fx": "log_fx.html",
    "glossary": "glossary.html",
    "links": "links.html",
    "guides": "practice.html",
    "ref": "reference.html",
    "vex": "vex.html",
    # 親は別リポジトリの入口（realestatewarrior.github.io/）。
    # この部のページは /houdini-lab/ 以下なので、1つ上が親になる。
    "parent": "../",
}

# 親ページ用。親は入口（/）に置き、この部は /houdini-lab/ 以下にある。
ROOT_URLS = {
    "home": "houdini-lab/index.html",
    "log": "houdini-lab/log.html",
    "log_pm": "houdini-lab/log.html",
    "log_fx": "houdini-lab/log_fx.html",
    "glossary": "houdini-lab/glossary.html",
    "links": "houdini-lab/links.html",
    "guides": "houdini-lab/practice.html",
    "ref": "houdini-lab/reference.html",
    "vex": "houdini-lab/vex.html",
    "parent": "index.html",
}

# ロゴ。S を書き終えた線から縦棒が下りて、S の下半分が P の腹になる。
# 押すと親（Saito Production）へ戻る。
LOGO_SVG = (
    '<svg viewBox="0 0 48 48" fill="none" aria-hidden="true">'
    '<g transform="translate(24 24) scale(1.46) translate(-22.7 -26.4)"'
    ' stroke="currentColor" stroke-width="2.3" stroke-linecap="round">'
    '<path d="M28.6 16.4c-1.2-1.6-3.2-2.5-5.5-2.5-3.3 0-5.6 1.7-5.6 4.1'
    ' 0 2.2 1.6 3.4 4.7 4.1l1.6.4c3.1.7 4.7 2 4.7 4.4 0 2.6-2.4 4.4-6 4.4'
    '-2.3 0-4.3-.7-5.7-2"/>'
    '<path d="M22.6 22.3v16.6"/>'
    "</g></svg>"
)
BRAND = "Saito Production"
DEPT = "Houdini 研究部"

# 親サイトと、その下の部。映像制作部はまだ無いので押せない印にしておく。
PARENT_URLS = {
    "pages": "sp.html",
    "artifact": "https://claude.ai/artifact/1ayTdyUEY1avfBfUARaiLo",
}
DEPARTMENTS = [
    ("houdini", "Houdini 研究部", True),
    ("film", "映像制作部", False),
]

SEARCH_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8"/>'
    '<path d="M15.4 15.4L20 20" stroke="currentColor" stroke-width="1.8"'
    ' stroke-linecap="round"/></svg>'
)
AI_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<path d="M12 3.5l1.9 4.9 4.9 1.9-4.9 1.9L12 17.1l-1.9-4.9-4.9-1.9 4.9-1.9z"'
    ' stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>'
    '<path d="M18.5 15.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"'
    ' fill="currentColor"/></svg>'
)
AI_BUTTON = ('      <button type="button" class="nav-icon nav-ai" id="ask-open" hidden'
             ' aria-label="AI に聞く（Beta 版）" title="AI に聞く（Beta 版）">'
             + AI_SVG + '<span class="nav-beta">Beta</span></button>')
NOTEBOOK_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<path d="M5 4.5h10.5a3 3 0 013 3V19.5H8a3 3 0 01-3-3z" stroke="currentColor"'
    ' stroke-width="1.6" stroke-linejoin="round"/>'
    '<path d="M5 16.5a3 3 0 013-3h10.5M9 8h6" stroke="currentColor" stroke-width="1.6"'
    ' stroke-linecap="round"/></svg>'
)
BURGER_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<path d="M4 9h16M4 15h16" stroke="currentColor" stroke-width="1.8"'
    ' stroke-linecap="round"/></svg>'
)


# ハブ内のタブ。読み込みなしで切り替わる。子ページでは同じ並びがリンクになる。
TABS = [
    ("overview", "ホーム"),
    ("guides", "実践"),
    ("works", "制作"),
    ("requests", "要望"),
    ("experiments", "実験"),
    ("speed", "効率化"),
    ("nodes", "ノード解説"),
    ("glossary", "用語集"),
    ("links", "参考リンク"),
]

# 上のバーは4つに畳む。乗せると下に大きなパネルが降りて、その中の行き先が並ぶ。
# 押したときは先頭の行き先へ飛ぶ。ページ自体はどれも今のまま。
#   (見出し, 押したときの行き先, [(行き先, 名前, 一言), ...])
# 行き先が "@" で始まるものは別ページ（urls の鍵）、それ以外はハブのタブ。
MENU = [
    ("ホーム", "overview", []),
    ("実践", "guides", [
        ("作り方", [
            ("guides", "実践", "作り方を順に並べたもの"),
            ("works", "制作", "頼まれて作った一点物の記録"),
        ]),
        ("順番待ち", [
            ("requests", "要望", "作ってほしいものと、その順番"),
        ]),
    ]),
    ("実験", "experiments", [
        ("測った記録", [
            ("experiments", "実験集", "1件ずつ。押すと中身が開く"),
        ]),
        ("全文を読む", [
            ("@log", "実験ログ モデリング編", "形を作る側"),
            ("@log_fx", "実験ログ エフェクト編", "動かす側"),
        ]),
        ("そのほか", [
            ("speed", "効率化", "速さについて分かったこと"),
            ("links", "参考リンク", "外の資料"),
        ]),
    ]),
    ("解説", "nodes", [
        ("調べる", [
            ("nodes", "ノード解説", "箱ひとつずつの説明"),
            ("glossary", "用語集", "言葉の意味"),
            ("@vex", "VEX 解説", "書き方・使い方・測って分かったこと"),
        ]),
    ]),
]

# その行き先にいるときに印を付けるための対応表
ACTIVE_OF = {"glossary": "解説", "vex": "解説", "links": "実験", "log": "実験", "log_fx": "実験"}

# Claude 版は1つの版に置けるファイルが512まで。パネルを全部1ページに入れると
# 529 必要で入らない（実践のパラメータ画面163・実験の図145・サムネイル104…）。
# そこでハブを3ページに分ける。枠は Artifact ごとに付くので、これで収まる。
# 外部から画像を読む案は使えない（Artifact は自分のファイルと Google Fonts と
# 一部のCDNしか通さない。2026-09-20 に発行して確かめた）。
PAGE_PANELS = {
    "home": ["overview", "experiments", "speed"],
    "guides": ["guides", "works", "requests"],
    "ref": ["nodes", "glossary", "links"],
}
PANEL_PAGE = {panel: page
              for page, panels in PAGE_PANELS.items()
              for panel in panels}

# ページの名前。Artifact の一覧では <title> がそのまま名前になるので、
# 3つのハブが同じ名前で並ばないように分ける。
PAGE_TITLE = {
    "home": "Houdini 研究部",
    "guides": "Houdini 研究部 — 実践と制作",
    "ref": "Houdini 研究部 — ノードと用語",
}


def panel_url(urls, panel):
    """そのパネルを持っているページの住所に #パネル を付けて返す。"""
    page = PANEL_PAGE.get(panel, "home")
    return f'{urls[page]}#{panel}'


def guide_page(guide_id):
    """実践（と制作）1本ずつのページの名前。ポップアップをやめて独立させた（2026-09-23）。"""
    return f"guide_{guide_id}.html"


def guide_url(urls, guide_id):
    """実践ひとつを開く住所。実践一覧のページと同じ場所に、1本ずつのページを置く。"""
    base = urls[PANEL_PAGE["guides"]]
    if base.startswith("http"):
        # Claude 版（Artifact）は出し直しをやめたので、古い形のまま
        return f'{base}#guide-{guide_id}'
    folder = base.rsplit("/", 1)[0] + "/" if "/" in base else ""
    return folder + guide_page(guide_id)


DONE = [
    {"no": "001", "anchor": "exp001", "tags": ["モデリング", "ノイズ", "基礎"], "log": "log_pm", "hip": "box_mountain.hipnc", "thumb": "box_mountain.png",
     "report": "box_mountain_report.json",
     "shots": ["box_mountain.png", "box_mountain_graph.png"],
     "title": "Box を山にして細分割し、位置で色を付ける",
     "note": "最小構成。mountain は点を増やさないと分かった"},
    {"no": "002", "anchor": "exp002", "tags": ["モデリング", "分割", "検算"], "log": "log_pm", "hip": "002_subdivide.hipnc", "thumb": "002_subdiv_3.png",
     "shots": ["002_subdiv_0.png", "002_subdiv_3.png"],
     "title": "subdivide の回数で、形と数はどう変わるか",
     "note": "面数は正確に4倍、点数は常に面数+2。縮む原因は分割ではなく平滑化"},
    {"no": "003", "anchor": "exp003", "tags": ["モデリング", "ノイズ", "分割"], "log": "log_pm", "hip": "003_order.hipnc", "thumb": "003_D.png",
     "shots": ["003_C.png", "003_D.png"],
     "title": "mountain と subdivide は、順序を変えると何が変わるか",
     "note": "点数は解像度を決め、凹凸の大きさは elementsize が決める"},
    {"no": "004", "anchor": "exp004", "tags": ["モデリング", "ノイズ", "パラメータ"], "log": "log_pm", "hip": "004_mountain_params.hipnc", "thumb": "004_rough_10.png",
     "shots": ["004_rough_00.png", "004_rough_10.png"],
     "title": "mountain のノイズパラメータは、それぞれ何に効くのか",
     "note": "rough が形の性質を決める。oct は点数が足りないと効かない"},
    {"no": "005", "anchor": "exp005", "tags": ["モデリング", "ノイズ", "比較"], "log": "log_pm", "hip": "005_noise_basis.hipnc", "thumb": "005_mworleyFA.png",
     "shots": ["005_perlin.png", "005_mworleyFA.png"],
     "title": "basis 14通りで、形はどこまで変わるか",
     "note": "振幅も性質も変わる。外向きに押すか内向きに削るかが種類で決まる"},
    {"no": "006", "anchor": "exp006", "tags": ["モデリング", "ノイズ", "パラメータ", "訂正"], "log": "log_pm", "hip": "006_height_shape.hipnc", "thumb": "006_bias_075.png",
     "shots": ["006_bias_025.png", "006_bias_075.png"],
     "title": "height は純粋な倍率か。gain と bias は何に効くか",
     "note": "005の「上限がある」は誤りだった。bias で突起と窪みを連続的に制御できる"},
    {"no": "007", "anchor": "exp007", "tags": ["モデリング", "地形", "指標"], "log": "log_pm", "hip": "007_grid_terrain.hipnc", "thumb": "007_frac_fBm.png",
     "shots": ["007_flat.png", "007_frac_fBm.png"],
     "title": "平面で地形を作り、指標を作り直す",
     "note": "勾配が止まる点が「足りている解像度」を教えてくれる。fractal は平面で差が出る"},
    {"no": "008", "anchor": "exp008", "tags": ["モデリング", "複製", "地形"], "log": "log_pm", "hip": "008_scatter_copy.hipnc", "thumb": "008_z_axis.png",
     "shots": ["008_plain.png", "008_z_axis.png"],
     "title": "scatter と copy to points — 地面に物を生やす",
     "note": "N はテンプレートのZ軸に対応する。Y軸のまま複製すると必ず横倒しになる"},
    {"no": "009", "anchor": "exp009", "tags": ["VEX", "速度"], "log": "log_pm", "hip": "009_vex.hipnc", "thumb": "009_wave.png",
     "shots": ["009_wave.png"],
     "title": "attribute wrangle で VEX を書く",
     "note": "実行対象でアトリビュートの置き場所が変わる。処理時間の計測は3回目で本物になった"},
    {"no": "010", "anchor": "exp010", "tags": ["VEX", "速度", "比較"], "log": "log_pm", "hip": "010_foreach.hipnc", "thumb": "010_ui_network.png",
     "shots": ["010_ui_network.png"],
     "title": "for-each ループと VEX を比べる",
     "note": "3,969面で85.9倍の差。ただし置き換え可能とは限らず、点の共有が鍵だった"},
    {"no": "011", "anchor": "exp011", "tags": ["モデリング", "分割", "指標"], "log": "log_pm", "hip": "011_crease.hipnc", "thumb": "011_w3_0.png",
     "shots": ["011_w0_0.png", "011_w3_0.png"],
     "title": "crease で角を残す — どれだけの重みが要るのか",
     "note": "分割回数と同じ重みで完全に角が残る。一辺だけ見ていると誤判定する"},
    {"no": "012", "anchor": "exp012", "tags": ["モデリング", "ブーリアン", "検算"], "log": "log_pm", "hip": "012_extrude_boolean.hipnc", "thumb": "012_bool_subtract.png",
     "shots": ["012_bool_union.png", "012_bool_subtract.png"],
     "title": "polyextrude と boolean — 硬い形を作る",
     "note": "押し出しは寸法が指定どおり。boolean は体積の関係式で正しさを検算できる"},
    {"no": "013", "anchor": "exp013", "tags": ["ツール", "時間"], "log": "log_fx", "hip": "013_time.hipnc", "thumb": "013_sheet.png",
     "shots": ["013_wave.gif", "013_sheet.png"],
     "title": "時間軸への対応 — フレームを進めて記録する",
     "note": "連番・コンタクトシート・GIF。パーティクルはSOPに0種でDOPに67種と判明"},
    {"no": "014", "anchor": "exp014", "tags": ["エフェクト", "剛体", "保存量"], "log": "log_fx", "hip": "014_rbd.hipnc", "thumb": "014_sheet.png",
     "shots": ["014_rbd.gif", "014_sheet.png"],
     "title": "RBD 破壊 — 最初の本物のシミュレーション",
     "note": "体積が全フレームで完全に保存。落下中は砕けず、着地して2.8倍に散らばる"},
    {"no": "015", "anchor": "exp015", "tags": ["エフェクト", "布", "保存量"], "log": "log_fx", "hip": "015_vellum.hipnc", "thumb": "015_sheet.png",
     "shots": ["015_cloth.gif", "015_sheet.png"],
     "title": "Vellum クロス — 布で保存されるべき量は何か",
     "note": "かたさは「値 × 10の指数乗」。既定の指数10のせいで値を触っても効かない"},
    {"no": "016", "anchor": "exp016", "tags": ["エフェクト", "煙", "式"], "log": "log_fx", "hip": "016_pyro.hipnc", "thumb": "016_sheet.png",
     "shots": ["016_sheet.png"],
     "title": "Pyro 煙 — dissipation の正体を式で突き止める",
     "note": "毎フレーム (1−d) 倍に減らす仕組み。立てた式と実測が4桁一致した"},
    {"no": "017", "anchor": "exp017", "tags": ["エフェクト", "液体", "保留"], "log": "log_fx", "hip": "017_flip.hipnc", "thumb": "017_graph.png",
     "shots": ["017_graph.png"],
     "title": "FLIP 液体 — 組み方が分からず保留",
     "note": "4通りの配線を試して全部同じエラー。他のソルバと作法が違うと判明"},
    {"no": "018", "anchor": "exp018", "tags": ["レンダリング", "式", "比較"], "log": "log_fx", "hip": "018_karma.hipnc", "thumb": "018_karma.png",
     "shots": ["018_noise_strip.png", "018_opengl.png", "018_karma.png"],
     "title": "Karma でのレンダリング — ノイズはサンプル数で本当に減るのか",
     "note": "サンプル数は上限であって指定ではない。頭打ちの犯人は varianceaa_thresh"},
    {"no": "019", "anchor": "exp019", "tags": ["エフェクト", "液体", "配線", "訂正"], "log": "log_fx", "hip": "019_flip.hipnc", "thumb": "019_sheet.png",
     "shots": ["019_pool.gif", "019_sheet.png"],
     "title": "FLIP 液体 — 配線が解けた。そして粒の数は体積ではなかった",
     "note": "017の保留を解決。コンテナは3チャンネルの中継点で、VDBの名前が役割を決める"},
    {"no": "020", "anchor": "exp020", "tags": ["エフェクト", "パーティクル", "式"], "log": "log_fx", "hip": "020_pop.hipnc", "thumb": "020_sheet.png",
     "shots": ["020_pop.gif", "020_graph.png"],
     "title": "POP パーティクル — 生まれる数と落ち方を式で確かめる",
     "note": "生まれる数は指定どおり。落ち方のずれは計算の刻み1.3個ぶんの遅れだった"},
    {"no": "021", "anchor": "exp021", "tags": ["エフェクト", "煙", "訂正"],
     "log": "log_fx", "hip": "021_smoke.hipnc", "thumb": "021_compare.png",
     "shots": ["021_compare.png", "021_rise.gif"],
     "title": "煙はなぜ動かなかったのか — 温度を入れると立ち上る",
     "note": "温度を供給しないと浮力が働かない。016と018の煙も止まっていた"},
    {"no": "022", "anchor": "exp022", "tags": ["エフェクト", "液体", "検算", "訂正"],
     "log": "log_fx", "hip": "022_surface.hipnc", "thumb": "022_clipped.png",
     "shots": ["022_particles.png", "022_clipped.png"],
     "title": "液体に表面を張る — そして019の係数が間違っていた",
     "note": "水の体積は「器の中の粒の数 × 間隔の3乗」ちょうど。比 1.0006"},
    {"no": "023", "anchor": "exp023", "tags": ["エフェクト", "炎", "比較"],
     "log": "log_fx", "hip": "023_fire.hipnc", "thumb": "023_compare.png",
     "shots": ["023_compare.png", "023_fire.gif"],
     "title": "炎を出す — shredding が効かなかった理由",
     "note": "炎があるときだけ効く。炎の合計が40%減り、ばらつきが9%増える"},
    {"no": "024", "anchor": "exp024", "tags": ["レンダリング", "煙", "比較"],
     "log": "log_fx", "hip": "024_karma.hipnc", "thumb": "024_compare.png",
     "shots": ["024_compare.png"],
     "title": "動く煙で撮り直す — 018の結論は変わらなかった",
     "note": "題材を入れ替えても指標はほぼ同じ。確かめた価値はあった"},
    {"no": "025", "anchor": "exp025", "tags": ["ツール", "速度", "検算"],
     "log": "log_fx", "hip": "025_cache.hipnc", "thumb": "025_graph.png",
     "shots": ["025_graph.png"],
     "title": "シミュレーションのキャッシュ — 速くなるが、値は変わっていないか",
     "note": "読み込みは4.6倍速く、値は完全に一致。範囲の指定で3.5GB無駄にした"},
    {"no": "026", "anchor": "exp026", "tags": ["エフェクト", "炎", "レンダリング", "VEX"],
     "log": "log_fx", "hip": "026_color.hipnc", "thumb": "026_fire_color.png",
     "shots": ["026_ramp.png", "026_fire_color.png"],
     "title": "炎に色を付ける — 黒体放射の式を、数字で追う",
     "note": "赤と青の比が1000Kから8000Kで23.6分の1に。1で切ると色味が消える"},
    {"no": "027", "anchor": "exp027", "tags": ["ツール", "速度", "検算", "煙"],
     "log": "log_fx", "hip": "027_cache_tool.hipnc", "thumb": "027_halved.png",
     "shots": ["027_default.png", "027_halved.png"],
     "title": "キャッシュを道具に組み込む — 古いファイルを読む事故を防ぐ",
     "note": "上流の指紋が変われば自動で計算し直す。無ければ29/30フレームで嘘の値を読んでいた"},
    {"no": "028", "anchor": "exp028", "tags": ["エフェクト", "布", "Vellum", "検算"],
     "log": "log_fx", "hip": "028_tear.hipnc", "thumb": "028_off.png",
     "shots": ["028_off.png", "028_t002.png"],
     "title": "布は破れなかった — 効かない条件を14通り潰す",
     "note": "しきい値の2.7×10^10倍の応力をかけても切れた拘束はゼロ。原因は特定できていない"},
    {"no": "029", "anchor": "exp029", "tags": ["エフェクト", "パーティクル", "POP", "検算"],
     "log": "log_fx", "hip": "029_forces.hipnc", "thumb": "029_axis.png",
     "shots": ["029_force.png", "029_wind.png", "029_axis.png"],
     "title": "粒に力をかける — 風は「押す」のではなく「追いつかせる」",
     "note": "見立てた式が外れ、風速を変えて測り直したら二乗抵抗だった。15点すべて一致"},
    {"no": "030", "anchor": "exp030", "tags": ["点検", "検算", "プロシージャルモデリング"],
     "log": "log_pm", "hip": None, "thumb": "030_audit.png",
     "shots": ["030_audit.png"],
     "title": "過去29回を測り直す — 書いたことは、いまも正しいか",
     "note": "7項目を再測定。5つは確認、2つは訂正。数字は動かず、動いたのは書き方だけ"},
    {"no": "031", "anchor": "exp031", "tags": ["エフェクト", "布", "Vellum", "検算"],
     "log": "log_fx", "hip": "031_break.hipnc", "thumb": "031_tear.png",
     "shots": ["031_hold.png", "031_tear.png"],
     "title": "Vellum の breaking は動く — ただし布の伸びには効かない",
     "note": "028の宿題を回収。glue の stitch は破れ、cloth の distance は同じ場面でも破れない"},
    {"no": "032", "anchor": "exp032", "tags": ["エフェクト", "布", "Vellum"],
     "log": "log_fx", "hip": "032_tear_line.hipnc", "thumb": "032_torn.png",
     "shots": ["032_intact.png", "032_torn.png"],
     "title": "狙った線で破れる布 — 先に切って、あとから貼る",
     "note": "波の線で切って glue で貼り直す。ずれは最大0.101でマス目1つぶん未満"},
    {"no": "033", "anchor": "exp033", "tags": ["エフェクト", "布", "Vellum", "検算"],
     "log": "log_fx", "hip": "033_impact.hipnc", "thumb": "033_hit.png",
     "shots": ["033_miss.png", "033_hit.png"],
     "title": "布を物にぶつけて破る — 破れ始めは当たった場所、そのあとは全体へ",
     "note": "球なし0本に対し球ありは最大80本。ただし最後は内外でほぼ同じ割合になる"},
    {"no": "034", "anchor": "exp034", "tags": ["モデリング", "地形", "HeightField"],
     "log": "log_pm", "hip": "034_heightfield.hipnc", "thumb": "034_eroded.png",
     "shots": ["034_raw.png", "034_eroded.png"],
     "title": "HeightField で地形を作る — 高さを面ではなく数の並びで持つ",
     "note": "プリミティブは2つだけ。浸食で勾配が32.7%下がる。Grid Samples は効かない"},
    {"no": "035", "anchor": "exp035", "tags": ["モデリング", "地形", "HeightField", "複製"],
     "log": "log_pm", "hip": "035_scatter.hipnc", "thumb": "035_masked.png",
     "shots": ["035_plain.png", "035_masked.png"],
     "title": "地形の上に生やし分ける — 浸食が残した情報で木の場所を決める",
     "note": "堆積を重みにすると生える場所の勾配が94.9%下がる。崖が裸になる"},
    {"no": "036", "anchor": "exp036", "tags": ["モデリング", "地形", "HeightField", "複製"],
     "log": "log_pm", "hip": "036_flow.hipnc", "thumb": "036_flow.png",
     "shots": ["036_flat.png", "036_flow.png"],
     "title": "流れの向きに草を寝かせる — flowdir は x と y が入れ替わっている",
     "note": "素直な並びは96.5度でハズレ。8通り総当たりで入れ替えが正解と決めた"},
    {"no": "037", "anchor": "exp037", "tags": ["モデリング", "地形", "HeightField", "レンダリング"],
     "log": "log_pm", "hip": "037_color.hipnc", "thumb": "037_color.png",
     "shots": ["037_plain.png", "037_color.png"],
     "title": "浸食のレイヤーで地形を塗り分ける — 色は情報を持っているか",
     "note": "岩肌は土の6.32倍急。しきい値は分布を見てから決める"},
    {"no": "038", "anchor": "exp038", "tags": ["レンダリング", "Karma", "地形", "訂正"],
     "log": "log_pm", "hip": "038_karma.hipnc", "thumb": "038_karma_mat.png",
     "shots": ["038_karma_nomat.png", "038_karma_mat.png"],
     "title": "塗り分けた地形を Karma で出す — 見立ては外れ、白飛びが本命だった",
     "note": "点の色は材質なしでも出る。ただし白飛びが43.4%→3.1%と14倍違う"},
    {"no": "039", "anchor": "exp039", "tags": ["テクスチャ", "COP", "ノイズ", "指標"],
     "log": "log_pm", "hip": "039_cop.hipnc", "thumb": "039_roughs.png",
     "shots": ["039_elements.png", "039_roughs.png"],
     "title": "Copernicus でテクスチャを作る — 細かさは解像度をどう食うのか",
     "note": "解像度を掛けて直すと007の勾配と同じ形。頭打ちが「足りている解像度」"},
    {"no": "040", "anchor": "exp040", "tags": ["テクスチャ", "COP", "Karma", "地形"],
     "log": "log_pm", "hip": "040_texture.hipnc", "thumb": "040_compare.png",
     "shots": ["040_compare.png"],
     "title": "作ったテクスチャを地形に貼る — 貼れたかどうかを画の数字で判定する",
     "note": "細かさ1.36倍で貼れたと判定。解像度4倍でも画は1.04倍しか変わらない"},
    {"no": "041", "anchor": "exp041", "tags": ["レンダリング", "Karma", "テクスチャ", "検算"],
     "log": "log_pm", "hip": "041_disp.hipnc", "thumb": "041_compare.png",
     "shots": ["041_compare.png"],
     "title": "凸凹の付け方3通り — 輪郭を見れば、どれが本当に形を変えたか分かる",
     "note": "bumpは細かさ1.77倍でも輪郭0.999倍。displacementは点を動かさず輪郭を変える"},
    {"no": "042", "anchor": "exp042", "tags": ["グルーム", "毛", "複製"],
     "log": "log_pm", "hip": "042_groom.hipnc", "thumb": "042_thick.png",
     "shots": ["042_thin.png", "042_thick.png"],
     "title": "毛を生やす — density は本数ではなく「面積あたりの本数」だった",
     "note": "100を入れて1,249本。面積12.53で割ると99.678。length は純粋な倍率"},
    {"no": "043", "anchor": "exp043", "tags": ["グルーム", "毛", "属性", "総当たり"],
     "log": "log_pm", "hip": "043_clump.hipnc", "thumb": "043_clumped.png",
     "shots": ["043_loose.png", "043_clumped.png"],
     "title": "毛を束ねる — つなぐ順番が、思っていたのと逆だった",
     "note": "hairgenは土台→ガイド、hairclumpは毛→土台。2つで逆。clumpsize 0.8は逆に広がる"},
    {"no": "044", "anchor": "exp044", "tags": ["グルーム", "毛", "属性", "訂正", "落とし穴"],
     "log": "log_pm", "hip": "044_influence.hipnc", "thumb": "044_guided.png",
     "shots": ["044_ignored.png", "044_guided.png"],
     "title": "つないだのに、ガイドが1本も使われていなかった — rest が (0,0,0) だった",
     "note": "addpointで作った点のrestは既定値のまま。hairgenはrest空間で距離を測る。警告も出ない"},
    {"no": "045", "anchor": "exp045", "tags": ["グルーム", "毛", "レンダリング", "Karma", "検算"],
     "log": "log_pm", "hip": "045_hair_render.hipnc", "thumb": "045_thick_0.008.png",
     "shots": ["045_thick_0.001.png", "045_thick_0.008.png"],
     "title": "毛を Karma で出す — 既定の太さは、画の上で 0.1ピクセルしかなかった",
     "note": "width は直径（比0.997）。既定0.001は0.103px。Apprenticeのロゴが測定に混ざっていた"},
    {"no": "046", "anchor": "exp046", "tags": ["グルーム", "毛", "色", "レンダリング", "検算"],
     "log": "log_pm", "hip": "046_hair_color.hipnc", "thumb": "046_ball_clump.png",
     "shots": ["046_ball_plain.png", "046_ball_tip.png", "046_ball_clump.png"],
     "title": "毛に色を付ける — 光を消して測ると、色は位置ぴったりに乗った",
     "note": "毛はPとwidthしか持たない。発光で測るとR²=0.99991。widthは毛先で0に先細り"},
    {"no": "047", "anchor": "exp047", "tags": ["グルーム", "毛", "アニメーション", "検算"],
     "log": "log_pm", "hip": "047_hair_follow.hipnc", "thumb": "047_follow.png",
     "shots": ["047_start.png", "047_follow.png"],
     "title": "土台が動いたとき、毛は付いてくるのか — 入力をひとつつなぐかどうかだけの差",
     "note": "入力2をつなぐと根元の離れは全フレーム0.000000。外すと変形の8.5%ずれる"},
    {"no": "048", "anchor": "exp048", "tags": ["グルーム", "毛", "Vellum", "シミュレーション", "検算"],
     "log": "log_pm", "hip": "048_hair_sim.hipnc", "thumb": "048_fall.png",
     "shots": ["048_start.png", "048_fall.png"],
     "title": "毛を揺らす — 曲がりにくさは「垂れる距離」ではなく「形」に効いていた",
     "note": "bendstiffnessを100万倍にしても毛先の高さは1.2%。まっすぐさは0.835→0.990"},
    {"no": "049", "anchor": "exp049", "tags": ["グルーム", "毛", "Vellum", "風", "検算"],
     "log": "log_pm", "hip": "049_hair_wind.hipnc", "thumb": "049_windy.png",
     "shots": ["049_calm.png", "049_windy.png"],
     "title": "毛に風を当てる — 実験029と同じ「二次の抵抗」だった",
     "note": "残差は一次0.0263に対し二次0.0074。3.5倍よく乗る。強い風では毛が5.9%伸びる"},
    {"no": "050", "anchor": "exp050", "tags": ["APEX", "リグ", "新分野", "落とし穴"],
     "log": "log_pm", "hip": "", "thumb": "050_parts.png",
     "shots": ["050_parts.png", "050_graph.png"],
     "title": "APEX に入る — 2,220個の部品と、いちばん小さいグラフ",
     "note": "部品2,220種。Add の2つ目の入力は可変長で、値を入れても無視される（警告なし）"},
    {"no": "051", "anchor": "exp051", "tags": ["APEX", "リグ", "KineFX", "検算"],
     "log": "log_pm", "hip": "051_skeleton.hipnc", "thumb": "051_bent.png",
     "shots": ["051_rest.png", "051_bent.png"],
     "title": "骨を作って動かす — rotate と prerotate を取り違えると、関節ごと飛んでいく",
     "note": "式とのずれ 6e-8。rotate だと 90度で 1.41 ずれ、回した関節まで動く"},
    {"no": "052", "anchor": "exp052", "tags": ["APEX", "リグ", "KineFX", "検算", "体積"],
     "log": "log_pm", "hip": "052_skin.hipnc", "thumb": "052_bent.png",
     "shots": ["052_rest.png", "052_bent.png", "052_sharp.png"],
     "title": "骨に肉を付ける — 曲げると痩せる。減り方は (1 − cos θ) にぴたり乗った",
     "note": "90度で体積27.13%減。減り = 27.1284% × (1 − cos θ)。骨1本なら0.85%"},
    {"no": "053", "anchor": "exp053", "tags": ["APEX", "リグ", "KineFX", "検算", "体積"],
     "log": "log_pm", "hip": "053_dualquat.hipnc", "thumb": "053_dualquat.png",
     "shots": ["053_linear.png", "053_dualquat.png"],
     "title": "痩せない曲げ方はあった — Dual Quaternion で体積の減りが 154分の1 になる",
     "note": "90度で 27.1284% 対 0.1764%。式に乗るのは Linear だけ（幅0.0001 対 0.0490）"},
    {"no": "054", "anchor": "exp054", "tags": ["APEX", "リグ", "KineFX", "速さ", "体積"],
     "log": "log_pm", "hip": "054_skin_cost.hipnc", "thumb": "054_linear.png",
     "shots": ["054_linear.png", "054_dualquat.png"],
     "title": "なぜ Linear が既定なのか — 速さではなかった。差は 4%",
     "note": "41万点で1.04倍。179度ひねると Linear は体積66.8%減。理由は決まらなかった"},
    {"no": "055", "anchor": "exp055", "tags": ["APEX", "リグ", "IK", "検算"],
     "log": "log_pm", "hip": "", "thumb": "055_reach.png",
     "shots": ["055_reach.png", "055_far.png"],
     "title": "逆運動学（IK）— 届かない場所を指すと、伸びきってそこで止まる",
     "note": "9通りすべてで式と全桁一致。blend は途中でいったん目標から遠ざかる"},
    {"no": "056", "anchor": "exp056", "tags": ["APEX", "リグ", "IK", "検算"],
     "log": "log_pm", "hip": "", "thumb": "056_long.png",
     "shots": ["056_short.png", "056_long.png"],
     "title": "長い鎖の IK — 式は同じ。ただし解き方は2種類あり、得意な範囲が逆",
     "note": "届く距離＝骨の本数。solver=1 は8割まで5〜100倍正確、9割超で逆転"},
    {"no": "057", "anchor": "exp057", "tags": ["APEX", "リグ", "ジオメトリ"],
     "log": "log_pm", "hip": "", "thumb": "057_graphgeo.png",
     "shots": ["057_graphgeo.png"],
     "title": "APEX のグラフを持ち歩く — ネットワークが、そのままジオメトリになる",
     "note": "ノード＝点、配線＝プリミティブ。2,617バイトのファイル1つで別プロセスへ渡る"},
    {"no": "058", "anchor": "exp058", "tags": ["書き出し", "Apprentice", "検証"],
     "log": "log_pm", "hip": "", "thumb": "058_formats.png",
     "shots": ["058_formats.png"],
     "title": "Apprentice で外へ出せる形式 — FBX も glTF も Alembic も止まる",
     "note": "9通り試して5通り。FBX/glTF/Alembic は不可。USD は .usdnc に変えられる"},
    {"no": "059", "anchor": "exp059", "tags": ["書き出し", "検証", "アトリビュート"],
     "log": "log_pm", "hip": "", "thumb": "059_obj.png",
     "shots": ["059_obj.png"],
     "title": "obj で渡せる範囲 — 色と UV は残る。自作のアトリビュートは全部落ちる",
     "note": "位置のずれ0。NURBSは2,160面に刻まれ点が7.2倍。グループもpscaleも消える"},
    {"no": "060", "anchor": "exp060", "tags": ["点検", "検算", "訂正"],
     "log": "log_pm", "hip": "", "thumb": "060_audit.png",
     "shots": ["060_audit.png"],
     "title": "031〜059 の振り返り点検 — 6件すべて一致。1件は「もっと強い結論」に変わった",
     "note": "条件を変えて測り直す。052の係数27.1284は形の大きさによらない定数だった"},
    {"no": "061", "anchor": "exp061", "tags": ["MPM", "新分野", "検算", "シミュレーション"],
     "log": "log_fx", "hip": "061_mpm.hipnc", "thumb": "061_fall.png",
     "shots": ["061_start.png", "061_fall.png"],
     "title": "MPM に入る — 落ち方は式に乗る。ただし時刻が 0.0742フレーム先に進んでいる",
     "note": "粒の数は幅0で完全保存。時刻のずれδ=0.003091秒を入れると誤差が41分の1"},
    {"no": "062", "anchor": "exp062", "tags": ["MPM", "シミュレーション", "体積", "落とし穴"],
     "log": "log_fx", "hip": "062_mpm.hipnc", "thumb": "062_sandy.png",
     "shots": ["062_elastic.png", "062_liquid.png", "062_sandy.png"],
     "title": "MPM でぶつける — 砂は 16% 膨らみ、既定の塊は 31% 縮む",
     "note": "数は保たれるが体積は保たれない。materialpreset はスクリプトから効かない"},
    {"no": "063", "anchor": "exp063", "tags": ["MPM", "体積", "検算", "機械学習"],
     "log": "log_fx", "hip": "063_mpm_surface.hipnc", "thumb": "063_fine.png",
     "shots": ["063_coarse.png", "063_fine.png"],
     "title": "MPM の粒を面に戻す — 27% 太る。膨らむ厚みは粒の間隔の 0.4倍",
     "note": "voxelscale は体積を0.6%しか変えないのに点は4.3倍。機械学習の方法は点が2.5分の1"},
    {"no": "064", "anchor": "exp064", "tags": ["MPM", "シミュレーション", "速さ", "検算"],
     "log": "log_fx", "hip": "", "thumb": "064_sub16.png",
     "shots": ["064_sub1.png", "064_sub16.png"],
     "title": "MPM の刻みを細かくする — 量によって、落ち着く速さが違った",
     "note": "高さはsubstep 1で落ち着くが、広がりは8必要。16は1の25.5倍の時間"},
    {"no": "065", "anchor": "exp065", "tags": ["MPM", "シミュレーション", "速さ", "検算"],
     "log": "log_fx", "hip": "", "thumb": "065_fine.png",
     "shots": ["065_coarse.png", "065_fine.png"],
     "title": "MPM の粒を細かくする — 刻みより粒のほうが効くし、しかも安い",
     "note": "粒24.7倍で時間は3.73倍。高さが23%動く。substepは16倍で25.5倍かかって動かない"},
    {"no": "066", "anchor": "exp066",
     "tags": ["MPM", "シミュレーション", "検算", "落とし穴", "空気抵抗"],
     "log": "log_fx", "hip": "", "thumb": "066_wind.png",
     "shots": ["066_calm.png", "066_wind.png"],
     "title": "MPM の風 — 風速だけ上げても何も起きない。抵抗は速さの2乗だった",
     "note": "風は空気抵抗を通してしか効かない。横方向は式と0.06%一致。地面は既定で y=0 にある"},
    {"no": "067", "anchor": "exp067",
     "tags": ["MPM", "シミュレーション", "摩擦", "検算"],
     "log": "log_fx", "hip": "", "thumb": "067_slip.png",
     "shots": ["067_slip.png", "067_grip.png"],
     "title": "MPM の地面の摩擦 — 教科書の式に 0.04% で乗る。ただし塊が潰れるまで",
     "note": "Ground Friction はクーロン摩擦のμそのもの。摩擦が強いと塊が潰れて式から外れる"},
    {"no": "068", "anchor": "exp068",
     "tags": ["MPM", "シミュレーション", "摩擦", "材質", "検算"],
     "log": "log_fx", "hip": "", "thumb": "068_sandy.png",
     "shots": ["068_chunky.png", "068_viscous.png", "068_sandy.png",
               "068_liquid.png"],
     "title": "MPM の材質5つで滑らせる — 摩擦の式に乗るのは、形が崩れない材質だけ",
     "note": "崩れる順と式から外れる順が完全一致。Liquidの摩擦1.0は発散していた"},
    {"no": "069", "anchor": "exp069",
     "tags": ["MPM", "シミュレーション", "摩擦", "落とし穴", "検算"],
     "log": "log_fx", "hip": "", "thumb": "069_collider.png",
     "shots": ["069_collider.png"],
     "title": "MPM のコライダの摩擦 — 式は同じ。ただし地面と重ねると完全に無視される",
     "note": "同じ高さだとコライダの摩擦が効かない。効くのは「先に触った面」だけ"},
    {"no": "070", "anchor": "exp070",
     "tags": ["MPM", "シミュレーション", "摩擦", "落とし穴", "検算"],
     "log": "log_fx", "hip": "", "thumb": "070_carried.png",
     "shots": ["070_carried.png", "070_still.png"],
     "title": "動く板は塊をどれだけ運ぶか — 追いつくまでは式どおり。追いついた先で潰れて遅れる",
     "note": "コライダのTypeは既定がStaticで板が動かない。追いつく前は式と0.4%一致"},
    {"no": "071", "anchor": "exp071",
     "tags": ["MPM", "シミュレーション", "摩擦", "回転", "検算"],
     "log": "log_fx", "hip": "071_spin.hipnc", "thumb": "071_fling.png",
     "shots": ["071_stay.png", "071_fling.png"],
     "title": "回る台は塊をどこまで乗せておけるか — 境目は式の形どおり。ただし摩擦は 0.3〜0.4 ぶんしか効かない",
     "note": "回転は台の0.98〜1.00倍で伝わる。滑り出す境目は式の0.58倍。ω²rはほぼ一定"},
    {"no": "072", "anchor": "exp072",
     "tags": ["MPM", "シミュレーション", "コライダ", "落とし穴", "効率化"],
     "log": "log_fx", "hip": "072_deform.hipnc", "thumb": "072_heights.png",
     "shots": ["072_heights.png"],
     "title": "たわむ板は塊を放り上げられるか — Deforming は板の速さを渡す。Rigid はたわみを平均の動きにしてしまう",
     "note": "Deformingは板の速さを渡すが高さは式の30〜76%。Rigidは平均の動き。cv切りはすり抜け"},
    {"no": "073", "anchor": "exp073",
     "tags": ["MPM", "シミュレーション", "液体", "落とし穴", "効率化"],
     "log": "log_fx", "hip": "073_liquid.hipnc", "thumb": "073_top.png",
     "shots": ["073_top.png", "073_wild.png"],
     "title": "液体はいつ暴れ出すか — 摩擦の境目ではなく「時間」だった。substep 8 で消えるが 5倍かかる",
     "note": "摩擦0.25〜1.0は全部暴れる（F28〜46から）。0と1.5以上は静か。substep 8で消えるが4.7〜6.3倍"},
    {"no": "074", "anchor": "exp074",
     "tags": ["MPM", "シミュレーション", "粘着", "落とし穴"],
     "log": "log_fx", "hip": "074_sticky.hipnc", "thumb": "074_ceiling_1000.png",
     "shots": ["074_ceiling_0.png", "074_ceiling_1000.png"],
     "title": "sticky は天井にぶら下げられるか — 地面とコライダで効き方は同じ。ただし重さに逆らう力は無い",
     "note": "stickyは1〜2で頭打ち、5以上で地面とコライダが6桁一致。1000でも天井から落ちる"},
    {"no": "075", "anchor": "exp075",
     "tags": ["MPM", "シミュレーション", "摩擦", "効率化", "検算"],
     "log": "log_fx", "hip": "071_spin.hipnc", "thumb": "075_mu.png",
     "shots": ["075_mu.png"],
     "title": "摩擦の上限は、粒の細かさで上がる — substep を 8 にしても1ミリも動かない",
     "note": "実効の摩擦は間隔0.12で0.34、0.04で0.79。substep 1/4/8は境目が完全に同じで時間だけ5倍"},
    {"no": "076", "anchor": "exp076",
     "tags": ["MPM", "シミュレーション", "摩擦", "検算"],
     "log": "log_fx", "hip": "", "thumb": "076_ratio.png",
     "shots": ["076_ratio.png"],
     "title": "粒を細かくしても、摩擦の式には戻らない — 細かいほど塊が潰れ、かえって式から離れる",
     "note": "摩擦1.0の外れは1.46倍→1.73倍へ広がる。摩擦0.25はどの細かさでも1.000。細かいほど潰れる"},
    {"no": "077", "anchor": "exp077",
     "tags": ["ツール", "Python", "効率化", "測り方"],
     "log": "log_fx", "hip": "", "thumb": "077_read.png",
     "shots": ["077_read.png"],
     "title": "測る処理が、計算より重くなっていた — 1粒ずつ読むのをやめると 740倍速い",
     "note": "15,591粒を1粒ずつ読むと1フレーム82ms（計算と同じ）。numpyでまとめて0.11ms"},
    {"no": "078", "anchor": "exp078",
     "tags": ["MPM", "シミュレーション", "液体", "落とし穴"],
     "log": "log_fx", "hip": "", "thumb": "078_top.png",
     "shots": ["078_top.png"],
     "title": "液体の暴れは、粒を細かくしても消えない — 飛ぶ高さは下がるが、始まる時刻は変わらない",
     "note": "間隔0.16〜0.06の全部で暴れる（F22〜40）。飛ぶ高さは46→4.4に下がる。止めるのはsubstep"},
    {"no": "079", "anchor": "exp079",
     "tags": ["POP", "パーティクル", "火花", "実践"],
     "log": "log_fx", "hip": "079_sparks.hipnc", "thumb": "079_sparks_18.png",
     "shots": ["079_sparks_6.png", "079_sparks_18.png", "079_alive.png"],
     "title": "火花を散らす — Life Variance は幅、Variance は球の半径。空気抵抗は速さの2乗で効く",
     "note": "寿命は±幅に一様、初速は半径の球に一様、popdragは速さの2乗（ずれ0.0000）"},
    {"no": "080", "anchor": "exp080",
     "tags": ["POP", "パーティクル", "雨", "衝突", "実践"],
     "log": "log_fx", "hip": "080_rain.hipnc", "thumb": "080_rain.png",
     "shots": ["080_rain.png"],
     "title": "雨を地面で跳ねさせる — Bounce は速さの比で、地面と粒の値は掛け算になる",
     "note": "跳ね上がる高さはBounce²に近い。地面0.5×粒0.5＝地面0.25×粒1（4桁一致）。DieでResponse"},
    {"no": "081", "anchor": "exp081",
     "tags": ["Vellum", "布", "風", "実践"],
     "log": "log_fx", "hip": "081_flag.hipnc", "thumb": "081_flag_16.png",
     "shots": ["081_flag_4.png", "081_flag_16.png", "081_angle.png"],
     "title": "旗を風になびかせる — 風速 2 まではほぼ垂れたまま。持ち上がり方は「抵抗 × 風速²」でそろう",
     "note": "風速0〜2で85〜78度、4で41度、16で9度。抵抗×風速²が同じ組は0.6度差でそろう"},
    {"no": "082", "anchor": "exp082",
     "tags": ["モデリング", "曲線", "複製", "効率化", "実践"],
     "log": "log_pm", "hip": "082_path.hipnc", "thumb": "082_posts.png",
     "shots": ["082_posts.png", "082_roll_n.png", "082_roll_n_up.png"],
     "title": "道に沿って物を並べる — N だけでは坂で杭が倒れる。up を足せば 0度。Pack で 250倍速い",
     "note": "坂でNだけだと横に最大49度倒れ、upを足すと0度。Packで1万個714ms→2.9ms・1878MB→4MB"},
    {"no": "083", "anchor": "exp083",
     "tags": ["モデリング", "文字", "厚み", "実践"],
     "log": "log_pm", "hip": "083_sign.hipnc", "thumb": "083_round.png",
     "shots": ["083_flat.png", "083_thick.png", "083_round.png"],
     "title": "看板の文字を立体にする — Distance はそのまま奥行き。角の丸めは 0.08 で止まる",
     "note": "LODは点の数に比例（大きさは不変）。Output Backを切ると面が2枚減る。丸めは面積でしか追えない"},
    {"no": "084", "anchor": "exp084",
     "tags": ["RBD", "剛体", "落とし穴", "実践"],
     "log": "log_fx", "hip": "084_dominoes.hipnc", "thumb": "084_dominoes_30.png",
     "shots": ["084_dominoes_30.png", "084_dominoes_60.png"],
     "title": "ドミノを倒す — 間隔は高さの 0.25〜1.03倍。初速は点に付けないと効かない",
     "note": "初速はプリミティブでは効かず点に付ける。間隔は高さの0.25〜1.03倍。速さは1秒に2〜10枚"},
    {"no": "085", "anchor": "exp085",
     "tags": ["RBD", "破壊", "落とし穴", "効率化", "実践"],
     "log": "log_fx", "hip": "085_wall.hipnc", "thumb": "085_wall_500_58.png",
     "shots": ["085_wall_700_58.png", "085_wall_500_58.png", "085_wall_100_58.png"],
     "title": "壁を崩す — 拘束の強さの窓は狭い。弱いと自重で崩れ、強いとぶつけても壊れない",
     "note": "既定1000では無傷、100では自重で崩れる。窓は500前後。破片20倍でも解く時間は4.4倍"},
    {"no": "086", "anchor": "exp086",
     "tags": ["POP", "パーティクル", "風", "実践"],
     "log": "log_fx", "hip": "086_leaves.hipnc", "thumb": "086_leaves_2.png",
     "shots": ["086_leaves_0.png", "086_leaves_2.png"],
     "title": "葉を風で舞わせる — 乱れは Amplitude で広がり、Swirl Size で渦の大きさが変わる",
     "note": "Amplitude 0→4で散らばり0.76→1.47・速さ1.88→3.59。小さい乱れ（0.5〜1）は差が出ない"},
    {"no": "087", "anchor": "exp087",
     "tags": ["レンダリング", "カメラ", "ツール", "実践"],
     "log": "log_pm", "hip": "", "thumb": "087_sheet.png",
     "shots": ["087_sheet.png"],
     "title": "ターンテーブルで見せる — 形は物を回してもカメラを回しても同じ。変わるのは光だけ",
     "note": "シルエットは0.01ポイントまで一致。明るさは物を回すと一定、カメラを回すと186→51"},
    {"no": "088", "anchor": "exp088",
     "tags": ["レンダリング", "Karma", "材質", "効率化", "実践"],
     "log": "log_fx", "hip": "", "thumb": "088_emit4.png",
     "shots": ["088_emit0.png", "088_emit4.png", "088_emit64.png"],
     "title": "文字を光らせる — 明るさは頭打ち、こぼれる光と時間だけが増える",
     "note": "Emission16→64で明るさ+1.8%、床は127→143、時間は3.8→12.4秒。emitillum切りで3倍速い"},
    {"no": "089", "anchor": "exp089",
     "tags": ["POP", "パーティクル", "衝突", "実践"],
     "log": "log_fx", "hip": "089_leaves.hipnc", "thumb": "089_fallen_stuck.png",
     "shots": ["089_fallen_stuck.png", "089_fallen_none.png"],
     "title": "落ち葉を積もらせる — 積もるかどうかは Response で決まる。摩擦では止まらない",
     "note": "Stickで400枚中180枚が停止、既定は20枚、Slideは0枚。摩擦1でも20枚どまり"},
    {"no": "090", "anchor": "exp090",
     "tags": ["点検", "測り方", "ツール"],
     "log": "log_pm", "hip": "", "thumb": "090_audit.png",
     "shots": ["090_audit.png"],
     "title": "061〜090 の振り返り点検 — 7件を測り直して全部一致。訂正は2件、黙って無視される設定は8件に",
     "note": "7件すべて記録と同じ値。訂正は068←073と071←075。黙って無視される設定は8件に"},
    {"no": "091", "anchor": "exp091",
     "tags": ["モデリング", "polyreduce", "軽くする", "効率化"],
     "log": "log_pm", "thumb": "091_reduce.png",
     "shots": ["091_reduce.png"],
     "title": "面を半分にすると、形のずれはおよそ2倍になる — 25%まで減らしてもずれは幅の0.119%",
     "note": "3,540面を885面（25%）に減らしてずれ平均0.119%。2%では1.750%。時間は割合とほぼ無関係"},
    {"no": "092", "anchor": "exp092",
     "tags": ["モデリング", "remesh", "張り直す", "効率化"],
     "log": "log_pm", "thumb": "092_remesh.png",
     "shots": ["092_remesh.png", "092_gap.png"],
     "title": "辺の長さを半分にすると、面は約4倍・ずれは約1/4・時間は約4倍",
     "note": "面の倍率は実測 4.289 / 3.961 / 4.101。面積あたりで増えるという見方と合う"},
    {"no": "093", "anchor": "exp093",
     "tags": ["モデリング", "smooth", "体積", "落とし穴"],
     "log": "log_pm", "thumb": "093_smooth.png",
     "shots": ["093_smooth.png", "093_gap.png"],
     "title": "ならしても体積はほとんど減らない — 強さ160でも99.60%、縮みは0.40%だけ",
     "note": "既定の強さ10で99.95%。曲率を見るやり方が最も保つ（99.73%）"},
    {"no": "094", "anchor": "exp094",
     "tags": ["ボリューム", "VDB", "ボクセル", "効率化"],
     "log": "log_pm", "thumb": "094_voxels.png",
     "shots": ["094_voxels.png", "094_gap.png"],
     "title": "升目を半分にしても、数は8倍ではなく約4倍 — VDBは表面の近くだけ持っている",
     "note": "倍率は実測 3.706 / 3.917 / 3.975 / 3.993。ずれは最後の段で頭打ち"},
    {"no": "095", "anchor": "exp095",
     "tags": ["モデリング", "fuse", "点をまとめる", "落とし穴"],
     "log": "log_pm", "thumb": "095_fuse.png",
     "shots": ["095_fuse.png"],
     "title": "隙間 0.01 の継ぎ目は、Snap Distance が 0.01 になって初めて閉じる — 0.0095 では閉じない",
     "note": "球では 0.02 まで点が減ってもずれ 0.0（重なり点の掃除）。0.04 を超えると形が動く"},
    {"no": "096", "anchor": "exp096",
     "tags": ["モデリング", "scatter", "ばらまく", "効率化"],
     "log": "log_pm", "thumb": "096_scatter.png",
     "shots": ["096_scatter.png", "096_per.png"],
     "title": "Force Total Count はぴったり合う — 10通り試して差は1つも出なかった",
     "note": "100万点で約1秒。1点あたりは100点で10.873μ秒、100万点で1.038μ秒"},
    {"no": "097", "anchor": "exp097",
     "tags": ["モデリング", "pack", "軽くする", "効率化"],
     "log": "log_pm", "thumb": "097_pack.png",
     "shots": ["097_pack.png", "097_time.png"],
     "title": "pack を入れると、点は362分の1・ファイルは198分の1になる — 1万個で 22.5MB が 0.114MB",
     "note": "計算は0.129秒→0.002秒。代わりに中身を触るには unpack が必要になる"},
    {"no": "098", "anchor": "exp098",
     "tags": ["モデリング", "boolean", "VDB", "落とし穴"],
     "log": "log_pm", "thumb": "098_ngon.png",
     "shots": ["098_ngon.png", "098_hole.png"],
     "title": "boolean は答えと6桁まで一致する — 差の正体は円ではなく多角形だった",
     "note": "Primitive Type が poly でないと boolean も cookie も黙って何もしない"},
    {"no": "099", "anchor": "exp099",
     "tags": ["モデリング", "subdivide", "体積", "落とし穴"],
     "log": "log_pm", "thumb": "099_subdiv.png",
     "shots": ["099_subdiv.png", "099_step.png"],
     "title": "立方体を割り続けると、体積は約32.76%に落ち着く — bilinear だけはちょうど1.000000のまま",
     "note": "深さ3でほぼ決まる（33.31%）。深さ6で32.76%、面は64倍になるのに差は0.55ポイント"},
    {"no": "100", "anchor": "exp100",
     "tags": ["モデリング", "peak", "法線", "検算"],
     "log": "log_pm", "thumb": "100_box.png",
     "shots": ["100_box.png", "100_peak.png"],
     "title": "peak は式どおりに動く — 球は((r+d)/r)³、立方体は(1+2d/√3)³に6桁一致",
     "note": "球は18通りすべて一致。粗い球でも倍率は同じ。立方体は1+2dだと27倍を期待して16.99外す"},
    {"no": "101", "anchor": "exp101",
     "tags": ["モデリング", "measure", "面積", "検算"],
     "log": "log_pm", "thumb": "101_ratio.png",
     "shots": ["101_ratio.png", "101_area.png"],
     "title": "面積の測りは、平らな面ならぴったり合う — 球の足りない分は分割の2乗で減る",
     "note": "板は分割2〜201でどれも4.000000。球は分割を倍にすると足りない分が4分の1"},
    {"no": "102", "anchor": "exp102",
     "tags": ["モデリング", "polyextrude", "体積", "検算"],
     "log": "log_pm", "thumb": "102_inset.png",
     "shots": ["102_inset.png", "102_extrude.png"],
     "title": "押し出した体積は式どおり — 面積×距離、Inset を入れても四角錐台の式に6桁一致",
     "note": "10通りすべて差0.000000。上の面をほぼ潰しても体積は37%までしか減らない"},
    {"no": "103", "anchor": "exp103",
     "tags": ["モデリング", "transform", "回転", "検算"],
     "log": "log_pm", "thumb": "103_order.png",
     "shots": ["103_order.png"],
     "title": "Rotate Order の xyz は「x から順に掛ける」 — 6通りで最大 0.725534（約42.5°）ずれる",
     "note": "6通りすべて Rz·Ry·Rx の式と差0.000000。1軸だけなら順番は関係ない（差 1e-9未満）"},
    {"no": "104", "anchor": "exp104",
     "tags": ["モデリング", "resample", "carve", "検算"],
     "log": "log_pm", "thumb": "104_resample.png",
     "shots": ["104_resample.png", "104_seg.png"],
     "title": "resample の点の数は切り上げ — 「最大の長さ」は本当に最大だった",
     "note": "9通りすべて ceil(L/s)+1。carve の First U は入切で、値は domainu1 にある"},
    {"no": "105", "anchor": "exp105",
     "tags": ["モデリング", "spiral", "長さ", "検算"],
     "log": "log_pm", "thumb": "105_spiral.png",
     "shots": ["105_spiral.png"],
     "title": "spiral の長さは折れ線の式に6桁一致 — 1巻き50分割で 0.06% 短い",
     "note": "10通りすべて折れ線の式と差0.000001以下。既定50分割で0.06%短い"},
    {"no": "106", "anchor": "exp106",
     "tags": ["モデリング", "attribrandomize", "乱数", "検算"],
     "log": "log_pm", "thumb": "106_discrete.png",
     "shots": ["106_discrete.png"],
     "title": "attribrandomize の分布は式どおり — Scale Around Middle は標準偏差だった",
     "note": "一様・正規5通りとも平均のずれは標準誤差の約1倍。Scale Around Middle は標準偏差、整数の一様は上端を含む"},
    {"no": "107", "anchor": "exp107",
     "tags": ["モデリング", "extractcentroid", "重心", "検算"],
     "log": "log_pm", "thumb": "107_centroid.png",
     "shots": ["107_centroid.png"],
     "title": "extractcentroid の Center of Mass は、閉じていれば体積・開いていれば面積の中心",
     "note": "閉じた形は体積の中心、開いた形は面積の中心。Convex Hull は凸包の体積の中心（19/21 に一致）"},
    {"no": "108", "anchor": "exp108",
     "tags": ["モデリング", "triangulate2d", "三角形分割", "検算"],
     "log": "log_pm", "thumb": "108_tris.png",
     "shots": ["108_tris.png"],
     "title": "triangulate2d の三角形は 2n−2−h 枚 — 9通りすべて式どおり、面積は凸包と一致",
     "note": "9通りすべて 2n−2−h 枚。面積は凸包と一致。10万点で0.62秒"},
    {"no": "109", "anchor": "exp109",
     "tags": ["モデリング", "groupexpand", "グループ", "検算"],
     "log": "log_pm", "thumb": "109_expand.png",
     "shots": ["109_expand.png"],
     "title": "groupexpand の1段は「隣」の決め方しだい — 点と辺共有は菱形、面の既定は正方形",
     "note": "点と辺共有は菱形 2k²+2k+1、面の既定は正方形 (2k+1)²。負の段数は外周を1列ずつ削る"},
    {"no": "110", "anchor": "exp110",
     "tags": ["モデリング", "copyxform", "複製", "検算"],
     "log": "log_pm", "thumb": "110_turn.png",
     "shots": ["110_turn.png"],
     "title": "copyxform は「1回分をくり返す」ではなく「値を i 倍して1回かける」 — 回転＋移動は輪にならない",
     "note": "i個目は 移動i倍・回転i倍・拡大i乗 を1回かけた形。回転＋移動は輪にならず、6個目が x=10.5"},
    {"no": "111", "anchor": "exp111",
     "tags": ["モデリング", "pointjitter", "乱数", "検算"],
     "log": "log_pm", "thumb": "111_var.png",
     "shots": ["111_var.png"],
     "title": "pointjitter の Scale は「幅」 — 各軸 −s/2〜+s/2 の一様で、箱の中に散る",
     "note": "Scale は幅: 各軸 −s/2〜+s/2 の一様（分散 s²/12）。球ではなく箱の中に散る"},
    {"no": "112", "anchor": "exp112",
     "tags": ["モデリング", "VDB", "vdbcombine", "検算"],
     "log": "log_pm", "thumb": "112_csg.png",
     "shots": ["112_csg.png"],
     "title": "vdbcombine の和・積・差は球2つの式に収束 — ボクセル 0.0125 で 0.08% 以内、どれも少なめ",
     "note": "和・積・差ともボクセル0.0125で式の0.08%以内、12通りすべて少なめ。Operation の選択肢は18個"},
    {"no": "113", "anchor": "exp113",
     "tags": ["エフェクト", "timeblend", "補間", "検算"],
     "log": "log_pm", "thumb": "113_blend.png",
     "shots": ["113_blend.png"],
     "title": "timeblend は速度が無ければ直線、あれば F² を誤差0でつなぐ — v は「1秒あたり」",
     "note": "速度なしは直線（1.5フレームで2.5）。1秒あたりの v を渡すと F² を誤差0で再現"},
    {"no": "114", "anchor": "exp114",
     "tags": ["モデリング", "sweep", "体積", "検算"],
     "log": "log_pm", "thumb": "114_sweep.png",
     "shots": ["114_sweep.png"],
     "title": "sweep の管は曲がり角で細る — 不足は 1−cos(角/2)、Stretch Around Turns で A×L に一致",
     "note": "直線なら断面積×長さちょうど。曲がり角では 1−cos(角/2) だけ細る。Stretch Around Turns で一致"},
    {"no": "115", "anchor": "exp115",
     "tags": ["モデリング", "attribfill", "距離", "検算"],
     "log": "log_pm", "thumb": "115_eikonal.png",
     "shots": ["115_eikonal.png"],
     "title": "attribfill の到着時間は「網の辺をたどる道のり」 — 四角の網ではマンハッタン距離そのもの",
     "note": "Interpolate は式どおり。1点からの Arrival Time は四角の網で |x|+|z| に一致し、細かくしても直線距離にならない"},
    {"no": "116", "anchor": "exp116",
     "tags": ["モデリング", "uvflatten", "UV", "検算"],
     "log": "log_pm", "thumb": "116_uv.png",
     "shots": ["116_uv.png"],
     "title": "uvflatten は円筒をゆがみ0.0001%で開く — 半球は SCP 13%・ABF 10% ゆがむ",
     "note": "円筒はゆがみ0.0001%で開き縦横比は式と6桁一致。半球は SCP 13.5%・ABF 10.4% ゆがむ"},
    {"no": "117", "anchor": "exp117",
     "tags": ["モデリング", "relax", "点の配置", "検算"],
     "log": "log_pm", "thumb": "117_relax.png",
     "shots": ["117_relax.png"],
     "title": "relax は点を 2×pscale 近くまで離す — 余裕があれば97%、詰め込みに近いと73〜77%",
     "note": "pscale は半径。余裕があれば最小距離は 2×pscale の97%、詰め込みに近いと73〜77%"},
    {"no": "118", "anchor": "exp118",
     "tags": ["モデリング", "revolve", "体積", "検算"],
     "log": "log_pm", "thumb": "118_revolve.png",
     "shots": ["118_revolve.png"],
     "title": "revolve の面積・体積は k 角の式に6桁一致 — ただし閉じた断面を回すと体積がマイナス（裏返し）",
     "note": "側面積・体積とも k 角の式に6桁一致。閉じた断面を回すと体積がマイナス（裏返し）。Reverse Cross Sections で直る"},
    {"no": "119", "anchor": "exp119",
     "tags": ["モデリング", "距離", "distancealonggeometry", "検算"],
     "log": "log_pm", "thumb": "119_distance.png",
     "shots": ["119_distance.png"],
     "title": "面に沿った距離は Surface が正解 — Edge と attribfill は辺の道のり、Heat は約1%短い",
     "note": "Surface はずれ0.0003未満。Edge と attribfill は辺の道のり（四角の網で |x|+|z|）、Heat は約1%短い"},
    {"no": "120", "anchor": "exp120",
     "tags": ["モデリング", "measurethickness", "厚み", "検算"],
     "log": "log_pm", "thumb": "120_thickness.png",
     "shots": ["120_thickness.png"],
     "title": "measurethickness は殻の厚みを6桁で返す — 板の縁ではぼかしで細く出る。box の Use Divisions は面にならない",
     "note": "殻の厚みはずれ0.000001。板は既定のぼかしで縁が細く出る。box の Use Divisions（Polygon）は開いた線の籠"},
    {"no": "121", "anchor": "exp121",
     "tags": ["点検", "検算", "測り方"],
     "log": "log_pm", "thumb": "121_audit.png",
     "shots": ["121_audit.png"],
     "title": "091〜120 の振り返り点検 — 30本すべて流し直し、結果の数字は1つを除いて全部一致",
     "note": "30本すべて流し直し。時間以外で違ったのはファイルの大きさ1バイトと、手で足した項目1つだけ"},
    {"no": "122", "anchor": "exp122",
     "tags": ["モデリング", "polyexpand2d", "オフセット", "検算"],
     "log": "log_pm", "thumb": "122_offset.png",
     "shots": ["122_offset.png"],
     "title": "polyexpand2d は角を丸めずに尖らせる — 20°の鋭い角でも。Divisions は距離を等分する",
     "note": "角は丸めず尖らせる（20°の角でも）。Divisions は Offset の距離を等分する"},
    {"no": "123", "anchor": "exp123",
     "tags": ["モデリング", "shrinkwrap", "凸包", "検算"],
     "log": "log_pm", "thumb": "123_hull.png",
     "shots": ["123_hull.png"],
     "title": "shrinkwrap は凸包そのもの — 中の点をいくら足しても立方体は体積1.000000、同じ平面の三角形はまとめる",
     "note": "中の点を足しても立方体は体積1.000000。2D も別計算の凸包と一致。scatter の点は既定で縁に乗る（1000点中52点）"},
    {"no": "124", "anchor": "exp124",
     "tags": ["モデリング", "lsystem", "フラクタル", "検算"],
     "log": "log_pm", "thumb": "124_koch.png",
     "shots": ["124_koch.png"],
     "title": "L-System のコッホ曲線は式どおり — 全長4^n・端の間隔3^n。小数の世代は途中の形になる",
     "note": "0〜6世代すべて 全長4^n・端の間隔3^n。Generations 2.5 は3世代と同じ点の数で、全長40"},
    {"no": "125", "anchor": "exp125",
     "tags": ["モデリング", "divide", "edgedivide", "検算"],
     "log": "log_pm", "thumb": "125_counts.png",
     "shots": ["125_counts.png"],
     "title": "点と面の数は式で先に分かる — divide は n−2、convertline は V+F−2。edgedivide は既定で点が2倍",
     "note": "divide は n−2 枚、convertline は 点+面−2 本。edgedivide は既定で面ごとに点を作り 8+24(k−1) 点"},
    {"no": "126", "anchor": "exp126",
     "tags": ["モデリング", "cluster", "k-means", "検算"],
     "log": "log_pm", "thumb": "126_cluster.png",
     "shots": ["126_cluster.png"],
     "title": "cluster（k-means）は塊を理論の上限どおりに分ける — 重なる塊でも Φ(s/σ)² と1%以内",
     "note": "離れた塊は純度100%。重なった塊でも理論の上限 Φ(s/σ)² と1%以内"},
    {"no": "127", "anchor": "exp127",
     "tags": ["モデリング", "findshortestpath", "距離", "検算"],
     "log": "log_pm", "thumb": "127_path.png",
     "shots": ["127_path.png"],
     "title": "findshortestpath の道のりは Edge の距離と同じ — 四角の網では |x|+|z|",
     "note": "4本とも cost＝道の長さ＝Edge の距離＝|x|+|z|。(1,1) まで 2.0（まっすぐなら1.414）"},
    {"no": "128", "anchor": "exp128",
     "tags": ["モデリング", "extracttransform", "回転", "検算"],
     "log": "log_pm", "thumb": "128_extract.png",
     "shots": ["128_extract.png"],
     "title": "extracttransform は移動と回転だけを取り出す — 拡大は捨てて distortion に出す",
     "note": "移動と回転はずれ0で取り出せる（(10,20,30)°は1軸35.8171°）。拡大は取り出さず distortion に出る"},
    {"no": "129", "anchor": "exp129",
     "tags": ["モデリング", "measure", "曲率", "検算"],
     "log": "log_pm", "thumb": "129_curvature.png",
     "shots": ["129_curvature.png"],
     "title": "measure の曲率は既定のままだと式と合わない — Divide Element Area を入れると球・円柱とも0.03%以内",
     "note": "既定では式の値が出ない（網と大きさで変わる）。Divide Element Area 入・Scale Normalize 切で球も円柱も0.03%以内"},
    {"no": "130", "anchor": "exp130",
     "tags": ["モデリング", "normal", "法線", "検算"],
     "log": "log_pm", "thumb": "130_cusp.png",
     "shots": ["130_cusp.png"],
     "title": "normal の Cusp Angle は「曲がり角がこれより大きければ角を立てる」 — ちょうど等しいと、なめらか",
     "note": "曲がり角 > Cusp Angle なら角が立つ（35通りすべて）。ちょうど等しい・0.1%ほど下でもなめらか"},
    {"no": "131", "anchor": "exp131",
     "tags": ["モデリング", "bend", "変形", "検算"],
     "log": "log_pm", "thumb": "131_bend.png",
     "shots": ["131_bend.png"],
     "title": "bend は長さを保って円弧に曲げる — 端の位置は式と差0、範囲の外は接線の向きにまっすぐ",
     "note": "範囲の終わりの点は円弧の式と差0（45〜360°）。範囲の外は接線の向きにまっすぐ。全長の不足は弦の分だけ"},
    {"no": "132", "anchor": "exp132",
     "tags": ["モデリング", "attribpromote", "属性", "検算"],
     "log": "log_pm", "thumb": "132_promote.png",
     "shots": ["132_promote.png"],
     "title": "attribpromote の11通りのまとめ方 — Median は偶数個なら上の方、Mode は同数なら最小の値",
     "note": "8通りは式どおり。Median は偶数個なら上の方（4.5 ではなく5）、Mode は同数なら最小の値"},
    {"no": "133", "anchor": "exp133",
     "tags": ["モデリング", "ray", "つまずき", "検算"],
     "log": "log_pm", "thumb": "133_ray.png",
     "shots": ["133_ray.png"],
     "title": "ray の Direction には最初から @N の式が入っている — Python で set しても変わらず、真下に落ちなかった",
     "note": "Direction には最初から @N の式。set しても値が変わらず真下に落ちない。式を消せば式の位置に落ちる"},
    {"no": "134", "anchor": "exp134",
     "tags": ["ツール", "スクリプト", "つまずき"],
     "log": "log_pm", "thumb": "134_expr.png",
     "shots": ["134_expr.png"],
     "title": "最初から式が入っているつまみは SOP 全体で488個 — set しても式が残り、値は変わらない",
     "note": "SOP 1,031種類のうち176種類・488個のつまみに最初から式。set は式を消さず値も変わらない"},
    {"no": "135", "anchor": "exp135",
     "tags": ["VEX", "ノイズ", "検算"],
     "log": "log_pm", "thumb": "135_noise.png",
     "shots": ["135_noise.png"],
     "title": "VEX のノイズの値の範囲 — noise() は 0.06〜0.92 にしか届かず、snoise() は ±1 を超える",
     "note": "noise() は 0.06〜0.92（標準偏差0.1）、snoise() は −1.95〜2.28 で ±1 を超える。flownoise(P,0) は noise と同じ"},
    {"no": "136", "anchor": "exp136",
     "tags": ["VEX", "nearpoints", "検算"],
     "log": "log_pm", "thumb": "136_near.png",
     "shots": ["136_near.png"],
     "title": "nearpoints は自分を先頭に数え、近い順に返す — 半径ちょうど1は入るが、ちょうど√2は入らなかった",
     "note": "自分が先頭で近い順。最大数は自分込み。半径ちょうど1は入るが、ちょうど√2は丸めで入らない。pcfind も同じ"},
    {"no": "137", "anchor": "exp137",
     "tags": ["VEX", "fit", "検算"],
     "log": "log_pm", "thumb": "137_fit.png",
     "shots": ["137_fit.png"],
     "title": "VEX の fit は範囲の外で止まり、efit と lerp は伸び続ける — smooth は 3x²−2x³",
     "note": "fit・fit01・smooth は範囲の外で止まり、efit・lerp は伸びる。smooth は 3x²−2x³ と一致"},
    {"no": "138", "anchor": "exp138",
     "tags": ["VDB", "SDF", "検算"],
     "log": "log_pm", "thumb": "138_sdf.png",
     "shots": ["138_sdf.png"],
     "title": "vdbfrompolygons の SDF は帯の中だけ本当の距離（ずれ0.0008以下）— 帯の外は ±（Band Voxels×ボクセル）で平ら",
     "note": "帯の中は本当の距離とずれ0.0008以下。帯の外は ±（Band Voxels×ボクセル）で平ら"},
    {"no": "139", "anchor": "exp139",
     "tags": ["モデリング", "attribblur", "ぼかし", "検算"],
     "log": "log_pm", "thumb": "139_blur.png",
     "shots": ["139_blur.png"],
     "title": "attribblur の1回は「となりの平均へ半分近づく」を2度 — ぼけ幅は √回数。線では Pin Border で全く動かない",
     "note": "線では Pin Border で1点も動かない。切ると1回＝『となりの平均へ s だけ近づく』を2度、ぼけ幅は √(2sN)"},
    {"no": "140", "anchor": "exp140",
     "tags": ["モデリング", "copytopoints", "向き", "検算"],
     "log": "log_pm", "thumb": "140_copy.png",
     "shots": ["140_copy.png"],
     "title": "copytopoints の向きは orient が N に勝つ — N は +z を、up は +y を合わせる。scale と pscale は掛け算",
     "note": "N は +z、up は +y を合わせる。orient があれば N は無視。scale と pscale は掛け算"},
    {"no": "141", "anchor": "exp141",
     "tags": ["モデリング", "pointsfromvolume", "点の数", "検算"],
     "log": "log_pm", "thumb": "141_points.png",
     "shots": ["141_points.png"],
     "title": "pointsfromvolume の点は、格子なら1点 s³・四面体なら s³/√2 — 箱では面の上にも並ぶ",
     "note": "格子は1点 s³、四面体は s³/√2（球で0.05%以内）。箱では面の上にも点が並び (2/s+1)(1/s+1)² 個"},
    {"no": "142", "anchor": "exp142",
     "tags": ["モデリング", "検算", "platonic"],
     "log": "log_pm", "thumb": "142_ratio.png",
     "shots": ["142_ratio.png"],
     "title": "platonic の Radius は、四面体・八面体・二十面体では頂点までの距離 — 立方体は辺が1、十二面体は0.9933",
     "note": "Radius は四面体・八面体・二十面体なら頂点まで。立方体は一辺"},
    {"no": "143", "anchor": "exp143",
     "tags": ["モデリング", "検算", "circle"],
     "log": "log_pm", "thumb": "143_circle.png",
     "shots": ["143_circle.png"],
     "title": "circle の Polygon は頂点が円周に乗る正 n 角形 — 弧の Divisions は辺の数",
     "note": "Polygon の円は内接正n角形。弧の Divisions は辺の数"},
    {"no": "144", "anchor": "exp144",
     "tags": ["モデリング", "検算", "torus"],
     "log": "log_pm", "thumb": "144_torus.png",
     "shots": ["144_torus.png"],
     "title": "torus の Rows は管の断面、Columns は大きな輪 — 体積は2つの内接多角形の積で決まる",
     "note": "Rows は管の断面、Columns は輪。体積は入れ替えても同じ"},
    {"no": "145", "anchor": "exp145",
     "tags": ["モデリング", "検算", "mirror"],
     "log": "log_pm", "thumb": "145_seam.png",
     "shots": ["145_seam.png"],
     "title": "mirror の継ぎ目は「元と鏡像の距離」が Consolidate Seam 未満ならまとまる — 境目ちょうどはまとまらない",
     "note": "継ぎ目は元と鏡像の距離で比べる。境目ちょうどはまとまらない"},
    {"no": "146", "anchor": "exp146",
     "tags": ["モデリング", "検算", "clip"],
     "log": "log_pm", "thumb": "146_clip.png",
     "shots": ["146_clip.png"],
     "title": "clip で切った球の面積は 2πh — 比は切る高さに関係なく、球全体と同じだけずれる",
     "note": "切った球の面積は 2πh。Both は切り口の点を共有したまま"},
    {"no": "147", "anchor": "exp147",
     "tags": ["モデリング", "検算", "変形"],
     "log": "log_pm", "thumb": "147_volume.png",
     "shots": ["147_volume.png"],
     "title": "twist SOP の6つの操作 — 体積を保つのは Shear だけ。Squash は長さ (1+s) 倍・太さ 1/(1+s) 倍",
     "note": "体積を保つのは Shear だけ。Squash は長さ(1+s)倍・太さ1/(1+s)倍"},
    {"no": "148", "anchor": "exp148",
     "tags": ["モデリング", "検算", "tube"],
     "log": "log_pm", "thumb": "148_cone.png",
     "shots": ["148_cone.png"],
     "title": "tube の円錐台は式 × 内接多角形の比 — Radius の1つ目が上、円錐の先は点が重なったまま",
     "note": "円錐台は式×内接多角形の比。Radius の1つ目が上"},
    {"no": "149", "anchor": "exp149",
     "tags": ["モデリング", "検算", "divide"],
     "log": "log_pm", "thumb": "149_convex.png",
     "shots": ["149_convex.png"],
     "title": "divide の Bricker は形の端（＋ Offset）から Size おきに線を引く — Convex は n 角形を n−2 枚の三角形か、その半分の四角形に",
     "note": "Bricker は形の端から Size おき。Convex は n−2 枚の三角形"},
    {"no": "150", "anchor": "exp150",
     "tags": ["点検"],
     "log": "log_pm", "thumb": "150_audit.png",
     "shots": ["150_audit.png"],
     "title": "122〜149 の振り返り点検 — 28本すべて流し直し、時間以外の数字は全部一致",
     "note": "122〜149 の28本を流し直し、時間以外は全部一致"},
    {"no": "151", "anchor": "exp151",
     "tags": ["モデリング", "検算", "sphere"],
     "log": "log_pm", "thumb": "151_deficit.png",
     "shots": ["151_deficit.png"],
     "title": "sphere の Polygon は点 10f²+2・面 20f² の測地球 — 同じ点の数なら Polygon Mesh より体積の不足が約3割小さい",
     "note": "Polygon は点 10f²+2 の測地球。同じ点の数なら体積の不足が約3割小さい"},
    {"no": "152", "anchor": "exp152",
     "tags": ["モデリング", "検算", "polybevel"],
     "log": "log_pm", "thumb": "152_round.png",
     "shots": ["152_round.png"],
     "title": "polybevel の Round は、分割を増やすと「角を丸めた箱」の体積に近づく — 平らな面取りは 1 − 6d² + (16/3)d³",
     "note": "Round は分割を増やすと丸めた箱の式へ。平らな面取りは 1−6d²+(16/3)d³"},
    {"no": "153", "anchor": "exp153",
     "tags": ["VEX", "検算", "トポロジー"],
     "log": "log_pm", "thumb": "153_hist.png",
     "shots": ["153_hist.png"],
     "title": "neighbourcount() の合計の半分は辺の数 — そこから出した V − E + F は、板 1・球と箱 2・トーラスと筒 0",
     "note": "neighbourcount の合計÷2は辺の数。V−E+F で板・球・トーラスを見分けられる"},
    {"no": "154", "anchor": "exp154",
     "tags": ["モデリング", "検算", "落とし穴", "polyfill"],
     "log": "log_pm", "thumb": "154_counts.png",
     "shots": ["154_counts.png"],
     "title": "polyfill の四角形の塞ぎ方は、辺が奇数の穴を塞がない — 三角形は 1つの穴に n−2 枚、Grid は少しふくらむ",
     "note": "四角形の塞ぎ方は辺が奇数の穴を塞がない。Grid は蓋がふくらむ"},
    {"no": "155", "anchor": "exp155",
     "tags": ["モデリング", "検算", "scatter"],
     "log": "log_pm", "thumb": "155_share.png",
     "shots": ["155_share.png"],
     "title": "scatter の density 属性は点を k/(1+k) に分ける — 数を決めないと Density Scale × 面積のあたりで揺れる",
     "note": "density は点を k/(1+k) に分ける。数を決めないと Density Scale×面積で揺れる"},
    {"no": "156", "anchor": "exp156",
     "tags": ["モデリング", "検算", "polywire"],
     "log": "log_pm", "thumb": "156_wire.png",
     "shots": ["156_wire.png"],
     "title": "polywire の管は Wire Radius に内接する正 n 角柱で両端に蓋 — 折れ目は Prevent Joint Buckling で r/cos(θ/2) に広がる",
     "note": "管は内接正n角柱で両端に蓋。折れ目は Prevent Joint Buckling で r/cos(θ/2) に広がる"},
    {"no": "157", "anchor": "exp157",
     "tags": ["エフェクト", "検算", "破壊"],
     "log": "log_fx", "thumb": "157_pieces.png",
     "shots": ["157_pieces.png"],
     "title": "voronoifracture は種 N 個で N 個のかけら、体積の合計は元のまま — 切り口を作らないと、中のかけらは消える",
     "note": "種 N 個で N 個のかけら、体積の合計は元のまま。切り口を作らないと中のかけらは消える"},
    {"no": "158", "anchor": "exp158",
     "tags": ["エフェクト", "落とし穴", "破壊", "scatter"],
     "log": "log_fx", "thumb": "158_relax.png",
     "shots": ["158_relax.png"],
     "title": "種を relax すると、voronoifracture のかけらはそろうどころかばらつく — 種が箱の壁へ押し出される",
     "note": "種を relax するとかけらはばらつく。種が箱の壁へ押し出される"},
    {"no": "159", "anchor": "exp159",
     "tags": ["エフェクト", "検算", "速度"],
     "log": "log_fx", "thumb": "159_vel.png",
     "shots": ["159_vel.png"],
     "title": "trail の速さは1秒あたり、差分の式どおり — 加速度は Central Difference のときだけ出て、Velocity Scale の2乗で縮む",
     "note": "trail の速さは1秒あたり。加速度は Central のときだけ出て、Scale の2乗で縮む"},
    {"no": "160", "anchor": "exp160",
     "tags": ["モデリング", "UV", "uvlayout"],
     "log": "log_pm", "thumb": "160_fill.png",
     "shots": ["160_fill.png"],
     "title": "uvlayout は長方形 12 枚で升の 48〜84% を埋める — Padding は Search Resolution が粗いほど大きく効く",
     "note": "長方形 12 枚で升の 48〜84% を埋める。Padding は Search Resolution が粗いほど効く"},
    {"no": "161", "anchor": "exp161",
     "tags": ["属性", "検算", "attribtransfer"],
     "log": "log_pm", "thumb": "161_blend.png",
     "shots": ["161_blend.png"],
     "title": "attribtransfer は Distance Threshold までそのまま運び、Blend Width の外側で (1 − t²)² に落とす",
     "note": "Threshold までそのまま、Blend Width の外側で (1−t²)² に落とす"},
    {"no": "162", "anchor": "exp162",
     "tags": ["モデリング", "検算", "subdivide"],
     "log": "log_pm", "thumb": "162_crease.png",
     "shots": ["162_crease.png"],
     "title": "subdivide の crease は「重み w の回数までは尖ったまま」— w ≥ Iterations なら箱はそのまま、体積 1",
     "note": "crease の重みは細分の回数。w ≥ Iterations なら箱はそのまま体積 1"},
    {"no": "163", "anchor": "exp163",
     "tags": ["シミュレーション", "Vellum", "検算"],
     "log": "log_fx", "thumb": "163_counts.png",
     "shots": ["163_counts.png"],
     "title": "vellumconstraints の Cloth は網を三角形にしてから、辺ごとに伸びの拘束、内側の辺ごとに曲げの拘束を作る",
     "note": "Cloth は網を三角形にしてから、辺ごとに伸び・内側の辺ごとに曲げの拘束を作る"},
    {"no": "164", "anchor": "exp164",
     "tags": ["エフェクト", "VDB", "検算"],
     "log": "log_pm", "thumb": "164_union.png",
     "shots": ["164_union.png"],
     "title": "vdbfromparticles の粒は pscale を半径にした球 — 2つ重ねると「2つの球の和」の体積に、升目の2乗で近づく",
     "note": "粒は pscale を半径にした球。2つ重ねると球の和の体積に、升目の2乗で近づく"},
    {"no": "165", "anchor": "exp165",
     "tags": ["シミュレーション", "パーティクル", "検算"],
     "log": "log_fx", "thumb": "165_fall.png",
     "shots": ["165_fall.png"],
     "title": "POP の粒は、生まれたフレームで 1 ステップ先に進む — 1 秒後の落下は Substeps 1 で 13% 多く、誤差は Substeps に反比例して縮む",
     "note": "粒は生まれたフレームで1ステップ先に進む。落下の誤差は Substeps に反比例"},
    {"no": "166", "anchor": "exp166",
     "tags": ["シミュレーション", "パーティクル", "検算", "落とし穴"],
     "log": "log_fx", "thumb": "166_drag.png",
     "shots": ["166_drag.png"],
     "title": "popdrag の終端速度は g/k ではなく √(g/k) に近づく — 速さの2乗に比例する抵抗と同じ振る舞い",
     "note": "popdrag の終端速度は g/k ではなく √(g/k) に近づく"},
    {"no": "167", "anchor": "exp167",
     "tags": ["シミュレーション", "RBD", "Bullet"],
     "log": "log_fx", "thumb": "167_drop.png",
     "shots": ["167_drop.png"],
     "title": "rbdbulletsolver の箱は地面ぴったりで止まる — Collision Padding を変えても止まる高さは同じ、当たった瞬間だけ少し沈む",
     "note": "箱は地面ぴったりで止まる。Collision Padding は止まる高さを変えない"},
    {"no": "168", "anchor": "exp168",
     "tags": ["地形", "検算", "heightfield"],
     "log": "log_pm", "thumb": "168_amp.png",
     "shots": ["168_amp.png"],
     "title": "heightfield_noise の Amplitude は高さの幅ではない — 幅は Amplitude の 23〜29%、Center Noise を切ると Amplitude の半分だけ上がる",
     "note": "Amplitude は高さの幅ではない。幅は Amplitude の 23〜29%"},
    {"no": "169", "anchor": "exp169",
     "tags": ["地形", "シミュレーション", "heightfield"],
     "log": "log_fx", "thumb": "169_mass.png",
     "shots": ["169_mass.png"],
     "title": "heightfield_erode は土の量を保たない — 40 フレームで height の平均が 5 下がり、削れた分の大半は地形から消える",
     "note": "erode は土の量を保たない。40 フレームで平均の高さが 5 下がる"},
    {"no": "170", "anchor": "exp170",
     "tags": ["シミュレーション", "Vellum", "布"],
     "log": "log_fx", "thumb": "170_stretch.png",
     "shots": ["170_stretch.png"],
     "title": "Vellum の布は既定の硬さでも Substeps 1 で 2% 伸びる — Substeps 1 では 10^4 と 10^10 の差が出ない",
     "note": "既定の硬さでも Substeps 1 で 2% 伸びる。Substeps 1 では 10^4 と 10^10 の差が出ない"},
    {"no": "171", "anchor": "exp171",
     "tags": ["VEX", "検算", "ノイズ"],
     "log": "log_pm", "thumb": "171_div.png",
     "shots": ["171_div.png"],
     "title": "curlnoise() はほぼ湧き出しのない流れ — 発散は、ふつうのノイズの約 3.5 万分の 1（周波数 1）",
     "note": "curlnoise はほぼ湧き出しのない流れ。発散はふつうのノイズの約 3.5 万分の 1"},
    {"no": "172", "anchor": "exp172",
     "tags": ["VEX", "パーティクル", "ノイズ"],
     "log": "log_pm", "thumb": "172_crowd.png",
     "shots": ["172_crowd.png"],
     "title": "curlnoise で流した粒は混み具合をほぼ保つ — ふつうのノイズで流すと、平均で2倍以上に固まる",
     "note": "curlnoise で流した粒は混み具合をほぼ保つ。ふつうのノイズでは2倍以上に固まる"},
    {"no": "173", "anchor": "exp173",
     "tags": ["VEX", "効率化", "Python"],
     "log": "log_pm", "thumb": "173_speed.png",
     "shots": ["173_speed.png"],
     "title": "同じ計算でも VEX（点ごと）は Detail のループの約170倍、Python の約260倍速い — 100 万点で 1.3 ミリ秒",
     "note": "VEX（点ごと）は Detail のループの約170倍、Python の約260倍速い"},
    {"no": "174", "anchor": "exp174",
     "tags": ["効率化", "VEX", "for-each"],
     "log": "log_pm", "thumb": "174_loop.png",
     "shots": ["174_loop.png"],
     "title": "for-each はかけら1つあたり約 0.037 ミリ秒 — compile block で 35% 速く、wrangle 1つにまとめれば 30 倍速い",
     "note": "for-each は1かけら約0.037ミリ秒。compile で35%速く、wrangle 1つなら30倍速い"},
    {"no": "175", "anchor": "exp175",
     "tags": ["シミュレーション", "パーティクル", "検算"],
     "log": "log_fx", "thumb": "175_wind.png",
     "shots": ["175_wind.png"],
     "title": "popwind の粒は、風との速さの差が 5/(1 + 5·k·t) で縮む — 差の2乗に比例する抵抗を、Substeps によらずぴったり解いている",
     "note": "風との差は 5/(1+5kt) で縮む。差の2乗の抵抗を Substeps によらずぴったり解く"},
    {"no": "176", "anchor": "exp176",
     "tags": ["地形", "検算", "heightfield"],
     "log": "log_pm", "thumb": "176_element.png",
     "shots": ["176_element.png"],
     "title": "heightfield_noise の高さの幅は、地面に入る模様の数で決まる — Element Size を地面の 1/20 にすると Amplitude の 6 割",
     "note": "高さの幅は地面に入る模様の数で決まる。20個入って Amplitude の6割"},
    {"no": "177", "anchor": "exp177",
     "tags": ["シミュレーション", "Vellum", "効率化"],
     "log": "log_fx", "thumb": "177_cost.png",
     "shots": ["177_cost.png"],
     "title": "Vellum の布の伸びは、Substeps より Constraint Iterations を上げる方が安く減る — 400 回で 0.2%、1600 回で 0.002%",
     "note": "伸びは Substeps より Constraint Iterations で安く減る。400 回で 0.2%"},
    {"no": "178", "anchor": "exp178",
     "tags": ["VEX", "効率化", "pcfind"],
     "log": "log_pm", "thumb": "178_cost.png",
     "shots": ["178_cost.png"],
     "title": "pcfind の時間は「見つかった点の数」で決まる — 半径を広げても、最大の数を 10 に絞れば 1 点 0.1 マイクロ秒",
     "note": "pcfind の時間は見つかった点の数で決まる。maxpts を絞れば半径が広くても軽い"},
    {"no": "179", "anchor": "exp179",
     "tags": ["シミュレーション", "パーティクル", "検算"],
     "log": "log_fx", "thumb": "179_speed.png",
     "shots": ["179_speed.png"],
     "title": "止まった空気の popwind と重力は、popdrag とぴったり同じ落ち方 — Substeps で差が出るのは重力と組み合わせたとき。Wind Speed は掛け算",
     "note": "止まった空気の popwind＋重力は popdrag と同じ落ち方。Wind Speed は掛け算"},
    {"no": "180", "anchor": "exp180",
     "tags": ["点検"],
     "log": "log_pm", "thumb": "180_audit.png",
     "shots": ["180_audit.png"],
     "title": "151〜179 の振り返り点検 — 29本すべて流し直し、時間以外の数字は全部一致",
     "note": "151〜179 の29本を流し直し、時間以外は全部一致"},
    {"no": "181", "anchor": "exp181",
     "tags": ["VEX", "効率化", "pcfind"],
     "log": "log_pm", "thumb": "181_speed.png",
     "shots": ["181_speed.png"],
     "title": "pcfind と nearpoints は同じ結果・同じ速さ — pcopen + pcfilter は 1.6 倍遅く、距離で重みを付けた平均になる",
     "note": "pcfind と nearpoints は同じ結果・同じ速さ。pcopen+pcfilter は1.6倍遅く重み付き平均"},
    {"no": "182", "anchor": "exp182",
     "tags": ["VEX", "pcfilter", "落とし穴"],
     "log": "log_pm", "thumb": "182_kernel.png",
     "shots": ["182_kernel.png"],
     "title": "pcfilter の重みは「半径に対する距離」だけでは決まらない — 見つかった点どうしの並びで変わり、式は分からなかった",
     "note": "pcfilter の重みは半径に対する距離だけでは決まらない。点の並びで変わる"},
    {"no": "183", "anchor": "exp183",
     "tags": ["シミュレーション", "RBD", "Bullet"],
     "log": "log_fx", "thumb": "183_substeps.png",
     "shots": ["183_substeps.png"],
     "title": "rbdbulletsolver の沈み込みは Bullet Substeps で決まる — 1 だと 0.38 めり込んで沈んだまま、50 でほぼ 0",
     "note": "沈み込みは Bullet Substeps で決まる。1 だと 0.38 めり込み沈んだまま"},
    {"no": "184", "anchor": "exp184",
     "tags": ["シミュレーション", "MPM", "検算"],
     "log": "log_fx", "thumb": "184_count.png",
     "shots": ["184_count.png"],
     "title": "mpmsource は箱に「体積 ÷ Particle Separation³」個の粒を詰める — pscale には Separation そのものが入る",
     "note": "箱に体積÷Separation³個の粒を詰める。pscale には Separation そのものが入る"},
    {"no": "185", "anchor": "exp185",
     "tags": ["モデリング", "検算", "smooth"],
     "log": "log_pm", "thumb": "185_smooth.png",
     "shots": ["185_smooth.png"],
     "title": "smooth の縮み方は r = 1/(1 + Strength·L^q/C(2q, q)) — 36 通りで6桁一致。Filter Quality を上げるほど形を保つ",
     "note": "縮み方は r = 1/(1+S·L^q/C(2q,q))。36通りで6桁一致"},
    {"no": "186", "anchor": "exp186",
     "tags": ["モデリング", "検算", "smooth"],
     "log": "log_pm", "thumb": "186_methods.png",
     "shots": ["186_methods.png"],
     "title": "smooth の3つの Method は、点が等間隔の円では同じ縮み方 — 開いた線の端は Constrained Boundary で止まり、波の高さは 1/(1 + S·L/2) だけ残る",
     "note": "等間隔の円では3つの Method は同じ。端を止めた波は 1/(1+S·L/2) だけ残る"},
    {"no": "187", "anchor": "exp187",
     "tags": ["モデリング", "smooth", "落とし穴"],
     "log": "log_pm", "thumb": "187_uneven.png",
     "shots": ["187_uneven.png"],
     "title": "点の間隔がそろわない円では、smooth は粗い側を大きく縮める — 3つの Method の差は小さく、どれも丸さを保たない",
     "note": "間隔がそろわない円では粗い側を大きく縮める。Method の差は小さい"},
    {"no": "188", "anchor": "exp188",
     "tags": ["毛", "グルーム", "検算"],
     "log": "log_pm", "thumb": "188_density.png",
     "shots": ["188_density.png"],
     "title": "hairgen の毛の本数は Density × 面積 — 1本は Segments + 1 点、長さは Length ちょうど",
     "note": "毛の本数は Density×面積。1本は Segments+1 点、長さは Length ちょうど"},
    {"no": "189", "anchor": "exp189",
     "tags": ["レンダリング", "USD", "Solaris"],
     "log": "log_pm", "thumb": "189_prims.png",
     "shots": ["189_prims.png"],
     "title": "箱 100 個を USD にすると、パックしなければメッシュ 1 つ、Point Instancer なら 6 プリム、Xforms なら 202 プリム",
     "note": "箱100個はパックしなければメッシュ1つ、Point Instancer なら6プリム、Xforms なら202"},
    {"no": "190", "anchor": "exp190",
     "tags": ["レンダリング", "USD", "効率化"],
     "log": "log_pm", "thumb": "190_size.png",
     "shots": ["190_size.png"],
     "title": "箱 1 万個の USD — Point Instancer は 0.32 MB・8 ミリ秒、Native Instances は 4.6 倍、Unpack は 7.4 倍の大きさ",
     "note": "1万個の USD は Point Instancer が 0.32MB・8ミリ秒。Native Instances は4.6倍、Unpack は7.4倍"},
    {"no": "191", "anchor": "exp191",
     "tags": ["モデリング", "検算", "VEX"],
     "log": "log_pm", "thumb": "191_gap.png",
     "shots": ["191_gap.png"],
     "title": "多角形の球のいちばん深いへこみは sin²(Δ/2) — 分割を倍にするたびに 1/4、平均はその 0.56 倍",
     "note": "多角形の球のいちばん深いへこみは sin²(Δ/2)。分割を倍にすると 1/4"},
    {"no": "192", "anchor": "exp192",
     "tags": ["モデリング", "検算", "polyextrude"],
     "log": "log_pm", "thumb": "192_inset.png",
     "shots": ["192_inset.png"],
     "title": "polyextrude の Inset は上の面を i だけ内側へ寄せる — 体積は角錐台の式どおり、i ≥ 0.5 で四角錐になり、それ以上は裏返らない",
     "note": "Inset は上の面を i だけ内側へ。体積は角錐台の式、0.5 で四角錐、それ以上は裏返らない"},
    {"no": "193", "anchor": "exp193",
     "tags": ["シミュレーション", "パーティクル", "落とし穴"],
     "log": "log_fx", "thumb": "193_birth.png",
     "shots": ["193_birth.png"],
     "title": "popsource の Constant Birth Rate は1秒あたり — 端数の粒はフレームごとに運で決まり、Life 0.5 秒の粒は 11 フレームで消える",
     "note": "Birth Rate は1秒あたり。端数は運で決まり、Life 0.5秒の粒は11フレームで消える"},
    {"no": "194", "anchor": "exp194",
     "tags": ["シミュレーション", "パーティクル", "検算"],
     "log": "log_fx", "thumb": "194_life.png",
     "shots": ["194_life.png"],
     "title": "POP の粒が数えられるフレームは Life × fps − 1/Substeps — 0.5 秒の粒は Substeps 1 で 11 フレーム、4 で 11.75",
     "note": "粒が数えられるフレームは Life×fps − 1/Substeps"},
    {"no": "195", "anchor": "exp195",
     "tags": ["VDB", "検算", "vdbreshapesdf"],
     "log": "log_pm", "thumb": "195_reshape.png",
     "shots": ["195_reshape.png"],
     "title": "vdbreshapesdf の Dilate・Erode は、球の半径を Offset × 升の大きさだけ変える — Iterations は効かず、Open・Close は形をほぼ変えない",
     "note": "Dilate・Erode は半径を Offset×升の大きさだけ変える。Iterations は効かない"},
    {"no": "196", "anchor": "exp196",
     "tags": ["VDB", "落とし穴", "vdbreshapesdf", "訂正"],
     "log": "log_pm", "thumb": "196_open.png",
     "shots": ["196_open.png"],
     "title": "vdbreshapesdf の Open は箱の角を r より少し大きく丸める — Close も凸な箱を少しだけ削る",
     "note": "Open は箱の角を r より大きく丸める（約3升の足し分。実験198で訂正）。Close も凸な箱を少し削る"},
    {"no": "197", "anchor": "exp197",
     "tags": ["VDB", "SDF", "モデリング"],
     "log": "log_pm", "thumb": "197_band.png",
     "shots": ["197_band.png"],
     "title": "SDF の帯を 25 升に広げると、vdbreshapesdf の Close は箱をほとんど削らなくなる — Open の丸みはかえって大きくなる",
     "note": "帯を25升に広げるとCloseはほぼ削らない。Openの丸みは逆に大きく"},
    {"no": "198", "anchor": "exp198",
     "tags": ["VDB", "SDF", "モデリング"],
     "log": "log_pm", "thumb": "198_arc.png",
     "shots": ["198_arc.png"],
     "title": "vdbreshapesdf の Open で丸めた辺の断面は円弧 — 半径は Offset × 升より 2.5〜3.2 升大きい",
     "note": "Openの断面は円弧。半径はOffset×升より約3升大きい"},
    {"no": "199", "anchor": "exp199",
     "tags": ["VDB", "SDF", "モデリング"],
     "log": "log_pm", "thumb": "199_band.png",
     "shots": ["199_band.png"],
     "title": "Open で丸めた辺の半径が約 3 升大きいのは、SDF の帯のせいではない — 帯 3〜25 升で足し分は変わらない",
     "note": "Openの辺の半径の足し分(約3升)は帯の幅によらない"},
    {"no": "200", "anchor": "exp200", "hip": "200_flip.hipnc",
     "tags": ["シミュレーション", "FLIP", "液体", "制作", "効率化", "落とし穴", "訂正"],
     "log": "log_fx", "thumb": "200_grid.png",
     "shots": ["200_grid.png", "200_cost.png", "200_volume.png"],
     "title": "FLIP のダムブレイクは Particle Separation 0.04 で足りる — 0.06 より粗いと壁ぎわの数粒が大きな塊に見え、水も 1〜2 割増える",
     "note": "ダムブレイクは粒の間隔0.04で足りる。粗いと壁ぎわの数粒が塊に見える"},
    {"no": "201", "anchor": "exp201",
     "tags": ["シミュレーション", "Pyro", "炎", "制作", "落とし穴"],
     "log": "log_fx", "thumb": "201_grid.png",
     "shots": ["201_grid.png", "201_height.png"],
     "title": "Pyro で焚き火の炎（高さ 1.2 m）を作るなら Flame Lifespan 0.25・Buoyancy 0.25・Cooling Rate 1 — 揺らすのは Turbulence で、Use Control Field を切る",
     "note": "焚き火はLifespan 0.25・Buoyancy 0.25・Cooling 1で1.2m。揺らすのはTurbulence"},
    {"no": "202", "anchor": "exp202",
     "tags": ["エフェクト", "Pyro", "炎", "速度"],
     "log": "log_fx", "thumb": "202_grid.png",
     "shots": ["202_grid.png", "202_height.png"],
     "title": "焚き火の Pyro を速く回すなら Voxel Size を 0.02 → 0.04 に — 5.1 倍速く、炎の高さの差は 3%。速度の升だけ粗くするのと Substeps 2 は、かえって遅い",
     "note": "焚き火は Voxel 0.04 で5倍速く、高さの差は3%"},
    {"no": "203", "anchor": "exp203",
     "tags": ["レンダリング", "Karma", "速度", "ガラス"],
     "log": "log_pm", "thumb": "203_compare.png",
     "shots": ["203_compare.png", "203_spp.png"],
     "title": "氷の入ったグラスを Karma で撮ると、サンプル1つあたり不透明の 6 倍の時間がかかる — 重ねた水と氷は +27% だけ。16 サンプル＋ノイズ除去なら約 3 分",
     "note": "透明な物はサンプル1つあたり6倍。16サンプル＋ノイズ除去で"},
    {"no": "204", "anchor": "exp204",
     "tags": ["エフェクト", "Pyro", "キャッシュ", "容量", "VDB"],
     "log": "log_fx", "thumb": "204_size.png",
     "shots": ["204_size.png", "204_graph.png"],
     "title": "焚き火の Pyro のキャッシュは、9 割以上が速度（vel）— vel を煙のある所だけに残して VDB・16 bit にすると 16 分の 1、描画に使う値のずれは 0.00025",
     "note": "焚き火のキャッシュの9割は vel。煙のある所だけに残して VDB・16 bit で 16 分の 1"},
    {"no": "205", "anchor": "exp205",
     "tags": ["レンダリング", "Karma", "速度", "被写界深度", "モーションブラー"],
     "log": "log_pm", "thumb": "205_look.png",
     "shots": ["205_look.png", "205_grain.png", "205_graph.png"],
     "title": "Karma のぼけ（被写界深度）とぶれ（モーションブラー）は、時間を +5%〜9% しか増やさない — ざらつきを消すのはサンプル数ではなくノイズ除去。16 サンプル＋OIDN で 27 秒",
     "note": "ぼけ・ぶれは +5〜9% だけ。ざらつきはサンプル数では消えず、16＋ノイズ除去で 27 秒"},
    {"no": "206", "anchor": "exp206",
     "tags": ["エフェクト", "Vellum", "布", "速度", "解像度"],
     "log": "log_fx", "thumb": "206_grid.png",
     "shots": ["206_grid.png", "206_anim.gif", "206_graph.png"],
     "title": "テーブルクロスを粗い布で試すなら 44×56 まで — 落ち方の差は平均 1.9 cm で、計算は 39 秒（実践の細かさの 39%）。ただし粗いほど角の垂れが短く、22×28 では 17 cm 高い",
     "note": "粗い布での試しは 44×56 まで。差は平均 1.9 cm、時間は 39%。角の垂れだけ短い"},
    {"no": "207", "anchor": "exp207",
     "tags": ["レンダリング", "Karma", "速度", "Pyro", "炎", "訂正"],
     "log": "log_pm", "thumb": "207_compare.png",
     "shots": ["207_compare.png", "207_graph.png"],
     "title": "焚き火を Karma で撮るとき、Volume Step Rate を 0.25 から下げても速くならず、1 に上げると遅い — 1920×1080 では 1 が 45 秒、0.125 が 36 秒。Pyro を粗くしても撮る時間は同じで、炎の形だけ変わる",
     "note": "Volume Step Rate は既定 0.25 のまま（1 に上げると 1080p で 23% 遅い）。訂正: 大きいほど細かい"},
    {"no": "208", "anchor": "exp208",
     "tags": ["エフェクト", "FLIP", "液体", "面にする", "速度"],
     "log": "log_fx", "thumb": "208_grid.png",
     "shots": ["208_grid.png", "208_graph.png"],
     "title": "FLIP の水を面にするとき、形を決めるのは Influence Scale と Method — Spherical はつぶつぶ、Influence 5 は体積 87%。なめらかにするなら Filtering（既定の 1.3 倍の時間）",
     "note": "水の面の形は Influence Scale と Method で決まる。なめらかにするなら Filtering（1.3 倍の時間）"},
    {"no": "209", "anchor": "exp209",
     "tags": ["ツール", "PDG", "速度", "Pyro"],
     "log": "log_pm", "thumb": "209_time.png",
     "shots": ["209_time.png", "209_graph.png"],
     "title": "焚き火を 8 通り回すなら、PDG で同時に 8 本が 1.6 倍速い — ただし同時に 1 本だと 2.2 倍遅く、2 本でほぼ並ぶ。Evaluate Using を Frame Range にしないと 1 フレームしか回らない",
     "note": "8 通りの焚き火は PDG で同時に 8 本が 1.6 倍速い。1 本だと 2.2 倍遅い。Evaluate Using の落とし穴"},
    {"no": "211", "anchor": "exp211",
     "tags": ["エフェクト", "Vellum", "布", "厚み"],
     "log": "log_fx", "thumb": "211_edge.png",
     "shots": ["211_edge.png", "211_drape.png", "211_graph.png"],
     "title": "テーブルクロスが机から浮くのは Thickness の分だけ — 既定 0.01 で 10 mm 浮く。0.0025 まで薄くしてもめり込まず、Calculate Uniform（辺の長さ × 0.25）なら 2.8 mm",
     "note": "テーブルクロスの浮きは Thickness の分。既定 0.01 で 10 mm。0.0025 でもめり込まない"},
    {"no": "212", "anchor": "exp212",
     "tags": ["レンダリング", "Karma", "材質", "金属"],
     "log": "log_pm", "thumb": "212_strip.png",
     "shots": ["212_strip.png", "212_chart.png", "212_graph.png"],
     "title": "金属の Roughness は 0.2 まで見た目がほぼ同じ — ハイライトが広がり始めるのは 0.3 から。0.5 で明るさ 36%・広さ 1.4 倍、0.7 で 15%・2.4 倍",
     "note": "金属の Roughness は 0.2 まで見た目がほぼ同じ。広がるのは 0.3 から、0.7 で明るさ 15%"},
    {"no": "213", "anchor": "exp213",
     "tags": ["レンダリング", "Karma", "材質", "SSS"],
     "log": "log_pm", "thumb": "213_back.png",
     "shots": ["213_back.png", "213_front.png", "213_graph.png"],
     "title": "SSS で透けて見せるなら、半径 0.5 の球では Subsurface Distance 0.1〜0.3 — 0.3 のとき逆光の真ん中が 5.3 倍明るい。1 にするとかえって暗く、正面から見ても 41% に沈む",
     "note": "SSS の透けは、半径 0.5 の球で Distance 0.1〜0.3。1 はかえって暗い。Random Walk はよく透ける"},
    {"no": "214", "anchor": "exp214",
     "tags": ["レンダリング", "Karma", "カメラ", "被写界深度", "検算"],
     "log": "log_pm", "thumb": "214_blur.png",
     "shots": ["214_blur.png", "214_chart.png", "214_graph.png"],
     "title": "Karma のぼけの大きさは f²(d−s)/(N·d·s) に 0.9% 以内で一致 — F を半分にすると直径は倍。写真の薄いレンズの式より約 5% 小さい",
     "note": "Karma のぼけは f²(d−s)/(N·d·s) に 0.9% 以内で一致。F を半分で直径は倍"},
    {"no": "216", "anchor": "exp216",
     "tags": ["レンダリング", "Karma", "煙", "Pyro", "検算"],
     "log": "log_pm", "thumb": "216_strip.png",
     "shots": ["216_strip.png", "216_chart.png", "216_graph.png"],
     "title": "煙の透け具合は光の吸収の式 exp(−Density Scale × 濃さ × 厚み[m]) どおり — Density Scale を倍にすると、届く光は 2 乗に減る。ただし Volume Step Rate 0.25（既定）では濃い煙が少し明るく出て、1 で式とぴったり",
     "note": "煙の透けは exp(−Density Scale×濃さ×厚み)。倍にすると届く光は2乗。Volume Step Rate は大きいほど細かい"},
    {"no": "217", "anchor": "exp217",
     "tags": ["エフェクト", "Vellum", "布", "曲げ"],
     "log": "log_fx", "thumb": "217_grid.png",
     "shots": ["217_grid.png", "217_graph.png"],
     "title": "テーブルクロスの曲げの硬さは、既定 0.1 から下げても形はほぼ同じ（差 1.1 cm）。10 に上げると布が張って机から 15 cm 張り出し、裾が 4 cm 上がる",
     "note": "テーブルクロスの曲げの硬さは 0.1 から下げても同じ。10 で布が張り、裾が上がる"},
    {"no": "210", "anchor": "exp210",
     "tags": ["ツール", "点検"],
     "log": "log_pm", "thumb": "210_summary.png",
     "shots": ["210_summary.png"],
     "title": "181〜209 の点検 — 29 本を流し直して 35,969 個の値を突き合わせた。22 本は完全に一致。201 は台本が 202 の変更に引きずられていたので直したが、Turbulence の 2 条件はまだ合わない",
     "note": "181〜209 を流し直し：22 本は完全一致。201 は台本を直したが Turbulence の 2 条件が合わない"},
    {"no": "218", "anchor": "exp218",
     "tags": ["エフェクト", "Karma", "海", "見た目"],
     "log": "log_fx", "thumb": "218_grid.png",
     "shots": ["218_grid.png", "218_graph.png"],
     "title": "海の光の道は、Roughness を上げると太い白い帯になり（0.02→0.15 で幅 15→61 列）、さざ波を高くすると粒のまま広がる（0.4→3.2 で 12→36 列）",
     "note": "海の光の道は Roughness で太い帯に、さざ波で粒のまま広がる"},
    {"no": "219", "anchor": "exp219",
     "tags": ["エフェクト", "Karma", "海", "速さ"],
     "log": "log_fx", "thumb": "219_grid.png",
     "shots": ["219_grid.png", "219_graph.png"],
     "title": "海の板の点を半分にすると、撮る時間は 12% 減り、きらめきの粒も 15% 減る。1/4 で時間 23% 減・粒 27% 減。1/16 でも時間は 64% までしか減らない",
     "note": "海の板の点を半分にすると時間12%減、粒15%減"},
    {"no": "220", "anchor": "exp220",
     "tags": ["シミュレーション", "Pyro", "炎", "落とし穴", "点検"],
     "log": "log_fx", "thumb": "220_heights.png",
     "shots": ["220_heights.png", "220_graph.png"],
     "title": "焚き火の Turbulence は、Use Control Field を入れると効かない（揺らぎなしと全フレーム同じ）。切ると炎の高さ 1.31 m（なし 1.21 m）。実験201 の結論は正しく、点検で合わなかったのは revertToDefaults が Use Control Field を「切り」に戻したため",
     "note": "焚き火の Turbulence は Use Control Field 入りだと効かない。201 の点検のずれの原因"},
    {"no": "215", "anchor": "exp215",
     "tags": ["Karma", "草", "速さ", "制作"],
     "log": "log_pm", "thumb": "215_grid.png",
     "shots": ["215_grid.png", "215_graph.png"],
     "title": "草を Karma で撮るならパックしたまま（1 万本 17 秒、解くと 128 秒）。ただし 10 万本は、ポイントインスタンサーにしても、地面を広げて混み具合を 1 万本と同じにしても 13 分かかった",
     "note": "草はパックしたまま（1万本17秒、解くと128秒）。10万本は13分"},
    {"no": "221", "anchor": "exp221",
     "tags": ["エフェクト", "Karma", "海", "速さ"],
     "log": "log_fx", "thumb": "221_grid.png",
     "shots": ["221_grid.png", "221_graph.png"],
     "title": "海の映像の 1 枚は、サンプル数を 16→4 にしても 8.8→7.2 秒、解像度を 640×360 にしても 8.3 秒。時間の大半は画の大きさによらない分で、下げるなら 4 サンプル＋ノイズ除去",
     "note": "海の映像はサンプル数・解像度を下げても2割しか速くならない"},
    {"no": "222", "anchor": "exp222",
     "tags": ["Karma", "Solaris", "草", "速さ", "制作"],
     "log": "log_pm", "thumb": "222_time.png",
     "shots": ["222_time.png", "222_grid.png", "222_lop_graph.png"],
     "title": "草を何万本も Karma で撮るなら、Solaris（LOP）の sopimport で「Create Point Instancer」にして撮る。10 万本が 793 秒 → 12 秒、100 万本も 37 秒",
     "note": "草は LOP の sopimport で Create Point Instancer に。10万本13分→12秒"},
    {"no": "223", "anchor": "exp223",
     "tags": ["エフェクト", "海", "白波", "制作"],
     "log": "log_fx", "thumb": "223_grid.png",
     "shots": ["223_grid.png", "223_graph.png"],
     "title": "海の白波の cusp のしきい値は、風 5 m/秒で 0.08・10 m/秒で 0.15・15 m/秒で 0.26（波の高さを本物に合わせたとき）。0.55 では風 15 m/秒でもほぼ白波が出ない",
     "note": "白波の cusp しきい値は風10m/秒で0.15。0.55ではほぼ出ない"},
    {"no": "224", "anchor": "exp224",
     "tags": ["シミュレーション", "Vellum", "布", "速さ", "制作"],
     "log": "log_fx", "thumb": "224_cost.png",
     "shots": ["224_cost.png", "224_grid.png", "224_graph.png"],
     "title": "Vellum の布の伸びは Substeps で決まる（1→5 で平均 2.8%→0.10%）。Constraint Iterations を 4 倍にするより Substeps を倍にする方が、短い時間でよく効く。布の目を細かくすると 4 倍伸びる",
     "note": "布の伸びは Substeps で決まる。Iterations より効く"},
    {"no": "225", "anchor": "exp225",
     "tags": ["Karma", "ライト", "夜", "速さ", "制作"],
     "log": "log_pm", "thumb": "225_grid.png",
     "shots": ["225_grid.png", "225_graph.png"],
     "title": "明かりを何百も置く場面は、照らすのをライトで。1000 個でも 16 サンプル 28 秒・ざらつき 5%。小さな光る球で照らすと、ざらつき 54% で、64 サンプルでも光が拾いきれない",
     "note": "明かり1000個はライトで。光る球で照らすとざらつく"},
    {"no": "226", "anchor": "exp226",
     "tags": ["シミュレーション", "RBD", "ガラス", "破壊", "制作"],
     "log": "log_fx", "thumb": "226_grid.png",
     "shots": ["226_grid.png", "226_graph.png"],
     "title": "ガラスのひびを増やすと、同じつながりの強さでは割れにくくなる（20 本で破片の 17% が動いたのが、80 本では 5%）。80 本なら強さを 0.8 → 0.6 に下げると同じくらい割れる。計算はどれも 3 秒以内",
     "note": "ガラスのひびを増やすと割れにくくなる。80本なら強さ0.6"},
    {"no": "227", "anchor": "exp227",
     "tags": ["地形", "Heightfield", "制作"],
     "log": "log_pm", "thumb": "227_grid.png",
     "shots": ["227_grid.png", "227_graph.png"],
     "title": "地形を削る heightfield_erode は、既定の 5 フレームでもう谷筋が刻まれる。20 フレームで谷の出口に土砂が広がり、100 フレームでは谷が埋まって山が低くなる（高さのばらつき 29 → 18 m）。時間はどれも 3 秒以内",
     "note": "地形の浸食は既定5フレームで谷筋、100で谷が埋まる"},
    {"no": "228", "anchor": "exp228",
     "tags": ["Karma", "粒", "速さ", "制作"],
     "log": "log_pm", "thumb": "228_grid.png",
     "shots": ["228_grid.png", "228_graph.png"],
     "title": "粒は点のまま Karma に渡す。1000 万個でも 8 秒（640×360・8 サンプル）。小さな球をパックして並べると 3 万個で 78 秒かかり、その 8 割は場面を渡す時間",
     "note": "粒は点のまま渡す。1000万個で8秒"},
    {"no": "229", "anchor": "exp229",
     "tags": ["Karma", "毛", "速さ", "制作"],
     "log": "log_pm", "thumb": "229_grid.png",
     "shots": ["229_grid.png", "229_graph.png"],
     "title": "毛は曲線のまま Karma に渡す。100 万本でも 12 秒（640×360・8 サンプル）。polywire で筒の面にすると 1 本あたりが重く、3 万本で 9 秒",
     "note": "毛は曲線のまま渡す。100万本で12秒"},
    {"no": "230", "anchor": "exp230",
     "tags": ["Karma", "モーションブラー", "制作"],
     "log": "log_pm", "thumb": "230_grid.png",
     "shots": ["230_grid.png", "230_graph.png"],
     "title": "速く回る物のブレは、オブジェクトごと回すなら既定（Rotation Blur・2 サンプル）で弧になる。SOP で形を回すと既定の Geometry Time Samples 2 ではまっすぐな線になり、8 で弧になる。時間はほぼ同じ",
     "note": "回る物のブレ: SOPで回すと Geometry Time Samples 8 で弧に"},
]

PLANNED = []

PLANNED_FX = []

PAGES = [
    # template, site出力, docs出力, ナビの現在位置, タブ形式か, 持つパネルの束
    # 親ページは docs/ には出さない。GitHub 版は別リポジトリの入口に置く。
    ("sp_template.html", "sp.html", None, "sp", False, None),
    ("home_template.html", "home.html", "index.html", "home", True, "home"),
    ("home_template.html", "practice.html", "practice.html", "guides", True,
     "guides"),
    ("home_template.html", "reference.html", "reference.html", "ref", True,
     "ref"),
    ("log_pm_template.html", "index.html", "log.html", "log", False, None),
    ("log_fx_template.html", "log_fx.html", "log_fx.html", "log_fx", False, None),
    ("glossary_template.html", "glossary.html", "glossary.html", "glossary",
     False, None),
    ("links_template.html", "links.html", "links.html", "links", False, None),
    ("vex_template.html", "vex.html", "vex.html", "vex", False, None),
]


THEME_SWITCH = ('      <div class="theme-switch" role="group" aria-label="表示の明るさ">'
                '<button type="button" data-theme-set="system" aria-pressed="true">自動</button>'
                '<button type="button" data-theme-set="light" aria-pressed="false">明</button>'
                '<button type="button" data-theme-set="dark" aria-pressed="false">暗</button></div>')


def render_deck(urls, count=8):
    """ホームの帯に重ねて出す、新着の実験のカード。押すとその実験の記事へ。"""
    items = list(reversed(DONE[-count:]))
    out = ['          <div class="deck" id="deck" aria-roledescription="カルーセル" aria-label="新着の実験">']
    for d in items:
        href = f'{urls[d["log"]]}#{d["anchor"]}'
        edition = "エフェクト編" if d["log"] == "log_fx" else "モデリング編"
        thumb = d.get("thumb") or ""
        thumb = f"thumb_{d['no']}.png" if os.path.exists(os.path.join(SITE, f"thumb_{d['no']}.png")) else thumb
        out.append(f'            <a class="deck-card" href="{href}">'
                   f'<img src="{thumb}" alt="" loading="lazy" decoding="async">'
                   f'<span class="deck-meta">実験{d["no"]} · {edition}</span>'
                   f'<span class="deck-t">{html.escape(d["title"].split(" — ")[0])}</span>'
                   f'<span class="deck-d">{html.escape(d.get("note", ""))}</span></a>')
    out.append("          </div>")
    out.append('          <div class="deck-ctrl">'
               '<button type="button" class="deck-play" id="deck-play" aria-label="自動の切り替えを止める"></button>'
               '<button type="button" class="deck-arrow" id="deck-prev" aria-label="前の実験">'
               '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 5l-7 7 7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
               '<div class="deck-dots" id="deck-dots"></div>'
               '<button type="button" class="deck-arrow" id="deck-next" aria-label="次の実験">'
               '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
               '</div>')
    return "\n".join(out)


def render_nav(active, tabs, urls, panels=None):
    """上部のバー。どのページでも同じ並びにする。

    左端は SP のロゴだけ。押すと親の Saito Production へ戻る。
    続くのは4つの見出しで、乗せると下にパネルが降りる。
    1列目は大きく、2列目から先は小さく出す。
    """
    # 2026-09-23 整え直し: 左にメニュー（2本線）、真ん中にロゴ、右にアイコン。
    # 上に並べていた見出し（nav-menu）は画面には出さず、メニューの一覧の元としてだけ残す
    out = [
        '  <nav class="sidenav" aria-label="サイト内の移動">',
        '    <div class="nav-inner">',
        '      <div class="nav-side nav-side--left">',
        '        <button type="button" class="nav-icon nav-burger" id="menu-open"'
        ' aria-label="メニューを開く" aria-expanded="false">'
        + BURGER_SVG + '<span class="nav-label">メニュー</span></button>',
        "      </div>",
        # SP のマークは親（Saito Production）へ、部の名前はこの部のホームへ（2026-09-23 ユーザー指示）
        '      <div class="brand">',
        f'        <a class="brand-logo" href="{urls.get("parent") or PARENT_URLS["pages"]}"'
        f' aria-label="{BRAND}（親のページへ）" title="{BRAND}へ">{LOGO_SVG}</a>',
        f'        <a class="brand-name" href="{urls["home"]}" title="{DEPT}のホームへ">{DEPT}</a>',
        "      </div>",
        '      <ul class="nav-menu" aria-hidden="true">',
    ]

    def control(target, label, extra="", ident=True):
        """行き先ひとつ。ハブではタブの切り替え、それ以外はリンクになる。
        ident=False は下のタブの列用（同じ id を2つ作らない）。"""
        if target.startswith("@"):
            href = urls[target[1:]]
            here = ' aria-current="page"' if (not ident and target[1:] == active) else ""
            return f'<a href="{href}"{extra}{here}>{html.escape(label)}</a>'
        # そのパネルを、いま出しているページが持っているならタブ。
        # 別のページが持っているなら、そのページへのリンクにする。
        if tabs and target in (panels or ()):
            tab_id = f' id="tab-{target}"' if ident else ""
            return (f'<button type="button" class="nav-tab" role="tab"'
                    f'{tab_id} data-panel="{target}"'
                    f' aria-controls="panel-{target}"'
                    f' aria-selected="false"{extra}>{html.escape(label)}</button>')
        here = ' aria-current="page"' if (not ident and target == active) else ""
        return (f'<a href="{panel_url(urls, target)}"{extra}{here}>'
                f"{html.escape(label)}</a>")

    for index, (head, target, columns) in enumerate(MENU):
        current = ' aria-current="page"' if ACTIVE_OF.get(active) == head else ""
        if not columns:
            out.append(f'        <li data-g="{index}">')
            out.append("          " + control(target, head, current))
            out.append("        </li>")
            continue

        out.append(f'        <li class="nav-drop" data-g="{index}">')
        out.append("          " + control(
            target, head,
            current + f' aria-expanded="false" aria-controls="mega-{index}"'))
        out.append(f'          <div class="mega" id="mega-{index}">')
        out.append('            <div class="mega-inner">')
        out.append('              <div class="mega-cols">')
        for col_index, (col_head, links) in enumerate(columns):
            lead = " col--lead" if col_index == 0 else ""
            out.append(f'                <div class="mega-col{lead}">')
            out.append(f'                  <p class="mega-head">'
                       f"{html.escape(col_head)}</p>")
            out.append("                  <ul>")
            for child_target, child_label, note in links:
                out.append("                    <li>"
                           + control(child_target, child_label)
                           + f'<span class="mega-note">{html.escape(note)}</span>'
                           + "</li>")
            out.append("                  </ul>")
            out.append("                </div>")
        out.append("              </div>")
        out.append("            </div>")
        out.append("          </div>")
        out.append("        </li>")

    # メニュー（左の一覧）の最後に親ページを置く（2026-09-23 ユーザー指示）
    out.append(f'        <li class="nav-parent"><a href="{urls.get("parent") or PARENT_URLS["pages"]}">'
               f'{BRAND}（親のページ）</a></li>')
    out.append("      </ul>")
    out.append('      <div class="nav-side nav-side--right">')
    out.append(AI_BUTTON.replace('<span class="nav-beta">Beta</span>',
                                 '<span class="nav-beta">Beta</span><span class="nav-label">AI</span>'))
    out.append('      <button type="button" class="nav-icon" id="search-open"'
               ' aria-label="Saito Production 全体を検索">' + SEARCH_SVG
               + '<span class="nav-label">検索</span></button>')
    out.append(f'      <a class="nav-icon nav-notebook" href="{NOTEBOOK_URL}" target="_blank"'
               ' rel="noopener" aria-label="Gemini Notebook（資料に質問できるノート）を開く">'
               + NOTEBOOK_SVG + '<span class="nav-label">Notebook</span></a>')
    out.append("      </div>")
    out.append("    </div>")
    # その区分のタブの列。いま居る区分の列だけを出す（どれを出すかは partial_chrome の JS）。
    # 降りてくるパネルの代わり。行き先は MENU の束をそのまま横に並べたもの（2026-09-22）
    # 2026-09-23: PC ではバーの左（メニューの隣）に入れ、スマホではバーの下に左寄せで出す
    rows = []
    for index, (head, target, columns) in enumerate(MENU):
        if not columns:
            continue
        links_html = "".join(
            control(child_target, child_label, f' title="{html.escape(note)}"', ident=False)
            for _col_head, links in columns for child_target, child_label, note in links)
        rows.append((index, links_html))
    left_close = out.index("      </div>")          # 左の箱の閉じ
    out[left_close:left_close] = [
        f'        <div class="subnav subnav--bar" data-g="{i}" hidden>{h.replace("実験ログ ", "")}</div>'
        for i, h in rows]
    for i, h in rows:
        out.append(f'    <div class="subnav subnav--row" data-g="{i}" hidden>{h}</div>')
    out.append("  </nav>")
    return "\n".join(out)


# 実験ログは、左に目次・右に本文の「文書の形」にする（2026-09-23。Google Cloud の文書を参考に）
DOC_TEMPLATES = {"log_pm_template.html": "log_pm", "log_fx_template.html": "log_fx"}
DOC_TITLE = {"log_pm": "実験ログ モデリング編", "log_fx": "実験ログ エフェクト編"}


def render_doc_toc(log_key, urls):
    """その編の実験の目次。30本ずつに区切り、いま読んでいる実験に印を付ける（印は JS）。"""
    items = [d for d in DONE if d.get("log", "log_pm") == log_key]
    other = "log_fx" if log_key == "log_pm" else "log_pm"
    out = [
        '  <aside class="doc-toc" aria-label="この編の実験">',
        '    <div class="doc-toc-inner">',
        '      <label class="doc-filter">' + SEARCH_SVG
        + '<input type="search" id="doc-filter" placeholder="この編を絞り込む" autocomplete="off"'
        ' aria-label="この編の実験を題で絞り込む"></label>',
        f'      <p class="doc-toc-head">{DOC_TITLE[log_key]}<small>{len(items)}本</small></p>',
        '      <ol class="doc-toc-list" id="doc-toc-list">',
    ]
    block = None
    for item in items:
        no = int(item["no"])
        start = (no - 1) // 30 * 30 + 1
        if start != block:
            block = start
            out.append(f'        <li class="doc-toc-sep" aria-hidden="true">'
                       f'{start:03d}–{start + 29:03d}</li>')
        out.append(f'        <li><a href="#{item["anchor"]}" data-anchor="{item["anchor"]}">'
                   f'<span class="doc-no">{item["no"]}</span>'
                   f'<span class="doc-t">{html.escape(item["title"])}</span></a></li>')
    out += [
        "      </ol>",
        f'      <a class="doc-other" href="{urls[other]}">{DOC_TITLE[other]}へ →</a>',
        "    </div>",
        "  </aside>",
    ]
    return "\n".join(out)


DATES = os.path.join(OUT, "dates.json")
_DATES_CACHE = {}


def pub_date(kind, key):
    """公開日（examples/dates_index.py が git の履歴から取ったもの）。無ければ空。"""
    if "d" not in _DATES_CACHE:
        _DATES_CACHE["d"] = {}
        if os.path.exists(DATES):
            with open(DATES, encoding="utf-8") as fp:
                _DATES_CACHE["d"] = json.load(fp)
    return _DATES_CACHE["d"].get(kind, {}).get(key, "")


def date_ja(day):
    y, m, d = day.split("-")
    return f"{int(y)}年{int(m)}月{int(d)}日"


def read_minutes(markup):
    """読む時間のめやす。日本語で1分に約600字として数える。"""
    text = re.sub(r"<[^>]+>|\s+", "", markup)
    return max(1, round(len(text) / 600))


def columnize(page):
    """実験ログの記事を、さっと読める形にする（2026-09-23）。

    題の下に「公開日・読む時間・タグ」と、要点（その記事の「わかったこと」の頭3つ）を出し、
    本文は「全文を読む」の中に畳む。本文そのものは変えない。
    """
    tags_of = {d["no"]: d.get("tags", []) for d in DONE}

    def fix(match):
        head, no, inner = match.group(1), match.group(2), match.group(3)
        cut = re.search(r'(<p class="path">.*?</p>|</h2>)', inner, re.S)
        close = inner.rfind("</div>")
        if not cut or close == -1:
            return match.group(0)
        top, rest, tail = inner[:cut.end()], inner[cut.end():close], inner[close:]
        points = re.findall(r"<li>(.*?)</li>",
                            (re.search(r'<ul class="findings">(.*?)</ul>', rest, re.S) or
                             re.search(r"()", "")).group(1), re.S)[:3]
        day = pub_date("exp", no)
        meta = []
        if day:
            meta.append(f'<time datetime="{day}">{date_ja(day)} 公開</time>')
        meta.append(f"<span>読む時間 約{read_minutes(rest)}分</span>")
        chips = "".join(f"<span class=\"coltag\">{html.escape(t)}</span>" for t in tags_of.get(no, [])[:4])
        block = ['\n        <div class="colhead">',
                 f'          <p class="colmeta">{"".join(meta)}{chips}</p>']
        thumb = f"thumb_{no}.png"
        has_thumb = os.path.exists(os.path.join(OUT, thumb))
        if points or has_thumb:
            block.append('          <div class="colbody">')
            if points:
                block.append('          <div class="colgist"><p class="colgist-label">要点</p><ul>')
                block += [f"            <li>{p.strip()}</li>" for p in points]
                block.append("          </ul></div>")
            if has_thumb:
                block.append(f'          <img class="colthumb" src="{thumb}" alt="" loading="lazy" decoding="async">')
            block.append("          </div>")
        block.append("        </div>")
        block.append('        <details class="colfull">'
                     f'<summary><span>全文を読む</span><small>約{read_minutes(rest)}分</small></summary>')
        return (head + top + "\n".join(block) + rest + "        </details>\n      " + tail
                + "</article>")

    return re.sub(r'(<article class="entry[^"]*" id="exp(\d{3})">)(.*?)</article>', fix, page,
                  flags=re.S)


def as_doc_layout(page, log_key, urls):
    """ひな形の本文（.shell）を、左の目次と並べる箱に入れる。"""
    page = page.replace('  <div class="shell">',
                        '  <div class="docwrap">\n' + render_doc_toc(log_key, urls)
                        + '\n  <div class="shell doc-main">', 1)
    mark = page.index("<!--GLOSSARY_DATA-->")
    close = page.rindex("</div>", 0, mark)      # .layout の閉じ
    return page[:close] + "</div>\n" + page[close:]


def crumb_table():
    """行き先（パネル名か "@ページ"）→ (区分の見出し, 区分の先頭の行き先, 名前)。MENU から作る。"""
    table = {"overview": (None, None, "ホーム")}
    for head, target, columns in MENU:
        for _col, links in columns:
            for child, label, _note in links:
                table.setdefault(child.lstrip("@"), (head, target, label))
    return table


def crumb_href(urls, target):
    return urls[target[1:]] if target.startswith("@") else panel_url(urls, target)


def render_crumbs(active, tabs, urls, panels, doc=False):
    """いまどこにいるか（Houdini 研究部 › 実験 › 実験ログ モデリング編）。どの段も押せる。

    タブのあるページでは、パネルごとに1行ずつ作っておき、選んだタブの行だけを出す
    （切り替えは partial_chrome の JS）。
    """
    table = crumb_table()

    def row(key, extra=""):
        if key == "overview":
            # 研究部のホームでは現在地を出さない（2026-09-23 ユーザー指示）
            return f'      <nav class="crumbs crumbs--home" aria-hidden="true"{extra}></nav>'
        head, head_target, label = table.get(key, (None, None, None))
        parts = [f'<a href="{urls.get("parent") or PARENT_URLS["pages"]}">{BRAND}</a>',
                 f'<a href="{urls["home"]}">{DEPT}</a>']
        if head and label:
            if head_target and head_target != key:
                parts.append(f'<a href="{crumb_href(urls, head_target)}">{html.escape(head)}</a>')
            parts.append(f'<span aria-current="page">{html.escape(label)}</span>')
        sep = '<span class="crumb-sep" aria-hidden="true">›</span>'
        return f'      <nav class="crumbs" aria-label="現在地"{extra}>' + sep.join(parts) + "</nav>"

    out = ['  <div class="crumbrow crumbrow--doc">' if doc else '  <div class="crumbrow">']
    if tabs and panels:
        for panel in panels:
            out.append(row(panel, f' data-crumb="{panel}" hidden'))
    else:
        out.append(row(active))
    out.append("  </div>")
    return "\n".join(out)


FOOT_ARROW = ('<svg class="foot-arrow" viewBox="0 0 16 16" fill="none" aria-hidden="true">'
              '<path d="M3 8h9M8.5 4.5L12 8l-3.5 3.5" stroke="currentColor" stroke-width="1.4"'
              ' stroke-linecap="round" stroke-linejoin="round"/></svg>')


def render_footer(urls, guides, data, nodes):
    """全ページの最後に置くリンク集（2026-09-23）。

    左にサイトの名前と一言・数、右に行き先。見出しの行は大きく、その下に中の行き先を小さく並べる。
    """
    def href(target):
        return crumb_href(urls, target)

    def group(head, target, columns):
        rows = [f'          <li class="foot-group">'
                f'<a class="foot-link" href="{href(target)}"><span>{html.escape(head)}</span>{FOOT_ARROW}</a>']
        kids = [(t, label) for _c, links in columns for t, label, _n in links if t != target]
        if kids:
            rows.append('            <ul class="foot-kids">')
            for t, label in kids:
                rows.append(f'              <li><a href="{href(t)}"><span>{html.escape(label)}</span></a></li>')
            rows.append("            </ul>")
        rows.append("          </li>")
        return rows

    by_head = {head: (head, target, cols) for head, target, cols in MENU}
    left = [by_head["ホーム"], by_head["実践"], by_head["解説"]]
    right = [by_head["実験"]]
    parent = urls.get("parent") or PARENT_URLS["pages"]
    year = datetime.date.today().year
    out = [
        '<footer class="sitefoot" id="sitemap">',
        '  <div class="sitefoot-inner">',
        '    <div class="foot-brand">',
        f'      <a class="foot-logo" href="{urls["home"]}">{LOGO_SVG}'
        f'<span><strong>{DEPT}</strong><small>{BRAND}</small></span></a>',
        '      <p class="foot-lede">Houdini の機能を1つずつ動かし、測った数値で記録する研究サイト。'
        '作り方の手順と、ノード・用語の解説もある。</p>',
        '      <dl class="foot-stats">',
        f'        <div><dt>実験</dt><dd>{len(DONE)}</dd></div>',
        f'        <div><dt>実践</dt><dd>{len(guides["guides"])}</dd></div>',
        f'        <div><dt>ノード</dt><dd>{count_nodes(nodes)}</dd></div>',
        f'        <div><dt>用語</dt><dd>{count_terms(data)}</dd></div>',
        "      </dl>",
        '      <div class="foot-ext">',
        f'        <a href="{NOTEBOOK_URL}" target="_blank" rel="noopener">{NOTEBOOK_SVG}'
        '<span>Gemini Notebook<small>資料に質問できるノート</small></span></a>',
        '        <a href="https://github.com/RealEstateWarrior/houdini-lab" target="_blank"'
        ' rel="noopener"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        '<path d="M8 17l-5-5 5-5M16 7l5 5-5 5" stroke="currentColor" stroke-width="1.6"'
        ' stroke-linecap="round" stroke-linejoin="round"/></svg>'
        '<span>GitHub<small>台本と hip の置き場</small></span></a>',
        "      </div>",
        "    </div>",
        '    <div class="foot-cols">',
    ]
    for col in (left, right):
        out.append('      <ul class="foot-list">')
        for head, target, columns in col:
            out += group(head, target, columns)
        out.append("      </ul>")
    out += [
        "    </div>",
        "  </div>",
        '  <div class="sitefoot-bottom">',
        THEME_SWITCH.strip(),
        '    <p class="foot-small">'
        f'<a href="{parent}">{BRAND}</a>'
        f'<span>確かめた版: {HOU_VERSION}</span></p>',
        f'    <p class="foot-copy">&copy; {year} {BRAND}</p>',
        "  </div>",
        "</footer>",
    ]
    return "\n".join(out)


def render_parent_nav(urls):
    """親（Saito Production）のバー。部の中と同じ形にする（2026-09-23）。

    左にメニューと部の切り替え、真ん中に SP のマークと名前、右に AI と検索。
    """
    out = [
        '  <nav class="sidenav" aria-label="サイト内の移動">',
        '    <div class="nav-inner">',
        '      <div class="nav-side nav-side--left">',
        '        <button type="button" class="nav-icon nav-burger" id="menu-open"'
        ' aria-label="メニューを開く" aria-expanded="false">'
        + BURGER_SVG + '<span class="nav-label">メニュー</span></button>',
        '        <div class="dept-switch" aria-label="部">',
    ]
    for dept_id, label, ready in DEPARTMENTS:
        if ready:
            out.append(f'          <a href="{urls["home"]}">{html.escape(label)}</a>')
        else:
            out.append(f'          <span class="soon">{html.escape(label)}<small>準備中</small></span>')
    kids = [(urls["home"], "ホーム"), (urls["guides"], "実践"), (urls["log_pm"], "実験ログ モデリング編"),
            (urls["log_fx"], "実験ログ エフェクト編"), (urls["ref"], "ノード解説と用語集")]
    menu = ['        <ul class="nav-menu" aria-hidden="true">']
    for dept_id, label, ready in DEPARTMENTS:
        if ready:
            menu.append(f'          <li class="nav-drop"><a href="{urls["home"]}">{html.escape(label)}</a>'
                        '<div class="mega"><div class="mega-col"><ul>'
                        + "".join(f'<li><a href="{h}">{html.escape(l)}</a></li>' for h, l in kids)
                        + "</ul></div></div></li>")
        else:
            menu.append(f'          <li><span class="sheet-soon">{html.escape(label)}（準備中）</span></li>')
    menu.append("        </ul>")
    out += menu
    out += [
        "        </div>",
        "      </div>",
        '      <div class="brand">',
        f'        <a class="brand-logo" href="#top" aria-label="{BRAND}（このページの頭へ）">{LOGO_SVG}</a>',
        f'        <a class="brand-name" href="#top">{BRAND}</a>',
        "      </div>",
        '      <div class="nav-side nav-side--right">',
        AI_BUTTON.replace('<span class="nav-beta">Beta</span>',
                          '<span class="nav-beta">Beta</span><span class="nav-label">AI</span>'),
        '      <button type="button" class="nav-icon" id="search-open"'
        ' aria-label="Saito Production 全体を検索">' + SEARCH_SVG + '<span class="nav-label">検索</span></button>',
        "      </div>",
        "    </div>",
        "  </nav>",
    ]
    return "\n".join(out)


def render_parent_footer(urls, guides, data, nodes):
    """親ページのリンク集。部ごとに、その中の行き先を並べる。"""
    year = datetime.date.today().year
    kids = [(urls["guides"], "実践"), (urls["log_pm"], "実験ログ モデリング編"),
            (urls["log_fx"], "実験ログ エフェクト編"), (urls["ref"], "ノード解説と用語集")]
    out = [
        '<footer class="sitefoot" id="sitemap">',
        '  <div class="sitefoot-inner">',
        '    <div class="foot-brand">',
        f'      <a class="foot-logo" href="#top">{LOGO_SVG}<span><strong>{BRAND}</strong>'
        '<small>部の入口</small></span></a>',
        '      <p class="foot-lede">作ったものと、作り方と、確かめた数字を置いておく場所。部ごとに分けている。</p>',
        '      <dl class="foot-stats">',
        f'        <div><dt>実験</dt><dd>{len(DONE)}</dd></div>',
        f'        <div><dt>実践</dt><dd>{len(guides["guides"])}</dd></div>',
        f'        <div><dt>ノード</dt><dd>{count_nodes(nodes)}</dd></div>',
        f'        <div><dt>用語</dt><dd>{count_terms(data)}</dd></div>',
        "      </dl>",
        "    </div>",
        '    <div class="foot-cols">',
        '      <ul class="foot-list">',
        f'          <li class="foot-group"><a class="foot-link" href="{urls["home"]}"><span>{DEPT}</span>{FOOT_ARROW}</a>',
        '            <ul class="foot-kids">',
    ]
    out += [f'              <li><a href="{h}"><span>{html.escape(l)}</span></a></li>' for h, l in kids]
    out += [
        "            </ul>",
        "          </li>",
        "      </ul>",
        '      <ul class="foot-list">',
        '          <li class="foot-group"><span class="foot-link foot-link--soon"><span>映像制作部</span><small>準備中</small></span></li>',
        "      </ul>",
        "    </div>",
        "  </div>",
        '  <div class="sitefoot-bottom">',
        THEME_SWITCH.strip(),
        f'    <p class="foot-copy">&copy; {year} {BRAND}</p>',
        "  </div>",
        "</footer>",
    ]
    return "\n".join(out)


def render_sp_depts(urls, guides, data):
    """部のカード。中身のある部だけ数字を出す。"""
    out = ['      <div class="depts">']
    for dept_id, label, ready in DEPARTMENTS:
        if ready:
            out.append(f'        <a class="dept" href="{urls["home"]}">')
            out.append(f"          <h3>{html.escape(label)}</h3>")
            out.append('          <p>Houdini を実際に動かして、測って、残す。'
                       "推測は書かない。数字が合わなかった回も、そのまま残す。</p>")
            out.append('          <dl class="dept-facts">')
            for term, value in (("実験", f"{len(DONE)} 件"),
                                ("実践", f"{len(guides['guides'])} 本"),
                                ("用語", f"{count_terms(data)} 語")):
                out.append(f"            <div><dt>{term}</dt>"
                           f"<dd>{value}</dd></div>")
            out.append("          </dl>")
            out.append('          <span class="dept-go">開く</span>')
            out.append("        </a>")
        else:
            out.append('        <div class="dept dept--soon">')
            out.append(f"          <h3>{html.escape(label)}</h3>")
            out.append("          <p>これから作ります。</p>")
            out.append('          <span class="dept-go">準備中</span>')
            out.append("        </div>")
    out.append("      </div>")
    return "\n".join(out)


def render_sp_recent(urls, count=6):
    """直近の実験。親から1手で中身へ入れるようにする。"""
    out = ['      <div class="thumbs">']
    for item in list(reversed(DONE))[:count]:
        log_url = urls[item.get("log", "log_pm")]
        card = f'thumb_{item["no"]}.png'
        if not os.path.exists(os.path.join(OUT, card)):
            card = item["thumb"]
        out.append(f'        <a class="thumb" href="{log_url}#{item["anchor"]}">')
        out.append(f'          <span class="thumb-img"><img src="{card}"'
                   f' loading="lazy" decoding="async"'
                   f' alt="実験{item["no"]}の結果"></span>')
        out.append('          <span class="thumb-body">')
        out.append(f'            <span class="thumb-no">実験 {item["no"]}</span>')
        out.append(f'            <h4>{html.escape(item["title"])}</h4>')
        out.append(f'            <p>{html.escape(item["note"])}</p>')
        out.append("          </span>")
        out.append("        </a>")
    out.append("      </div>")
    return "\n".join(out)


def render_sp_guides(guides, urls, count=3):
    """新しい手順。親から「作り方」へ直行させる。"""
    out = ['      <div class="tiles">']
    for guide in list(reversed(guides["guides"]))[:count]:
        out.append('        <a class="tile" href="'
                   + guide_url(urls, guide["id"]) + '" target="_blank" rel="noopener">')
        out.append(f'          <img src="{guide["hero"]}" loading="lazy"'
                   f' decoding="async" alt="{html.escape(guide["title"])}の完成図">')
        out.append('          <span class="tile-body">')
        out.append(f"            <h4>{html.escape(guide['title'])}</h4>")
        out.append(f"            <p>{html.escape(guide['lede'][:88])}…</p>")
        out.append("          </span>")
        out.append("        </a>")
    out.append("      </div>")
    return "\n".join(out)


# 概要タブの「これまでに作ったもの」。
# 実験番号・手順の id・見出し・一文・横長か。文面の数字は各実験の記録から引く。
# 押すと実験のポップアップ、または手順のポップアップがそのまま開く。
SHOWCASE = [
    ("008", "grow", "地面に物を生やす",
     "200個すべての向きを測って、複製の向きが N のどの軸に対応するかを確定させた。答えは Z 軸。", True),
    ("002", "smooth", "割ると丸くなる",
     "面の数はちょうど4倍ずつ増える。縮む原因は分割ではなく平滑化だった。", False),
    ("005", "terrain", "ノイズの種類で形が変わる",
     "14通り並べると振幅に9.3倍の開きがあった。外へ押すものと内へ削るものがある。", False),
    ("014", "rbd", "落として、砕く",
     "硬い物体なので体積は全フレームで 8.00000。ばらつきは 0.0000000 だった。", False),
    ("016", "smoke", "煙の減り方を式にする",
     "毎フレーム (1−d) 倍という仮説を立て、実測と4桁一致させた。", False),
    ("042", "groom", "毛を生やす",
     "density は本数ではなく面積あたりの本数。100 を入れて 1,249本、面積 12.53 で割ると 99.678。", False),
    ("053", "rig", "曲げても痩せない骨",
     "90度曲げたときの体積の減りが Linear で 27.1284%、Dual Quaternion で 0.1764%。", False),
    ("067", "mpm", "塊を滑らせて、摩擦を式で確かめる",
     "MPM の Ground Friction は教科書のクーロン摩擦の μ そのもの。止まる距離が式と 0.04% で合った。"
     "ただし塊が潰れ始めると式から外れる。", True),
    ("018", None, "ノイズはどこまで減るのか",
     "サンプル数を4倍にすればノイズは半分、という式は狭い範囲でしか当たらなかった。"
     "指定した数がそのまま使われていない。", False),
    ("055", None, "届かない場所を指す",
     "逆運動学で届かない目標を指すと、腕は伸びきってそこで止まる。9通りすべてで式と全桁一致。", False),
    ("066", "mpm", "風を当てる",
     "風速だけ上げても何も起きない。風は空気抵抗を通してしか効かず、その抵抗は速さの2乗だった。", False),
]


def render_showcase(guides):
    """概要タブの「これまでに作ったもの」。カードから実験と作り方へ直行できる。"""
    known = {g["id"]: g["title"] for g in guides["guides"]}
    by_no = {item["no"]: item for item in DONE}
    out = ['      <div class="tiles">']
    for no, guide_id, head, text, wide in SHOWCASE:
        item = by_no.get(no)
        if item is None:
            continue
        img = f"thumb_{no}.png"
        if not os.path.exists(os.path.join(OUT, img)):
            img = item["thumb"]
        cls = "tile tile--wide" if wide else "tile"
        out.append(f'        <div class="{cls}">')
        out.append(f'          <button type="button" class="tile-img" data-exp="{no}"'
                   f' aria-label="実験{no}を開く"><img src="{img}" loading="lazy"'
                   f' decoding="async" alt="{html.escape(item["title"])}"></button>')
        out.append('          <div class="tile-body">')
        out.append(f"            <h4>{html.escape(head)}</h4>")
        out.append(f"            <p>{html.escape(text)}</p>")
        out.append('            <p class="tile-actions">')
        out.append(f'              <button type="button" class="tile-go" data-exp="{no}">'
                   f"実験{no} を読む</button>")
        if guide_id and guide_id in known:
            out.append(f'              <button type="button" class="tile-go tile-go--guide"'
                       f' data-guide="{guide_id}">作り方を見る</button>')
        out.append("            </p>")
        out.append("          </div>")
        out.append("        </div>")
    out.append("      </div>")
    return "\n".join(out)


def load_speed():
    with open(SPEED, encoding="utf-8") as fp:
        return json.load(fp)


def render_speed():
    """効率化タブ。重くなりがちなところと、実測した対処を並べる。

    結論（太字の一文）→ 実測の数字 → 元の実験へのボタン、の順。
    数字は speed_tips.json に書いたものをそのまま出す。"""
    data = load_speed()
    titles = {item["no"]: item["title"] for item in DONE}
    out = ['      <p class="lede speed-lede">' + html.escape(data["lede"]) + "</p>"]
    out.append('      <nav class="gloss-nav" aria-label="効率化の分類">')
    for group in data["groups"]:
        out.append(f'        <a href="#speed-{group["id"]}">{html.escape(group["title"])}</a>')
    out.append("      </nav>")
    for group in data["groups"]:
        out.append(f'      <section class="speed-group" id="speed-{group["id"]}">')
        out.append(f'        <h3>{html.escape(group["title"])}</h3>')
        out.append('        <ol class="speed-list">')
        for index, tip in enumerate(group["tips"]):
            out.append(f'          <li class="speed-tip" id="speed-{group["id"]}-{index}">')
            out.append(f'            <h4>{html.escape(tip["rule"])}</h4>')
            out.append(f'            <p>{html.escape(tip["evidence"])}</p>')
            out.append('            <p class="speed-exps">')
            for no in tip["exps"]:
                if no in titles:
                    out.append(f'              <button type="button" class="speed-exp"'
                               f' data-exp="{no}" title="{html.escape(titles[no])}">'
                               f'実験{no}</button>')
            out.append("            </p>")
            out.append("          </li>")
        out.append("        </ol>")
        out.append("      </section>")
    out.append('      <p class="hint">これからの実験では、結果と一緒にかかった時間も必ず記録する。'
               "分かったことはこのタブに足していく。</p>")
    return "\n".join(out)


def all_tags():
    """使われているタグを、使用数の多い順に並べる。"""
    counts = {}
    for item in DONE:
        for tag in item.get("tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def render_thumbs(urls):
    """実験の一覧。カードはリンクではなくボタンで、押すとポップアップが開く。"""
    out = ['      <div class="stage"><h3>完了した実験</h3>'
           "<p>カードを押すと、実験ログの記事が新しいタブで開く。タグで絞り込める。</p></div>"]
    out.append('      <div class="tagbar" id="tagbar">')
    out.append('        <button type="button" class="tagchip is-on" data-tag="">'
               f"すべて <span>{len(DONE)}</span></button>")
    for tag, count in all_tags():
        out.append(f'        <button type="button" class="tagchip" data-tag="{tag}">'
                   f"{html.escape(tag)} <span>{count}</span></button>")
    out.append("      </div>")
    out.append('      <div class="thumbs" id="thumbs">')
    for item in DONE:
        tags = " ".join(item.get("tags", []))
        out.append(f'        <button type="button" class="thumb"'
                   f' data-exp="{item["no"]}" data-tags="{tags}">')
        # make_thumbs.py が作った 4:3 の板があればそちらを使う。
        # 元の画をそのまま入れると、正方形のものは上下が切られて
        # 何をしているか分からなくなる（70件中52件がそうだった）
        card = f'thumb_{item["no"]}.png'
        if not os.path.exists(os.path.join(OUT, card)):
            card = item["thumb"]
        out.append(f'          <span class="thumb-img"><img src="{card}"'
                   f' loading="lazy" decoding="async"'
                   f' alt="実験{item["no"]}の結果のレンダリング"></span>')
        out.append('          <span class="thumb-body">')
        out.append(f'            <span class="thumb-no">実験 {item["no"]}</span>')
        out.append(f'            <h4>{html.escape(item["title"])}</h4>')
        out.append(f'            <p>{html.escape(item["note"])}</p>')
        if item.get("tags"):
            chips = "".join(f"<span>{html.escape(t)}</span>"
                            for t in item["tags"])
            out.append(f'            <span class="thumb-tags">{chips}</span>')
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


def nodes_by_experiment(nodes):
    """ノード解説を実験番号で引けるようにひっくり返す。

    nodes.json には「このノードは実験003で使った」と書いてある。
    実験ログ側から「この実験で使ったノード」を出したいので、向きを変える。
    """
    table = {}
    index = -1
    for group in nodes["groups"]:
        for node in group["nodes"]:
            index += 1
            for no in node.get("exps", []):
                table.setdefault(no, []).append((node["name"], index))
    return table


def inject_experiment_links(page, urls, nodes):
    """実験ログの各記事に「使ったノード」と「シーンファイル」の行を足す。

    記事は手で書いているので、ここで機械的に差し込む。場所は各記事の
    <p class="path"> の直後。実験が増えても書き忘れが出ない。
    """
    table = nodes_by_experiment(nodes)
    hips = {item["no"]: item.get("hip") for item in DONE}
    # 本文にもうノードの画がある記事には、折りたたみを足さない
    has_graph = {m.group(1) for m in re.finditer(
        r'<article class="entry[^"]*" id="exp(\d+)">(?:(?!</article>).)*?\1_graph\.png', page, re.S)}
    pattern = re.compile(
        r'(<article class="entry[^"]*" id="exp(\d+)">.*?<p class="path">.*?</p>)',
        re.S)

    def build(match):
        whole, no = match.group(1), match.group(2)
        rows = []
        chips = [f'<a href="{panel_url(urls, "nodes")}">{html.escape(name)}</a>'
                 for name, _ in table.get(no, [])]
        if chips:
            rows.append('        <p class="usedby">'
                        '<span class="usedby-tag">使ったノード</span>'
                        + "".join(chips) + "</p>")
        # 091 以降は hip_export.py で後から作った NNN_scene.hipnc を使う（DONE に書いていなくても出す）
        hip = hips.get(no) or (f"{no}_scene.hipnc"
                               if os.path.exists(os.path.join(OUT, f"{no}_scene.hipnc")) else None)
        if hip:
            rows.append('        <p class="usedby">'
                        '<span class="usedby-tag">シーンファイル</span>'
                        f'<a href="{GITHUB_RAW}{hip}"'
                        ' target="_blank" rel="noopener noreferrer">'
                        f'{hip}</a></p>')
        if os.path.exists(os.path.join(OUT, f"{no}_graph.png")) and no not in has_graph:
            rows.append('        <details class="netgraph"><summary>ノードのつなぎ方を見る</summary>'
                        f'<img src="{no}_graph.png" alt="実験{no} のノードのつなぎ方" loading="lazy" decoding="async"></details>')
        if not rows:
            return whole
        return whole + "\n" + "\n".join(rows)

    return pattern.sub(build, page)


def link_terms_in(markup):
    """生成したHTMLに用語リンクを差し込む。実験ログと同じ仕組みを使う。

    手順ページは初心者が最初に読むところなので、用語の取りこぼしが一番痛い。
    差し込むのはタグだけで、本文の文字は変えない（ここでも検算する）。
    """
    ordered = sorted(link_terms.ALLOW, key=len, reverse=True)
    already = set(re.findall(r'data-term="([^"]+)"', markup))
    remaining = [t for t in ordered if t not in already]
    if not remaining:
        return markup
    pattern = re.compile("|".join(re.escape(t) for t in remaining))
    linked, _ = link_terms.link_article(markup, pattern, set())
    if link_terms.strip_tags(linked) != link_terms.strip_tags(markup):
        raise SystemExit("用語リンクの差し込みで本文が変わった")
    return linked


def node_index(nodes):
    """ノード名 → (種類, 一言, 解説での番号)。番号は解説ページの id="node-N" と同じ数え方。"""
    table = {}
    index = -1
    for group in nodes["groups"]:
        for node in group["nodes"]:
            index += 1
            table.setdefault(node["name"], (node["kind"], node["one"], index))
    return table


def render_node_data(nodes, urls):
    """ノード名のポップアップが読む表。解説ページの住所も一緒に渡す。"""
    ref = panel_url(urls, "nodes").split("#")[0]
    body = json.dumps({"ref": ref,
                       "nodes": {name: list(v) for name, v in node_index(nodes).items()}},
                      ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/json" id="node-data">{body}</script>'


NODE_CODE = re.compile(r"<code>([A-Za-z][\w]*(?:::[\d.]+)?)</code>")


def link_nodes_in(markup, table):
    """本文の <code>ノード名</code> を、押すと説明が出る札にする（2026-09-23）。

    名前がノード解説にあるものだけ。<script> の中（検索用の JSON など）は触らない。
    """
    def fix(match):
        name = match.group(1).split("::")[0]
        if name not in table:
            return match.group(0)
        return (f'<code class="node-ref" data-node="{name}" tabindex="0"'
                f' role="button">{match.group(1)}</code>')

    parts = re.split(r"(<script\b.*?</script>)", markup, flags=re.S)
    return "".join(part if part.startswith("<script") else NODE_CODE.sub(fix, part)
                   for part in parts)


PARM_INDEX = os.path.join(OUT, "parm_index.json")
_PARM_CACHE = {}


def parm_table():
    if "t" not in _PARM_CACHE:
        _PARM_CACHE["t"] = {}
        if os.path.exists(PARM_INDEX):
            with open(PARM_INDEX, encoding="utf-8") as fp:
                _PARM_CACHE["t"] = json.load(fp)
    return _PARM_CACHE["t"]


def link_parms_in(body, guide_id, step_no):
    """段の本文の太字に、つまみの置き場所を出す札を付ける（2026-09-23）。

    表は examples/parm_index.py が hip から取ったもの。その段のノードのつまみだけと突き合わせる。
    """
    step = parm_table().get(guide_id, {}).get(str(step_no))
    if not step:
        return body
    labels = sorted(step["parms"], key=len, reverse=True)

    def fix(match):
        text = re.sub(r"<[^>]+>", "", match.group(2))
        found, taken = [], []
        for label in labels:
            at = text.find(label)
            while at != -1:
                span = (at, at + len(label))
                if not any(a < span[1] and span[0] < b for a, b in taken):
                    taken.append(span)
                    found.append(label)
                    break
                at = text.find(label, at + 1)
        if not found:
            return match.group(0)
        rows = [[label] + step["parms"][label][:4] for label in found]
        payload = html.escape(json.dumps({"node": step["node"], "name": step["name"], "rows": rows},
                                         ensure_ascii=False), quote=True)
        return (f'<strong{match.group(1)} class="parm-ref" data-parm="{payload}" tabindex="0"'
                f' role="button">{match.group(2)}</strong>')

    return re.sub(r"<strong([^>]*)>(.*?)</strong>", fix, body, flags=re.S)


SIM_MARKS = ("シミュレーション", "エフェクト", "Vellum", "Pyro", "FLIP", "RBD", "MPM", "POP")
SIM_NODES = ("vellumsolver", "pyrosolver", "flipsolver", "rbdbulletsolver", "popnet",
             "mpmsolver", "dopnet", "flipcontainer")


def guide_level(guide):
    """難易度（2026-09-23）。決め方は決まりで出す（感覚で付けない）:
    シミュレーションを回すものは「応用」、VEX（wrangle）を書くか6段以上のものは「基本」、それ以外は「入門」。"""
    nodes = {step.get("node", "") for step in guide.get("steps", [])}
    tags = set(guide.get("tags", []))
    if tags & set(SIM_MARKS) or nodes & set(SIM_NODES):
        return 3, "応用"
    if "attribwrangle" in nodes or "VEX" in tags or len(guide.get("steps", [])) >= 6:
        return 2, "基本"
    return 1, "入門"


def level_badge(guide):
    level, name = guide_level(guide)
    dots = "".join('<i class="on"></i>' if n <= level else "<i></i>" for n in (1, 2, 3))
    return (f'<span class="level level--{level}" title="難易度: {name}'
            f'（シミュレーションは応用、VEX か6段以上は基本、ほかは入門）">'
            f'<span class="level-dots" aria-hidden="true">{dots}</span>難易度 {name}</span>')


def render_guide_cards(guides):
    """手順の一覧。カードを押すとポップアップで開く。

    手順が増えてきたので、全部を縦に並べると目当てのものに辿り着けない。
    実験タブと同じで、まず一覧、押したら中身。
    """
    out = ['      <div class="thumbs" id="guide-cards">']
    for index, guide in enumerate(guides["guides"], start=1):
        facts = dict(guide.get("facts") or [])
        chips = [level_badge(guide), f'{len(guide["steps"])}ステップ']
        if facts.get("ノードの数"):
            chips.append(facts["ノードの数"])
        if facts.get("かかる時間"):
            chips.append(facts["かかる時間"])
        out.append('        <button type="button" class="thumb"'
                   f' data-guide="{guide["id"]}">')
        out.append('          <span class="thumb-img">'
                   f'<img src="{guide["hero"]}" alt="" loading="lazy"></span>')
        out.append('          <span class="thumb-body">')
        out.append(f'            <span class="thumb-no">実践 {index:02d}'
                   f'{" · 実験" + guide["exp"] if guide.get("exp") else ""}'
                   '</span>')
        out.append(f'            <h4>{html.escape(guide["title"])}</h4>')
        out.append(f'            <p>{html.escape(guide["lede"])}</p>')
        out.append('            <span class="thumb-tags">'
                   + "".join(c if c.startswith("<span class=\"level") else f"<span>{html.escape(c)}</span>"
                             for c in chips)
                   + "</span>")
        out.append("          </span>")
        out.append("        </button>")
    out.append("      </div>")
    return "\n".join(out)


_FIRST_BY_CONTENT = {}


def same_image(name):
    """中身（バイト列）が同じ画像なら、最初に出てきた名前を返す。"""
    import hashlib
    with open(os.path.join(OUT, name), "rb") as fp:
        digest = hashlib.sha1(fp.read()).hexdigest()
    return _FIRST_BY_CONTENT.setdefault(digest, name)


def render_requests(requests):
    """実践の要望。状態ごとにまとめて、上から手を付けている順に並べる。

    済んだものも消さずに残す。何を断ったかも理由ごと残す。
    そうしないと、同じ要望が何度も出てくる。
    """
    by_state = {}
    for item in requests["requests"]:
        by_state.setdefault(item["state"], []).append(item)

    out = []
    for state in requests["states"]:
        items = by_state.get(state["id"])
        if not items:
            continue
        out.append(f'      <div class="queue queue--{state["tone"]}">')
        out.append('        <div class="queue-head">')
        out.append(f'          <span class="queue-tag">{html.escape(state["label"])}'
                   f'<b>{len(items)}</b></span>')
        out.append(f'          <p>{html.escape(state["note"])}</p>')
        out.append("        </div>")
        out.append("        <ul>")
        for item in items:
            out.append("          <li>")
            out.append(f'            <h4>{html.escape(item["title"])}</h4>')
            out.append(f'            <p>{html.escape(item["why"])}</p>')
            meta = [f'出した人: {html.escape(item["from"])}',
                    html.escape(item["when"])]
            if item.get("block"):
                meta.append("止まっている理由: " + html.escape(item["block"]))
            if item.get("reason"):
                meta.append("見送った理由: " + html.escape(item["reason"]))
            out.append('            <p class="queue-meta">'
                       + " · ".join(meta) + "</p>")
            if item.get("guide"):
                out.append('            <button type="button" class="queue-go"'
                           f' data-guide="{item["guide"]}">'
                           "できた実践を見る</button>")
            out.append("          </li>")
        out.append("        </ul>")
        out.append("      </div>")
    if not out:
        return ('      <p class="empty">いまのところ順番待ちはありません。'
                "作ってほしいものを言ってもらえれば、ここに並びます。</p>")
    return "\n".join(out)


def render_strip(guides, urls):
    """ホームの帯。小さな札が横へ流れる。

    乗せると止まり、押すとその実践がそのまま開く。
    実践の中身は実践のページにしか無いので、札はそのページへのリンクにする
    （以前は button で、ホームでは押しても何も起きなかった。2026-09-22）。
    継ぎ目なく回すために、同じ並びを2回置いて半分ぶん動かす。
    2周目は読み上げに要らないので隠す。
    """
    items = guides["guides"][-14:]
    if not items:
        return ""
    out = ['      <div class="strip" aria-label="最近の実践">',
           '        <div class="strip-track">']
    for pass_no in (1, 2):
        hidden = ' aria-hidden="true" tabindex="-1"' if pass_no == 2 else ""
        for guide in items:
            out.append(f'          <a class="chip-card" href="{guide_url(urls, guide["id"])}"'
                       f' target="_blank" rel="noopener"{hidden}>')
            out.append(f'            <img src="{guide["hero"]}" alt=""'
                       ' loading="lazy" decoding="async">')
            out.append(f'            <span>{html.escape(guide["title"])}</span>')
            out.append("          </a>")
    out.append("        </div>")
    out.append("      </div>")
    return "\n".join(out)


# ハンバーガーを開いたときに並べる実践。絵として見栄えのするものを選んでいる（2026-09-23）。
# 2026-09-24: 「サムネイルが面白くない」とのことで、写真と見比べて作った新しい実践に差し替え、12 本に増やした。
# 入口（ノード解説・用語集）の画も、実験のつなぎ方の図をやめて実践の仕上がりにした
MENU_GUIDES = ["ocean", "neon", "fireworks", "donut", "lava", "sunflower", "cloud", "glasscup", "jelly", "balloon", "snow", "tree"]


def render_menu_cards(guides, urls, data, nodes):
    """ハンバーガーの中身の上半分。実践のサムネイルと、実験・解説への入口。

    下半分の文字の一覧は、これまでどおり JS が上のバーから写して作る。
    """
    by_id = {g["id"]: g for g in guides["guides"]}
    picks = [by_id[i] for i in MENU_GUIDES if i in by_id]
    out = ['    <div class="menu-cards">',
           '      <div class="menu-cards-head"><span>実践</span>'
           f'<a href="{panel_url(urls, "guides")}">すべて見る（{len(guides["guides"])}本）</a></div>',
           '      <div class="menu-rail">']
    for g in picks:
        out.append(f'        <a class="menu-card" href="{guide_url(urls, g["id"])}" target="_blank" rel="noopener">'
                   f'<img src="{g["hero"]}" alt="" loading="lazy" decoding="async">'
                   f'<span>{html.escape(g["title"])}</span></a>')
    out.append("      </div>")
    out.append('      <div class="menu-doors">')
    doors = (
        (panel_url(urls, "nodes"), by_id["campfire"]["hero"], "ノード解説", f"{count_nodes(nodes)}件"),
        (panel_url(urls, "glossary"), by_id["gems"]["hero"], "用語集", f"{count_terms(data)}語"),
        # 2026-09-23: メニューにも Notebook を置く（ユーザー指示）
        (NOTEBOOK_URL, "NB", "Gemini Notebook", "資料に質問できるノート"),
    )
    for href, img, label, sub in doors:
        if img == "NB":
            pic = '<span class="menu-door-mark menu-door-mark--nb" aria-hidden="true">' + NOTEBOOK_SVG + "</span>"
        elif img:
            pic = f'<img src="{img}" alt="" loading="lazy" decoding="async">'
        else:
            pic = '<span class="menu-door-mark" aria-hidden="true">Aa</span>'
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        out.append(f'        <a class="menu-door" href="{href}"{ext}>{pic}'
                   f'<span class="menu-door-text"><strong>{label}</strong><small>{html.escape(sub)}</small></span></a>')
    out.append("      </div>")
    out.append('      <p class="menu-cards-head menu-cards-head--list"><span>すべてのページ</span></p>')
    out.append("    </div>")
    return "\n".join(out)


def render_work_cards(works):
    """制作の一覧。まだ1本も無いときは、そう書いておく。"""
    if not works["works"]:
        return ('      <p class="empty">まだ1本もありません。'
                "作ってほしいものを言ってもらえれば、ここに記録が並びます。</p>")
    out = ['      <div class="thumbs" id="work-cards">']
    for index, work in enumerate(works["works"], start=1):
        out.append('        <button type="button" class="thumb"'
                   f' data-guide="{work["id"]}">')
        out.append('          <span class="thumb-img">'
                   f'<img src="{work["hero"]}" alt="" loading="lazy"></span>')
        out.append('          <span class="thumb-body">')
        out.append(f'            <span class="thumb-no">制作 {index:02d}</span>')
        out.append(f'            <h4>{html.escape(work["title"])}</h4>')
        out.append(f'            <p>{html.escape(work["lede"])}</p>')
        if work.get("facts"):
            out.append('            <span class="thumb-tags">'
                       + "".join(f"<span>{html.escape(v)}</span>"
                                 for _, v in work["facts"])
                       + "</span>")
        out.append("          </span>")
        out.append("        </button>")
    out.append("      </div>")
    return "\n".join(out)


def render_guides(guides, works, urls):
    """実践一覧のページには、もう中身を置かない（1本ずつのページへ移した。2026-09-23）。"""
    return ""


def render_guide_sections(guides, works, urls):
    """実践と制作の中身を1本ずつ作る。{id: (見出し, HTML, 実践か制作か, 元のデータ)}

    1段ごとに図を置く。最後に完成図と、組み上がったノードグラフを出して、
    詳しく知りたい人だけが実験ログへ行けるようにする。
    """
    anchors = {item["no"]: (item["anchor"], item.get("log", "log_pm"))
               for item in DONE}
    sections = {}
    out = []
    # 実践（guides.json）と制作（works.json）は同じ形で出す。
    # 画像の名前だけが guide_… / work_… で分かれるので、頭を付け替えて回す。
    items = ([(item, "guide") for item in guides["guides"]]
             + [(item, "work") for item in works["works"]])
    for guide, prefix in items:
        section_start = len(out)
        out.append(f'      <section class="guide" id="guide-{guide["id"]}">')
        out.append('        <div class="guide-hero">')
        out.append(f'          <img src="{guide["hero"]}" loading="lazy"'
                   f' decoding="async"'
                   f' alt="{html.escape(guide["title"])}の完成図">')
        out.append("        </div>")
        out.append('        <div class="guide-head">')
        out.append(f'          <h3>{html.escape(guide["title"])}</h3>')
        day = pub_date("guide", guide["id"]) if prefix == "guide" else ""
        if day:
            out.append(f'          <p class="guide-date"><time datetime="{day}">{date_ja(day)} 公開</time>'
                       f'<span>{len(guide["steps"])}ステップ</span>{level_badge(guide)}</p>')
        if guide.get("revisions"):
            last = guide["revisions"][-1]["date"]
            out.append(f'          <p class="guide-revised"><a href="#revisions">{html.escape(date_ja(last))} に作り直しました。'
                       '前の版との違いは「改訂の記録」へ</a></p>')
        out.append(f'          <p class="guide-lede">{guide["lede"]}</p>')
        for var in guide.get("variants", []):
            out.append(f'          <p class="guide-lede"><a href="#variant-{var["id"]}">もう一つの版: {html.escape(var["title"])} ↓</a></p>')
        if guide.get("facts"):
            out.append('          <dl class="guide-facts">')
            for label, value in guide["facts"]:
                out.append(f"            <div><dt>{html.escape(label)}</dt>"
                           f"<dd>{html.escape(value)}</dd></div>")
            out.append("          </dl>")
        # 制作だけ。どう頼まれたかを、言葉そのままで残す
        if guide.get("order"):
            out.append('          <blockquote class="work-order">')
            out.append(f'            <p>{html.escape(guide["order"])}</p>')
            out.append("            <cite>依頼</cite>")
            out.append("          </blockquote>")
        # 2026-09-23: hip と手順の目次を頭に置く（hip が最後にしか無く、探しにくかった）
        out.append('          <div class="guide-actions">')
        if guide.get("hip"):
            out.append(f'            <a class="guide-hip" href="{GITHUB_RAW}{guide["hip"]}"'
                       ' target="_blank" rel="noopener noreferrer">'
                       '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 4v11m0 0l-4.5-4.5M12 15l4.5-4.5M5 19.5h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                       f'<span>hip を開く<small>{html.escape(guide["hip"])}</small></span></a>')
        if guide.get("exp") in anchors:
            anchor, log_key = anchors[guide["exp"]]
            out.append(f'            <a class="guide-exp" href="{urls[log_key]}#{anchor}">'
                       f'実験{guide["exp"]} の全文</a>')
        out.append("          </div>")
        out.append('          <nav class="guide-toc" aria-label="手順の目次">')
        out.append('            <p class="label">手順</p>')
        out.append("            <ol>")
        for index, step in enumerate(guide["steps"], start=1):
            out.append(f'              <li><a href="#step-{index}">{html.escape(step["title"])}</a></li>')
        out.append("            </ol>")
        out.append("          </nav>")
        out.append("        </div>")

        # 動き（2026-09-23）。静止画だけでは揺れ・流れ・燃え方が伝わらないので、
        # practice_kit の anim() で撮った短い映像を、音なしで繰り返し流す
        anim = f'pr_{guide["id"]}_anim.mp4'
        if prefix == "guide" and os.path.exists(os.path.join(OUT, anim)):
            out.append('        <figure class="guide-anim">')
            out.append(f'          <video src="{anim}" autoplay muted loop playsinline preload="metadata"'
                       f' poster="{guide["hero"]}"></video>')
            out.append(f'          <figcaption>{html.escape(guide.get("anim_cap") or "動き。ビューポートでフレームを順に撮ったもの。")}'
                       "</figcaption>")
            out.append("        </figure>")

        # 本物の Houdini で撮ったネットワーク全体（guide_ui_capture.py）
        net = f'{prefix}_{guide["id"]}_net.png'
        if os.path.exists(os.path.join(OUT, net)):
            out.append('        <figure class="guide-net">')
            out.append('          <img src="' + net + '" loading="lazy" decoding="async"'
                       f' alt="{html.escape(guide["title"])}のネットワーク'
                       '（Houdini の画面）">')
            out.append("          <figcaption>組み上がったネットワーク。"
                       "Houdini の画面をそのまま撮ったもの。</figcaption>")
            out.append("        </figure>")
        elif os.path.exists(os.path.join(OUT, f'pr_{guide["id"]}_graph.png')):
            # Houdini の画面が撮れていないときは、hip から描いたつなぎ方の図を出す
            out.append('        <figure class="guide-net">')
            out.append(f'          <img src="pr_{guide["id"]}_graph.png" loading="lazy" decoding="async"'
                       f' alt="{html.escape(guide["title"])}のノードのつなぎ方">')
            out.append("          <figcaption>組み上がったネットワーク（hip から描いた、ノードのつなぎ方の図）。</figcaption>")
            out.append("        </figure>")

        out.append('        <ol class="steps">')
        for index, step in enumerate(guide["steps"], start=1):
            out.append(f'          <li class="step" id="step-{index}">')
            out.append('            <div class="step-body">')
            out.append(f'              <h4>{html.escape(step["title"])}'
                       f'<code>{html.escape(step["node"])}</code></h4>')
            out.append(f'              <p>{link_parms_in(step["body"], guide["id"], index) if prefix == "guide" else step["body"]}</p>')
            # その段のノードを選んだときのパラメータ欄（guide_parm_capture.py）。
            # 開いたときだけ読み込むよう details に入れる。ポップアップが重くならない
            parm = f'{prefix}_{guide["id"]}_p{index}_parm.png'
            if os.path.exists(os.path.join(OUT, parm)):
                # 同じノードを別の段でも撮ると、中身がまったく同じ画像になる。
                # 最初の1枚だけを使えば、ページに載せるファイルが減る
                # （Claude 版は1つの版に置けるファイルが 512 まで）
                parm = same_image(parm)
                out.append('              <details class="step-ui">')
                out.append("                <summary>Houdini のパラメータ画面</summary>")
                out.append('                <img src="' + parm + '" loading="lazy"'
                           ' decoding="async"'
                           f' alt="{html.escape(step["title"])}のパラメータ">')
                out.append("              </details>")
            out.append("            </div>")
            if step.get("img"):
                out.append('            <figure class="step-figure">')
                out.append('              <div class="frame-light">'
                           f'<img src="{step["img"]}" loading="lazy"'
                           f' decoding="async"'
                           f' alt="{html.escape(step["title"])}の結果"></div>')
                if step.get("cap"):
                    out.append(f"              <figcaption>{html.escape(step['cap'])}"
                               "</figcaption>")
                out.append("            </figure>")
            out.append("          </li>")
        out.append("        </ol>")

        # 制作だけ。作っている間に何が起きたかを、順に残す
        if guide.get("process"):
            out.append('        <p class="label">過程</p>')
            out.append('        <ol class="work-log">')
            for entry in guide["process"]:
                out.append('          <li><span class="work-when">'
                           f'{html.escape(entry["when"])}</span>'
                           f'<p>{entry["what"]}</p></li>')
            out.append("        </ol>")

        if guide.get("traps"):
            out.append('        <p class="label">つまずくところ</p>')
            for trap in guide["traps"]:
                out.append('        <div class="trap">')
                out.append(f'          <h4>{html.escape(trap["title"])}</h4>')
                out.append(f'          <p>{trap["body"]}</p>')
                if trap.get("img"):
                    out.append('          <figure>')
                    out.append('            <div class="frame-light">'
                               f'<img src="{trap["img"]}" loading="lazy"'
                               f' decoding="async"'
                               f' alt="{html.escape(trap["title"])}"></div>')
                    if trap.get("cap"):
                        out.append(f"            <figcaption>"
                                   f"{html.escape(trap['cap'])}</figcaption>")
                    out.append("          </figure>")
                out.append("        </div>")

        # もう一つの版（2026-09-24）。同じ題材を場面を変えて作ったものを、同じページの後ろに並べる
        for var in guide.get("variants", []):
            vid = var["id"]
            out.append(f'        <section class="guide-variant" id="variant-{vid}">')
            out.append('          <p class="label">もう一つの版</p>')
            out.append(f'          <h3>{html.escape(var["title"])}</h3>')
            out.append(f'          <p class="guide-lede">{var["lede"]}</p>')
            out.append('          <div class="guide-hero">')
            out.append(f'            <img src="{var["hero"]}" loading="lazy" decoding="async"'
                       f' alt="{html.escape(var["title"])}の完成図">')
            out.append("          </div>")
            if var.get("hero_cap"):
                out.append(f'          <p class="guide-cap">{html.escape(var["hero_cap"])}</p>')
            if var.get("facts"):
                out.append('          <dl class="guide-facts">')
                for label, value in var["facts"]:
                    out.append(f"            <div><dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd></div>")
                out.append("          </dl>")
            if var.get("hip"):
                out.append(f'          <a class="guide-hip" href="{GITHUB_RAW}{var["hip"]}" download>'
                           f'<span>hip を開く<small>{html.escape(var["hip"])}</small></span></a>')
            anim = f"pr_{vid}_anim.mp4"
            if os.path.exists(os.path.join(OUT, anim)):
                out.append('          <figure class="guide-anim">')
                out.append(f'            <video src="{anim}" autoplay muted loop playsinline preload="metadata"'
                           f' poster="{var["hero"]}"></video>')
                out.append(f'            <figcaption>{html.escape(var.get("anim_cap", ""))}</figcaption>')
                out.append("          </figure>")
            if os.path.exists(os.path.join(OUT, f"guide_{vid}_net.png")):
                out.append('          <figure class="guide-net">')
                out.append(f'            <img src="guide_{vid}_net.png" loading="lazy" decoding="async"'
                           f' alt="{html.escape(var["title"])}のネットワーク">')
                out.append("            <figcaption>組み上がったノードのつなぎ方（Houdini の画面）</figcaption>")
                out.append("          </figure>")
            elif os.path.exists(os.path.join(OUT, f"pr_{vid}_graph.png")):
                out.append('          <figure class="guide-net">')
                out.append(f'            <img src="pr_{vid}_graph.png" loading="lazy" decoding="async"'
                           f' alt="{html.escape(var["title"])}のノードのつなぎ方">')
                out.append("            <figcaption>ノードのつなぎ方（hip から描いた図）</figcaption>")
                out.append("          </figure>")
            out.append('          <ol class="steps">')
            for index, step in enumerate(var["steps"], start=1):
                out.append(f'            <li class="step" id="{vid}-step-{index}">')
                out.append('              <div class="step-body">')
                out.append(f'                <h4>{html.escape(step["title"])}<code>{html.escape(step["node"])}</code></h4>')
                out.append(f'                <p>{step["body"]}</p>')
                parm = f"guide_{vid}_p{index}_parm.png"
                if os.path.exists(os.path.join(OUT, parm)):
                    out.append('                <details class="step-ui">')
                    out.append("                  <summary>Houdini のパラメータ画面</summary>")
                    out.append(f'                  <img src="{parm}" loading="lazy" decoding="async" alt="{html.escape(step["title"])}のパラメータ">')
                    out.append("                </details>")
                out.append("              </div>")
                if step.get("img"):
                    out.append('              <figure class="step-figure">')
                    out.append(f'                <div class="frame-light"><img src="{step["img"]}" loading="lazy"'
                               f' decoding="async" alt="{html.escape(step["title"])}の結果"></div>')
                    if step.get("cap"):
                        out.append(f"                <figcaption>{html.escape(step['cap'])}</figcaption>")
                    out.append("              </figure>")
                out.append("            </li>")
            out.append("          </ol>")
            if var.get("traps"):
                out.append('          <p class="label">つまずくところ</p>')
                for trap in var["traps"]:
                    out.append('          <div class="trap">')
                    out.append(f'            <h4>{html.escape(trap["title"])}</h4>')
                    out.append(f'            <p>{trap["body"]}</p>')
                    out.append("          </div>")
            if var.get("compare"):
                out.append(f'          <p class="revision-ref">{var["compare"]}</p>')
            for rev in var.get("revisions", []):
                out.append('          <div class="revision">')
                out.append(f'            <h4>{html.escape(date_ja(rev["date"]))} に作り直した</h4>')
                if rev.get("why"):
                    out.append(f'            <p>{rev["why"]}</p>')
                out.append('            <ul>')
                for change in rev.get("changes", []):
                    out.append(f"              <li>{change}</li>")
                out.append("            </ul>")
                if rev.get("before"):
                    out.append('            <div class="revision-compare">')
                    for img, cap in ((rev["before"], "作り直す前"), (var["hero"], "作り直したあと")):
                        out.append('              <figure>')
                        out.append(f'                <img src="{img}" loading="lazy" decoding="async" alt="{cap}の仕上がり">')
                        out.append(f"                <figcaption>{cap}</figcaption>")
                        out.append("              </figure>")
                    out.append("            </div>")
                if rev.get("reference"):
                    out.append(f'            <p class="revision-ref">見比べた本物: {rev["reference"]}</p>')
                out.append("          </div>")
            out.append("        </section>")

        # 改訂の記録（2026-09-24）。作り直した実践は、前の版から何をなぜ変えたかを、前の仕上がりと並べて残す
        if guide.get("revisions"):
            out.append('        <section class="revisions" id="revisions">')
            out.append('          <p class="label">改訂の記録</p>')
            for rev in guide["revisions"]:
                out.append('          <div class="revision">')
                out.append(f'            <h4>{html.escape(date_ja(rev["date"]))} に作り直した</h4>')
                if rev.get("why"):
                    out.append(f'            <p>{rev["why"]}</p>')
                out.append('            <ul>')
                for change in rev.get("changes", []):
                    out.append(f"              <li>{change}</li>")
                out.append("            </ul>")
                if rev.get("before"):
                    out.append('            <div class="revision-compare">')
                    for img, cap in ((rev["before"], "作り直す前"), (guide["hero"], "作り直したあと")):
                        out.append('              <figure>')
                        out.append(f'                <img src="{img}" loading="lazy" decoding="async" alt="{cap}の仕上がり">')
                        out.append(f"                <figcaption>{cap}</figcaption>")
                        out.append("              </figure>")
                    out.append("            </div>")
                if rev.get("reference"):
                    out.append(f'            <p class="revision-ref">見比べた本物: {rev["reference"]}</p>')
                out.append("          </div>")
            out.append("        </section>")

        # 本物の画面（_net.png）があるときは、自動で描いた図は重複なので出さない
        graph = f'{prefix}_{guide["id"]}_graph.png'
        if os.path.exists(os.path.join(OUT, graph)) and                 not os.path.exists(os.path.join(OUT, f'{prefix}_{guide["id"]}_net.png')):
            out.append('        <p class="label">組み上がったノードグラフ</p>')
            out.append('        <div class="figs figs--wide">')
            out.append("          <figure>")
            out.append('            <div class="frame-dark">'
                       f'<img src="{graph}" loading="lazy"'
                       f' alt="{html.escape(guide["title"])}の'
                       'ノードネットワークの図"></div>')
            out.append("            <figcaption>ここまでを組んだ状態。"
                       "水色の点は表示フラグ。</figcaption>")
            out.append("          </figure>")
            out.append("        </div>")

        out.append('        <div class="guide-end">')
        out.append('          <p class="label">完成図</p>')
        out.append(f'          <img src="{guide["hero"]}" loading="lazy"'
                   f' decoding="async"'
                   f' alt="{html.escape(guide["title"])}の完成図">')
        out.append(f'          <p>{html.escape(guide.get("hero_cap", ""))}</p>')
        out.append('          <p class="guide-more">')
        if guide.get("exp") in anchors:
            anchor, log_key = anchors[guide["exp"]]
            out.append(f'            <a href="{urls[log_key]}#{anchor}">'
                       f'実験{guide["exp"]} の全文を読む</a>')
        if guide.get("hip"):
            out.append(f'            <a href="{GITHUB_RAW}{guide["hip"]}"'
                       ' target="_blank" rel="noopener noreferrer">'
                       f'{guide["hip"]}</a>')
        out.append("          </p>")
        out.append("        </div>")
        out.append("      </section>")
        sections[guide["id"]] = (guide["title"],
                                 link_terms_in("\n".join(out[section_start:])),
                                 prefix, guide)
    return sections


def render_exp_data(urls):
    """実験ポップアップの中身。out/*_report.json をそのまま流用する。

    Claude 版（Artifacts）は1つの版に置けるファイルが 512 までなので、
    ポップアップの図は1枚だけにする。GitHub Pages 版は全部載せる。
    """
    # 2026-09-23: カードは実験ログの記事を開くだけになったので、渡すのは行き先と題だけ
    payload = {item["no"]: {"title": item["title"],
                            "href": f'{urls[item.get("log", "log_pm")]}#{item["anchor"]}'}
               for item in DONE}
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/json" id="experiment-data">{body}</script>'
    slim = str(urls.get("home", "")).startswith("http")
    payload = {}
    for item in DONE:
        shots = item.get("shots") or [item["thumb"]]
        entry = {
            "title": item["title"],
            "href": f'{urls[item.get("log", "log_pm")]}#{item["anchor"]}',
            "shots": shots[:1] if slim else shots,
            "summary": [html.escape(item["note"])],
            "points": [],
            "next": [],
        }
        path = os.path.join(OUT, item.get("report", f'{item["no"]}_report.json'))
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fp:
                rep = json.load(fp)
            entry["title"] = rep.get("title", entry["title"])
            # レポートの **太字** は、ポップアップでも <strong> にする
            summary = [re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p.strip())
                       for p in rep.get("summary", "").split("\n\n")]
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
            else:
                # 実験で動かしていないものは、そうと分かるようにしておく。
                # 名前・つまみ・既定値は Houdini 本体から取っているので確か。
                out.append('            <p class="node-unused">まだ実験では動かしていない。'
                           f'名前とつまみは {HOU_VERSION} で確認した。</p>')
            out.append("          </div>")
            if node.get("img"):
                out.append('          <div class="node-shot">')
                out.append(f'            <img src="{node["img"]}" loading="lazy"'
                           f' decoding="async"'
                           f' alt="{html.escape(node["name"])}の結果">')
                if node.get("cap"):
                    out.append(f'            <span>{html.escape(node["cap"])}</span>')
                out.append("          </div>")
            out.append("        </article>")
        out.append("      </div>")
    return "\n".join(out)


def report_summary(no, limit=240):
    """実験のレポートの要約の頭。検索で本文にも当てるため。"""
    path = os.path.join(OUT, f"{no}_report.json")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fp:
        text = json.load(fp).get("summary", "").replace("**", "")
    return re.sub(r"\s+", " ", text)[:limit]


def report_facts(no, count=3, limit=420):
    """実験の「わかったこと」の頭。AI に答えさせるときの根拠にする。

    検索の点数には使わない（語が多すぎて何にでも当たるため）。
    数字はここからそのまま引かせるので、タグを外すだけで書き換えない。
    """
    path = os.path.join(OUT, f"{no}_report.json")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fp:
        notes = json.load(fp).get("notes", [])[:count]
    text = " / ".join(re.sub(r"<[^>]+>", "", n) for n in notes)
    return re.sub(r"\s+", " ", text)[:limit]


def render_search_data(data, nodes, guides, urls, tabs):
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
            "href": f'{urls[item.get("log", "log_pm")]}#{item["anchor"]}',
            "exp": item["no"],
            "tags": item.get("tags", []),
            "body": report_summary(item["no"]),
            "facts": report_facts(item["no"]),
        })

    # 効率化の項目。「重い」「遅い」で探したときの行き先
    for group in load_speed()["groups"]:
        for index, tip in enumerate(group["tips"]):
            items.append({
                "kind": "効率化",
                "label": tip["rule"],
                "note": tip["evidence"][:70],
                "href": panel_url(urls, "speed"),
                "tab": "speed",
                "anchor": f'speed-{group["id"]}-{index}',
                "tags": ["速さ", "効率", "時間", group["title"]],
                "body": tip["evidence"],
            })

    # 手順ページが索引に入っていなかった。「作り方」を探している人が
    # いちばん先に当てたいものなので、実験の次に置く
    for guide in guides["guides"]:
        steps = " ".join(s["title"] for s in guide.get("steps", []))
        traps = " ".join(t["title"] for t in guide.get("traps", []))
        items.append({
            "kind": "実践",
            "label": guide["title"],
            "note": guide["lede"][:70],
            "href": guide_url(urls, guide["id"]),
            "tab": "guides",
            "guide": guide["id"],
            "body": f"{steps} {traps}",
        })

    index = -1
    for group in nodes["groups"]:
        for node in group["nodes"]:
            index += 1
            items.append({
                "kind": "ノード",
                "label": node["name"],
                "note": node["one"],
                "href": panel_url(urls, "nodes"),
                "tab": "nodes",
                "anchor": f"node-{index}",
                "body": f'{node.get("what", "")} {node.get("gotcha", "")}',
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
                "body": entry["def"],
            })

    for panel, label in TABS:
        items.append({"kind": "ページ", "label": label,
                      "note": "タブを開く", "href": panel_url(urls, panel),
                      "tab": panel})
    items.append({"kind": "ページ", "label": "実験ログ（全文）",
                  "note": "すべての実験の記録", "href": urls["log"]})
    items.append({"kind": "ページ", "label": BRAND,
                  "note": "親のページ。部の入口",
                  "href": urls.get("parent") or PARENT_URLS["pages"],
                  "body": "サイトウプロダクション SP 部 映像制作部"})

    with open(SYNONYMS, encoding="utf-8") as fp:
        synonyms = json.load(fp)
    syn = {"groups": [{"label": g["label"], "words": g["words"],
                       "expand": g["expand"]} for g in synonyms["groups"]],
           "fillers": synonyms["fillers"]}

    body = json.dumps({"tabs": False, "items": items, "syn": syn},
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


def strip_panels(page, keep):
    """このページが持たないパネルを、ひな形から取り除く。

    パネルは <section class="panel" id="panel-XXX" …> … </section> の1かたまり。
    ひな形の中では入れ子になっていないので、開きから閉じまでを素直に切れる。
    取り除くと中の差し込み札も消えるので、その画像はページに入らない
    （これがファイル数を下げる仕組み）。
    """
    while True:
        target = None
        for match in re.finditer(
                r'    <section class="panel" id="panel-(\w+)"', page):
            if match.group(1) not in keep:
                target = match
                break
        if target is None:
            return page
        start = target.start()
        close = page.index("    </section>", start) + len("    </section>")
        # 改行の書き方（LF か CRLF）に左右されないよう、その行の終わりまで進める
        while close < len(page) and page[close] in "\r\n":
            close += 1
        # 消すたびに位置がずれるので、毎回もう一度探し直す
        page = page[:start] + page[close:]


# GitHub Pages 版では、どのページにも入る大きなデータ（検索・用語・ノード・実験）を
# 別のファイルに出し、ページからは読み込むだけにする。同じ中身は同じファイル名になるので、
# 2ページ目からはブラウザに残った分が使われる（1ページ約1MB → 軽く。2026-09-23）
SHARED_DATA_IDS = ("glossary-data", "search-data", "node-data", "experiment-data")
SHARED_WRITTEN = set()


def externalize_data(page, out_dir):
    folder = os.path.join(out_dir, "data")
    os.makedirs(folder, exist_ok=True)

    def swap(match):
        ident, body = match.group(1), match.group(2)
        digest = hashlib.sha1(body.encode("utf-8")).hexdigest()[:10]
        name = f"{ident}-{digest}.js"
        path = os.path.join(folder, name)
        if name not in SHARED_WRITTEN:
            code = ("(function(){var s=document.currentScript,e=document.createElement('script');"
                    f"e.type='application/json';e.id={json.dumps(ident)};e.textContent="
                    + json.dumps(body, ensure_ascii=False)
                    + ";s.parentNode.insertBefore(e,s);})();\n")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(code)
            SHARED_WRITTEN.add(name)
        return f'<script src="data/{name}"></script>'

    pattern = re.compile(r'<script type="application/json" id="(' + "|".join(SHARED_DATA_IDS)
                         + r')">(.*?)</script>', re.S)
    return pattern.sub(swap, page)


def clean_shared_data(out_dir):
    """前の版で書いたデータのうち、今回どのページも使わなかったものを消す。"""
    folder = os.path.join(out_dir, "data")
    if not os.path.isdir(folder):
        return
    for name in os.listdir(folder):
        if name.endswith(".js") and name not in SHARED_WRITTEN:
            os.remove(os.path.join(folder, name))


def render(template_name, out_dir, out_name, active, tabs, urls,
           data, nodes, guides, works, requests, css, links_body,
           popover, chrome, bundle=None, extra=None):
    with open(os.path.join(SITE, template_name), encoding="utf-8") as fp:
        page = fp.read()
    # 1本ずつのページ（実践）の差し込み。共通の差し込みより先に埋める
    for needle, value in (extra or {}).items():
        page = page.replace(needle, value)

    panels = PAGE_PANELS.get(bundle) if bundle else None
    if panels:
        page = strip_panels(page, set(panels))
    if template_name in DOC_TEMPLATES:
        page = as_doc_layout(page, DOC_TEMPLATES[template_name], urls)
        page = columnize(page)

    # 実験ポップアップの中身はパネルの外にあるので、実験を持つページだけに入れる
    exp_data = render_exp_data(urls) if (not panels or "experiments" in panels) \
        else '<script type="application/json" id="experiment-data">{}</script>'

    for needle, value in (
        ("<!--CSS-->", css),
        ("<!--NAV-->", render_nav(active, tabs, urls, panels)
         # 実践の1本ずつのページは、題まで入った自分の現在地を本文の頭に持っている
         + ("" if template_name == "guide_template.html"
            else "\n" + render_crumbs(active, tabs, urls, panels,
                                       doc=template_name in DOC_TEMPLATES))),
        ("<!--THUMBS-->", render_thumbs(urls)),
        ("<!--EXP_DATA-->", exp_data),
        ("<!--NODES-->", render_nodes(nodes, urls)),
        ("<!--GUIDES-->", render_guides(guides, works, urls)),
        ("<!--GUIDE_CARDS-->", render_guide_cards(guides)),
        ("<!--WORK_CARDS-->", render_work_cards(works)),
        ("<!--STRIP-->", render_strip(guides, urls)),
        ("<!--DECK-->", render_deck(urls)),
        ("<!--GUIDE_COUNT-->", str(len(guides["guides"]))),
        ("<!--REQUESTS-->", render_requests(requests)),
        ("<!--REQUEST_COUNT-->", str(len(requests["requests"]))),
        ("<!--ISSUE_NEW-->", ISSUE_NEW),
        ("<!--WORK_COUNT-->", str(len(works["works"]))),
        ("<!--NODE_NAV-->", render_node_nav(nodes)),
        ("<!--LINKS_BODY-->", links_body),
        ("<!--GLOSSARY_SECTION-->", render_section(data)),
        ("<!--GLOSSARY_NAV-->", render_gloss_nav(data)),
        ("<!--GLOSSARY_DATA-->", render_data(data)),
        ("<!--POPOVER-->", render_node_data(nodes, urls) + "\n" + popover),
        ("<!--CHROME-->", (render_parent_footer(urls, guides, data, nodes)
                           if template_name == "sp_template.html"
                           else render_footer(urls, guides, data, nodes)) + "\n" + chrome),
        ("<!--MENU_CARDS-->", render_menu_cards(guides, urls, data, nodes)),
        ("<!--SEARCH_DATA-->",
         render_search_data(data, nodes, guides, urls, tabs)),
        ("<!--EXP_COUNT-->", str(len(DONE))),
        ("<!--EXP_TOTAL-->", str(len(DONE) + len(PLANNED) + len(PLANNED_FX))),
        ("<!--NODE_COUNT-->", str(count_nodes(nodes))),
        ("<!--TERM_COUNT-->", str(count_terms(data))),
        ("<!--PAGE_TITLE-->", PAGE_TITLE.get(bundle, "Houdini 研究部")),
        ("<!--URL_GUIDES-->", panel_url(urls, "guides")),
        ("<!--URL_EXPERIMENTS-->", panel_url(urls, "experiments")),
        ("<!--URL_GLOSSARY-->", panel_url(urls, "glossary")),
        ("<!--URL_NODES-->", panel_url(urls, "nodes")),
        ("<!--NOTEBOOK_URL-->", NOTEBOOK_URL),
        ("<!--HOME_URL-->", urls["home"]),
        ("<!--LOG_URL-->", urls["log"]),
        ("<!--LOGPM_URL-->", urls["log_pm"]),
        ("<!--LOGFX_URL-->", urls["log_fx"]),
        ("<!--GLOSSARY_URL-->", urls["glossary"]),
        ("<!--LINKS_URL-->", urls["links"]),
        ("<!--NOTEBOOK_URL-->", NOTEBOOK_URL),
        ("<!--PARENT_NAV-->", render_parent_nav(urls)),
        ("<!--SHOWCASE-->", render_showcase(guides)),
        ("<!--SPEED-->", render_speed()),
        ("<!--SP_DEPTS-->", render_sp_depts(urls, guides, data)),
        ("<!--SP_RECENT-->", render_sp_recent(urls)),
        ("<!--SP_GUIDES-->", render_sp_guides(guides, urls)),
        ("<!--GUIDE_COUNT-->", str(len(guides["guides"]))),
        ("<!--VEX_RECIPES-->", render_vex_recipes() if "<!--VEX_RECIPES-->" in page else ""),
        ("<!--VEX_GUIDES-->", render_vex_guides(guides, urls) if "<!--VEX_GUIDES-->" in page else ""),
    ):
        page = page.replace(needle, value)

    leftover = re.findall(r"<!--[A-Z_]+-->", page)
    if leftover:
        raise SystemExit(f"{template_name}: placeholder left unfilled: {leftover}")

    unknown = sorted(set(re.findall(r'data-term="([^"]+)"', page)) - all_keys(data))
    if unknown:
        raise SystemExit(f"{template_name}: 用語集に存在しない用語: {unknown}")

    if active == "vex":
        page = link_vex_page(page, urls)

    if "entry" in page and 'id="exp' in page:
        page = inject_experiment_links(page, urls, nodes)
        page = retarget_exp_anchors(page)

    # ノード名のポップアップ。ノード解説そのもの（ref）は、つまみ名の <code> と
    # ノード名がぶつかるので付けない
    if bundle != "ref":
        page = link_nodes_in(page, node_index(nodes))

    if out_dir == DOCS:
        page = externalize_data(page, DOCS)

    if out_dir in (DOCS, ROOT):
        page = as_document(page, out_name if out_dir == DOCS else None)

    if out_dir == ROOT:
        # 画像は houdini-lab 側に置いたままなので、入口から見た道に直す。
        page = re.sub(r'src="(?=[\w.\-]+\.(?:png|gif)")', 'src="houdini-lab/', page)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, out_name)
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(page)
    return out_path


VEX_RECIPES = os.path.join(OUT, "vex_recipes.json")


def render_vex_recipes():
    """VEX 解説のお手本。コードは examples/vex_recipes.py が書き出した json から取る（手で写さない）。"""
    with open(VEX_RECIPES, encoding="utf-8") as fp:
        recipes = json.load(fp)
    out = []
    for i, r in enumerate(recipes, 1):
        pics = []
        if r.get("before"):
            pics.append(f'<figure><img src="vex_{r["id"]}_before.png" alt="Wrangle に入る前" loading="lazy">'
                        '<figcaption>Wrangle に入る前</figcaption></figure>')
        else:
            pics.append('<figure><div class="vx-box" style="height:100%;margin:0;display:flex;align-items:center;">'
                        '<p>入力は何もつながない。空っぽのところに、コードが点と線を作る。</p></div></figure>')
        pics.append(f'<figure><img src="vex_{r["id"]}.png" alt="{html.escape(r["title"])}の結果" loading="lazy">'
                    '<figcaption>Wrangle を通した後</figcaption></figure>')
        out.append(
            f'      <div class="vx-recipe" id="recipe-{r["id"]}">\n'
            f'        <h3>{i}. {html.escape(r["title"])}</h3>\n'
            f'        <p class="meta">Run Over: {html.escape(r["run"])} ／ 結果は 点 {r["points"]:,} 個・面（線）{r["prims"]:,} 枚</p>\n'
            f'        <p>{r["why"]}</p>\n'
            f'<pre><code>{html.escape(r["code"])}</code></pre>\n'
            f'        <div class="pics">{"".join(pics)}</div>\n'
            f'        <p>{r.get("result", "")}</p>\n'
            '      </div>')
    return "\n".join(out)


def render_vex_guides(guides, urls):
    """Wrangle を使っている実践の一覧（多い順）。"""
    rows = []
    for g in guides["guides"]:
        n = json.dumps(g, ensure_ascii=False).count("wrangle")
        if n:
            rows.append((n, g))
    rows.sort(key=lambda x: -x[0])
    items = "".join(f'<li><a href="{guide_url(urls, g["id"])}">{html.escape(g["title"])}<small>{n}</small></a></li>'
                    for n, g in rows)
    return f'      <ul class="vx-guides">{items}</ul>'


def link_vex_page(page, urls):
    """VEX 解説の本文の href="exp:NNN" を実験ログの記事へ、hip を GitHub へ向け、用語にポップアップを付ける。"""
    logs = {e["no"]: e["log"] for e in DONE}

    def exp(m):
        no = m.group(1)
        return f'href="{urls[logs.get(no, "log_pm")]}#exp{no}" target="_blank" rel="noopener"'
    page = re.sub(r'href="exp:(\d+)"', exp, page)
    page = page.replace('href="vex_recipes.hipnc"', f'href="{GITHUB_RAW}vex_recipes.hipnc"')
    return link_terms_in(page)


# 1本ずつの実践ページの説明文とカード画像（page_meta と sitemap が読む）
GUIDE_META = {}


def write_guide_pages(out_dir, urls, data, nodes, guides, works, requests, css,
                      links_body, popover, chrome):
    """実践と制作を1本ずつのページにする（2026-09-23。ポップアップは見づらかった）。

    頭に「いまどこにいるか」（ホーム › 実践 › 題）を出し、終わりに前後の実践への送りを置く。
    """
    sections = render_guide_sections(guides, works, urls)
    order = {"guide": [g["id"] for g in guides["guides"]],
             "work": [w["id"] for w in works["works"]]}
    written = 0
    for gid, (title, body, prefix, guide) in sections.items():
        kind_label, kind_panel = ("実践", "guides") if prefix == "guide" else ("制作", "works")
        crumbs = "\n".join([
            f'      <a href="{urls.get("parent") or PARENT_URLS["pages"]}">{BRAND}</a>',
            '      <span aria-hidden="true">›</span>',
            f'      <a href="{urls["home"]}">{DEPT}</a>',
            '      <span aria-hidden="true">›</span>',
            f'      <a href="{panel_url(urls, kind_panel)}">{kind_label}</a>',
            '      <span aria-hidden="true">›</span>',
            f'      <span aria-current="page">{html.escape(title)}</span>',
        ])
        # ページの主題なので、見出しは h1 にする（ポップアップのときは h3 だった）
        body = body.replace(f'          <h3>{html.escape(title)}</h3>',
                            f'          <h1>{html.escape(title)}</h1>', 1)
        ids = order[prefix]
        at = ids.index(gid)
        by_id = {g["id"]: g for g in guides["guides"] + works["works"]}
        pager = []
        if at > 0:
            prev = by_id[ids[at - 1]]
            pager.append(f'      <a class="prev" href="{guide_page(prev["id"])}">'
                         f'<small>← 前の{kind_label}</small>{html.escape(prev["title"])}</a>')
        if at + 1 < len(ids):
            nxt = by_id[ids[at + 1]]
            pager.append(f'      <a class="next" href="{guide_page(nxt["id"])}">'
                         f'<small>次の{kind_label} →</small>{html.escape(nxt["title"])}</a>')
        pager_html = ('    <nav class="guide-pager" aria-label="前後の' + kind_label + '">\n'
                      + "\n".join(pager) + "\n    </nav>") if pager else ""
        name = guide_page(gid)
        lede = re.sub(r"<[^>]+>", "", guide.get("lede", ""))
        GUIDE_META[name] = (lede[:120], guide.get("hero", OG_IMAGE))
        render("guide_template.html", out_dir, name, "guides", False, urls,
               data, nodes, guides, works, requests, css, links_body, popover, chrome,
               None, extra={"<!--GUIDE_TITLE-->": html.escape(title),
                            "<!--CRUMBS-->": crumbs,
                            "<!--GUIDE_BODY-->": body,
                            "<!--GUIDE_PAGER-->": pager_html})
        written += 1
    return written


def retarget_exp_anchors(page):
    """本文の <a href="#exp024"> のうち、この編に無い実験を正しい編へ向け直す。

    実験ログをモデリング編とエフェクト編に分けたので、本文のページ内リンクが
    もう片方の編を指していることがある。ページ内の移動では読み込み時の
    振り分けが効かないので、書き出す時点で直す。
    """
    here = set(re.findall(r'id="(exp\d+)"', page))
    where = {no: href for href, no in re.findall(r'"href":"([^"]*#exp(\d+))"', page)}

    def fix(match):
        no = match.group(1)
        if "exp" + no in here or no not in where:
            return match.group(0)
        return f'href="{where[no]}"'

    return re.sub(r'href="#exp(\d+)"', fix, page)


PAGES_BASE = "https://realestatewarrior.github.io/houdini-lab/"

# 検索結果や SNS のカードに出る説明。GitHub Pages 版だけに付ける。
PAGE_DESCRIPTION = {
    "index.html": "Houdini の機能を1つずつ動かし、結果を数値で記録する研究サイト。実験ログ、作り方の手順、ノードと用語の解説。",
    "practice.html": "Houdini で物を作る手順。地面に物を生やす、布を垂らす、煙を出す、水を落とすなど、測って確かめた作り方。",
    "reference.html": "Houdini のノード解説と用語集。つまみ名は実物から取り、実験で分かった落とし穴を添えている。",
    "log.html": "Houdini 実験ログ モデリング編。形・VEX・VDB・レンダリングなどを1つずつ動かし、測った数値で記録。",
    "log_fx.html": "Houdini 実験ログ エフェクト編。RBD・Vellum・POP・MPM・煙などのシミュレーションを測った数値で記録。",
    "glossary.html": "Houdini の用語辞典。実験で確かめた値を添えた日本語の説明。",
    "links.html": "Houdini を学ぶための参考リンク集。",
    "vex.html": "Houdini の VEX の解説。何をするものか、どこに書くか、書き方、お手本6つ、実験で測って分かったこと、落とし穴。",
}
OG_IMAGE = "thumb_008.png"


def favicon_link():
    svg = LOGO_SVG.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1) \
        .replace("currentColor", "#0071e3")
    return ('<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'
            + urllib.parse.quote(svg) + '">')


def page_meta(head, out_name):
    """説明文・SNS のカード・アイコンを <head> 用に組み立てる。"""
    found = re.search(r"<title>(.*?)</title>", head, re.S)
    title = found.group(1).strip() if found else DEPT
    if "<!--" in title:
        title = DEPT
    image = OG_IMAGE
    if out_name in GUIDE_META:
        desc, image = GUIDE_META[out_name]
        desc = html.escape(desc)
    else:
        desc = html.escape(PAGE_DESCRIPTION.get(out_name, PAGE_DESCRIPTION["index.html"]))
    url = PAGES_BASE + ("" if out_name == "index.html" else out_name)
    return "\n".join([
        f'<meta name="description" content="{desc}">',
        f'<link rel="canonical" href="{url}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{DEPT}">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{PAGES_BASE}{image}">',
        '<meta name="twitter:card" content="summary_large_image">',
        favicon_link(),
    ])


def write_sitemap():
    """docs/ に sitemap.xml と robots.txt を置く。"""
    pages = [spec[2] for spec in PAGES if spec[2]] + sorted(GUIDE_META)
    today = datetime.date.today().isoformat()
    rows = "".join(
        f"  <url><loc>{PAGES_BASE}{'' if name == 'index.html' else name}</loc>"
        f"<lastmod>{today}</lastmod></url>\n" for name in pages)
    with open(os.path.join(DOCS, "sitemap.xml"), "w", encoding="utf-8") as fp:
        fp.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                 f"{rows}</urlset>\n")
    with open(os.path.join(DOCS, "robots.txt"), "w", encoding="utf-8") as fp:
        fp.write(f"User-agent: *\nAllow: /\nSitemap: {PAGES_BASE}sitemap.xml\n")


def as_document(page, out_name=None):
    """docs/ 用に完全なHTMLに包む。

    Artifact 側は発行時に doctype と charset を付けてくれるが、GitHub Pages は
    ファイルをそのまま配る。charset が無いと日本語が化け、doctype が無いと
    ブラウザが互換モードになってレイアウトが崩れる。
    """
    # 属性が付くこともあるので、開きタグの途中までで探す
    split = page.find('<div class="layout"')
    if split == -1:
        raise SystemExit("レイアウトの開始位置が見つからない")
    head, body = page[:split].strip(), page[split:]
    return (
        "<!doctype html>\n"
        '<html lang="ja">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        + (page_meta(head, out_name) + "\n" if out_name else "")
        + f"{head}\n"
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
            names |= set(re.findall(r'"([\w.\-]+\.(?:png|gif|mp4))"', fp.read()))

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
    with open(GUIDES, encoding="utf-8") as fp:
        guides = json.load(fp)
    with open(WORKS, encoding="utf-8") as fp:
        works = json.load(fp)
    with open(REQUESTS, encoding="utf-8") as fp:
        requests = json.load(fp)
    with open(os.path.join(SITE, "base.css"), encoding="utf-8") as fp:
        css = fp.read()
    with open(os.path.join(SITE, "partial_links.html"), encoding="utf-8") as fp:
        links_body = fp.read()
    with open(os.path.join(SITE, "partial_popover.html"), encoding="utf-8") as fp:
        popover = fp.read()
    with open(os.path.join(SITE, "partial_chrome.html"), encoding="utf-8") as fp:
        chrome = fp.read()

    for template_name, site_out, docs_out, active, tabs, bundle in PAGES:
        render(template_name, SITE, site_out, active, tabs,
               ARTIFACT_URLS, data, nodes, guides, works, requests, css,
               links_body, popover, chrome, bundle)
        if docs_out:
            render(template_name, DOCS, docs_out, active, tabs,
                   PAGES_URLS, data, nodes, guides, works, requests, css,
                   links_body, popover, chrome, bundle)

    # 実践と制作を1本ずつのページに（site/ と docs/ の両方）
    guide_pages = 0
    for out_dir, urls in ((SITE, ARTIFACT_URLS), (DOCS, PAGES_URLS)):
        guide_pages = write_guide_pages(out_dir, urls, data, nodes, guides, works, requests,
                                        css, links_body, popover, chrome)

    # 親ページ。クローンが置いてあるときだけ書き出す。
    root_note = "置き場が無いので飛ばした"
    if os.path.isdir(ROOT):
        render("sp_template.html", ROOT, "index.html", "sp", False,
               ROOT_URLS, data, nodes, guides, works, requests, css,
               links_body, popover, chrome, None)
        root_note = os.path.join(ROOT, "index.html")

    write_sitemap()
    clean_shared_data(DOCS)

    # GitHub Pages に Jekyll 処理をさせない
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fp:
        fp.write("")

    total, copied = copy_images()
    docs_count = sum(1 for spec in PAGES if spec[2])
    print(f"site/ に {len(PAGES)} ページ、docs/ に {docs_count} ページ生成（ほかに実践・制作 {guide_pages} ページずつ）")
    print(f"親ページ: {root_note}")
    print(f"ノード {count_nodes(nodes)} 件 / 用語 {count_terms(data)} 件")
    print(f"画像 {total} 件（うち {copied} 件をコピー）")


if __name__ == "__main__":
    main()
