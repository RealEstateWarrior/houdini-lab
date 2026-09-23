# Gemini Notebook ソース運用方針

「Houdini 操作ガイド」`9e4a30fe-e11f-455d-8179-df0765435022` は**他の人にも共有されている**。
ソース上限は300件で、現在40件。

## 原則: 実験1件につき1ソースにはしない

実験ごとに新規ソースを足すと、14実験で14ソース、その先も無限に増えて上限を無駄に食う。
かといって全部を1ソースに詰めると、Notebook側が広く薄い1文書として扱うため引用の精度が落ちる。

**中間を取る。テーマ単位で1ソースにまとめ、実験が増えたらそのソースを差し替える。**

| ソース | 中身 | 現在 |
|---|---|---|
| 実験ログ: プロシージャルモデリング（001〜120） | out/nb/exp_model1.pdf | 51f4ce89-91c4-455f-a30c-fa1f1a8e9ff2 |
| 実験ログ: プロシージャルモデリング（121〜） | out/nb/exp_model2.pdf | c5044614-bfab-475c-92ac-5282cce42a10 |
| 実験ログ: 地形（HeightField） | out/nb/exp_terrain.pdf | f4fca645-ed59-4af3-a82f-7ed36c563cb1 |
| 実験ログ: VEX・道具・速さ | out/nb/exp_tools.pdf | 8c6592c8-fb89-4259-85e7-5853abc14105 |
| 実験ログ: 剛体と破壊（RBD） | out/nb/exp_rbd.pdf | fd1be2a5-7c57-455d-9c59-d22b95f27e66 |
| 実験ログ: 布とやわらかい物（Vellum） | out/nb/exp_vellum.pdf | d76d1347-50aa-43bd-a30f-6cbe7276e5db |
| 実験ログ: 煙と炎（Pyro・ボリューム） | out/nb/exp_pyro.pdf | db4b664f-b240-4831-bed8-40664646fd36 |
| 実験ログ: 液体と MPM（FLIP・砂・雪） | out/nb/exp_fluid.pdf | 7a7a9c51-8e5e-4c83-9419-f1ff1c35e812 |
| 実験ログ: 見た目（Karma・材質・テクスチャ） | out/nb/exp_look.pdf | 29943822-bf4d-4ae8-bf8b-3f2927e4c4ad |
| 実験ログ: 粒（POP） | out/nb/exp_pop.pdf | 049721b3-7dc6-452f-a837-c378c7947c89 |
| 実験ログ: 毛とリグ（グルーム・APEX） | out/nb/exp_groom.pdf | b68bdae5-af17-41e0-903e-325d3787b7c7 |
| 実践: Houdini で作る手順 | out/nb/practice.md | 16db60df-7d7e-4771-a00a-257e7e6784b7 |
| ノード解説 | out/nb/nodes.md | 81acf710-b838-4070-b7dc-407eb3c2d616 |
| 用語集: Houdini 初心者向け | out/nb/glossary.pdf | f47d1bd1-bf8a-4cac-9e31-218137976af3 |

2026-09-24 に作り直した（右の列はソースの ID）。それまでは全実験が「実験ログ A」1つ（30MB）に入っていて、
方針の「テーマ単位で約10本」が 001 の段階で止まったままだった（ユーザーの指摘）。
作るのは `python nb_sources.py`（題材の振り分けは THEMES。どれにも当たらないモデリングは 120 で2つに分ける）、
用語集は `python glossary_pdf.py glossary.json out/nb/glossary.pdf`。
**実践・実験が5本ほど増えたら、変わったものだけ削除→追加→名前を戻す**（ID は上の表を書き換える）。

これで全カリキュラムを通しても **+5件程度**に収まる。

## 差し替えのやり方

ファイルソースは中身を更新するAPIがないため、**削除して再追加**する。
1. テーマPDFを再生成（全実験分を1つのPDFに束ねる）
2. `source_delete(source_id, confirm=True)` で旧ソースを削除
3. `source_add(source_type="file", file_path=...)` で新PDFを追加
4. `source_rename` で決まった表示名に戻す

PDFはローカル（`out/`）に残るので、削除しても内容は失われない。
ただし **共有ノートブックに対する削除**なので、実行時は都度その旨を伝える。

## 取捨選択の基準

入れる:
- 実験ログ（自分で確かめた事実。Notebookに無い一次情報なので価値が高い）
- 誤っていた通説と、その実測結果（例: 「Apprenticeでhythonは使えない」は誤り）
- 実験で実際に扱ったノードの公式解説

入れない:
- Houdiniヘルプの全文（ソース数と容量の無駄。すでに39件投入済みの範囲と重複する）
- 環境構築の手順そのもの（`houdini_notebooklm_handoff.md` に置けば足りる。Houdiniの理解には寄与しない）
- 一般的なPython/ライブラリの使い方
