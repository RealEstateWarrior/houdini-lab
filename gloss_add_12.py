# -*- coding: utf-8 -*-
"""用語を足す（その12: 実践47〜で出てきた言葉）。"""

ADD = {
    "render": [
        {"term": "シーン / Sheen", "reading": "シーン",
         "def": "布や苔のような細かい毛のある表面が、斜めから見たときにふわっと明るく光る見え方。principledshader の Sheen を上げると足せる（実践「苔むした石を作る」「テーブルクロスを掛ける」）。"},
        {"term": "発光 / Emission", "reading": "はっこう",
         "def": "表面そのものが光を出すこと。principledshader の Emission Intensity で強さ、Emission Color で色を決める。Use Point Color を入れると点の色 Cd がそのまま光の色になる（実践「花火を打ち上げる」）。"},
        {"term": "透過色 / Transmission Color", "reading": "とうかしょく",
         "def": "透ける材質の中を光が通るときに付く色。Transmission Distance の長さを進むと、その色になる。厚い所ほど濃く色づく（ゼリーの赤、板ガラスの縁の緑）。"},
    ],
    "simulation": [
        {"term": "active 属性", "reading": "アクティブぞくせい",
         "def": "RBD（Bullet）で、その塊を動かすかどうかを決める点の値。0 にすると、ぶつかられても動かない壁のようになる。窓枠にはまったガラスの縁の破片を止めるのに使った（実践「窓ガラスを割る」）。"},
        {"term": "拘束の強さ / Strength", "reading": "こうそくのつよさ",
         "def": "破片どうしをくっつけておくつながり（Glue）が、どれだけの衝撃で切れるか。小さいほど広く割れる。同じ場面で 0.8 なら 41 個、5 以上なら 0 個の破片が動いた（実践「窓ガラスを割る」）。"},
        {"term": "インパルス発生 / Impulse Activation", "reading": "インパルスはっせい",
         "def": "popsource で、決めたフレームに一度にまとめて粒を生む仕組み。Emission Type が All Points のときは、Activation が 1 のフレームごとに全部の点から生まれるので、1 フレーム目だけ生むなら式 $FF == 1 を入れる（実践「花火を打ち上げる」）。"},
    ],
}
