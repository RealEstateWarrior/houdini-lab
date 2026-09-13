"""Render a Houdini node network (JSON) into a network-editor-style PNG.

Pure Python + Pillow, so it runs without a Houdini license.
Input JSON is produced by hbridge.dump_graph().

Usage:
    python graph_report.py graph.json out.png
"""

import json
import sys
from PIL import Image, ImageDraw, ImageFont

BG = (34, 36, 40)
GRID = (44, 47, 52)
NODE_FILL = (92, 99, 112)
NODE_EDGE = (150, 158, 172)
NODE_TEXT = (238, 240, 244)
TYPE_TEXT = (168, 176, 190)
WIRE = (140, 148, 162)
DISPLAY_FLAG = (86, 196, 233)
TITLE_TEXT = (226, 230, 238)
SUB_TEXT = (150, 158, 172)
ERROR_EDGE = (226, 112, 100)

NODE_W = 164
NODE_H = 46
GAP_X = 80
GAP_Y = 62
MARGIN = 46
HEADER_H = 76

FONT_UI = "C:/Windows/Fonts/meiryo.ttc"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _auto_layout(nodes, edges):
    """Assign layered positions when Houdini positions are absent."""
    incoming = {n["name"]: [] for n in nodes}
    for e in edges:
        if e["to"] in incoming:
            incoming[e["to"]].append(e["from"])

    depth = {}

    def resolve(name, seen):
        if name in depth:
            return depth[name]
        if name in seen:
            return 0
        seen = seen | {name}
        parents = incoming.get(name, [])
        depth[name] = max((resolve(p, seen) + 1 for p in parents), default=0)
        return depth[name]

    for n in nodes:
        resolve(n["name"], frozenset())

    per_row = {}
    for n in nodes:
        d = depth[n["name"]]
        col = per_row.get(d, 0)
        per_row[d] = col + 1
        n["_grid"] = (col, d)


def _to_pixels(nodes):
    """Map Houdini network coords (Y up) to pixel coords (Y down)."""
    if all("pos" in n for n in nodes):
        xs = [n["pos"][0] for n in nodes]
        ys = [n["pos"][1] for n in nodes]
        scale_x = NODE_W + GAP_X
        scale_y = NODE_H + GAP_Y
        for n in nodes:
            n["_px"] = (
                (n["pos"][0] - min(xs)) * scale_x,
                (max(ys) - n["pos"][1]) * scale_y,
            )
    else:
        for n in nodes:
            col, row = n["_grid"]
            n["_px"] = (col * (NODE_W + GAP_X), row * (NODE_H + GAP_Y))


def _rounded(draw, box, radius, fill, outline, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def render(graph, out_path):
    nodes = [dict(n) for n in graph["nodes"]]
    edges = graph.get("edges", [])
    by_name = {n["name"]: n for n in nodes}

    if not all("pos" in n for n in nodes):
        _auto_layout(nodes, edges)
    _to_pixels(nodes)

    width = int(max(n["_px"][0] for n in nodes) + NODE_W + MARGIN * 2)
    height = int(max(n["_px"][1] for n in nodes) + NODE_H + MARGIN * 2 + HEADER_H)
    width = max(width, 620)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    for x in range(0, width, 28):
        draw.line([(x, HEADER_H), (x, height)], fill=GRID)
    for y in range(HEADER_H, height, 28):
        draw.line([(0, y), (width, y)], fill=GRID)

    f_title = _font(FONT_UI, 19)
    f_sub = _font(FONT_UI, 12)
    f_name = _font(FONT_UI, 13)
    f_type = _font(FONT_MONO, 10)

    draw.text((MARGIN, 20), graph.get("title", "Houdini network"), font=f_title, fill=TITLE_TEXT)
    subtitle = graph.get("network", "")
    if graph.get("houdini_version"):
        subtitle = f"{subtitle}    Houdini {graph['houdini_version']}"
    draw.text((MARGIN, 47), subtitle, font=f_sub, fill=SUB_TEXT)

    def anchor(node, side):
        x, y = node["_px"]
        x += MARGIN
        y += MARGIN + HEADER_H
        return (x + NODE_W / 2, y if side == "in" else y + NODE_H)

    for e in edges:
        src, dst = by_name.get(e["from"]), by_name.get(e["to"])
        if not src or not dst:
            continue
        x0, y0 = anchor(src, "out")
        x1, y1 = anchor(dst, "in")
        mid = (y0 + y1) / 2
        draw.line([(x0, y0), (x0, mid), (x1, mid), (x1, y1)], fill=WIRE, width=2, joint="curve")
        draw.polygon([(x1, y1), (x1 - 5, y1 - 8), (x1 + 5, y1 - 8)], fill=WIRE)

    for n in nodes:
        x, y = n["_px"]
        x += MARGIN
        y += MARGIN + HEADER_H
        outline = ERROR_EDGE if n.get("errors") else NODE_EDGE
        _rounded(draw, (x, y, x + NODE_W, y + NODE_H), 6, NODE_FILL, outline)

        draw.text((x + 12, y + 7), n["name"], font=f_name, fill=NODE_TEXT)
        type_label = n.get("type", "")
        if type_label:
            draw.text((x + 12, y + 26), type_label, font=f_type, fill=TYPE_TEXT)

        if n.get("flags", {}).get("display"):
            draw.ellipse((x + NODE_W - 9, y + NODE_H - 9, x - 1 + NODE_W, y - 1 + NODE_H),
                         fill=DISPLAY_FLAG)

    img.save(out_path)
    return out_path


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    with open(sys.argv[1], encoding="utf-8") as fp:
        graph = json.load(fp)
    print(render(graph, sys.argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
