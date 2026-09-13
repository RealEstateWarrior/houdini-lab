# Houdini 実験室

Houdiniのノードネットワークを hython で実際に組み、結果を**接続図・レンダ画像・実測値**として
記録していくプロジェクト。重点はプロシージャルモデリングとエフェクト。

**ここに書いてある数値はすべて実行して得た値で、推測は含まない。**

## 方針

- **Houdiniの挙動は実測を正とする。** ネットの情報は出典を確認し、動かせるものは動かして確かめる。
  実際に「Apprenticeでは hython が使えない」「mountain のパラメータ名は `roughness`」は
  どちらも誤りだった（どちらも実測で判明）
- **測り方も記録する。** 実験003では最初に選んだ指標（表面積）が不適切で途中で切り替えた。
  失敗した測り方も残す
- **仮説は否定できる条件で試す。** 「縮む原因は平滑化」は平滑化しない Bilinear で、
  「oct が効かないのは点数のせい」は点数を増やして予測どおりになるかで確かめた

## 実行方法

Houdini 21.0.x の hython が必要（Apprentice で動作確認済み）。

```
"C:\Program Files\Side Effects Software\Houdini 21.0.700\bin\hython.exe" examples\005_noise_basis.py
```

実験スクリプトは `out/` に接続図用JSON・プレビュー画像・統計JSONを書き出す。そこから:

```
python graph_report.py out\005_graph.json out\005_graph.png   # 接続図の画像
python report_pdf.py out\005_report.json out\005_report.pdf   # レポートPDF
python build_site.py                                          # サイト生成
```

`graph_report.py` と `report_pdf.py` と `build_site.py` は Houdini に依存しないので、
通常の Python（Pillow と reportlab が必要）で動く。

## ファイル構成

| パス | 役割 |
|---|---|
| `examples/` | 実験スクリプト。1ファイル1実験で、実行すれば結果を再現できる |
| `hou_tools.py` | hython側の共通処理。ノード構成のJSON化、ジオメトリ統計、プレビューレンダ |
| `graph_report.py` | ノード構成JSON → ネットワークエディタ風のPNG |
| `report_pdf.py` | 実験レポートのPDF生成。`--bundle` で複数実験を1冊にまとめる |
| `glossary.json` | 用語の単一の情報源。用語辞典ページ・ポップアップ・PDFの3つを生成する |
| `glossary_pdf.py` | 用語集PDF（Gemini Notebook 用ソース） |
| `build_site.py` | サイト生成。`site/`（Artifact用・絶対URL）と `docs/`（GitHub Pages用・相対パス）の2系統 |
| `site/*_template.html` | ページのテンプレート。**生成物ではなくこちらを編集する** |
| `docs/` | GitHub Pages が配信するフォルダ（生成物） |
| `out/` | 実験の生成物（JSON・PNG・PDF） |
| `BACKLOG.md` | 実験の予定と、確立した実験の進め方 |
| `REFERENCES.md` | 参照した資料と、実測で覆した情報 |
| `SOURCE_STRATEGY.md` | Gemini Notebook のソース運用方針（上限300件への対処） |

## ハマりどころ

- `hlight` の既定はポイントライトで距離減衰する。強度1のまま距離7に置くと被写体が真っ黒になる
- レンダは既定の `smooth` ではなく `smoothwire` を使う。ワイヤーフレームが乗るので、
  そのネットワークが実際に作ったトポロジが画で分かる
- メニュー系パラメータは文字列ではなく数値で入ることがある。
  迷ったら `parm.menuItems()` / `parm.menuLabels()` で確認する
- 接続図を出す前に表示フラグを意図した位置に立てる。`dump_graph` はその時点の状態をそのまま写す
- **Windows PowerShell 5.1 の `Get-Content` / `Set-Content` で日本語ファイルを書き換えると
  文字化けする。** UTF-8 を明示した Python か、エディタで編集すること

## ライセンス表記について

レンダ画像に入っている Houdini のウォーターマークは Apprentice（非商用）ライセンスによるもの。
