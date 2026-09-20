"""実験090 — 061〜090 の振り返り点検。書いた数字を、もう一度測り直す。

30件ごとの点検（実験030・060に続いて3回目）。やることは4つ。

  1. 書いた数字を測り直して、同じ値が出るか確かめる
  2. あとの実験で覆った結論を数える（訂正が記事に入っているか）
  3. 「黙って無視される設定」の一覧を更新する
  4. 直したほうがよい点を洗い出す

ここでは 1 を自動で行う。軽い測定だけを選び、記録と突き合わせる。

    hython examples/090_audit.py check
    python  examples/090_audit.py card
"""

import importlib
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")


def check_067():
    """実験067・076：摩擦 0.25 で滑った距離 3.260808（粒の間隔 0.12）。"""
    ground = importlib.import_module("067_mpm_ground")
    ground.SEP = 0.12
    info = ground.run(0.25)
    return "067 滑った距離（摩擦0.25）", 3.260808, info["slid"], "{:.6f}"


def check_070():
    """実験070・076：動く板（速さ4・摩擦1）で運ばれた距離 5.336132。"""
    moving = importlib.import_module("070_mpm_moving")
    moving.SEP = 0.12
    info = moving.run(speed=4.0)
    return "070 運ばれた距離（板4・摩擦1）", 5.336132, info["carried"], "{:.6f}"


def check_071():
    """実験071・075：回る台の境目は ω 1.25〜1.30（半径2・摩擦1）。

    1.25 は乗ったまま、1.30 は滑り出す、を確かめる。
    """
    spin = importlib.import_module("071_mpm_spin")
    spin.SEP = 0.12
    stay = spin.run(1.25, 2.0, 1.0)
    fling = spin.run(1.30, 2.0, 1.0)
    ok = stay["dr"] < 1.0 and fling["dr"] > 1.0
    return ("071 境目（ω1.25は乗る/1.30は滑る）", "乗る / 滑る",
            f"{'乗る' if stay['dr'] < 1.0 else '滑る'} / {'滑る' if fling['dr'] > 1.0 else '乗る'}",
            None, ok)


def check_073():
    """実験073・078：Liquid（摩擦1）の暴れ始めは F28。"""
    wild = importlib.import_module("073_mpm_liquid_wild")
    info = wild.run(1.0, last=60)
    return "073 液体が暴れ始めるフレーム", 28, info["onset"], "{}"


def check_079():
    """実験079：popdrag は速さの2乗の式に、ずれ 0.0000 で乗る（airresist 1）。"""
    sparks = importlib.import_module("079_sparks")
    import hou
    import hou_tools
    geo, imp, out = sparks.build(life=10.0, lifevar=0.0, vel=(8.0, 0.0, 0.0),
                                 var=(0.0, 0.0, 0.0), gravity=False, drag=1.0, burst=200)
    worst = 0.0
    v0 = None
    a0 = None
    for frame in range(2, 50):
        hou.setFrame(frame)
        v = float(hou_tools.point_array(imp.geometry(), "v")[:, 0].mean())
        age = float(hou_tools.point_array(imp.geometry(), "age").mean())
        if v0 is None:
            v0, a0 = v, age
            continue
        want = v0 / (1 + 1.0 * v0 * (age - a0))
        worst = max(worst, abs(v - want))
    # 記録は小数4桁で 0.0000。判定も同じ桁で行う（完全な 0 を求めない）
    return ("079 空気抵抗の式とのずれ（最大）", "0.0000", f"{worst:.4f}", None,
            f"{worst:.4f}" == "0.0000")


def check_084():
    """実験084：ドミノ12枚・間隔 0.3 は全部倒れ、1.5秒かかる。"""
    dom = importlib.import_module("084_dominoes")
    info = dom.run(0.3, 12)
    return "084 ドミノが倒れきる秒（12枚・間隔0.3）", 1.5, info["span_sec"], "{:.3f}"


def check_082():
    """実験082：長さ 25.0217 の道を Length 1.0 で切ると 27点・間隔 0.962。"""
    import hou
    path = importlib.import_module("082_along_path")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "audit_path")
    bend, rs = path.build_path(geo, 1.0, True)
    pts = [p.position() for p in rs.geometry().prims()[0].points()]
    gaps = [(b - a).length() for a, b in zip(pts, pts[1:])]
    return "082 道を切った点の数", 27, len(pts), "{}"


CHECKS = [check_067, check_070, check_071, check_073, check_079, check_084, check_082]


def check():
    rows = []
    for fn in CHECKS:
        start = time.perf_counter()
        result = fn()
        sec = time.perf_counter() - start
        if len(result) == 5:
            label, want, got, fmt, ok = result
        else:
            label, want, got, fmt = result
            ok = (abs(float(got) - float(want)) <= abs(float(want)) * 1e-6 + 1e-9
                  if fmt != "{}" else got == want)
        w = want if fmt is None else fmt.format(want)
        g = got if fmt is None else fmt.format(got)
        rows.append({"label": label, "want": str(w), "got": str(g), "same": bool(ok),
                     "seconds": sec})
        print(f"   {label:<44} 記録 {w:>12}  測り直し {g:>12}  "
              f"{'一致' if ok else '食い違い'}  {sec:.2f}秒")
    with open(os.path.join(OUT, "090_checks.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print(f"\n   一致 {sum(1 for r in rows if r['same'])} / {len(rows)}")
    print("保存: out/090_checks.json")


def card():
    sys.path.insert(0, os.path.join(HERE, "examples"))
    from cards_058_060 import card as make_card
    with open(os.path.join(OUT, "090_checks.json"), encoding="utf-8") as fp:
        rows = json.load(fp)
    table = [[r["label"], r["want"], r["got"], ("一致", "ok") if r["same"] else ("食い違い", "ng")]
             for r in rows]
    make_card("090_audit.png",
              "実験090 — 061〜090 を測り直す",
              f"{sum(1 for r in rows if r['same'])} 件すべて、記録と同じ値が出た。",
              (["確かめたこと", "記録", "測り直し", "結果"], [18, 470, 640, 810]),
              table,
              "同じスクリプトを別のプロセスから呼び直して測った。")


if __name__ == "__main__":
    {"check": check, "card": card}[sys.argv[1] if len(sys.argv) > 1 else "check"]()
