"""実験058 — Apprentice で外へ出せる形式はどれか。全部試す。

Houdini で組んだものは、最後は別のソフト（Unreal Engine など）へ渡すことになる。
その橋渡しに使われるのが FBX や glTF、USD、Alembic といった形式。

<strong>ところが Apprentice には書き出しの制限がある。</strong>
どれが通ってどれが止まるのか、噂ではなく<strong>全部試して確かめる</strong>。

通った形式については、<strong>読み直して往復の誤差も測る</strong>。

  A. 形式ごとに、書き出せるか
  B. 通ったものは、読み直して点の位置が保たれるか
  C. ファイルの大きさ

    hython examples/058_export.py
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "058_stats.json")
EXP_DIR = os.path.join(OUT, "058_export")

JOINTS_VEX = """
int prim = addprim(0, "polyline");
for (int i = 0; i < 9; i++) {
    int pt = addpoint(0, set(0.0, float(i) * 0.25, 0.0));
    setpointattrib(0, "name", pt, sprintf("joint%d", i));
    addvertex(0, prim, pt);
}
"""


def build():
    """骨（点と線）と、皮（球）を1つにまとめたもの。"""
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "payload")

    make = geo.createNode("attribwrangle", "make_joints")
    make.parm("class").set(0)
    make.parm("snippet").set(JOINTS_VEX)

    doc = geo.createNode("kinefx::rigdoctor", "doctor")
    doc.setFirstInput(make)
    doc.parm("transformations").set(1)
    doc.parm("inittransforms").set(1)
    doc.parm("outputparentidx").set(1)

    skin = geo.createNode("sphere", "skin")
    skin.parm("type").set(2)
    skin.parm("rows").set(20)
    skin.parm("cols").set(20)
    skin.parm("ty").set(1.0)
    skin.parmTuple("rad").set((0.4, 1.0, 0.4))

    merged = geo.createNode("merge", "both")
    merged.setInput(0, doc)
    merged.setInput(1, skin)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    geo.layoutChildren()
    return geo, doc, skin, merged


def save_direct(node, path):
    """hou.Geometry.saveToFile で直接書き出す。"""
    node.geometry().saveToFile(path)


def save_rop(geo, node, path, rop_type, parm):
    import hou
    try:
        rop = geo.createNode(rop_type, "out_" + rop_type.replace(":", "_"))
    except hou.OperationFailed:
        # SOP の中に作れない種類は /out に作る
        out = hou.node("/out")
        rop = out.createNode(rop_type, "out_" + rop_type.replace(":", "_"))
    try:
        rop.setFirstInput(node)
    except hou.Error:
        pass
    if rop.parm("soppath") is not None:
        rop.parm("soppath").set(node.path())
    rop.parm(parm).set(path.replace("\\", "/"))
    if rop.parm("mkpath") is not None:
        rop.parm("mkpath").set(1)
    if rop.parm("trange") is not None:
        rop.parm("trange").set(0)
    rop.parm("execute").pressButton()


FORMATS = [
    ("bgeo.sc", "直接", None, None),
    ("geo", "直接", None, None),
    ("obj", "直接", None, None),
    ("ply", "直接", None, None),
    ("stl", "直接", None, None),
    ("fbx", "rop", "rop_fbx", "sopoutput"),
    ("gltf", "rop", "rop_gltf", "file"),
    ("abc", "rop", "rop_alembic", "filename"),
    ("usd", "rop", "usd", "lopoutput"),
]


def main():
    import hou
    os.makedirs(EXP_DIR, exist_ok=True)
    stats = {}

    geo, doc, skin, merged = build()
    source = merged.geometry()
    print(f"書き出すもの: {len(source.points())}点 / "
          f"{len(source.prims())}プリミティブ")
    print(f"   （骨9関節＋球 {len(skin.geometry().points())}点）")
    stats["source"] = {"points": len(source.points()),
                       "prims": len(source.prims())}

    # 書き出しのたびにシーンを作り直すので、比べる値は先に取り出しておく
    before = [(float(p.position()[0]), float(p.position()[1]),
               float(p.position()[2])) for p in source.points()]

    print("\nA・C. 形式ごとに書き出せるか")
    print(f"   {'形式':>10} {'やり方':>6} {'結果':>8} {'バイト':>12}  "
          f"{'止まった理由'}")
    rows = []
    for ext, how, rop_type, parm in FORMATS:
        path = os.path.join(EXP_DIR, f"payload.{ext}")
        if os.path.exists(path):
            os.remove(path)
        reason = ""
        try:
            if how == "直接":
                save_direct(merged, path)
            else:
                geo2, doc2, skin2, merged2 = build()
                save_rop(geo2, merged2, path, rop_type, parm)
        except Exception as exc:  # noqa: BLE001
            reason = str(exc).replace("\n", " ")[:70]
        ok = os.path.exists(path) and os.path.getsize(path) > 0
        size = os.path.getsize(path) if os.path.exists(path) else 0
        rows.append({"ext": ext, "how": how, "ok": ok, "bytes": size,
                     "reason": reason})
        print(f"   {ext:>10} {how:>6} {('通った' if ok else '止まった'):>8} "
              f"{size:>12,}  {reason}")
    stats["formats"] = rows

    print("\nA-2. USD は LOP を経由すると通るのか")
    geo2, doc2, skin2, merged2 = build()
    usd_path = os.path.join(EXP_DIR, "payload_lop.usd")
    for stale in (usd_path, usd_path + "nc"):
        if os.path.exists(stale):
            os.remove(stale)
    stage = hou.node("/stage") or hou.node("/").createNode("stage")
    imp = stage.createNode("sopimport", "fromsop")
    imp.parm("soppath").set(merged2.path())
    urop = None
    for name in ("usd", "usd_rop", "usdexport", "usdrop"):
        try:
            urop = stage.createNode(name, "usdout")
            print(f"   使えたノード: {name}")
            break
        except hou.OperationFailed:
            continue
    if urop is None:
        kinds = sorted(stage.type().childTypeCategory().nodeTypes().keys())
        print("   USD を書き出すノードが見つからない:",
              [n for n in kinds if "usd" in n][:12])
        stats["usd"] = {"asked": os.path.basename(usd_path), "made": [],
                        "message": ["書き出しノードが見つからない"]}
        urop = None
    if urop is not None:
        urop.setFirstInput(imp)
        urop.parm("lopoutput").set(usd_path.replace("\\", "/"))
        if urop.parm("trange") is not None:
            urop.parm("trange").set(0)
        urop.parm("execute").pressButton()
        made = [p for p in (usd_path, usd_path + "nc")
                if os.path.exists(p)]
        usd_note = [m.replace("\n", " ")[:120] for m in urop.errors()]
        print(f"   指定したパス: {os.path.basename(usd_path)}")
        print(f"   実際にできたもの: "
              f"{[os.path.basename(p) for p in made] or 'なし'}")
        for p in made:
            print(f"      {os.path.basename(p)}: "
                  f"{os.path.getsize(p):,} バイト")
        print(f"   出たメッセージ: {usd_note}")
        stats["usd"] = {"asked": os.path.basename(usd_path),
                        "made": [os.path.basename(p) for p in made],
                        "bytes": [os.path.getsize(p) for p in made],
                        "message": usd_note}

    print("\nB. 通ったものを読み直して、点の位置が保たれるか")
    print(f"   {'形式':>10} {'点 元':>8} {'点 後':>8} "
          f"{'位置のずれ 最大':>16} {'名前が残ったか':>16}")
    back = []
    for row in rows:
        if not row["ok"]:
            continue
        path = os.path.join(EXP_DIR, f"payload.{row['ext']}")
        try:
            g2 = hou.Geometry()
            g2.loadFromFile(path)
        except Exception as exc:  # noqa: BLE001
            print(f"   {row['ext']:>10} 読めない: {str(exc)[:50]}")
            back.append({"ext": row["ext"], "readable": False})
            continue
        after = [(float(p.position()[0]), float(p.position()[1]),
                  float(p.position()[2])) for p in g2.points()]
        worst = None
        if len(after) == len(before):
            worst = max(math.dist(a, b) for a, b in zip(before, after))
        has_name = g2.findPointAttrib("name") is not None
        back.append({"ext": row["ext"], "readable": True,
                     "points_before": len(before),
                     "points_after": len(after),
                     "worst": worst, "has_name": has_name})
        shown = "—" if worst is None else f"{worst:.9f}"
        print(f"   {row['ext']:>10} {len(before):>8} {len(after):>8} "
              f"{shown:>16} "
              f"{('はい' if has_name else 'いいえ'):>16}")
    stats["roundtrip"] = back

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/058_stats.json")


if __name__ == "__main__":
    main()
