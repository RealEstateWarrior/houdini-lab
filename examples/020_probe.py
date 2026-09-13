"""実験020の下調べ — POP の DOP ネットワークはどう組むのか。

019で学んだとおり、まず入力の名前を見る。総当たりはしない。
"""

import hou

geo = hou.node("/obj").createNode("geo", "pop_test")
dop = geo.createNode("dopnet", "popnet")

for kind in ("popobject", "popsolver", "popsource", "gravity", "merge"):
    node = dop.createNode(kind, f"probe_{kind}")
    print(f"--- {kind}")
    print("  入力:", node.inputNames())
    print("  出力:", node.outputNames())
    if kind == "popsource":
        names = [p.name() for p in node.parms()]
        print("  発生に関係しそうなパラメータ:",
              [n for n in names if any(k in n.lower()
                                       for k in ("rate", "birth", "const", "impulse",
                                                 "emit", "sourcegroup", "soppath"))][:16])
    if kind == "gravity":
        print("  重力の既定:", node.parmTuple("force").eval()
              if node.parmTuple("force") else "なし")

print("\ndopimport SOP の入口")
imp = geo.createNode("dopimport", "imp")
names = [p.name() for p in imp.parms()]
print("  ", [n for n in names if any(k in n.lower()
                                     for k in ("doppath", "objects", "importstyle",
                                               "geometrytype"))][:14])
