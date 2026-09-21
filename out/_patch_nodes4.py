# -*- coding: utf-8 -*-
import io
p = "nodes_add_4.py"
s = io.open(p, encoding="utf-8").read()
G = {
 "spiral": ("多角形で出した長さは折れ線の式と6桁一致。既定の1巻き50分割で、なめらかならせんより 0.06% 短い。高さ0で半径一定だと、同じ円を何周もなぞるだけ（実験105）。", "105"),
 "attribrandomize": ("正規分布の Scale Around Middle は標準偏差。整数の一様（Uniform Discrete）は上端を含む。Inside Sphere は球の中まで均一（長さの平均 0.75）（実験106）。", "106"),
 "extractcentroid": ("Center of Mass は、閉じた形なら体積の中心、開いた形なら面積の中心。点の平均ではない。Convex Hull Center は凸包の体積の中心（実験107）。", "107"),
 "triangulate2d::3.0": ("三角形は必ず 2n−2−h 枚（n は点、h は外周の点）。面を張る範囲は凸包で、へこみも埋まる（実験108）。", "108"),
 "groupexpand": ("点は辺でつながった隣へ（k 段で菱形 2k²+2k+1 個）。面の既定は角を共有する隣まで広がる（(2k+1)² 個）。辺だけにしたいときは Require Primitives Share Edge を入れる（実験109）。", "109"),
 "copyxform": ("同じ変形をくり返すのではない。i 個目は 移動 i 倍・回転 i 倍・拡大 i 乗 を1回かけた形。回転と移動を混ぜると輪にならず前へ進む（実験110）。", "110"),
 "pointjitter": ("Scale は幅。各軸 −s/2〜+s/2 の一様で、球ではなく箱の中に散る（角の方向には √3 倍動く）（実験111）。", "111"),
 "vdbcombine": ("Operation の選択肢は18個あり、SDF Intersect / Difference は後ろのほう。球2つの和・積・差は式に収束するが、どれも体積は少なめに出る（実験112）。", "112"),
 "timeblend::2.0": ("速度が無いと直線でつなぐ。v を持たせて Use Velocity When Interpolating Position を入れると2次の動きは誤差0。v は1秒あたりの値として読まれる（実験113）。", "113"),
}
for name, (gotcha, exp) in G.items():
    key = '{"name": "%s", "kind": "SOP",' % name
    i = s.index(key)
    j = s.index('"params":', i)
    j = s.index("]]", j) + 2
    s = s[:j] + ',\n         "gotcha": "%s",\n         "exps": ["%s"]' % (gotcha, exp) + s[j:]
io.open(p, "w", encoding="utf-8").write(s)
print("ok")
