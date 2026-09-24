# -*- coding: utf-8 -*-
"""ノード解説を足す（その12: 実践「夕暮れの海」の作り直しで出てきたノード）。

つまみの表示名は 21.0.700 の実物（hython の parm().description()）で確かめた。
"""

ADD = {
    "sim": [
        {"name": "oceanspectrum", "kind": "SOP",
         "one": "風の強さと向きから、海の波の設計図（スペクトル）を作る。",
         "what": "「どの長さの波が、どれだけの高さで、どちらへ進むか」をまとめた設計図を作る。自分では形を動かさず、oceanevaluate に渡して点を動かしてもらう。"
                 "Grid Size は設計図がくり返す間隔（m）で、その幅より広く写すと同じ波の並びが出てくる。Wind の Speed が強いほど長く高い波が混ざり、Chop は波の頭のとがり方。"
                 "Amplitude の Scale（既定 3）は高さの倍率で、Grid Size 300・Speed 7 では既定のままだと高さのばらつき（標準偏差）が 1.92 m にもなった。"
                 "実践「夕暮れの海」では、うねり（Grid Size 300）・風の波（37）・さざ波（4.3）の 3 つを merge でまとめて、1 つの oceanevaluate に渡した。",
         "params": [["gridsize", "くり返す間隔（Grid Size）"], ["windspeed", "風の強さ（Wind の Speed、m/秒）"],
                    ["winddir", "風の向き（Direction）"], ["chopscale", "波の頭のとがり（Chop）"],
                    ["ampscale", "波の高さの倍率（Amplitude の Scale）"], ["res", "設計図の細かさ（Resolution Exponent）"]]},
        {"name": "oceanevaluate", "kind": "SOP",
         "one": "波の設計図どおりに、板の点を上下・前後に動かす。",
         "what": "左の入力に動かしたい形（grid など）、右に oceanspectrum の設計図（いくつ merge してもよい）をつなぐ。"
                 "Time に $T（今の秒数）を書くと、再生に合わせて波が進む。Time が 0 のままだと、どのフレームも同じ形で止まる。"
                 "Cusp Attribute を入れると、波の頭がとがった所に cusp という値が付き、白波の目印に使える。"
                 "点の並びは自由なので、カメラから水平線まで扇形に広げた板（近くは細かく遠くは粗い）を渡すと、足もとから水平線まで 1 枚で波立てられる（実践「夕暮れの海」）。",
         "params": [["time", "何秒目の波か（Time）"], ["cusp", "波の頭のとがりを cusp に書く（Cusp Attribute）"],
                    ["deformgeo", "入力の形を動かす（Deform Input Geometry）"]]},
    ],
}
