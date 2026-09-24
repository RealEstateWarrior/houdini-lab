# -*- coding: utf-8 -*-
"""ノード解説を足す（その11: VEX 解説ページと実験204〜206 で出てきたノード）。

つまみ名は out/_dump11.json（21.0.700 の実物）から取った。
"""

ADD = {
    "pdg": [
        {"name": "localscheduler", "kind": "TOP",
         "one": "PDG の仕事を、手元のパソコンで同時にいくつか走らせる係。",
         "what": "topnet を作ると最初から 1 つ入っている。仕事（work item）ごとに別の Houdini を立ち上げて回す。Total Slots で同時に回す数を決め、"
                 "既定は「CPU の 1/4」（32 スレッドなら 8）。焚き火を 8 通り回したとき、同時 8 本は 1 つの Houdini で順に回すより 1.6 倍速く、"
                 "同時 1 本では 2.2 倍遅かった（実験209）。Custom Slot Count にすると数を直接入れられる。",
         "params": [["maxprocsmenu", "同時に回す数の決め方"], ["maxprocs", "同時に回す数（Custom のとき）"]]},
    ],
    "program": [
        {"name": "attribexpression", "kind": "SOP",
         "one": "よく使う属性を、1 行の VEX で書き換える。",
         "what": "Attribute Wrangle の手軽な版。Attribute で書き換える属性（Position・Color・Scale など 10 種と Custom）を選び、"
                 "VEXpression に 1 行の式を書く。式の中の self は「いまの値」。作った直後は Attribute が Position (P)、式が self で、"
                 "形は何も変わらない。Attribute Class は Detail・Primitives・Points・Vertices から選ぶ（既定は Points）。"
                 "何行にもわたる処理は attribwrangle で書く（VEX 解説）。",
         "params": [["preset1", "書き換える属性"], ["snippet1", "式（VEXpression）"], ["bindclass", "何ごとに走らせるか"]]},
        {"name": "volumevop", "kind": "SOP",
         "one": "ボリュームの升ごとの計算を、箱（VOP）をつないで組む。",
         "what": "volumewrangle のコードの代わりに、中に VOP の箱を並べて組む。中身は VEX になって、升 1 つずつに走る。"
                 "コードを書くなら volumewrangle の方が短い。実験204 では、煙の無い升の速度を 0 にする処理を volumewrangle の 2 行で書いた。",
         "params": [["vex_exportlist", "書き込むボリューム"], ["autobind", "名前で自動で結ぶ"], ["vex_multithread", "同時に並べて計算する"]]},
        {"name": "solver", "kind": "SOP",
         "one": "前のフレームの結果に、同じ処理を毎フレーム重ねていく。",
         "what": "中に入ると Prev_Frame（前のフレームの形）があり、そこから処理をつないで OUT へ出す。"
                 "中に「@P.y += 0.1;」の wrangle を置いたところ、点の高さはフレーム 1 で 0.1、2 で 0.2、10 で 1.0 になった"
                 "（Start Frame 1 のフレームですでに 1 回重なる）。フレームを戻すと、覚えている結果（4 なら 0.4）が出た。"
                 "足跡が残る・少しずつ育つ・濡れが広がる、のような「前の結果を覚えておく」処理に使う。",
         "params": [["startframe", "始めるフレーム"], ["substep", "1 フレームを何回に分けるか"], ["resimulate", "計算をやり直す"],
                    ["cacheenabled", "結果を覚えておく"]]},
    ],
}
