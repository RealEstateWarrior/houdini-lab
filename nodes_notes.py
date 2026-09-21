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
    "scatter": ("既定の Relax Iterations のままだと、点の一部が板の縁の上にぴったり乗る（1,000点中52点）（実験123）。", ["123"]),
    "lsystem": ("コッホ曲線（F=F+F--F+F、60°）は 全長4^n・端の間隔3^n どおり。小数の世代は次の世代と同じ点の数で、長さは途中の値（実験124）。", ["124"]),
    "divide": ("既定では n 角形1枚を三角形 n−2 枚に割る（3〜100角形で確認）（実験125）。", ["125"]),
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
}


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
