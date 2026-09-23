# -*- coding: utf-8 -*-
"""実践（作り方の手順）を1本作るための土台。

実践ごとの台本（examples/pr_<id>.py）は、ここにある Guide を使って
「組む → 手順ごとに撮る → Karma で見栄えのよい絵を撮る → hip を保存 → guides.json 用の記録を書く」だけを書く。

    import practice_kit as kit
    g = kit.Guide("rock", "岩を作る", "リード文", tags=["モデリング"])
    sphere = g.node("sphere", "base", type="polymesh")
    g.step(sphere, "もとの形を置く", "本文", cap="キャプション")
    ...
    g.hero(final, material=...)
    g.save(facts=[...], traps=[...])

撮るもの（どれも out/ に置く）:
    pr_<id>_<n>.png   手順 n のビューポート（OpenGL、どの段も同じカメラ）
    pr_<id>_hero.png  Karma で撮った仕上がり（サムネイルにも使う）
    pr_<id>.hipnc     シーンファイル（読者がそのまま開ける）
    pr_<id>.json      guides.json に足す1本分（practice_merge.py で混ぜる）
ノードの画面（guide_parm_capture.py / guide_ui_capture.py）は、hip ができたあとで GUI の Houdini で撮る。
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou  # noqa: E402
import hou_tools  # noqa: E402

HERO_RES = (1280, 720)
STEP_RES = (720, 405)


class Guide:
    def __init__(self, gid, title, lede, tags, net_name=None):
        hou.hipFile.clear(suppress_save_prompt=True)
        self.id = gid
        self.title = title
        self.lede = lede
        self.tags = tags
        self.geo = hou.node("/obj").createNode("geo", net_name or gid)
        self.steps = []
        self.hero_sec = None
        self.hero_cap = ""
        self.shot_dir = (1.0, 0.62, 1.15)
        self.shot_bbox = None
        self.t0 = time.perf_counter()

    # ---------- 組む ----------
    def node(self, kind, name, inputs=(), parent=None, **parms):
        n = (parent or self.geo).createNode(kind, name)
        for i, src in enumerate(inputs):
            if src is not None:
                n.setInput(i, src)
        set_parms(n, parms)
        return n

    def mat(self, name, kind="principledshader::2.0", **parms):
        """/mat に材質を作る（既定は principledshader）。basecolor=(r,g,b) rough= metallic= emitcolor= emitint= など。"""
        matnet = hou.node("/mat") or hou.node("/").createNode("mat")
        m = matnet.node(name) or matnet.createNode(kind, name)
        set_parms(m, parms)
        return m

    def assign(self, src, mat, name=None, group=""):
        a = self.node("material", name or f"assign_{mat.name()}", [src])
        a.parm("shop_materialpath1").set(mat.path())
        if group:
            a.parm("group1").set(group)
        return a

    # ---------- 撮る ----------
    def step(self, node, title, body, cap="", shot=True, shading="smooth", ui_parm=None, bbox=None, direction=None):
        """手順を1段足す。shot なら、そのノードの結果をビューポートで撮る（どの段も同じ向き）。"""
        index = len(self.steps) + 1
        img = ""
        if shot:
            img = f"pr_{self.id}_{index}.png"
            hou_tools.render_preview(node.path(), os.path.join(OUT, img), res=STEP_RES,
                                     direction=direction or self.shot_dir, shading=shading,
                                     frame_bbox=bbox or self.shot_bbox)
        entry = {"title": title, "node": node.type().name().split("::")[0], "ui_node": node.name(),
                 "body": body, "img": img, "cap": cap}
        if ui_parm:
            entry["ui_parm"] = ui_parm
        self.steps.append(entry)
        return node

    def hero(self, node, cap, direction=(0.9, 0.45, 1.2), backdrop=(0.045, 0.047, 0.055), key=3.2, rim=4.0,
             dome=0.25, spp=48, margin=1.18, floor=True, bbox=None, dome_color=(1, 1, 1), key_color=(1.0, 0.96, 0.9),
             rim_color=(0.75, 0.85, 1.0), res=HERO_RES, frame=None):
        """Karma で仕上がりを撮る。暗い幕（曲げた床）・キー・リム・弱いドームの3灯で、どの実践も同じ撮り方にする。"""
        if frame is not None:
            hou.setFrame(frame)
        node.setDisplayFlag(True)
        node.setRenderFlag(True)
        box = bbox or node.geometry().boundingBox()
        size = box.sizevec()
        span = max(size[0], size[2], size[1] * 0.8)
        obj = hou.node("/obj")
        if floor:
            studio = obj.node("studio") or obj.createNode("geo", "studio")
            for c in studio.children():
                c.destroy()
            cyc = studio.createNode("grid", "backdrop")
            cyc.parmTuple("size").set((span * 30, span * 30))
            cyc.parm("rows").set(200)
            cyc.parm("cols").set(2)
            # 奥を上へ曲げて、床と壁の境目が見えない幕にする（写真スタジオのホリゾント）
            bend = studio.createNode("attribwrangle", "curve_up")
            bend.setFirstInput(cyc)
            bend.parm("snippet").set(
                f"float z0 = {-span * 1.2};\n"
                f"if (@P.z < z0) {{ float d = z0 - @P.z; @P.y += d * d / {span * 1.5}; }}")
            place = studio.createNode("xform", "place")
            place.setFirstInput(bend)
            place.parmTuple("t").set((box.center()[0], box.minvec()[1] - 0.001, box.center()[2]))
            matnet = hou.node("/mat") or hou.node("/").createNode("mat")
            bm = matnet.node("backdrop_mat") or matnet.createNode("principledshader::2.0", "backdrop_mat")
            bm.parmTuple("basecolor").set(backdrop)
            bm.parm("rough").set(0.75)
            bm.parm("reflect").set(0.2)
            asg = studio.createNode("material", "assign")
            asg.setFirstInput(place)
            asg.parm("shop_materialpath1").set(bm.path())
            asg.setDisplayFlag(True)
            asg.setRenderFlag(True)
        c = box.center()
        r = max(size[0], size[1], size[2])
        lights = {
            "hero_key": (key, key_color, (c[0] + r * 1.6, c[1] + r * 2.2, c[2] + r * 1.4)),
            "hero_rim": (rim, rim_color, (c[0] - r * 1.4, c[1] + r * 1.6, c[2] - r * 2.0)),
        }
        for name, (inten, col, pos) in lights.items():
            lt = obj.node(name) or obj.createNode("hlight::2.0", name)
            lt.parm("light_type").set("grid")
            lt.parmTuple("areasize").set((r * 1.2, r * 1.2))
            lt.parm("light_intensity").set(inten)
            lt.parmTuple("light_color").set(col)
            lt.parmTuple("t").set(pos)
            look = hou.hmath.buildRotateLookAt(hou.Vector3(pos), hou.Vector3(c), hou.Vector3(0, 1, 0))
            lt.parmTuple("r").set(look.extractRotates())
            if lt.parm("normalizearea") is not None:
                lt.parm("normalizearea").set(1)
        env = obj.node("hero_dome") or obj.createNode("envlight", "hero_dome")
        env.parm("light_intensity").set(dome)
        env.parmTuple("light_color").set(dome_color)
        for old in ("report_dome", "report_key"):
            if obj.node(old) is not None:
                obj.node(old).parm("light_intensity").set(0)
        cam = obj.node("hero_cam") or obj.createNode("cam", "hero_cam")
        cam.parm("resx").set(res[0])
        cam.parm("resy").set(res[1])
        hou_tools._frame_camera(cam, box, res, direction, margin=margin)
        karma = hou.node("/out").node("hero_karma") or hou.node("/out").createNode("karma", "hero_karma")
        karma.parm("camera").set(cam.path())
        karma.parm("denoiser").set("off")
        karma.parm("resolutionx").set(res[0])
        karma.parm("resolutiony").set(res[1])
        karma.parm("samplesperpixel").set(spp)
        karma.parm("varianceaa_maxsamples").set(spp)
        path = os.path.join(OUT, f"pr_{self.id}_hero.png")
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(hou.frame(), hou.frame(), 1), verbose=False)
        self.hero_sec = time.perf_counter() - t0
        self.hero_cap = cap
        return path

    def anim(self, node, frames, cap, bbox=None, direction=None, shading="smooth", res=(960, 540), fps=24,
             every=1, keep_color=True):
        """動きを撮る（2026-09-23）。frames のフレームを1から順に進めて（シミュレーションは飛ばすと崩れる）、
        every ごとにビューポートで撮り、pr_<id>_anim.mp4 にする。カメラは全フレームで同じ（bbox で決める）。"""
        import subprocess
        import tempfile
        tmp = tempfile.mkdtemp(prefix=f"anim_{self.id}_")
        first, last = frames
        box = bbox or node.geometry().boundingBox()
        # 透ける材質（ゼリー・ガラス・水）はビューポートで消えるので、撮るときだけ材質を外す。
        # Karma 用の幕（studio）も隠す。撮り終えたら元に戻す
        bare = node.parent().createNode("attribdelete", "anim_no_material")
        bare.setFirstInput(node)
        bare.parm("primdel").set("shop_materialpath material_override")
        bare.parm("ptdel").set("shop_materialpath" + ("" if keep_color else " Cd"))
        if not keep_color:  # 海のように、点の色が暗い（泡の印など）ものは色も外して形だけ見せる
            bare.parm("primdel").set("shop_materialpath material_override Cd")
            bare.parm("vtxdel").set("Cd")
        studio = hou.node("/obj/studio")
        if studio is not None:
            studio.setDisplayFlag(False)
        # hero() は手順用の明かりを 0 にし、Karma 用の強い明かりを置く。撮る間だけ手順用に戻す
        hou_tools._ensure_lights()
        saved = {}
        for name, value in (("report_dome", 0.55), ("report_key", 1.6), ("hero_key", 0), ("hero_rim", 0),
                            ("hero_dome", 0)):
            lt = hou.node("/obj/" + name)
            if lt is not None:
                saved[name] = lt.parm("light_intensity").eval()
                lt.parm("light_intensity").set(value)
        t0 = time.perf_counter()
        n = 0
        for f in range(1, last + 1):
            hou.setFrame(f)
            if f < first or (f - first) % every:
                bare.geometry()  # 飛ばすフレームも計算だけはする
                continue
            hou_tools.render_preview(bare.path(), os.path.join(tmp, f"f{n:04d}.png"), res=res,
                                     direction=direction or self.shot_dir, shading=shading, frame_bbox=box)
            n += 1
        bare.destroy()
        node.setDisplayFlag(True)
        node.setRenderFlag(True)
        if studio is not None:
            studio.setDisplayFlag(True)
        for name, value in saved.items():
            hou.node("/obj/" + name).parm("light_intensity").set(value)
        path = os.path.join(OUT, f"pr_{self.id}_anim.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i",
                        os.path.join(tmp, "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-crf", "26", "-movflags", "+faststart", path], check=True)
        self.anim_cap = cap
        print(f"動き: {n}枚 {time.perf_counter() - t0:.1f}秒 → {os.path.getsize(path) // 1024}KB")
        return path

    # ---------- しまう ----------
    def save(self, facts, traps, exp=""):
        hou.node("/obj").layoutChildren()
        self.geo.layoutChildren()
        hip = f"pr_{self.id}.hipnc"
        hou.hipFile.save(os.path.join(OUT, hip))
        # ノードのつなぎ方の図（GUI で撮れないとき＝画面が消えている夜の間の代わり）。画は graph_report.py が描く
        hou_tools.write_graph(self.geo.path(), os.path.join(OUT, f"pr_{self.id}_graph.json"), title=self.title)
        entry = {
            "id": self.id, "title": self.title, "lede": self.lede,
            "hero": f"pr_{self.id}_hero.png", "hero_cap": self.hero_cap,
            "facts": facts + [["仕上がりを撮る時間", f"{self.hero_sec:.1f}秒（Karma 1280×720）"]],
            "exp": exp, "hip": hip, "tags": self.tags, "steps": self.steps, "traps": traps,
        }
        if getattr(self, "anim_cap", ""):
            entry["anim_cap"] = self.anim_cap
        with open(os.path.join(OUT, f"pr_{self.id}.json"), "w", encoding="utf-8") as fp:
            json.dump(entry, fp, ensure_ascii=False, indent=1)
        print(f"保存: {hip}  手順 {len(self.steps)}  Karma {self.hero_sec:.1f}秒  全体 {time.perf_counter() - self.t0:.1f}秒")
        return entry


def set_parms(n, parms):
    for k, v in parms.items():
        if isinstance(v, (tuple, list)):
            n.parmTuple(k).set(v)
        elif isinstance(v, str) and v.startswith("="):
            n.parm(k).setExpression(v[1:])
        else:
            p = n.parm(k)
            if p is None:
                raise KeyError(f"{n.type().name()} に {k} が無い")
            p.set(v)


def count_nodes(geo):
    return len([c for c in geo.children()])
