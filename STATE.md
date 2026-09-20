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

- 最後に再発行した実験: **090**（次は 093 を終えたとき。その次は 096）
- 再発行したら、上の番号を書き換える
- 再発行のとき全ページを対象にする（検索の中身が全ページに入るため）。ファイル数の差分は houdini-sites の記憶にある手順で出す

## 更新のルール

実験を1つ終えるごとに、「いまの状態」の数字だけ書き換える。詳細は書かない（詳細は実験ログにある）。
