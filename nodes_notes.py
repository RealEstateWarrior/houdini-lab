# -*- coding: utf-8 -*-
"""実験で分かったことを、すでにあるノード解説に書き足す。

nodes_add_*.py を1つずつ直す代わりに、ここへ名前ごとにまとめる。
nodes_merge.py が最後にこれを当てる（gotcha は後ろに足し、exps は足し合わせる）。
"""

NOTES = {
    "sweep::2.0": ("既定では曲がり角で管が細り、体積が 1−cos(曲がる角/2) だけ足りない。Stretch Around Turns を入れると 断面積×長さ に一致（実験114）。", ["114"]),
    "attribfill": ("Arrival Time は面に沿った距離ではなく、辺をたどった道のり。四角の網では |x|+|z| になり、細かくしても直らない（実験115・119）。", ["115", "119"]),
    "uvflatten::3.0": ("展開できる形（円筒）はゆがみ0で開く。半球は SCP で13%、ABF で10% ゆがんだ。UV は幅1に収められる（実験116）。", ["116"]),
    "relax": ("pscale は半径。余裕があれば最小距離は 2×pscale の約97%、詰め込みに近いと73〜77% までしか離れない（実験117）。", ["117"]),
    "revolve::2.0": ("閉じた断面を回すと面が裏返り、measure の体積がマイナスになった。Reverse Cross Sections で直る（実験118）。", ["118"]),
    "distancealonggeometry": ("面に沿った本当の距離は Surface（既定）。Edge は辺をたどった道のりで、四角の網では |x|+|z|。Heat Geodesic は約1%短い（実験119）。", ["119"]),
    "heatgeodesic": ("平らな板で、本当の距離より平均1%ほど短く出た。網の向きには左右されにくい（実験119）。", ["119"]),
    "measurethickness": ("丸い殻の厚みはずれ0.000001。角のある板では既定のぼかし（Use Blur / Median of Neighbors）で縁の短い値がにじむ（実験120）。", ["120"]),
    "box": ("Primitive Type が Polygon のまま Use Divisions を入れると、面ではなく開いた線の籠になる（体積0）。点を増やすなら Polygon Mesh と Axis Divisions（実験120）。", ["120"]),
    "polyexpand2d": ("角は丸めずに尖らせる（頂角20°でも）。Divisions は Offset の距離を等分する（0.2・4本なら0.05刻み）（実験122）。", ["122"]),
    "shrinkwrap::2.0": ("中の点は使われず、凸包そのものになる。同じ平面の三角形は1枚の多角形にまとめる（実験123）。", ["123"]),
    "scatter": ("既定の Relax Iterations のままだと、点の一部が板の縁の上にぴったり乗る（1,000点中52点）（実験123）。 density 属性は点を面積あたりの比で配り、Force Total Count を切ると数は Density Scale × 面積のあたりで揺れる（実験155）。", ["123", "155"]),
    "lsystem": ("コッホ曲線（F=F+F--F+F、60°）は 全長4^n・端の間隔3^n どおり。小数の世代は次の世代と同じ点の数で、長さは途中の値（実験124）。", ["124"]),
    "divide": ("既定では n 角形1枚を三角形 n−2 枚に割る（3〜100角形で確認）（実験125）。Maximum Edges = 4 なら (n−2)/2 枚（切り上げ、奇数角形は三角形が1枚混ざる）。Bricker の線は形の端＋Offset から Size おき（実験149）。", ["125", "149"]),
    "facet": ("Unique Points を入れると、点の数が頂点の数まで増える（球 12×24 で 242→1,008）（実験125）。", ["125"]),
    "convertline": ("線の本数は辺の数。閉じた形では 点+面−2（オイラーの式）（実験125）。", ["125"]),
    "polysoup": ("面が1つになり、頂点の数が点の数まで減る（箱 24→8）（実験125）。", ["125"]),
    "edgedivide": ("既定では隣り合う面がそれぞれ新しい点を作るので、箱の辺を k 分割すると 8+24(k−1) 点になる。Share New Points で 8+12(k−1)（実験125）。", ["125"]),
    "cluster": ("重なった塊でも、純度は理論の上限 Φ(s/σ)² どおり（差0.2%以内）。番号は cluster 属性に入る（実験126）。", ["126"]),
    "findshortestpath": ("道の長さ（cost）は distancealonggeometry の Edge と同じ。四角の網では |x|+|z|（実験127）。", ["127"]),
    "extracttransform": ("出すのは P・pivot・orient・distortion だけ。移動と回転はずれ0で取り出せるが、拡大は取り出さず distortion に出る（実験128）。", ["128"]),
    "measure": ("Curvature は既定のまま（Divide Element Area 切・Scale Normalize 入）だと、網の細かさで変わる値になり、式の曲率にならない。Divide Element Area を入れ Scale Normalize を切ると、球・円柱とも0.03%以内（実験129）。", ["129"]),
    "normal": ("Cusp Angle は「隣の面との曲がりがこれより大きければ角を立てる」しきい値。ちょうど等しいとなめらか。既定60°では6角柱まで丸い（実験130）。", ["130"]),
    "bend": ("捕まえる範囲いっぱいに曲げると、長さを保った円弧（半径 = 範囲の長さ ÷ 角度）。範囲の外は曲がり終わりの向きにまっすぐ伸びる（実験131）。", ["131"]),
    "attribpromote": ("Median は値が偶数個のとき真ん中2つの大きい方を返す（平均ではない）。Mode は同数なら最小の値。他の8通りは式どおり（実験132）。", ["132"]),
    "ray": ("Direction（dirx・diry・dirz）には最初から @N.x などの式が入っていて、Python の set では値が変わらない。deleteAllKeyframes() してから入れる。法線の無い形から飛ばすと面の向きへ飛ぶ（実験133・134）。", ["133", "134"]),
    "vdbfrompolygons": ("SDF の値は、表面のまわりの帯の中だけ本当の距離（ずれ0.001未満）。帯の外は ±（Band Voxels × ボクセル）で平らになる（実験138）。", ["138"]),
    "attribblur": ("開いた線では、既定の Pin Border で全部の点が縁とみなされ、1点も動かない。1回のぼかしは「となりの平均へ Step Size だけ近づく」を2度で、ぼけ幅は √(2·s·回数)（実験139）。", ["139"]),
    "copytopoints::2.0": ("N は元の +z を、up は +y を合わせる。orient があれば N と up は使われない。pscale と scale は掛け算（実験140）。", ["140"]),
    "pointsfromvolume": ("1点あたりの体積は、Grid なら s³、Tetrahedral なら s³/√2。箱を Grid で埋めると面の上にも点が並ぶ（実験141）。", ["141"]),
    "platonic": ("Radius は、四面体・八面体・二十面体では頂点までの距離（面積・体積が式と6桁一致）。立方体は一辺が Radius、十二面体は頂点まで 0.9933（実験142）。", ["142"]),
    "circle": ("Polygon は頂点が円周に乗る内接正 n 角形（周 2n·sin(π/n)）。弧の Divisions は辺の数で、点は Divisions+1。Sliced Arc は三角形が Divisions 枚（実験143）。", ["143"]),
    "torus": ("Rows は管の断面、Columns は大きな輪を刻む。体積は Rows と Columns を入れ替えても同じ（内接多角形の比の積）。面積は Columns に敏感（実験144）。", ["144"]),
    "mirror": ("継ぎ目は「元と鏡像の距離」が Consolidate Seam 未満のときだけまとまる（境目ちょうどは不可）。まとまった点は面の上に寄る（実験145）。", ["145"]),
    "clip": ("切った球の面積は 2πh に合う。切り口の点は面の上に乗る。Keep = Both は上下を分けるが、切り口の点は共有のまま（実験146）。", ["146"]),
    "twist": ("体積を保つのは Shear だけ（Twist はほぼ）。Twist の Strength は長さ1あたりの角度（度）。Squash は長さ(1+s)倍・太さ1/(1+s)倍。Taper 系は Strength=1 で変化なし（実験147）。", ["147"]),
    "tube": ("Radius の1つ目が上。体積は円錐台の式 × n·sin(2π/n)/2π。円錐にしても先の点は Columns 個重なったまま（実験148）。", ["148"]),
    "sphere": ("Primitive Type = Polygon は二十面体を分けた測地球で、点 10f²+2・面 20f²（f = Frequency）。同じ点の数なら Polygon Mesh より体積の不足が約3割小さい（実験151）。", ["151"]),
    "polybevel": ("Offset は丸みの半径。Round は Divisions を増やすと角を丸めた箱の体積に近づき、Divisions 1 は Solid（平らな面取り、箱なら 1−6d²+(16/3)d³）と同じ形（実験152）。", ["152"]),
    "polyfill": ("四角形の塞ぎ方（Quadrilateral Fan / Quadrilaterals / Quadrilateral Grid）は辺が奇数の穴を塞がず、警告だけ出して穴のまま流す。Grid は蓋が外へふくらむ。Triangles は1つの穴に n−2 枚（実験154）。", ["154"]),
    "polywire": ("管は Wire Radius の円に内接する正 n 角柱で、両端に蓋が付く（体積を測れる）。Prevent Joint Buckling を入れると、折れ目の輪が曲がりの面の中で r/cos(θ/2) に広がって太さを保つ（実験156）。", ["156"]),
    "voronoifracture::2.0": ("種 N 個で N 個のかけらになり、体積の合計は元のまま。Create Interior Surfaces を切ると表面に触れないかけらは消える。scatter の relax で種を広げると、種が壁へ寄ってかえって大きさがばらつく（実験157・158）。", ["157", "158"]),
    "trail": ("Compute Velocity の v は1秒あたりで、差分の式どおり。Compute Acceleration は Central Difference のときだけ値が入り、Velocity Scale の2乗で縮む（実験159）。", ["159"]),
    "uvlayout::3.0": ("島どうしの大きさの比は保って並べる。長方形12枚で升の48〜84%を埋めた。Island Padding は Search Resolution が粗いほど大きく効く（実験160）。", ["160"]),
    "attribwrangle": ("neighbourcount(0, @ptnum) の合計 ÷ 2 は辺の数。V − E + F で板 1・球 2・トーラス 0 を見分けられた（実験153）。 Python の hou で cook(force=True) しても計算し直さないことがある（時間をはかるときは、コードが読むつまみを変える）。Run Over = Points は Detail のループの約170倍速い（実験173・174）。", ["153", "173", "174"]),
    "attribtransfer": ("Distance Threshold までは値をそのまま運び、その外側 Blend Width の幅で (1 − t²)² に弱める（t = はみ出した距離 ÷ 幅）。届く距離は Threshold + Blend Width（実験161）。", ["161"]),
    "subdivide": ("OpenSubdiv Catmull-Clark では、辺の crease の重み w は「何回目の細分まで尖らせるか」。w ≥ Iterations なら箱は元の形のまま（体積 1）。重み 0 の箱は体積 1/3 ほどに縮む（実験162）。", ["162"]),
    "crease": ("付けた重みは subdivide（OpenSubdiv）で「尖ったまま残す細分の回数」として効く（実験162）。", ["162"]),
    "vellumconstraints": ("Cloth は網を三角形にしてから、辺ごとに伸び（distance）、内側の辺ごとに曲げ（bend）の拘束を作る。四角形で渡しても三角形で渡しても本数は同じ（実験163）。", ["163"]),
    "vellumsolver": ("既定（Constraint Iterations 100・Substeps 1）では、ぶら下げた布が 2.3% 伸びる。伸びは Iterations を上げる方が安く減る（400 回で 0.2%・時間 1.5 倍）。Stretch Stiffness は Substeps 1 では 10^4 と 10^10 で差が出ない（実験170・177）。", ["170", "177"]),
    "vdbfromparticles": ("粒は pscale を半径にした球。重なった粒は尖った和（2つの球の和の体積）になり、Voxel Size を半分にすると体積の不足は約 1/4（実験164）。", ["164"]),
    "popsolver::2.0": ("粒は生まれたフレームでもう1ステップ進む。重力の落下は「速さを先に足す」半陰的オイラーで、1 秒後の落下は Substeps 1 で +13%、誤差は 1/Substeps で縮む（実験165）。", ["165"]),
    "popdrag": ("重力と組み合わせた終端速度は g/k ではなく √(g/k) に近づく（差の2乗に比例する抵抗）。Substeps 1 では 6〜12% 遅い。止まった空気の popwind と同じ落ち方（実験166・179）。", ["166", "179"]),
    "popwind": ("風との速さの差は u₀/(1 + u₀·k·t) で縮む（差の2乗に比例する抵抗）。風だけなら Substeps によらず同じ値。Wind Velocity は windx・windy・windz で、Wind Speed はその倍率（実験175・179）。", ["175", "179"]),
    "rbdbulletsolver": ("落とした箱は地面ぴったり（底 −0.0001）で止まり、Collision Padding を 0・0.02・0.05 と変えても止まる高さは6桁まで同じ。当たった瞬間だけ 0.007〜0.008 沈む（実験167）。", ["167"]),
    "heightfield_noise": ("Amplitude は高さの幅ではない。幅は地面に入る模様の数で決まり、Element Size が地面の半分なら Amplitude の 23%、1/20 なら 62%。高さは Amplitude にぴったり比例し、Center Noise を切ると全体が Amplitude/2 上がる（実験168・176）。", ["168", "176"]),
    "heightfield_erode": ("土の量（高さの合計）を保たない。40 フレームで平均の高さが約 5 下がり、sediment・debris を足しても元に戻らない（実験169）。", ["169"]),
}


# 実験181〜199 の分。すでにある名前には後ろへ足す。
MORE = {
    "attribwrangle": ("近くの点を探すなら pcfind と nearpoints は同じ結果・同じ速さ。pcopen + pcfilter は約1.6倍遅く、距離で重みを付けた平均になる（重みの形は点の並びしだいで、式は分からなかった）（実験181・182）。", ["181", "182"]),
    "rbdbulletsolver": ("沈み込みは Bullet Substeps で決まる。1 だと 0.38 めり込んで 0.06 沈んだまま、既定 10 でも当たった瞬間 0.005 沈み、50 でほぼ 0。時間はほぼ変わらない（実験183）。", ["183"]),
    "mpmsource": ("箱に詰める粒は 体積 ÷ Particle Separation³ 個。pscale には Separation そのものが入る（球で見せると隣と重なる）。Jitter 0 では面の上にも並び (1/s + 1)³ 個（実験184）。", ["184"]),
    "smooth": ("縮み方は r = 1/(1 + Strength·L^q/C(2q, q))（L = 2(1 − cos(2π/点の数))、q は Filter Quality）で、36 通り6桁一致。Strength をいくら上げてもゼロまでは縮まず、Filter Quality を上げるほど形を保つ。点が等間隔なら3つの Method は同じで、開いた線の端は Constrained Boundary（既定）で止まる。点の間隔がそろわないと粗い側を大きく縮め、Method を変えても直らない（実験185〜187）。", ["185", "186", "187"]),
    "hairgen::2.0": ("毛の本数は Density × 面積。1本は Segments + 1 点で、長さは Length ちょうど（実験188）。", ["188"]),
    "pack": ("箱 100 個を USD にすると、パックしなければメッシュ 1 つ、Point Instancer で 6 プリム、Xforms で 202 プリム。1 万個では Point Instancer 0.32 MB に対し Native Instances 4.6 倍、Unpack 7.4 倍の大きさ（実験189・190）。", ["189", "190"]),
    "sphere": ("Polygon Mesh の球のいちばん深いへこみは sin²(Δ/2)（Δ は隣の行の角度）。分割を倍にするたび 1/4 になり、平均はその 0.56 倍（実験191）。", ["191"]),
    "polyextrude": ("Inset は上の面を縁から i だけ内側へ寄せ、上の面の辺は 1 − 2i。体積は角錐台の式どおり。i ≥ 0.5 で四角錐になり、それ以上は裏返らず上の点が重なる（実験192）。", ["192"]),
    "popsource": ("Constant Birth Rate は1秒あたり。端数の粒はフレームごとに運で決まる（Rate 10 で 2 秒 27 粒）。数えられるフレームは Life × fps − 1/Substeps で、0.5 秒の粒は Substeps 1 で 11 フレーム（実験193・194）。", ["193", "194"]),
    "vdbreshapesdf": ("Dilate・Erode は面を Offset × 升の大きさだけ押し出す（引っ込める）。Iterations は効かない。Open・Close は球をほぼ変えない。箱の角では、Open は辺を円弧で丸め、半径は Offset × 升より約 3 升大きい（帯の幅によらない）。Close は凸な箱も少し削り、帯を 25 升に広げると削れは 0.2〜0.4% まで減る（実験195〜199）。", ["195", "196", "197", "198", "199"]),
    "vdbfrompolygons": ("箱を Open で丸めたときの体積は、帯 3 升と 6 升で違い、6 升以上では同じだった。広げるほど時間は増える（実験197・199）。", ["197", "199"]),
    "convertvdb": ("Pyro の出力を VDB にしただけでは、キャッシュは小さくならなかった（焚き火 48 フレームで 150 MB → 155 MB）。0 でない値を持つ速度 vel が升の 6 割以上に残るため。Prune Tolerance 0.01 でも変わらない。16 bit で書くと約半分（実験204）。", ["204"]),
    "volumewrangle": ("vel.x・vel.y・vel.z の 3 つのボリュームは、コードの中で v@vel として 1 つにまとめて読み書きできた。煙も炎も無い升の v@vel を 0 にしてから VDB・16 bit にすると、焚き火のキャッシュが 16 分の 1 になった（実験204）。", ["204"]),
    "blast": ("Group に @name=vel.* と書き、Group Type を Primitives にすると、Pyro の速度のボリューム 3 つだけを消せる。焚き火のキャッシュは 24 分の 1 になった（実験204）。", ["204"]),
    "karma": ("被写界深度（Enable Depth of Field）とモーションブラーを入れても、960×540・16 サンプルで 25 秒 → 27 秒ほどしか延びなかった。Primary Samples を 16 → 256 にすると 3.3 倍の時間でも、既定の Noise Level 0.01 のままではざらつきは減らなかった。Denoiser を oidn にすると、ほぼ同じ時間でいちばん滑らかだった（実験205）。Volume Step Rate は大きいほど細かい。焚き火では既定 0.25 のままでよい（0.125 に下げても速くならず、1 に上げると 1920×1080 で 23% 遅い。実験207）。濃い煙を正しい濃さで撮るなら上げる（一様な煙の箱で、1 は光の吸収の式とぴったり、0.25 は Density Scale 4 で 12% 明るい。実験216）。", ["205", "207"]),
    "particlefluidsurface": ("形を決めるのは Influence Scale と Method。ダムブレイクの跳ね上がりで、Influence 2 は体積 104%（しぶきが細かく残る）、5 は 87%（丸まって痩せる）。Spherical は粒の球が残ってつぶつぶになる。Filtering（Dilate・Smooth・Erode）でさざ波が消え、時間は 1.3 倍。Voxel Scale 0.5 は面が 1.9 倍・時間 2.3 倍。Neural Point Surface は 1.6 倍（実験208）。", ["208"]),
    "ropgeometry": ("TOP の ropgeometry でシミュレーションを書き出すときは、Evaluate Using を Frame Range にし、Frame Range（最初から式が入っている）を入れ、All Frames in One Batch を入れる。既定の Single Frame では仕事 1 つにつき 1 フレーム目しか書かず、焚き火が燃え始めのまま（34 KB）だった。Valid Frame Range を変えても効かない（実験209）。", ["209"]),
    "vellumsolver": ("布は、ぶつかる物から Default Thickness の分だけ離れて止まる。テーブルクロスは既定 0.01 で天板から 10 mm 浮き、0.0025 で 2.5 mm（めり込みは 0）。厚いほど裾が短く垂れる（実験211）。試しは 44×56 程度の粗い布で足りるが、角の垂れは短く出る（実験206）。", ["206", "211"]),
    "vellumconstraints": ("Cloth の曲げの硬さ（Bend の Stiffness、既定 1 × 10⁻¹）は、テーブルクロス（1.9 × 1.45 m、66×84）では下げても形がほぼ同じ（0.001 で差 1.1 cm）。10 以上にすると布が張り、机の縁から 15 cm 張り出して裾が 4 cm 上がった（実験217）。", ["217"]),
    "kma_pyroshader": ("Enable Scatter を切った煙は、光の吸収の式 exp(−Density Scale × density × 厚み[m]) どおりに光を減らした。Density Scale を倍にすると、届く光は 2 乗に減る。Karma の Volume Step Rate が既定 0.25 だと濃い煙が少し明るく出て（Density Scale 4 で +12%）、1 で式とぴったり（実験216）。", ["216"]),
    "cam": ("Enable Depth of Field（Karma）を入れたときのぼけの直径は f²(d−s)/(N·d·s) に 0.9% 以内で一致した（焦点距離 100 mm・ピント 2 m・物まで 20 m）。F-Stop を半分にすると直径は倍。写真の薄いレンズの式より約 5% 小さい（実験214）。", ["214"]),
    "principledshader::2.0": ("金属（Metallic 1）の Roughness は 0.2 まで見た目がほぼ同じで、0.3 からハイライトが広がる。0.7 で明るさ 15%・広さ 2.4 倍（実験212）。Subsurface を入れた半径 0.5 の球は、Subsurface Distance 0.1〜0.3 で逆光に透け（0.3 で真ん中 5.3 倍）、1 ではかえって暗い。SSS Mode を Random Walk にすると同じ距離でもよく透けた（実験213）。", ["212", "213"]),
    "pyrosolver": ("出力のボリュームは density・temperature・flame と vel.x・vel.y・vel.z の 6 つ。そのまま .bgeo.sc に書くと、Voxel Size 0.04 の焚き火で 1 フレーム約 3 MB、その 9 割以上が vel だった（実験204）。Turbulence は、Use Control Field が入っていると焚き火でまったく効かず（揺らぎなしと全フレーム同じ）、切ると炎が 1.21 → 1.31 m になった。作った直後の Use Control Field は「入り」だが、revertToDefaults で戻る値は「切り」なので、台本で戻すときは注意（実験220）。", ["204", "220"]),
}
for _k, (_t, _e) in MORE.items():
    if _k in NOTES:
        NOTES[_k] = (NOTES[_k][0] + " " + _t, sorted(set(NOTES[_k][1]) | set(_e)))
    else:
        NOTES[_k] = (_t, _e)


def apply(groups):
    by_name = {}
    for g in groups:
        for n in g["nodes"]:
            by_name[n["name"]] = n
    missing = []
    for name, (text, exps) in NOTES.items():
        node = by_name.get(name)
        if node is None:
            missing.append(name)
            continue
        old = node.get("gotcha", "")
        if text not in old:
            node["gotcha"] = (old + " " + text).strip()
        node["exps"] = sorted(set(node.get("exps", [])) | set(exps))
    return missing
