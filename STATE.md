# STATE — 新しいセッションはまずこれだけ読む

最終更新: 2026-09-20（実験104・実践36本・ノード186件・用語256語・効率化38項目）

## いまの状態

- 実験 001〜104 完了。振り返り点検は 090 まで済み、次は 120（対象 091〜120）
- 091〜104 は「答えが計算で出る形と突き合わせる」型（検算）で回した。効きが良い
  - 式と6桁一致したもの: boolean(098) / peak(100) / polyextrude(102) / transform の回転順序(103) / carve(104)
  - 式とずれたもの: VDB は升目次第(098)、球の面積は分割の2乗で近づく(101)
  - 検算で見つけた落とし穴: boolean は poly 以外だと黙って何もしない(098)、carve の First U は入切(104)
- **名前が変わった**: 「手順」→「実践」（画面の言葉だけ。ファイル名は guides.json のまま）
- 新設: 「制作」（works.json、まだ0本）と「要望」（requests.json、4件）
- 実践 36本、効率化のまとめ 34項目、ノード解説 186件、用語 255語
- ナビは4つに畳んだ（ホーム／実践／実験／解説）。乗せるとパネルが降りる
- 親ページは別リポジトリ https://realestatewarrior.github.io/ （クローンは D:\Claude\sp）
- ユーザー待ち: Cloudflare+Gemini の鍵、UE の導入、Houdini 22 のライセンス
- **Claude 版のハブは3ページに分かれた**（概要と実験216 / 実践と制作319 / ノードと用語39。上限512）
  URL は build_site.py の ARTIFACT_URLS。新しい2つは guides / ref の鍵
  外部から画像を読む案は使えない（Artifact は自分のファイル・Google Fonts・一部CDNのみ）
- **Houdini 22.0.368 はライセンスが無く hython が起動しない**（21 のライセンスでは動かない）
- 残りの宿題: 実践「テクスチャを貼る」「ターンテーブル」「文字を光らせる」の Houdini 画面（GUI が要るので自動では撮れない）。要望ページ（#requests）で追う

## ノードと用語を増やすときの型（091〜098 で確立）

1. `"…/hython.exe" node_dump.py out/_nodes_dump.json --file 一覧.txt`
   でノードの**実物を作って**つまみ名・ラベル・既定値・メニューを取る（型に聞くと漏れる）
2. `nodes_add_1〜3.py` に日本語の説明を書く（つまみ名は1つだけ書く）
3. `python nodes_merge.py` で混ぜる。**つまみ名が実物に無ければ止まる**
   （`cp out/_nodes_backup.json nodes.json` してから実行する）
4. 用語は `gloss_add_1〜3.py` → `python gloss_merge.py`

版番号に注意: `createNode("remesh")` は remesh::2.0 になり、つまみ名が 1.0 と違う
（target_edge→targetsize、smooth の iterations→strength、measure の type→measure など）。

## SOP を測る型（091〜098 で確立）

`examples/sop_bench.py` を使う。`fresh()` でシーンを捨てて組み直し、
`spread(a, b)` で「a の各点から b の面までの最短距離」の平均と最大を取る。
体積は measure（Measure=Volume）を面ごとに足す。**答えが計算で出る形を使うと、
アルゴリズムのずれと近似のずれを分けられる**（実験098）。

## 1実験の流れ

1. hython で測る（1プロセス1レンダ。時間も記録）
2. `out/NNN_report.json` を作る
3. 実践向きの題材なら `guides.json` に1本足す（画像と .hipnc は `examples/guide_cache.py` / `guide_more.py` 系で作る）
4. 速さの結論は `speed_tips.json`、新しい用語は `glossary.json`
5. `python publish.py "実験NNNを追加"` で生成・コミット・push
6. Artifact を再発行する（公開先の URL は auto-memory の houdini-sites）
7. この STATE.md を更新する

## やることメモ（全チャット共通。2026-09-21 に共有データ化）

https://claude.ai/artifact/7Yd8cWYRkjTEaB6wRe6kqj （サイドバーに固定済み。ページの「編集モード」で直せる）

- 中身はこのページの共有データが正。`memo.json` と `make_memo.py` は使わない（古い控え）
- 読む: `ArtifactData` の `query` で必要な分だけ。例 `items` の `group == "you"` かつ `done == false`。全部読むより軽い
- 区分: `you`=あなた待ち / `mine`=私の宿題 / `open`=未解決 / `rules`=決めごと。項目は `title`・`detail`・`state`・`done`・`order`
- 書く: `update` に `if_version` を付ける。他の所で直されていたら失敗するので、読み直してからやり直す
- リンクは `links/all`（`bands`）、直近やったことは `recent/log`（`entries`、新しい順、40件まで）
- 実験や作業が済んだら、`recent/log` に1行足す

## 読み方のルール（トークン節約）

丸ごと読まない。Grep か offset/limit で必要な所だけ。

| ファイル | 大きさ | 使い方 |
|---|---|---|
| guides.json | 約186KB | Grep でキーや題名を探す |
| out/_nodes_dump.json | 約1.5MB | **開かない**。Python で名前を絞って読む |
| build_site.py | 約94KB | Grep で関数名を探す |
| glossary.json / nodes.json | 約45KB / 約62KB | Grep で用語・ノード名を探す |
| PROGRESS.md | 約20KB | **古い**（手順15本の時点）。読まない。履歴として残すだけ |
| ROADMAP.md | 約4KB | 先頭の「いま進んでいるところ」と E「決めごと」だけ有効 |
| BACKLOG.md | 約4KB | 019〜021 の記述は古い。「実験の進め方」の型だけ有効 |

- hython や build のログは、必要な値だけを出力する。長ければファイルに書いて Grep
- 画像は縮小して見るか、数値で確かめる

## Artifact 再発行

**3実験に1回**（ユーザー決定 2026-09-20）。GitHub Pages は実験ごとに `publish.py` で更新し、Artifact だけ間を空ける。

- 最後に再発行した実験: **104**（2026-09-21 に8ページ全部を再発行。親ページの thumb_099 欠けを直した）
- 次は **107** を終えたとき。その次は 110
- 再発行したら、上の番号を書き換え、下の「使用量の記録」に1行足す

### 再発行の手順（2026-09-21 に確立。トークンを食うのは公開中の版を読むところ）

Artifact ツールは、公開中の版を「全行読んだ」後でないと上書きを通さない（1ページ約15万トークンの見込み）。
これを避けるには `force: true` で上書きする。**公開中の版を破棄するので、その都度ユーザーの同意を取る。**
8ページとも `site/` のビルドが元で、ページ内で保存される仕組みは無い（capabilities は sample のみ）。

1. `python publish.py` で `site/` を作り直す
2. **足すファイルの差分だけ Haiku に出させる**（読み取り専用。list と手元の突き合わせだけ。公開はさせない）。
   参照ファイルの抽出は `[A-Za-z0-9_./%\-]+\.(?:png|jpg|jpeg|gif|webp|svg|css|js|hipnc|json)` で、site 内に実在し .html でないもの。
   期待数: sp=9, home=215, practice=318, reference=38, index=126, log_fx=89, glossary=0, links=0
3. 8ページを `url` + `force: true` で発行。足すファイルがあるページだけ `root: D:\Claude\houdini\site` と `files: [相対パス]` を付ける
4. 余ったファイル（親26・index18・log_fx2）は過去の版の残り。参照されていないので、消さずに置いておく
5. サブエージェントの公開は自動判定に拒否される（2026-09-21）。公開はメインで行う

## セッションの切り方（2026-09-21 決定）

- **3実験ごとにセッションを切る**（再発行と同じ区切り）。切る前に STATE.md の「いまの状態」を更新する
- 新しいセッションは STATE.md だけ読んで始める。PROGRESS.md と BACKLOG.md は古いので読まない
- 前のセッションは約130MBのログまで育っていた。長いほど毎ターン重い

## 使用量の記録（Pro プラン。週の枠。再発行のたびに1行）

| 日付 | 実験 | 週の使用率 | 週の経過 | メモ |
|---|---|---|---|---|
| 09-21 | 104 | 62% | 4割強 | 基準点。ペースは約1.4倍 |
| 09-21 | 104 | 63% | 4割強 | 再発行の試験後。この相談全体（Haiku 2回・診断・再発行8ページ）で +1%。5時間枠は12%→17% |
- 再発行のとき全ページを対象にする（検索の中身が全ページに入るため）。ファイル数の差分は houdini-sites の記憶にある手順で出す

## 更新のルール

実験を1つ終えるごとに、「いまの状態」の数字だけ書き換える。詳細は書かない（詳細は実験ログにある）。
