# -*- coding: utf-8 -*-
"""ノード解説を足す（その13: 実験222 で出てきた LOP と ROP）。つまみの表示名は 21.0.700 の実物で確かめた。"""

ADD = {
    "lop": [
        {"name": "sopimport", "kind": "LOP",
         "one": "SOP の形を、Solaris（USD の場面）に読み込む。",
         "what": "SOP Path に読みたい SOP ノードを入れる。パックした形の渡し方は Enable Packed Primitives を入れて Packed Primitives で選ぶ。"
                 "Create Point Instancer（形 1 つ＋置く点の並び）・Create Native Instances（既定）・Create Xforms・Unpack の 4 つ。"
                 "草 3 万本では、Point Instancer 6.7 秒・Native Instances 17.1 秒・Xforms 31.0 秒で撮れた。"
                 "Point Instancer なら 10 万本 12 秒・100 万本 37 秒で、/obj の Karma（10 万本 793 秒）より段違いに速い（実験222）。",
         "params": [["soppath", "読む SOP（SOP Path）"], ["enable_packedhandling", "パックの渡し方を選ぶ（Enable Packed Primitives）"],
                    ["packedhandling", "パックの渡し方（Packed Primitives）"]]},
        {"name": "sceneimport", "kind": "LOP",
         "one": "/obj のオブジェクト・カメラ・ライトを、まとめて Solaris に読み込む。",
         "what": "Objects に読みたいオブジェクトの名前を並べる。/obj で組んだカメラとライトはそのまま使い、重い形だけ sopimport で読み直す、という使い方ができる（実験222）。"
                 "/obj の Karma（ROP）も、中ではこれと同じように場面を USD に直してから撮っている。",
         "params": [["objects", "読むオブジェクト（Objects）"], ["filter", "種類で絞る（Filter）"]]},
    ],
    "rop": [
        {"name": "usdrender", "kind": "ROP",
         "one": "Solaris（LOP）の場面を、Karma などで撮って画にする。",
         "what": "LOP Path に撮りたい LOP ノードを入れ、Render Delegate で Karma（BRAY_HdKarma）を選ぶ。"
                 "Override Camera でカメラの場所（例 /hero_cam）、Override Resolution で画の大きさ、Override Output Image で書き出す先を決められる。"
                 "草を LOP の sopimport で読んで撮るときに使った（実験222）。",
         "params": [["loppath", "撮る LOP（LOP Path）"], ["renderer", "描く係（Render Delegate）"],
                    ["override_camera", "カメラ（Override Camera）"], ["outputimage", "書き出す先（Override Output Image）"]]},
    ],
}
