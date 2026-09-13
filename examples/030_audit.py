"""実験030 — 過去29回を測り直す。書いたことは、いまも正しいか。

実験が30回たまったので、001〜029を1つずつ見直した。
読み返すだけでは「そう書いてあった」以上のことは分からないので、
<strong>確かめ直せる主張は、もう一度動かして測る</strong>。

測り直したのは7つ。どれも「外れていたら過去の記事を直さなければならない」もの。

  A. 002 … ポイント数はいつも「プリミティブ数 + 2」か
  B. 004 … パラメータ名は rough / oct / lac で、roughness は存在しないか
  C. 009 … rand(@ptnum) は何度走らせても同じ値か
  D. 011 … crease の重み N は、分割 N 回まで角を保つか（分割4回で確かめる）
  E. 012 … sphere の rows / cols はどの type で効くのか
  F. 008 … scatter の出力はいつも N を持つのか
  G. 002 … 一辺の縮みは、外挿した 0.83951 に本当に収束するか

    hython examples/030_audit.py
"""

import json
import math
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402


def fresh(name):
    hou.hipFile.clear(suppress_save_prompt=True)
    return hou.node("/obj").createNode("geo", name)


# ---------- A. 002「点数 = 面数 + 2」 ----------

def check_euler():
    geo = fresh("euler")
    box = geo.createNode("box", "box")
    sub = geo.createNode("subdivide", "sub")
    sub.setFirstInput(box)
    rows = []
    for iterations in range(0, 7):
        sub.parm("iterations").set(iterations)
        node = box if iterations == 0 else sub
        g = node.geometry()
        points, prims = len(g.points()), len(g.prims())
        rows.append({"iterations": iterations, "points": points,
                     "prims": prims, "holds": points == prims + 2})
    return rows


# ---------- B. 004 パラメータ名 ----------

def check_mountain_parms():
    geo = fresh("parms")
    grid = geo.createNode("grid", "grid")
    mountain = geo.createNode("mountain", "mountain")
    mountain.setFirstInput(grid)
    names = {p.name() for p in mountain.parms()}
    wanted = ("rough", "oct", "lac", "height", "elementsize",
              "roughness", "octaves", "lacunarity")
    return {name: (name in names) for name in wanted}


# ---------- C. 009 rand(@ptnum) の再現性 ----------

def check_rand():
    geo = fresh("rand")
    grid = geo.createNode("grid", "grid")
    grid.parm("rows").set(20)
    grid.parm("cols").set(20)

    values = []
    for index in range(2):
        wrangle = geo.createNode("attribwrangle", f"w{index}")
        wrangle.setFirstInput(grid)
        wrangle.parm("snippet").set("f@r = rand(@ptnum);")
        values.append([p.attribValue("r") for p in wrangle.geometry().points()])

    worst = max(abs(a - b) for a, b in zip(values[0], values[1]))
    return {"points": len(values[0]), "worst_diff": worst,
            "identical": worst == 0.0}


# ---------- D. 011 crease の重みと分割回数 ----------

def edge_length(geometry):
    """+X 側の端の長さ。立方体の一辺の縮み具合を見る。"""
    xs = [p.position()[0] for p in geometry.points()]
    return max(xs) - min(xs)


def max_angle(geometry, adjacency="edge"):
    """面どうしの折れ角の最大。角が鋭いほど大きい。

    数え方を2通り用意する。どちらを選ぶかで数字が変わるので、
    過去の記事と突き合わせるときはここを揃える必要がある。

      edge  … 辺を共有する面どうし（点を2つ共有）
      point … 点を1つでも共有する面どうし。edge より必ず大きいか等しい
    """
    normals = {p.number(): p.normal() for p in geometry.prims()}
    points_of = {p.number(): {v.point().number() for v in p.vertices()}
                 for p in geometry.prims()}

    by_point = {}
    for number, points in points_of.items():
        for point in points:
            by_point.setdefault(point, set()).add(number)

    pairs = set()
    for prims in by_point.values():
        ordered = sorted(prims)
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                pairs.add((ordered[i], ordered[j]))

    worst = 0.0
    for a, b in pairs:
        shared = len(points_of[a] & points_of[b])
        if adjacency == "edge" and shared < 2:
            continue
        dot = max(-1.0, min(1.0, normals[a].dot(normals[b])))
        worst = max(worst, math.degrees(math.acos(dot)))
    return worst


def check_crease(iterations):
    rows = []
    for weight in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0):
        geo = fresh(f"crease{iterations}_{int(weight)}")
        box = geo.createNode("box", "box")
        crease = geo.createNode("crease", "crease")
        crease.setFirstInput(box)
        crease.parm("group").set("*")
        crease.parm("crease").set(weight)
        sub = geo.createNode("subdivide", "sub")
        sub.setFirstInput(crease)
        sub.parm("iterations").set(iterations)
        g = sub.geometry()
        by_edge = max_angle(g, "edge")
        by_point = max_angle(g, "point")
        rows.append({"iterations": iterations, "weight": weight,
                     "edge": edge_length(g), "angle_edge": by_edge,
                     "angle_point": by_point,
                     "sharp": abs(by_edge - 90.0) < 0.01})
    return rows


# ---------- E. 012 sphere の type と rows / cols ----------

def check_sphere_types():
    geo = fresh("spheres")
    sphere = geo.createNode("sphere", "sphere")
    labels = sphere.parm("type").menuLabels()
    items = sphere.parm("type").menuItems()
    rows = []
    for index, (item, label) in enumerate(zip(items, labels)):
        entry = {"index": index, "name": item, "label": label}
        for rows_cols in (6, 30):
            sphere.parm("type").set(index)
            sphere.parm("rows").set(rows_cols)
            sphere.parm("cols").set(rows_cols)
            try:
                g = sphere.geometry()
                entry[f"prims_{rows_cols}"] = len(g.prims())
                entry[f"points_{rows_cols}"] = len(g.points())
            except hou.Error as exc:
                entry[f"prims_{rows_cols}"] = f"エラー: {exc}"
        entry["responds"] = (entry.get("prims_6") != entry.get("prims_30"))
        rows.append(entry)
    return rows


# ---------- F. 008 scatter は N を出すのか ----------

def check_scatter_normals():
    rows = []
    for with_normal in (False, True):
        geo = fresh(f"scatter_{int(with_normal)}")
        grid = geo.createNode("grid", "grid")
        grid.parm("rows").set(20)
        grid.parm("cols").set(20)
        upstream = grid
        if with_normal:
            normal = geo.createNode("normal", "normal")
            normal.setFirstInput(grid)
            upstream = normal
        scatter = geo.createNode("scatter", "scatter")
        scatter.setFirstInput(upstream)
        scatter.parm("npts").set(200)
        g = scatter.geometry()
        up = upstream.geometry()
        rows.append({
            "normal_sop": with_normal,
            "upstream_point_N": up.findPointAttrib("N") is not None,
            "upstream_vertex_N": up.findVertexAttrib("N") is not None,
            "scatter_point_N": g.findPointAttrib("N") is not None,
            "attribs": sorted(a.name() for a in g.pointAttribs()),
            "points": len(g.points()),
        })
    return rows


# ---------- G. 002 一辺の縮みの極限 ----------

def check_limit():
    geo = fresh("limit")
    box = geo.createNode("box", "box")
    sub = geo.createNode("subdivide", "sub")
    sub.setFirstInput(box)
    rows = []
    for iterations in range(1, 9):
        sub.parm("iterations").set(iterations)
        rows.append({"iterations": iterations,
                     "edge": edge_length(sub.geometry())})
    return rows


def main():
    stats = {}

    print("A. 002「点数 = 面数 + 2」は今も成り立つか")
    euler = check_euler()
    for row in euler:
        print(f"   {row['iterations']}回: {row['points']:6d}点 / "
              f"{row['prims']:6d}面  {'○' if row['holds'] else '×'}")
    stats["euler"] = euler
    print(f"   7通りすべて成立: "
          f"{'はい' if all(r['holds'] for r in euler) else 'いいえ'}")

    print("\nB. 004 mountain のパラメータ名")
    parms = check_mountain_parms()
    for name, exists in parms.items():
        print(f"   {name:14s} {'ある' if exists else 'ない'}")
    stats["mountain_parms"] = parms

    print("\nC. 009 rand(@ptnum) の再現性")
    rand = check_rand()
    print(f"   {rand['points']}点で最大の差 {rand['worst_diff']:.12f} "
          f"→ {'完全に一致' if rand['identical'] else '一致しない'}")
    stats["rand"] = rand

    print("\nD. 011 crease の重み N は、分割 N 回まで角を保つか")
    crease = []
    for iterations in (3, 4, 5):
        rows = check_crease(iterations)
        crease.extend(rows)
        print(f"   分割 {iterations}回")
        for row in rows:
            print(f"     重み {row['weight']:<4} 一辺 {row['edge']:.5f} "
                  f"折れ角 辺どうし {row['angle_edge']:6.2f}度 / "
                  f"点どうし {row['angle_point']:6.2f}度 "
                  f"{'← 元の鋭さ' if row['sharp'] else ''}")
    stats["crease"] = crease

    print("\nE. 012 sphere の type と rows / cols")
    spheres = check_sphere_types()
    print(f"   {'type':<14} {'表示名':<16} {'6分割':>10} {'30分割':>10}  効くか")
    for row in spheres:
        print(f"   {row['name']:<14} {row['label']:<16} "
              f"{str(row.get('prims_6')):>10} {str(row.get('prims_30')):>10}  "
              f"{'○' if row['responds'] else '×'}")
    stats["spheres"] = spheres

    print("\nF. 008 scatter は N を出すのか")
    scatters = check_scatter_normals()
    for row in scatters:
        where = []
        if row["upstream_point_N"]:
            where.append("点")
        if row["upstream_vertex_N"]:
            where.append("バーテックス")
        print(f"   normal SOP {'あり' if row['normal_sop'] else 'なし'} → "
              f"入力の N は {'/'.join(where) if where else 'どこにも無い'} / "
              f"scatter の出力に点の N が "
              f"{'ある' if row['scatter_point_N'] else '無い'} "
              f"（属性: {', '.join(row['attribs'])}）")
    stats["scatter"] = scatters

    print("\nG. 002 一辺の縮みは 0.83951 に収束するか")
    limit = check_limit()
    previous = None
    for row in limit:
        gap = row["edge"] - 0.83951
        line = (f"   {row['iterations']}回: {row['edge']:.6f} "
                f"（0.83951 との差 {gap:+.6f}）")
        if previous is not None:
            line += f" 前回差の {(row['edge'] - 0.83951) / previous:.3f}倍"
        previous = gap
        print(line)
    stats["limit"] = limit
    stats["limit_gap"] = limit[-1]["edge"] - 0.83951

    with open(os.path.join(OUT, "030_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/030_stats.json")


if __name__ == "__main__":
    main()
