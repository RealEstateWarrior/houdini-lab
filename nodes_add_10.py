# -*- coding: utf-8 -*-
"""ノード解説を足す（その10: 実践47〜で出てきたノード）。

つまみ名は out/_dump10.json（21.0.700 の実物）から取った。
"""

ADD = {
    "uv": [
        {"name": "material", "kind": "SOP",
         "one": "形に材質（マテリアル）を割り当てる。",
         "what": "Material に /mat の中の材質の場所を入れると、その形を Karma で撮ったときにその材質で描かれる。"
                 "Group を指定すれば一部だけに当てられ、後ろにもう1つつなげば、そのグループだけ上書きできる"
                 "（実践「窓ガラスを割る」で、球だけを鉄にした）。ビューポートでは透明や光る材質はそのままには見えない。",
         "params": [["shop_materialpath1", "当てる材質"], ["group1", "当てる範囲（グループ）"], ["num_materials", "当てる組の数"]]},
    ],
    "vop": [
        {"name": "kma_pyroshader", "kind": "VOP",
         "one": "Karma で煙と炎を撮るための材質。",
         "what": "ボリュームの値から、煙の濃さと炎の光を決める。Enable Fire を入れ、Intensity Volume と Color Volume に"
                 "光らせたいボリュームの名前（flame など）を書く。色は Fire Color Ramp で決める。"
                 "焚き火では Intensity Scale 1.5、数 mm の厚みしかないろうそくの炎では 150 が要った（実践「焚き火を燃やす」「ろうそくの炎をともす」）。",
         "params": [["enablefire", "炎を光らせる"], ["fireintscale", "炎の明るさの倍率"], ["fireint_volumename", "明るさを読むボリューム"],
                    ["firecolor_volumename", "色を読むボリューム"], ["firecolorramp", "炎の色の並び"], ["densityscale", "煙の濃さの倍率"]]},
    ],
    "pop": [
        {"name": "popwrangle", "kind": "DOP",
         "one": "POP の粒に、VEX で自分の決まりを足す。",
         "what": "dopnet の中で popsolver の力の入口につなぐ。毎ステップ、粒ごとに VEX が走る。@TimeInc（1ステップの秒数）を使うと、"
                 "向き orient を qmultiply で少しずつ回したり、速さ v に揺れを足したりできる（実践「桜の花びらが舞い散る」）。",
         "params": [["snippet", "VEX のコード"], ["activate", "有効にする"]]},
    ],
    "pdg": [
        {"name": "topnet", "kind": "OBJ",
         "one": "PDG（TOP ノード）を置くためのネットワーク。",
         "what": "中に wedge や ropgeometry などの TOP ノードを並べ、「番号を変えて同じ処理を何回も回す」作業を組む。"
                 "作ると localscheduler（手元のパソコンで順に処理する係）が1つ入っている。",
         "params": [["topscheduler", "既定の係（スケジューラー）"]]},
        {"name": "wedge", "kind": "TOP",
         "one": "番号や値を少しずつ変えた「作業」を、決めた数だけ作る。",
         "what": "Wedge Count の数だけ作業ができ、それぞれに番号 @wedgeindex（0, 1, 2, …）が付く。SOP のつまみに @wedgeindex を使う式を"
                 "入れておくと、作業ごとに違う形になる。値の並びを属性として足すこともできる（実践「PDG で形違いを一度に書き出す」）。",
         "params": [["wedgecount", "作業の数"], ["wedgeattributes", "変える属性の数"]]},
        {"name": "ropgeometry", "kind": "TOP",
         "one": "作業ごとに、SOP の形をファイルに書き出す。",
         "what": "SOP Path に書き出すノード、Output File に名前を入れる。名前に `@wedgeindex` を入れないと、全部の作業が同じファイルに"
                 "上書きして1つしか残らなかった。作業は別の Houdini が保存済みの hip を開いて行うので、Cook の前に保存する。",
         "params": [["soppath", "書き出す SOP"], ["sopoutput", "書き出すファイル名"]]},
    ],
    "vdb": [
        {"name": "cloud::2.0", "kind": "SOP",
         "one": "面で囲んだ形を、雲のボリューム（濃さの升目）にする。",
         "what": "中まで density で満たしたボリュームになる。升の細かさは Uniform Sampling Divs（長い辺をいくつに割るか）、"
                 "濃さは Density Multiplier。縁のふわふわは後ろの cloudnoise で付ける（実践「もくもくの雲を浮かべる」）。",
         "params": [["samplediv", "長い辺の分割数"], ["densitymultiplier", "濃さの倍率"]]},
        {"name": "cloudnoise", "kind": "SOP",
         "one": "雲のボリュームの縁を、ノイズで削ってふわふわにする。",
         "what": "Amplitude で削る深さ、Element Size で渦の大きさ、Octaves で重ねる細かさを決める。中の濃さを削るもので、"
                 "雲の大きさを変えたいときは元の形を変える。",
         "params": [["noiseamount", "削る深さ"], ["noiseelementsize", "渦の大きさ"], ["noiseoctaves", "重ねる細かさ"]]},
        {"name": "volume", "kind": "SOP",
         "one": "空の箱型のボリューム（升目に値を持つ入れ物）を作る。",
         "what": "Name に density と書けば「濃さ」の入れ物になり、後ろの volumewrangle で升ごとに値を入れる。"
                 "大きさは Size、升の細かさは Uniform Sampling Divs で決める（長い辺をその数で割った大きさが升）。"
                 "霧のようにゆるやかに変わるものは升が粗くてよい（実践「霧の森に光の筋を差す」は 30 m を 110 分割）。",
         "params": [["name", "ボリュームの名前（density など）"], ["size", "箱の大きさ"], ["t", "箱の中心"],
                    ["initialval", "はじめの値"]]},
    ],
}

GROUPS_NEW = [
    ("pdg", "PDG（TOPs）で作業を回す",
     "番号や値を変えながら、同じ処理を何回も回して結果を書き出す道具。"),
]
