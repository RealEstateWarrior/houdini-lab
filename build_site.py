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
    "home": "https://claude.ai/code/artifact/e6fa0709-06ab-4ab9-9591-ed52742a88fa",
    "log": "https://claude.ai/code/artifact/f9b31321-23e5-4e7c-b6bc-ad2bcf9c1129",
    "log_pm": "https://claude.ai/code/artifact/f9b31321-23e5-4e7c-b6bc-ad2bcf9c1129",
    "log_fx": "https://claude.ai/code/artifact/087548d5-0c09-40b5-8e2e-7bfc084e1f0c",
    "glossary": "https://claude.ai/code/artifact/5236e98a-7bc1-4fd0-b523-856c80513868",
    "links": "https://claude.ai/code/artifact/0085c322-cc2d-4d35-ac08-f39eb4e63f4f",
    "parent": "https://claude.ai/artifact/1ayTdyUEY1avfBfUARaiLo",
}

# GitHub Pages 版。ルートがハブになるよう index.html をハブに割り当てる。
PAGES_URLS = {
    "home": "index.html",
    "log": "log.html",
    "log_pm": "log.html",
    "log_fx": "log_fx.html",
    "glossary": "glossary.html",
    "links": "links.html",
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
        ]),
    ]),
]

# その行き先にいるときに印を付けるための対応表
ACTIVE_OF = {"glossary": "解説", "links": "実験", "log": "実験"}

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
]

PLANNED = []

PLANNED_FX = []

PAGES = [
    # template, site出力, docs出力, ナビの現在位置, タブ形式か
    # 親ページは docs/ には出さない。GitHub 版は別リポジトリの入口に置く。
    ("sp_template.html", "sp.html", None, "sp", False),
    ("home_template.html", "home.html", "index.html", "home", True),
    ("log_pm_template.html", "index.html", "log.html", "log", False),
    ("log_fx_template.html", "log_fx.html", "log_fx.html", "log", False),
    ("glossary_template.html", "glossary.html", "glossary.html", "glossary", False),
    ("links_template.html", "links.html", "links.html", "links", False),
]


def render_nav(active, tabs, urls):
    """上部のバー。どのページでも同じ並びにする。

    左端は SP のロゴだけ。押すと親の Saito Production へ戻る。
    続くのは4つの見出しで、乗せると下にパネルが降りる。
    1列目は大きく、2列目から先は小さく出す。
    """
    parent = urls.get("parent") or PARENT_URLS["pages"]
    out = [
        '  <nav class="sidenav" aria-label="サイト内の移動">',
        '    <div class="nav-inner">',
        f'      <a class="logo" href="{parent}"'
        f' aria-label="{BRAND}（親のページへ）">',
        f"        {LOGO_SVG}",
        "      </a>",
        '      <ul class="nav-menu">',
    ]

    def control(target, label, extra=""):
        """行き先ひとつ。ハブではタブの切り替え、それ以外はリンクになる。"""
        if target.startswith("@"):
            href = urls[target[1:]]
            return f'<a href="{href}"{extra}>{html.escape(label)}</a>'
        if tabs:
            return (f'<button type="button" class="nav-tab" role="tab"'
                    f' id="tab-{target}" data-panel="{target}"'
                    f' aria-controls="panel-{target}"'
                    f' aria-selected="false"{extra}>{html.escape(label)}</button>')
        return (f'<a href="{urls["home"]}#{target}"{extra}>'
                f"{html.escape(label)}</a>")

    for index, (head, target, columns) in enumerate(MENU):
        current = ' aria-current="page"' if ACTIVE_OF.get(active) == head else ""
        if not columns:
            out.append("        <li>")
            out.append("          " + control(target, head, current))
            out.append("        </li>")
            continue

        out.append('        <li class="nav-drop">')
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

    out.append(f'        <li><a href="{NOTEBOOK_URL}" class="nav-ext"'
               ' target="_blank" rel="noopener noreferrer">Notebook</a></li>')
    out.append("      </ul>")
    out.append('      <button type="button" class="nav-icon" id="search-open"'
               ' aria-label="Saito Production 全体を検索">' + SEARCH_SVG + "</button>")
    out.append('      <button type="button" class="nav-icon nav-burger" id="menu-open"'
               ' aria-label="メニューを開く" aria-expanded="false">'
               + BURGER_SVG + "</button>")
    out.append("    </div>")
    out.append("  </nav>")
    return "\n".join(out)


def render_parent_nav(urls):
    """親（Saito Production）のバー。ロゴと部だけの1段。"""
    out = [
        '  <nav class="sidenav" aria-label="サイト内の移動">',
        '    <div class="nav-inner">',
        f'      <a class="logo" href="#top" aria-label="{BRAND}">',
        f"        {LOGO_SVG}",
        "      </a>",
        '      <ul class="nav-depts">',
    ]
    for dept_id, label, ready in DEPARTMENTS:
        if ready:
            out.append(f'        <li><a href="{urls["home"]}">'
                       f"{html.escape(label)}</a></li>")
        else:
            out.append(f'        <li><span class="soon">{html.escape(label)}'
                       "<small>準備中</small></span></li>")
    out.append("      </ul>")
    out.append('      <button type="button" class="nav-icon" id="search-open"'
               ' aria-label="Saito Production 全体を検索">' + SEARCH_SVG + "</button>")
    out += ["    </div>", "  </nav>"]
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
        out.append(f'        <a class="tile" href="{urls["home"]}#guides">')
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
           "<p>カードを押すと要点が開く。タグで絞り込める。</p></div>"]
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
    pattern = re.compile(
        r'(<article class="entry[^"]*" id="exp(\d+)">.*?<p class="path">.*?</p>)',
        re.S)

    def build(match):
        whole, no = match.group(1), match.group(2)
        rows = []
        chips = [f'<a href="{urls["home"]}#nodes">{html.escape(name)}</a>'
                 for name, _ in table.get(no, [])]
        if chips:
            rows.append('        <p class="usedby">'
                        '<span class="usedby-tag">使ったノード</span>'
                        + "".join(chips) + "</p>")
        if hips.get(no):
            rows.append('        <p class="usedby">'
                        '<span class="usedby-tag">シーンファイル</span>'
                        f'<a href="{GITHUB_RAW}{hips[no]}"'
                        ' target="_blank" rel="noopener noreferrer">'
                        f'{hips[no]}</a></p>')
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


def render_guide_cards(guides):
    """手順の一覧。カードを押すとポップアップで開く。

    手順が増えてきたので、全部を縦に並べると目当てのものに辿り着けない。
    実験タブと同じで、まず一覧、押したら中身。
    """
    out = ['      <div class="thumbs" id="guide-cards">']
    for index, guide in enumerate(guides["guides"], start=1):
        facts = dict(guide.get("facts") or [])
        chips = [f'{len(guide["steps"])}ステップ']
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
                   + "".join(f"<span>{html.escape(c)}</span>" for c in chips)
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


def render_strip(guides):
    """ホームの帯。小さな札が横へ流れる。

    乗せると止まり、押すとその実践がそのまま開く。
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
            out.append('          <button type="button" class="chip-card"'
                       f' data-guide="{guide["id"]}"{hidden}>')
            out.append(f'            <img src="{guide["hero"]}" alt=""'
                       ' loading="lazy" decoding="async">')
            out.append(f'            <span>{html.escape(guide["title"])}</span>')
            out.append("          </button>")
    out.append("        </div>")
    out.append("      </div>")
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
    """実践と制作の中身。ふだんは隠しておき、カードを押したらポップアップへ移す。

    1段ごとに図を置く。最後に完成図と、組み上がったノードグラフを出して、
    詳しく知りたい人だけが実験ログへ行けるようにする。
    """
    anchors = {item["no"]: (item["anchor"], item.get("log", "log_pm"))
               for item in DONE}
    out = ['      <div id="guide-store" hidden>']
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
        out.append(f'          <p class="guide-lede">{guide["lede"]}</p>')
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
        out.append("        </div>")

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

        out.append('        <ol class="steps">')
        for index, step in enumerate(guide["steps"], start=1):
            out.append('          <li class="step">')
            out.append('            <div class="step-body">')
            out.append(f'              <h4>{html.escape(step["title"])}'
                       f'<code>{html.escape(step["node"])}</code></h4>')
            out.append(f'              <p>{step["body"]}</p>')
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
        out[section_start:] = [link_terms_in("\n".join(out[section_start:]))]
    out.append("      </div>")
    out.append("")
    out.append('      <div class="modal modal--wide" id="guide-modal" hidden>')
    out.append('        <div class="modal-card">')
    out.append('          <button type="button" class="modal-close"'
               ' id="guide-close" aria-label="閉じる">&#10005;</button>')
    out.append('          <div class="modal-body" id="guide-modal-body"></div>')
    out.append("        </div>")
    out.append("      </div>")
    return "\n".join(out)


def render_exp_data(urls):
    """実験ポップアップの中身。out/*_report.json をそのまま流用する。

    Claude 版（Artifacts）は1つの版に置けるファイルが 512 までなので、
    ポップアップの図は1枚だけにする。GitHub Pages 版は全部載せる。
    """
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
        text = json.load(fp).get("summary", "")
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
                "href": f'{urls["home"]}#speed',
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
            "href": f'{urls["home"]}#guide-{guide["id"]}',
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
                "href": f'{urls["home"]}#nodes',
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
                      "note": "タブを開く", "href": f'{urls["home"]}#{panel}',
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

    body = json.dumps({"tabs": bool(tabs), "items": items, "syn": syn},
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
           data, nodes, guides, works, requests, css, links_body,
           popover, chrome):
    with open(os.path.join(SITE, template_name), encoding="utf-8") as fp:
        page = fp.read()

    for needle, value in (
        ("<!--CSS-->", css),
        ("<!--NAV-->", render_nav(active, tabs, urls)),
        ("<!--THUMBS-->", render_thumbs(urls)),
        ("<!--EXP_DATA-->", render_exp_data(urls)),
        ("<!--NODES-->", render_nodes(nodes, urls)),
        ("<!--GUIDES-->", render_guides(guides, works, urls)),
        ("<!--GUIDE_CARDS-->", render_guide_cards(guides)),
        ("<!--WORK_CARDS-->", render_work_cards(works)),
        ("<!--STRIP-->", render_strip(guides)),
        ("<!--REQUESTS-->", render_requests(requests)),
        ("<!--REQUEST_COUNT-->", str(len(requests["requests"]))),
        ("<!--ISSUE_NEW-->", ISSUE_NEW),
        ("<!--WORK_COUNT-->", str(len(works["works"]))),
        ("<!--NODE_NAV-->", render_node_nav(nodes)),
        ("<!--LINKS_BODY-->", links_body),
        ("<!--GLOSSARY_SECTION-->", render_section(data)),
        ("<!--GLOSSARY_NAV-->", render_gloss_nav(data)),
        ("<!--GLOSSARY_DATA-->", render_data(data)),
        ("<!--POPOVER-->", popover),
        ("<!--CHROME-->", chrome),
        ("<!--SEARCH_DATA-->",
         render_search_data(data, nodes, guides, urls, tabs)),
        ("<!--EXP_COUNT-->", str(len(DONE))),
        ("<!--EXP_TOTAL-->", str(len(DONE) + len(PLANNED) + len(PLANNED_FX))),
        ("<!--NODE_COUNT-->", str(count_nodes(nodes))),
        ("<!--TERM_COUNT-->", str(count_terms(data))),
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
    ):
        page = page.replace(needle, value)

    leftover = re.findall(r"<!--[A-Z_]+-->", page)
    if leftover:
        raise SystemExit(f"{template_name}: placeholder left unfilled: {leftover}")

    unknown = sorted(set(re.findall(r'data-term="([^"]+)"', page)) - all_keys(data))
    if unknown:
        raise SystemExit(f"{template_name}: 用語集に存在しない用語: {unknown}")

    if "entry" in page and 'id="exp' in page:
        page = inject_experiment_links(page, urls, nodes)

    if out_dir in (DOCS, ROOT):
        page = as_document(page)

    if out_dir == ROOT:
        # 画像は houdini-lab 側に置いたままなので、入口から見た道に直す。
        page = re.sub(r'src="(?=[\w.\-]+\.(?:png|gif)")', 'src="houdini-lab/', page)

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

    for template_name, site_out, docs_out, active, tabs in PAGES:
        render(template_name, SITE, site_out, active, tabs,
               ARTIFACT_URLS, data, nodes, guides, works, requests, css, links_body,
               popover, chrome)
        if docs_out:
            render(template_name, DOCS, docs_out, active, tabs,
                   PAGES_URLS, data, nodes, guides, works, requests, css, links_body,
                   popover, chrome)

    # 親ページ。クローンが置いてあるときだけ書き出す。
    root_note = "置き場が無いので飛ばした"
    if os.path.isdir(ROOT):
        render("sp_template.html", ROOT, "index.html", "sp", False,
               ROOT_URLS, data, nodes, guides, works, requests, css, links_body,
               popover, chrome)
        root_note = os.path.join(ROOT, "index.html")

    # GitHub Pages に Jekyll 処理をさせない
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fp:
        fp.write("")

    total, copied = copy_images()
    print(f"site/ に {len(PAGES)} ページ、docs/ に {len(PAGES) - 1} ページ生成")
    print(f"親ページ: {root_note}")
    print(f"ノード {count_nodes(nodes)} 件 / 用語 {count_terms(data)} 件")
    print(f"画像 {total} 件（うち {copied} 件をコピー）")


if __name__ == "__main__":
    main()
