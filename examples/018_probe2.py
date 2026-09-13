"""本番前の最後の確認。乱数の種・背景・解像度のパラメータ名を洗う。

ノイズの量を正しく測るには、同じ設定で種だけ変えた2枚が要る。
基準画との差で測ると、基準画自身のノイズが混ざるため。
"""

import hou

karma = hou.node("/out").createNode("karma", "probe2")
names = [p.name() for p in karma.parms()]

for key in ("seed", "background", "resolution", "res", "engine", "aa", "variance"):
    hits = [n for n in names if key in n.lower()]
    print(f"{key:12s}: {hits[:14]}")

print()
for name in ("resolutionx", "resolutiony", "res_fraction", "override_camerares"):
    parm = karma.parm(name)
    if parm is None:
        continue
    print(f"{name}: value={parm.eval()!r} disabled={parm.isDisabled()} "
          f"hidden={parm.isHidden()}")
