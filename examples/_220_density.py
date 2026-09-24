# 実験220 の補足: 焚き火の density（Use Control Field が見る場）がどれだけあるか
import importlib.util, os, sys, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "examples"))
import hou
import numpy as np
spec = importlib.util.spec_from_file_location("e202", os.path.join(HERE, "examples", "202_pyro_campfire_cost.py"))
e202 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e202)
_, s0, _ = e202.build(0.1); hou.setFrame(3); s0.geometry()
geo, solver, _ = e202.build(0.04)
for k in ("flames_lifespan", "buoyancylift", "tempcooling", "enable_turbulence", "turbulence", "turbulence_usecontrol"):
    solver.parm(k).revertToDefaults()
for k, v in {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0}.items():
    solver.parm(k).set(v)
out = {}
for f in range(1, 49):
    hou.setFrame(f); g = solver.geometry()
    if f in (24, 48):
        vals = {}
        for name in ("density", "temperature", "flame"):
            v = g.prim(0) and [p for p in g.prims() if p.attribValue("name") == name] if g.findPrimAttrib("name") else []
            vals[name] = round(float(np.max(np.array(v[0].allVoxels()))), 4) if v else None
        out[f] = vals
print(json.dumps(out))
json.dump(out, open(os.path.join(HERE, "out", "220_density.json"), "w"))
