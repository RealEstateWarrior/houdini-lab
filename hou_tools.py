"""Helpers for building Houdini networks headlessly and reporting the result.

Run under hython:
    "C:/Program Files/Side Effects Software/Houdini 21.0.700/bin/hython.exe" script.py

Apprentice works with hython, but saves must use .hipnc and renders carry a
Houdini watermark.
"""

import json
import math
import os

import hou


def _changed_parms(node):
    """Parameters the script moved off their defaults.

    These are the pedagogically interesting ones: everything else is just
    Houdini's out-of-the-box behaviour and would bury the report in noise."""
    changed = {}
    for parm in node.parms():
        try:
            if parm.isAtDefault():
                continue
            value = parm.eval()
        except hou.Error:
            continue
        if not isinstance(value, (int, float, str, bool)):
            value = str(value)
        if isinstance(value, str) and len(value) > 120:
            value = value[:117] + "..."
        changed[parm.name()] = value
    return changed


def dump_graph(network_path, title=None):
    """Capture a network's nodes, wiring and flags as JSON-ready data."""
    parent = hou.node(network_path)
    if parent is None:
        raise ValueError(f"no such network: {network_path}")

    nodes = []
    edges = []
    for node in parent.children():
        pos = node.position()
        entry = {
            "name": node.name(),
            "type": node.type().name(),
            "pos": [round(pos[0], 3), round(pos[1], 3)],
            "flags": {},
            "params": _changed_parms(node),
        }
        try:
            entry["flags"]["display"] = bool(node.isDisplayFlagSet())
        except AttributeError:
            pass
        if node.errors():
            entry["errors"] = [str(e) for e in node.errors()]
        nodes.append(entry)

        for connection in node.inputConnections():
            edges.append({
                "from": connection.inputNode().name(),
                "from_output": connection.outputIndex(),
                "to": node.name(),
                "to_input": connection.inputIndex(),
            })

    return {
        "title": title or network_path,
        "network": network_path,
        "houdini_version": hou.applicationVersionString(),
        "nodes": nodes,
        "edges": edges,
    }


def write_graph(network_path, json_path, title=None):
    graph = dump_graph(network_path, title)
    os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(graph, fp, ensure_ascii=False, indent=2)
    return graph


def geometry_stats(sop_path):
    """Point/prim counts and attribute names of a SOP's cooked output."""
    node = hou.node(sop_path)
    if node is None:
        raise ValueError(f"no such node: {sop_path}")
    geo = node.geometry()
    if geo is None:
        return {"node": sop_path, "empty": True}

    bbox = geo.boundingBox()
    return {
        "node": sop_path,
        "points": len(geo.points()),
        "prims": len(geo.prims()),
        "bbox_min": [round(v, 4) for v in bbox.minvec()],
        "bbox_max": [round(v, 4) for v in bbox.maxvec()],
        "point_attribs": [a.name() for a in geo.pointAttribs()],
        "prim_attribs": [a.name() for a in geo.primAttribs()],
        "detail_attribs": [a.name() for a in geo.globalAttribs()],
    }


def _ensure_lights():
    """A dome light plus a distant key light. Point lights fall off with
    distance, which is why a default hlight renders the subject black."""
    obj = hou.node("/obj")
    if obj.node("report_dome") is None:
        dome = obj.createNode("envlight", "report_dome")
        dome.parm("light_intensity").set(0.55)
    if obj.node("report_key") is None:
        key = obj.createNode("hlight", "report_key")
        key.parm("light_type").set("distant")
        key.parm("light_intensity").set(1.6)
        key.parmTuple("r").set((-38, -32, 0))


def _frame_camera(cam, bbox, res, direction=(1.0, 0.62, 1.15), margin=1.12):
    """Place cam so the bbox exactly fills the frame, looking down `direction`.

    Projects the eight bbox corners into camera space and solves for the
    distance where the widest corner still fits. A bounding-sphere estimate
    would badly overshoot for flat objects like terrain, rendering them tiny."""
    center = bbox.center()
    low, high = bbox.minvec(), bbox.maxvec()
    corners = [hou.Vector3(x, y, z) - center
               for x in (low[0], high[0])
               for y in (low[1], high[1])
               for z in (low[2], high[2])]

    focal = cam.parm("focal").eval()
    aperture = cam.parm("aperture").eval()
    tan_h = (aperture * 0.5) / focal
    tan_v = tan_h * res[1] / res[0]

    forward = -hou.Vector3(direction).normalized()
    world_up = hou.Vector3(0, 1, 0)
    if abs(forward.dot(world_up)) > 0.999:
        world_up = hou.Vector3(0, 0, 1)
    right = forward.cross(world_up).normalized()
    up = right.cross(forward).normalized()

    distance = 0.0
    for corner in corners:
        depth_offset = corner.dot(forward)
        distance = max(distance,
                       abs(corner.dot(right)) / tan_h - depth_offset,
                       abs(corner.dot(up)) / tan_v - depth_offset)
    distance = max(distance, 1e-3) * margin

    eye = center - forward * distance
    cam.parmTuple("t").set(eye)
    rotate = hou.hmath.buildRotateLookAt(eye, center, hou.Vector3(0, 1, 0))
    cam.parmTuple("r").set(rotate.extractRotates())


SHADING_MODES = {
    "wire": 0, "wireghost": 1, "hidden": 2, "ghost": 3,
    "flat": 4, "flatwire": 5, "smooth": 6, "smoothwire": 7,
}


def bbox_union(sop_paths):
    """One bounding box covering several SOPs.

    Pass the result to render_preview as frame_bbox so every variant in a
    comparison is shot from the same camera — otherwise each is auto-framed to
    fill the frame and differences in scale disappear."""
    box = None
    for path in sop_paths:
        node = hou.node(path)
        if node is None:
            raise ValueError(f"no such node: {path}")
        current = node.geometry().boundingBox()
        if box is None:
            box = current
        else:
            box.enlargeToContain(current)
    return box


def render_preview(sop_path, out_png, res=(960, 540), direction=(1.0, 0.62, 1.15),
                   shading="smoothwire", frame_bbox=None, margin=1.12):
    """Render the SOP's geometry with the hardware renderer, camera auto-framed.

    Default shading draws the wireframe over the shaded surface so the topology
    the network produced is visible, not just the silhouette."""
    node = hou.node(sop_path)
    if node is None:
        raise ValueError(f"no such node: {sop_path}")
    node.setDisplayFlag(True)
    node.setRenderFlag(True)

    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    _ensure_lights()

    obj = hou.node("/obj")
    cam = obj.node("report_cam") or obj.createNode("cam", "report_cam")
    cam.parm("resx").set(res[0])
    cam.parm("resy").set(res[1])
    _frame_camera(cam, frame_bbox or node.geometry().boundingBox(), res, direction,
                  margin=margin)

    out = hou.node("/out")
    rop = out.node("report_opengl") or out.createNode("opengl", "report_opengl")
    rop.parm("camera").set(cam.path())
    rop.parm("picture").set(out_png.replace("\\", "/"))
    rop.parm("shadingmode").set(SHADING_MODES[shading])
    rop.parm("tres").set(True)
    rop.parm("res1").set(res[0])
    rop.parm("res2").set(res[1])
    rop.render(verbose=False)

    return out_png


def bbox_over_frames(sop_path, frames):
    """フレーム範囲全体を覆うバウンディングボックス。

    シミュレーションは時間とともに広がるので、1フレーム目だけで枠を決めると
    途中で画面からはみ出す。全フレームを通した範囲で一度だけ枠を決める。"""
    node = hou.node(sop_path)
    if node is None:
        raise ValueError(f"no such node: {sop_path}")

    original = hou.frame()
    box = None
    try:
        for frame in frames:
            hou.setFrame(frame)
            current = node.geometry().boundingBox()
            if current.isValid():
                if box is None:
                    box = current
                else:
                    box.enlargeToContain(current)
    finally:
        hou.setFrame(original)
    return box


def render_sequence(sop_path, out_dir, prefix, frames, res=(480, 360),
                    direction=(1.0, 0.62, 1.15), shading="smoothwire",
                    frame_bbox=None):
    """フレームごとに1枚ずつ書き出し、ファイルパスの一覧を返す。

    カメラは全フレームで固定する。フレームごとに枠を合わせ直すと、
    動いているのか大きさが変わっているのか画から判断できなくなる。"""
    node = hou.node(sop_path)
    if node is None:
        raise ValueError(f"no such node: {sop_path}")
    os.makedirs(out_dir, exist_ok=True)

    if frame_bbox is None:
        frame_bbox = bbox_over_frames(sop_path, frames)

    original = hou.frame()
    paths = []
    try:
        for frame in frames:
            hou.setFrame(frame)
            path = os.path.join(out_dir, f"{prefix}_{int(frame):04d}.png")
            render_preview(sop_path, path, res=res, direction=direction,
                           shading=shading, frame_bbox=frame_bbox)
            paths.append(path)
    finally:
        hou.setFrame(original)
    return paths


def save_hip(path):
    """Apprentice can only write .hipnc."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    hou.hipFile.save(path)
    return path
