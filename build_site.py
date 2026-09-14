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
OUT = os.path.join(HERE, "out")
GLOSSARY = os.path.join(HERE, "glossary.json")
NODES = os.path.join(HERE, "nodes.json")
GUIDES = os.path.join(HERE, "guides.json")

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/9e4a30fe-e11f-455d-8179-df0765435022"
GITHUB_RAW = ("https://github.com/RealEstateWarrior/houdini-lab/raw/main/out/")

# 発行済みArtifactのURL。新規発行したらここを更新して再ビルドする。
ARTIFACT_URLS = {
    "home": "https://claude.ai/code/artifact/e6fa0709-06ab-4ab9-9591-ed52742a88fa",
    "log": "https://claude.ai/code/artifact/f9b31321-23e5-4e7c-b6bc-ad2bcf9c1129",
    "log_pm": "https://claude.ai/code/artifact/f9b31321-23e5-4e7c-b6bc-ad2bcf9c1129",
    "log_fx": "https://claude.ai/code/artifact/087548d5-0c09-40b5-8e2e-7bfc084e1f0c",
    "glossary": "https://claude.ai/code/artifact/5236e98a-7bc1-4fd0-b523-856c80513868",
    "links": "https://claude.ai/code/artifact/0085c322-cc2d-4d35-ac08-f39eb4e63f4f",
}

# GitHub Pages 版。ルートがハブになるよう index.html をハブに割り当てる。
PAGES_URLS = {
    "home": "index.html",
    "log": "log.html",
    "log_pm": "log.html",
    "log_fx": "log_fx.html",
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
    ("guides", "手順"),
    ("experiments", "実験"),
    ("nodes", "ノード解説"),
    ("glossary", "用語集"),
    ("links", "参考リンク"),
]

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
]

PLANNED = []

PLANNED_FX = [
    {"no": "048", "title": "毛を揺らす",
     "note": "Vellum で毛をシミュレーションする。重力と風でどう動くか"},
]

PAGES = [
    # template, site出力, docs出力, ナビの現在位置, タブ形式か
    ("home_template.html", "home.html", "index.html", "home", True),
    ("log_pm_template.html", "index.html", "log.html", "log", False),
    ("log_fx_template.html", "log_fx.html", "log_fx.html", "log", False),
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
    out.append(f'        <li><a href="{NOTEBOOK_URL}" class="nav-ext"'
               ' target="_blank" rel="noopener noreferrer">Notebook</a></li>')
    out.append("      </ul>")
    out.append('      <button type="button" class="nav-icon" id="search-open"'
               ' aria-label="サイト内を検索">' + SEARCH_SVG + "</button>")
    out.append('      <button type="button" class="nav-icon nav-burger" id="menu-open"'
               ' aria-label="メニューを開く" aria-expanded="false">'
               + BURGER_SVG + "</button>")
    out.append("    </div>")
    out.append("  </nav>")
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
        out.append(f'          <span class="thumb-img"><img src="{item["thumb"]}"'
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
        out.append(f'            <span class="thumb-no">手順 {index:02d}'
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


def render_guides(guides, urls):
    """手順の中身。ふだんは隠しておき、カードを押したらポップアップへ移す。

    1段ごとに図を置く。最後に完成図と、組み上がったノードグラフを出して、
    詳しく知りたい人だけが実験ログへ行けるようにする。
    """
    anchors = {item["no"]: (item["anchor"], item.get("log", "log_pm"))
               for item in DONE}
    out = ['      <div id="guide-store" hidden>']
    for guide in guides["guides"]:
        section_start = len(out)
        out.append(f'      <section class="guide" id="guide-{guide["id"]}">')
        out.append('        <div class="guide-hero">')
        out.append(f'          <img src="{guide["hero"]}"'
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
        out.append("        </div>")

        out.append('        <ol class="steps">')
        for step in guide["steps"]:
            out.append('          <li class="step">')
            out.append('            <div class="step-body">')
            out.append(f'              <h4>{html.escape(step["title"])}'
                       f'<code>{html.escape(step["node"])}</code></h4>')
            out.append(f'              <p>{step["body"]}</p>')
            out.append("            </div>")
            if step.get("img"):
                out.append('            <figure class="step-figure">')
                out.append('              <div class="frame-light">'
                           f'<img src="{step["img"]}"'
                           f' alt="{html.escape(step["title"])}の結果"></div>')
                if step.get("cap"):
                    out.append(f"              <figcaption>{html.escape(step['cap'])}"
                               "</figcaption>")
                out.append("            </figure>")
            out.append("          </li>")
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
                               f'<img src="{trap["img"]}"'
                               f' alt="{html.escape(trap["title"])}"></div>')
                    if trap.get("cap"):
                        out.append(f"            <figcaption>"
                                   f"{html.escape(trap['cap'])}</figcaption>")
                    out.append("          </figure>")
                out.append("        </div>")

        graph = f'guide_{guide["id"]}_graph.png'
        if os.path.exists(os.path.join(OUT, graph)):
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
        out.append(f'          <img src="{guide["hero"]}"'
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
    """実験ポップアップの中身。out/*_report.json をそのまま流用する。"""
    payload = {}
    for item in DONE:
        entry = {
            "title": item["title"],
            "href": f'{urls[item.get("log", "log_pm")]}#{item["anchor"]}',
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
            "href": f'{urls[item.get("log", "log_pm")]}#{item["anchor"]}',
            "exp": item["no"],
            "tags": item.get("tags", []),
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
           data, nodes, guides, css, links_body, popover, chrome):
    with open(os.path.join(SITE, template_name), encoding="utf-8") as fp:
        page = fp.read()

    for needle, value in (
        ("<!--CSS-->", css),
        ("<!--NAV-->", render_nav(active, tabs, urls)),
        ("<!--THUMBS-->", render_thumbs(urls)),
        ("<!--EXP_DATA-->", render_exp_data(urls)),
        ("<!--NODES-->", render_nodes(nodes, urls)),
        ("<!--GUIDES-->", render_guides(guides, urls)),
        ("<!--GUIDE_CARDS-->", render_guide_cards(guides)),
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
        ("<!--LOGPM_URL-->", urls["log_pm"]),
        ("<!--LOGFX_URL-->", urls["log_fx"]),
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

    if "entry" in page and 'id="exp' in page:
        page = inject_experiment_links(page, urls, nodes)

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
    with open(GUIDES, encoding="utf-8") as fp:
        guides = json.load(fp)
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
               ARTIFACT_URLS, data, nodes, guides, css, links_body,
               popover, chrome)
        render(template_name, DOCS, docs_out, active, tabs,
               PAGES_URLS, data, nodes, guides, css, links_body,
               popover, chrome)

    # GitHub Pages に Jekyll 処理をさせない
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fp:
        fp.write("")

    total, copied = copy_images()
    print(f"site/ と docs/ に {len(PAGES)} ページずつ生成")
    print(f"ノード {count_nodes(nodes)} 件 / 用語 {count_terms(data)} 件")
    print(f"画像 {total} 件（うち {copied} 件をコピー）")


if __name__ == "__main__":
    main()
