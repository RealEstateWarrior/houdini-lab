# 参考にした資料

Notebookのソースとは別に、作業中に参照した外部資料の記録。
ある程度溜まったらこのファイルを1つのソースとしてNotebookに投入し、
以降は**同じソースを差し替える**形で更新する（ソース数を増やさないため）。

## SideFX 公式

- **Houdini ライセンス比較** — https://www.sidefx.com/products/compare/
  Apprenticeの制限（非商用のみ、レンダー解像度1920x1080まで、GUIと出力画像にウォーターマーク、
  Karma/Mantraトークン各1個）。ただし「コマンドラインアクセス ✓」の記載は曖昧で、
  これだけではApprenticeでhythonが使えるか判断できなかった。
- **Rendering as part of a workflow** — https://www.sidefx.com/docs/houdini/render/batch.html
  hython / hbatch でのバッチレンダリングの位置づけ。

## 注意: 誤っていた情報

- **「Apprenticeでは hython / hbatch が使えない」** — フォーラム由来の情報として複数箇所で見かけたが、
  **実測では普通に動いた**（Houdini 21.0.700 Apprentice、GUIがライセンスを保持している状態でも同時起動可、
  OpenGL ROP / Karma ROP でのheadlessレンダリングも成功）。
  この前提でGUI遠隔操作（hrpyc）方式を作りかけて無駄になったので、同種の制約は必ず実測で確認する。
- **Apprenticeのライセンス入れ直しは `hkey.exe` からはできない。** ログインすると
  「Installing licenses through hkey is reserved for non-apprentice accounts」と弾かれる。
  正解はHoudini本体を起動し、出てくる「Unable to Acquire a License」ダイアログから進めること。
- **mountain SOP のパラメータ名は `roughness` / `octaves` ではない。** 実際は `rough` / `oct` / `lac`。
  一般的な名前で書くとパラメータが見つからずエラーになる。
  ノードのパラメータ名は `[p.name() for p in node.parms()]` で確認してから使う。
  メニュー項目の値も `parm.menuItems()` / `parm.menuLabels()` で確認する
  （例: `color` SOP の `colortype` は数値、`subdivide` の `algorithm` の既定は 2 = OpenSubdiv Catmull-Clark）。

## ツール運用で踏んだ罠

- **PowerShell の `Get-Content` / `Set-Content` で日本語ファイルを書き換えると文字化けする。**
  Windows PowerShell 5.1 は既定でANSIとして読むため、UTF-8のHTMLが壊れた。
  テキストの書き換えは Write/Edit ツールか、`encoding="utf-8"` を明示したPythonで行う。

## MCPツール（Gemini Notebook連携）

- **jacob-bd/notebooklm-mcp-cli** — https://github.com/jacob-bd/notebooklm-mcp-cli （採用）
  `pip install notebooklm-mcp-cli`。CLI（`nlm`）とMCPサーバーとエージェントスキルの3点セット。
- **PleasePrompto/notebooklm-mcp** — https://github.com/PleasePrompto/notebooklm-mcp
  当初の候補だが **2026-09-10にアーカイブされ開発終了**。star 3.4kあっても保守状況は別途確認が必要。
- 比較検討した他候補: roomi-fields/notebooklm-mcp、Pantheon-Security/notebooklm-mcp-secure、
  m4yk3ldev/notebooklm-mcp

## ローカルにあるHoudiniヘルプ（未活用・宝の山）

`C:\Program Files\Side Effects Software\Houdini 21.0.700\houdini\help\`

zipで固められている。特に価値が高いもの:

| ファイル | サイズ | 中身 |
|---|---|---|
| `nodes.zip` | 6.2 MB | 全ノードのリファレンス |
| `images.zip` | 307 MB | ノードの図解・スクリーンショット類 |
| `vex.zip` | 0.7 MB | VEX リファレンス |
| `hom.zip` | 1.1 MB | Python (HOM) API リファレンス |
| `shelf.zip` | 0.3 MB | シェルフツール解説 |
| `character.zip` | 2.4 MB | キャラクター関連 |

実験で扱ったノードの解説だけを抜き出して実験ログに添える、という使い方が現実的。
全部投入するとソース数制限（300）を無駄に消費するため、**実験に関係する範囲だけ抜粋する**。
