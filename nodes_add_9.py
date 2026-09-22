# -*- coding: utf-8 -*-
"""ノード解説を足す（その9: 繰り返しと Python）。

つまみ名は out/_dump9.json（21.0.700 の実物）から取った。
"""

ADD = {
    "program": [
        {"name": "python", "kind": "SOP",
         "one": "Python のコードで形を作り変える。",
         "what": "hou.pwd().geometry() で入ってきた形を読み書きする。点の値はまとめて読み書き（pointFloatAttribValues など）すると速い。同じ処理なら VEX の wrangle の方がずっと速い（実験173）。",
         "params": [["python", "コード"]]},
        {"name": "block_begin", "kind": "SOP",
         "one": "繰り返し（for-each）の入口。",
         "what": "block_end と組で使う。Method で「かけらごと」「回数ぶん前の結果を渡す」などを選ぶ。中に置いた処理が、かけら1つずつ（または1回ずつ）に走る。",
         "params": [["method", "繰り返しの種類"], ["blockpath", "組になる出口"]]},
        {"name": "block_end", "kind": "SOP",
         "one": "繰り返し（for-each）の出口。回数やかけらの分け方を決める。",
         "what": "Iteration Method で、かけらごと（Pieces）か回数（Count）かを選び、Gather Method で結果を合わせる（Merge）か次へ渡す（Feedback）かを選ぶ。かけらの数に比例して時間がかかる（1000 個で約 37 ミリ秒、実験174）。",
         "params": [["itermethod", "繰り返し方"], ["method", "結果のまとめ方"], ["attrib", "かけらを分ける属性"], ["iterations", "回数"]]},
        {"name": "compile_begin", "kind": "SOP",
         "one": "まとめて組み立てる区間（compile block）の入口。",
         "what": "compile_end と組で使い、中のノードをまとめて組み立てて速く回す。for-each を囲むと約 35% 速くなった（実験174）。",
         "params": [["blockpath", "組になる出口"]]},
        {"name": "compile_end", "kind": "SOP",
         "one": "まとめて組み立てる区間（compile block）の出口。",
         "what": "Enable Compilation を入れると、入口からここまでを一度に組み立てる。中で使えないノードがあると組み立てられない。",
         "params": [["docompile", "組み立てを使う"], ["forcerecompile", "組み立て直す"]]},
    ],
}
