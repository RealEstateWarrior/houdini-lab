# STATE — 新しいセッションはまずこれだけ読む

最終更新: 2026-09-24 夕方（実験217・実践71本・ノード388件・用語452語・VEX 解説ページ）

## いまの状態

- **2026-09-24 午後（ユーザー指示「実践を想定した実験を17時まで・用語とノードも・VEX 解説ページ」）**:
  - 実験204 Pyro のキャッシュ容量（9 割以上が vel。煙のある所だけ残して VDB・16bit で 16 分の 1）/ 205 Karma のぼけ・ぶれ（+5〜9%。サンプル数を上げてもざらつきは減らず、16＋OIDN が最良）/
    206 テーブルクロスの試しは 44×56（差 1.9 cm・時間 39%、角の垂れは短い）/ 207 Volume Step Rate は既定 0.25 のまま（1 に上げると遅い。大きいほど細かい＝216 で訂正）/
    208 FLIP の面は Influence Scale と Method で形が決まる、Filtering でなめらか / 209 PDG で同時 8 本が 1.6 倍、1 本だと 2.2 倍遅い（Evaluate Using の落とし穴）/
    211 テーブルクロスの浮きは Thickness の分（既定 0.01 で 10 mm）/ 212 金属の Roughness は 0.2 まで同じ見た目 / 213 SSS の透けは半径 0.5 の球で Distance 0.1〜0.3 /
    214 Karma のぼけは f²(d−s)/(N·d·s) に 0.9% 以内（薄いレンズの式より 5% 小さい）/
    216 煙の透けは exp(−Density Scale×濃さ×厚み)。**Volume Step Rate は大きいほど細かい**（1 で式とぴったり、0.05 でほぼ素通り。207 を訂正）/
    217 布の曲げの硬さは 0.1 から下げても同じ、10 以上で板のように張る
  - **点検 210（181〜209）済み**: 22 本は完全一致。200・205 は足した項目、204・209 はファイルの大きさの揺れ（最大 0.6%）、181・208 は時間の項目。
    201 は台本が 202 の build（焚き火の設定）を借りていて合わなかった → 既定値に戻すよう直した。Turbulence の 2 条件のずれは **220 で解決**:
    pyrosolver を作った直後の Use Control Field は「入り」だが revertToDefaults で戻る値は「切り」。201 の台本を「入り」に直すと記録と全フレーム一致（201 の結論は正しかった）。次の点検は 240
  - **2026-09-24 夜**: 実践「海」を作り直し（水平線まで扇形の板・スペクトル 3 枚・夕日、Karma の映像）＋冬の朝の七里ヶ浜版を同じページに（variants.json →
    practice_merge が out/pr_<版>.json を親の variants に入れ、build_site が「もう一つの版」として出す。practice_kit に camera= と karma_anim()）。
    落とし穴: 空の球（半径 20 km）は distant ライトをさえぎる（vm_rendervisibility -shadow も効かない）→ 空の内側に disk ライト。空の材質は reflect=0。
    VEX の smooth(大, 小, x) は逆向きにならない（1 - smooth を使う）。レンダー用カメラ・render_preview は Far Clipping 10000 に注意（render_preview は直した）。
    実験 218 光の道（Roughness で白い帯、さざ波で粒のまま広がる）/ 219 海の板の点を半分で時間 12% 減・粒 15% 減（1 枚目は Karma の立ち上がりで遅いので捨ててから測る）/ 220 上の Turbulence / 221 海はサンプル数・解像度を下げても 2 割減、下げるなら 4 サンプル＋OIDN /
    215 草はパックしたまま（1 万本 17 秒、解くと 128 秒）、10 万本はポイントインスタンサーでも地面を広げても 13 分（原因未確認、mine215 に残す）
  - **2026-09-25 夜（〜6:10）**: 実験 222〜239。222 草は LOP の sopimport で Create Point Instancer（10 万本 13 分 → 12 秒）/ 223 白波の cusp しきい値は風速で決まる（10 m/秒で 0.15）/
    224 Vellum の布の伸びは Substeps / 225 明かり 1000 個はライトで / 226 ガラスのひびを増やすと割れにくい / 227 浸食は既定 5 フレームで谷筋 / 228 粒は点のまま（1000 万個 8 秒。scatter は 100 万個が上限）/
    229 毛は曲線のまま / 230 SOP で回す物のブレは Geometry Time Samples 8 / 231 焚き火の明かりは炎のボリュームで / 232 XPU は 7〜14 倍速いが色が出ない所あり /
    233 Pyro の升目 28 倍でも撮る時間 25% 増 / 234 室内は Diffuse Limit 4 以上 / 235 雲は Volume Limit で明るく（16 でも落ち着かない）/ 236 グラスは Refraction Limit 8 /
    237 風船の体積は Rest Length Scale の倍率ちょうど / 238 Color Limit はきらめきを切り詰める / 239 解像度 9 倍で時間はドーナツ 7.9 倍・海 2.1 倍。
    冬の朝の七里ヶ浜版を作り直し（泡の筋・水面の傾き 9°・縞の解消）。全実践の Houdini 画面を撮り直し（capture は variants も撮る）。ハンバーガーを実践の画 12 枚に。
    落とし穴: Karma の時間は 1 枚目に立ち上がりが入る（小さく 1 枚捨ててから測る）。ライトが無い場面は Karma が自動で明かりを足す（明るさ 0 の envlight で止める）。
    python の heredoc で日本語を含む置き換えが一致しないことが多い（Edit を使う）。点検 240（211〜239、215 は除く）済み: 26/28 一致。218・219 は実践の hip を作り直したあとで読んでいた → git の履歴から out/pr_ocean_winter_v1.hipnc を戻して読むよう直した。
    226 は Bullet の弱いつながりで割れ方が回ごとに揺れる（0.6 で 54〜116 個）→ 記事に 5 回分の幅。**実験が実践の hip を読むときは、測ったときの hip を _vN で残す**。次の点検は 270
    実験 241〜245: 241 ノイズ除去は 4 サンプルで 32 サンプル並み（OptiX がわずかに良い）/ 242 XPU で Cd のある形は白くなった（訂正あり）/ 243 **XPU は形に Cd があると principledshader の色が Cd に置き換わる。MaterialX なら CPU と同じ** / 244 実践の焚き火は火元から density を出しておらず Dissipation が効かない。出すと煙の量は Dissipation に反比例 / 245 地形の谷の細かさは Erosion Feature Size で決まる
    246 Bullet の割れ方の揺れはマルチスレッドのため（HOUDINI_MAXTHREADS=1 なら毎回同じ、約 3 倍遅い）。
    247 映像にノイズ除去（OptiX）を使っても空のちらつきは増えない / 248 グラスも MaterialX なら CPU と XPU がほぼ同じ絵（明るさが違ったのは principledshader の CPU の方）。
    メモ: 実践「焚き火」は火元から density を出していない（煙が出ない）。作り直すなら火元に density を足す（実験244）
  - **EXR を測る**: hython に OpenImageIO 2.5 が入っている（`import OpenImageIO as oiio`、`ImageBuf(path).get_pixels(oiio.FLOAT)`）。1 を超える明るさも切れずに測れる（212〜214）
  - **Apprentice の透かしは EXR にも入る**（画の右下）。明るさを測るときは窓を切って避ける（214 で最初これを数えた）
  - 時間を測らない実験（形・明るさ）は、点検や他の重い処理と同時に回してよい。時間を測る実験は単独で
  - **VEX 解説ページ（site/vex_template.html → vex.html）**: 解説メニューに追加。お手本 6 つは examples/vex_recipes.py（画・hip・コードを json に書き出し、build_site の render_vex_recipes が読む）。
    本文の href="exp:NNN" は link_vex_page が実験ログへ向け直す。VEX を使う実践の一覧は自動。用語ポップアップは link_terms_in（title・pre・svg には付けないよう SKIP_TAGS に足した）
  - 実験の記事に動画は載らない（mp4 は実践だけ）。動きは GIF にして comparisons の画像に入れる（206_anim.py）
  - 点検 210（181〜209）は examples/210_audit.py。200 番台は条件ごとの引数を部分ファイルの名前から作る
  - 落とし穴: finish_exp.py に間違った引数を渡すと、make_entry が先に記事を差し込む（DONE の確認より前）。間違えたらひな形から手で消す
- 実験 001〜248 完了（200 から制作寄り。これからは実践を増やすほうへ重心を移す）。振り返り点検は 210（examples/210_audit.py）まで済み、次は 240
  （点検の番号は 030・060・090・121・150・180・210）。Artifact（サイトの写し）は 150 時点のまま。**出し直しは 2026-09-23 にやめた**（本体は GitHub Pages。ユーザーに頼まれたときだけ出す）
- **2026-09-22 見た目の刷新をサイトに当てた（17a74ea）**: tools_redesign_2026_09_22.py。白黒＋青（--flag）とコーラル（--coral、AI だけ）、
  ライト/ダーク（右上の自動・明・暗）、フォントは Schibsted Grotesk + Zen Kaku Gothic New、上のバーは4つの見出し＋区分のタブの列（.subnav。
  降りてくるパネルは display:none）、ホーム冒頭は動く灰色の帯（.band。検索窓・AI・新着の実験8件の重なったカード）、
  区画の題は英語＋日本語、バージョンと件数はホームの最後（.site-facts）。参考は Apple・Superlist・landsolution・チケプラTrade
- **2026-09-23 hip**: 091〜201 に out/NNN_scene.hipnc とノードの画 NNN_graph.png を付けた（examples/hip_export.py。台本を流し直し、out/ への書き込みは逃がす）。記事には build_site が自動で「シーンファイル」と「ノードのつなぎ方を見る」を差し込む。**実践・実験には必ず hip とノードの画を付け、初心者向けに書く**
- **2026-09-23 メニュー**: ハンバーガーに実践のサムネイル8枚（MENU_GUIDES）と入口カード
- 202（焚き火を速く回す設定）は 2026-09-24 に公開済み（Voxel 0.02→0.04 で5.1倍速く高さの差3%。reports_202.py）。制作1回目は MetaHuman の Groom（ユーザーの指示待ち）
- **2026-09-23 不具合直し**: 本文の別編への実験リンクはビルド時に向け直す（retarget_exp_anchors）。make_entry.py がレポートの `**太字**` を <strong> にする（093〜199 の107本が記号のまま出ていた）。GitHub 版に description・OGP・アイコン・sitemap.xml・robots.txt。実験196 に訂正
- 181〜199 の要点: pcfind＝nearpoints、pcfilter は重み付き平均（重みの式は不明）/ Bullet Substeps で沈み込みが決まる /
  mpmsource の粒数＝体積÷Separation³ / smooth の縮み 1/(1+S·L^q/C(2q,q))（間隔が不ぞろいだと粗い側が縮む）/ hairgen＝Density×面積 /
  USD：Point Instancer がいちばん小さい / 球のへこみ sin²(Δ/2) / polyextrude の Inset と角錐台 / popsource の Rate と Life×fps−1/Substeps /
  vdbreshapesdf：Dilate・Erode は Offset×升、Open は辺を円弧で丸め半径は Offset×升＋約3升（帯によらない）、Close は帯を広げると削りが減る
  - ノードは nodes_notes.py の MORE、用語は gloss_add_11.py
  - 光線で断面を測る型: hou.Geometry.intersect で点を取り、numpy で円を当てはめる（examples/198_vdb_open_arc.py）
- 151〜179 の要点: sphere の測地球 / polybevel / neighbourcount とオイラー標数 / polyfill は奇数の穴を四角で塞がない / scatter density /
  polywire / voronoifracture（relax で種が壁へ）/ trail / uvlayout / attribtransfer の (1−t²)² / subdivide の crease = 回数 /
  vellumconstraints の本数 / vdbfromparticles / POP 落下（生まれたフレームで1ステップ）/ popdrag は √(g/k) / RBD の Padding /
  heightfield の Amplitude・erode / Vellum の伸び（Iterations の方が安い）/ curlnoise の発散 / VEX と Python / for-each と compile / pcfind / popwind
  - **finish_exp.py は、タグに「シミュレーション」か「エフェクト」があればエフェクト編（log_fx）へ入れる**（それまでは全部モデリング編だった。157〜159・163・165〜167 を移した）
  - **時間をはかる台本の落とし穴: hou の cook(force=True) では VEX の wrangle が計算し直さない。コードが読むつまみ（ch('k')）を毎回わずかに変える**（実験173）
  - ノードは nodes_add_9.py（Python SOP・for-each・compile の5件）、用語は gloss_add_9.py・gloss_add_10.py
- 142〜149: platonic の Radius / circle の内接多角形 / torus の Rows・Columns / mirror の継ぎ目 / clip と 2πh / twist の6操作 / tube の円錐台 / divide の Bricker
  - ノードは nodes_add_8.py（19件）、用語は gloss_add_8.py（12語）。新しいノードの素性は out/_dump8.json → _nodes_dump.json に足した
  - 147 の Taper の体積が倍率の平均と 0.45% 合わない理由は確かめていない
- GitHub Pages 版の「AI に聞く」は houdini-relay（Gemini）経由で動作確認済み。検索の横に AI アイコン（Beta の札）。Claude 版は従来どおり
- **2026-09-22 追加修正**（ユーザー依頼、私が publish.py まで実行・コミット4a70d5e）:
  スマホでAIアイコンが検索の左横に来るよう base.css を修正（以前は検索とハンバーガーだけ右へ寄り、AIアイコンが取り残されていた）。
  AIアイコンと検索アイコンで同じ画面が開いていたのを分離（partial_chrome.html）。
  AIアイコンは候補一覧を出さず直接チャット入力（プレースホルダー「AI に何を聞きますか？」）、検索は今までどおり。
  入力欄は元々共有なので、検索で打った文字のまま「AI に聞く」を押せば質問になる（実装済みの構造で確認しただけ）。
  実サイトで3点とも実機確認済み
- **2026-09-22 さらに作り直し（Houdini実験道場セッションが担当・push済み 347e095）**:
  「AI に聞く」は検索と別の専用チャット画面（#chat-sheet。広い画面は右から出る460pxの板、スマホは全面）に。
  Enter送信・Shift+Enter改行、会話前に質問例3つ、検索側は「この言葉でAIに聞く」ボタンでチャットへ移動して即送信、
  upstream_error/rate_limited/empty_completion は1回だけ自動再送。worker.js は変更なし。
  **partial_chrome.html・base.css の AI 関連部分は当面 Houdini実験道場セッションが持つ。
  触る前に一声かける（向こうからの申し出）**
- **2026-09-22「考察（未確認）」を追加（push 6fde578）**: パラメータ調整やVEXの質問で資料が足りないときだけ、
  本文のあとに見出し「考察（未確認）」を置き、一般知識の案を2つまで（末尾は必ず「このサイトではまだ確かめていません。」、
  パラメータ名は実際の表示名、実測値のような書き方は禁止）。画面では点線の枠で本文と分ける。本文側は今までどおり資料のみが根拠。
  やることメモ open06 は完了扱いにした
- 2026-09-21 の作業（105〜）: 実験を片付けるのは `python examples/finish_exp.py NNN "タグ,…" "一言" 図.png`
  （記事の差し込みと DONE への追加を1回で）。ノードは nodes_add_4.py、用語は gloss_add_4.py
  - 105 spiral の長さ / 106 attribrandomize の分布 / 107 extractcentroid の中心 / 108 triangulate2d の枚数
  - 109 groupexpand の広がり / 110 copyxform は「値を i 倍して1回」 / 111 pointjitter は幅
  - 112 vdbcombine の和積差 / 113 timeblend（v は1秒あたり）
  - 114 sweep の体積 / 115 attribfill の到着時間 / 116 uvflatten / 117 relax / 118 revolve の裏返し
  - 119 面に沿った距離 / 120 measurethickness（box の Use Divisions は線の籠）/ 121 点検
  - ノードは nodes_add_5.py まで（274件。deform・measure の2グループを新設）
  - **Write で作ったファイルを sed や python で書き換えると、ファイル全体が差分として返ってきてトークンを食う。Edit を使う**
  - 122〜134: polyexpand2d / shrinkwrap / lsystem / 数の式 / cluster / 最短経路 / extracttransform / 曲率 / Cusp / bend / attribpromote / ray / 式の入ったつまみ
  - **スクリプトの落とし穴: 最初から式が入っているつまみ（SOP で488個。ray の dir は @N.x）は set しても変わらない。deleteAllKeyframes() してから set**（実験133・134）
  - 実験で分かったことを既存ノードに足すのは nodes_notes.py（名前 → 追記文と実験番号）
  - node_dump.py がメニューを12個で切っていた → 直した（vdbcombine は18個）
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

## サイトの形（2026-09-23 変更）

- 上のバー: 左にメニュー（2本線）と区分のタブ、真ん中にロゴ、右に AI・検索・Notebook。頭では背景になじみ、読み進めるとガラスになる（is-scrolled）。スマホは区分のタブをバーの下に左寄せ
- 全ページ: バーの下に現在地（render_crumbs）、最後にリンク集（render_footer, id=sitemap）
- 実験ログ: 左に目次（絞り込み・いま読んでいる所に印）、記事はコラムの形（公開日・読む時間・タグ・要点3つ・サムネイル、本文は「全文を読む」に畳む）。1000px 未満は目次なし
- 実験カードは実験ログの記事を新しいタブで開く（ポップアップはやめた）
- 公開日は `python examples/dates_index.py`（git の履歴から。out/dates.json）。**実践・実験を足したら回す**
- つまみのポップアップは `hython examples/parm_index.py`（hip から。out/parm_index.json）。**実践を足したら回す**
- 難易度は build_site.py の guide_level（シミュレーション=応用、VEX か6段以上=基本、ほか=入門）
- docs/ では検索・用語・ノード・実験のデータを docs/data/*.js に出す（ページが約1.2MB→約0.2MB）
- ページ確認は headless Chrome（スクラッチの shot.sh）。ブラウザの枠は PC 幅が小さく写る
- 上バーのロゴは2つのリンク: SP マーク＝親（Saito Production）、「Houdini 研究部」＝この部のホーム。現在地の先頭も Saito Production
- 親ページ（D:\Claude\sp → RealEstateWarrior.github.io）も同じ形（バー・題の板・リンク集）。**publish.py が親のリポジトリも一緒に送る**（それまで一度も送っていなかった）
- 要望のメール転送は未（ユーザーの判断待ち）
- これからの実践: エフェクトは映像か GIF を付ける

- 実践・制作は1本ずつのページ `guide_<id>.html`（build_site.py の write_guide_pages／site/guide_template.html）。カードは新しいタブで開く。頭に現在地（Houdini 研究部 › 実践 › 題）、終わりに前後の実践
- 本文の `<code>ノード名</code>` は押すと種類・一言・ノード解説へのリンクが出る（link_nodes_in／render_node_data／partial_popover.html）。reference ページには付けない
- エフェクトはフォトリアルを目指す。作る前に本物の参考写真を集める（ユーザー指示 2026-09-23）

## 2026-09-24 夜の作業で分かったこと（実践 47〜70）

- **動き**: practice_kit の `g.anim(node, (1, LAST), cap, bbox=…)` で pr_<id>_anim.mp4（ビューポートの連番→ffmpeg）。透明な材質は消えるので、撮る間だけ材質と幕を外している。
  前に作ったシミュレーション24本は `hython examples/pr_anim_add.py <id> <最後のフレーム> "キャプション" [ノード]` で後付け（キャプションは out/_anim_caps.json → practice_merge.py が混ぜる）。
  Git Bash で /obj/… を渡すときは `MSYS_NO_PATHCONV=1` を付ける（付けないとパスが化ける）
- **難易度**は build_site の guide_level が自動で出す（シミュレーション＝応用、VEX か6段以上＝基本、ほか入門）
- **夜（画面が消えている・ロック中）は GUI のスクショが撮れない**（真っ黒。Qt の grabWindow は前の場面が写る）。代わりに hip から描いた
  ノードのつなぎ方の図 pr_<id>_graph.png を載せる（practice_kit の save が json を書き、`python graph_report.py out/pr_<id>_graph.json out/pr_<id>_graph.png`）。
  **47〜70 の GUI 画面（guide_ui_capture / guide_parm_capture / crop_ui_shots）は、画面の点いているときに撮り直す**
- **Karma が遅くなるもの**（実験203）: 透明な物は、サンプルを1増やすごとの時間が不透明の6倍（480×270 で 5.0 秒 vs 0.83 秒）。重ねた数はあまり効かない（+27%）。
  1枚ごとの準備が約13秒。**透明な物は spp 16＋`denoise=True`**（グラスは 83 秒で撮れて実践71 として公開）。SSS も重い（雪だるま 384 秒）
- **小さな物（10〜30 cm）は hero の明かりが近くに置かれて強すぎ、真っ白に飛ぶ**（ドーナツ・グラス）。key 0.1〜0.35・rim 0.5 程度に下げる
- **トークン**: 自分で Write/Read したファイルを python や sed で書き換えると、ファイル全体が差分として返ってくる。必ず Edit を使う
- Notebook のソースは題材ごと14本（SOURCE_STRATEGY.md の表。作り直しは nb_sources.py）。publish.py は log_A.pdf を作らなくなった
- 落とし穴メモ: MPM は Material Type を Sandy にしないと砂にならない／Bullet の Collision Margin 0.02 で薄い物が浮く／
  TOP の ropgeometry は保存済みの hip を別プロセスで開くので Cook 前に保存／copytopoints の色は Karma では Points に移すと確実／
  VEX の smooth(大, 小, x) は効かない（1 − smooth(小, 大, x) と書く）／配列の { } の中に計算は書けない（append）／lsystem の J の葉は縮む

## 実践を作る型（2026-09-23 確立。目標70本）

1. `examples/pr_<id>.py` を書く（`examples/practice_kit.py` の Guide を使う: node / step / mat / assign / hero / save）。
   手順ごとのビューポート画 pr_<id>_<n>.png、Karma の仕上がり pr_<id>_hero.png（暗い幕＋キー・リム・ドーム）、hip、pr_<id>.json ができる
2. `hython examples/pr_<id>.py` → hero を目で見て直す（見栄えが第一。サムネイルで惹きつける）
3. `python examples/practice_merge.py <id> ...` で guides.json に足す
4. GUI の Houdini（受け口 bridge_server が開いているほう）で撮る:
   `python311/python.exe guide_ui_capture.py <id>` と `guide_parm_capture.py <id>`、そのあと `python crop_ui_shots.py`
   （Houdini が2つ起動していても、受け口のあるプロセスの窓だけ撮るよう gui_capture を直した）
5. `python publish.py "..."`。5本ごとにメモ更新
- 落とし穴は測った値で書く。思い込みを書かない（resample・透ける色の件で2回まちがえて直した）
- H21 の copytopoints は既定で属性（Cd など）を移さない。grid の点に並べると N に合わせて倒れる（orient を入れる）
- Karma の炎は kma_pyroshader。明るさ・色は既定で temperature を見るので flame に変える
- 済み: rock neon gems campfire nightcity ／ curtain balloon jelly ocean snow（46本、50768be）
- 次の候補: ほかの分野から5本（例: 木と葉・霧のかかった森・溶ける氷・ロープの吊り橋・花火）
- Vellum の注意: vellumsolver・2つ目の vellumconstraints は左右の出口を両方つなぐ（setInput(1, n, 1)）。timeshift の Frame は式が入っているので set() では止まらない（pointdeform の元の形は tetrahedralize の出力をそのまま使う）
- attribwrangle の class: 0=Detail 1=Primitives 2=Points。copytopoints の Cd は Vellum を通した形には Points に移すと効いた
- heredoc の中の \n は改行に化ける。コード内の \n を含む置き換えは Edit ツールで

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

## Gemini 中継（houdini-relay）2026-09-22 に動作確認

- Cloudflare Worker。コードは `D:\Claude\houdini\relay\worker.js`、設定は同じ場所の `wrangler.toml`
- デプロイは **`npx.cmd wrangler deploy`**（`relay` フォルダで）。
  Cloudflare のダッシュボードの「Deploy」ボタンは効かなかった（Active が切り替わらない、原因不明）。
  今後の更新もダッシュボードではなく wrangler を使う
- PowerShell で `npx wrangler ...` がそのまま通らないときは `npx.cmd wrangler ...`
  （実行ポリシーで .ps1 が止められるため。設定は変えない）
- 鍵は Cloudflare の Secret（`GEMINI_API_KEY`）。モデル名は `GEMINI_MODEL`（既定 `gemini-3.6-flash`。ユーザー指定、動作確認済み）
- 許可する呼び出し元は worker.js の `ALLOW_ORIGINS`（`https://realestatewarrior.github.io` と手元確認用の localhost:8765）
- curl で GET・許可外origin・許可origin の3通りを確認済み（405 / 403 / 200 で Gemini の答えが返る）
- **2026-09-22 修正**: maxOutputTokens が 1024 だと、3.x系は「考える」分もそこから引かれ、
  答えが全部出ていても finishReason が MAX_TOKENS になり「答えが途中で切れました」と誤表示された
  （Opus 側が実機で発見）。maxOutputTokens を 4096 に上げ、thinkingConfig.thinkingBudget を 512 に絞って
  wrangler deploy で直した。curl で truncated:false を確認済み。GitHub Pages 版でも実機確認済み
  （2026-09-22、実験145を根拠にした質問で最後まで答えが返り、誤表示は出なくなった）
- サイト側の呼び出し口は `site/partial_chrome.html`（`window.claude` が無いときだけ relay を使う）。
  build_site.py 側の変更は無し。GitHub Pages に公開した後の実機確認も済み（2026-09-22）

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

**2026-09-23 にやめた。ユーザーに頼まれたときだけ出す**（「絶対出さなきゃ駄目なの？」→ 本体は GitHub Pages なので必須ではない）。以下は頼まれたときの手順として残す。

- 最後に再発行した実験: **150**（2026-09-22 に8ページ全部を force で再発行。足すファイルは「前回公開時の site/ の git 一覧」（34b3e62）との差: 親6・概要と実験18・ログ前半9）
- 次は **153** を終えたとき。その次は 156（ユーザーがまとめて出すよう指示したときはそれに従う）
- 差を出すときの比べる相手は、前回の再発行を記録したコミット（今回なら 8ab360d の次の STATE コミット）の site/
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

- **5件ごとにセッションを切る**（再発行と同じ区切り。2026-09-23 に3件から変更）。切る前に STATE.md の「いまの状態」を更新する
- 新しいセッションは STATE.md だけ読んで始める。PROGRESS.md と BACKLOG.md は古いので読まない
- 前のセッションは約130MBのログまで育っていた。長いほど毎ターン重い

## 使用量の記録（Pro プラン。週の枠。再発行のたびに1行）

| 日付 | 実験 | 週の使用率 | 週の経過 | メモ |
|---|---|---|---|---|
| 09-21 | 104 | 62% | 4割強 | 基準点。ペースは約1.4倍 |
| 09-21 | 104 | 63% | 4割強 | 再発行の試験後。この相談全体（Haiku 2回・診断・再発行8ページ）で +1%。5時間枠は12%→17% |
- 再発行のとき全ページを対象にする（検索の中身が全ページに入るため）。ファイル数の差分は houdini-sites の記憶にある手順で出す

## デザイン刷新（renewal01）を本体に反映（2026-09-22、push 17a74ea）

Houdini実験道場セッションが担当。実装は `tools_redesign_2026_09_22.py`（build_site.py・base.css・partial_chrome.html・各templateを書き換え）。

- 配色は白黒＋青（リンク・現在地）＋コーラル（AIのみ）の2色。ライト/ダーク両対応、右上で「自動・明・暗」切替
- フォントは Schibsted Grotesk（欧文）＋ Zen Kaku Gothic New（和文）
- 上のバーは「4見出し＋タブの列」に。降りてくるメガメニューは廃止
- ホーム冒頭は霞が動く帯。検索・AI・新着実験8件の自動切替カードを重ねる。件数・バージョン表示はホーム最後に移動
- 区画見出しは英語を大きく・日本語を小さく添える形
- 私の2案（v1近黒+オレンジ、v2明るい地+寒色）は採用されず、Houdiniのビューポート/スプレッドシートを起点にした別案が採用された（やることメモ renewal01 参照）

## 更新のルール

実験を1つ終えるごとに、「いまの状態」の数字だけ書き換える。詳細は書かない（詳細は実験ログにある）。
