"""実験018の下調べ。Karma のROPが何という名前で、どんなパラメータを持つかを見る。

先に名前と既定値を確かめてから本番を組む。mountain の rough / oct のときのように、
思い込んだ名前が存在しないことがあるため。
"""

import hou

out = hou.node("/out")
names = sorted(out.type().childTypeCategory().nodeTypes())
hits = [n for n in names if "karma" in n.lower() or "usdrender" in n.lower()]
print("ROP の候補:", hits)

for name in hits:
    node = out.createNode(name, f"probe_{name}")
    parms = [p.name() for p in node.parms()]
    interesting = [p for p in parms
                   if any(k in p.lower() for k in
                          ("sample", "picture", "camera", "res", "engine", "denois"))]
    print(f"\n--- {name} / 入力{len(node.inputs())} / パラメータ{len(parms)}")
    print("   関係ありそうなもの:", interesting[:24])
    node.destroy()

# LOP 側にもレンダラーがある。どちらで組むかを決めるために見ておく。
stage = hou.node("/stage")
if stage is not None:
    lop_types = sorted(stage.type().childTypeCategory().nodeTypes())
    print("\nLOP のレンダ関係:",
          [n for n in lop_types if "karma" in n.lower() or "rendersettings" in n.lower()])
