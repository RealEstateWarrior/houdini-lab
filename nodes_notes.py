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
