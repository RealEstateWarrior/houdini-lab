"""Build a PDF report for one Houdini experiment.

Browser-viewable and directly ingestible by Gemini Notebook / NotebookLM
(.pdf is an accepted source type, and the text stays real text so it can be
grounded on rather than OCR'd).

Usage:
    python report_pdf.py experiment.json out.pdf

The input JSON bundles one experiment:
{
  "title": "...",
  "summary": "何を作ったかの説明（複数段落は \\n\\n 区切り）",
  "graph": "out/xxx_graph.json",
  "graph_image": "out/xxx_graph.png",
  "render": "out/xxx.png",
  "stats": "out/xxx_stats.json",
  "notes": ["学んだこと1", "学んだこと2"],
  "next": ["次にやること"]
}
"""

import datetime
import json
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Table, TableStyle)

ACCENT = colors.HexColor("#3f6fa8")
MUTED = colors.HexColor("#5c6470")
RULE = colors.HexColor("#c9cfd8")
HEAD_BG = colors.HexColor("#eef1f5")

PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 40 * mm


def _register_fonts():
    """Meiryo covers Japanese; fall back to reportlab's built-in CJK font."""
    candidates = [
        ("Meiryo", "C:/Windows/Fonts/meiryo.ttc", 0),
        ("YuGothic", "C:/Windows/Fonts/YuGothM.ttc", 0),
        ("MSGothic", "C:/Windows/Fonts/msgothic.ttc", 0),
    ]
    for name, path, index in candidates:
        if not os.path.exists(path):
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=index))
            return name
        except Exception:
            continue

    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    return "HeiseiKakuGo-W5"


def _styles(font):
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], fontName=font,
                                fontSize=20, leading=26, alignment=TA_LEFT,
                                textColor=colors.HexColor("#1c2430"), spaceAfter=2),
        "meta": ParagraphStyle("m", fontName=font, fontSize=8.5, leading=12,
                               textColor=MUTED, spaceAfter=10),
        "h2": ParagraphStyle("h", fontName=font, fontSize=12.5, leading=17,
                             textColor=ACCENT, spaceBefore=14, spaceAfter=5),
        "body": ParagraphStyle("b", fontName=font, fontSize=9.8, leading=15.5,
                               textColor=colors.HexColor("#232a33"), spaceAfter=5),
        "cell": ParagraphStyle("c", fontName=font, fontSize=8.2, leading=11.5,
                               textColor=colors.HexColor("#232a33")),
        "cellhead": ParagraphStyle("ch", fontName=font, fontSize=8.2, leading=11.5,
                                   textColor=colors.HexColor("#1c2430")),
        "caption": ParagraphStyle("cap", fontName=font, fontSize=8, leading=11,
                                  textColor=MUTED, spaceBefore=3, spaceAfter=8),
    }


def _load(path, base_dir):
    full = path if os.path.isabs(path) else os.path.join(base_dir, path)
    with open(full, encoding="utf-8") as fp:
        return json.load(fp)


def _resolve(path, base_dir):
    if not path:
        return None
    full = path if os.path.isabs(path) else os.path.join(base_dir, path)
    return full if os.path.exists(full) else None


def _fit_image(path, max_w, max_h=150 * mm):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    scale = min(max_w / w, max_h / h)
    return Image(path, width=w * scale, height=h * scale)


def _bullets(items, styles):
    flow = []
    for item in items:
        flow.append(Paragraph(f"・{item}", styles["body"]))
    return flow


def _image_row(items, styles, base_dir, per_row=4):
    """Variants side by side, so a comparison reads as one object."""
    cell_w = (CONTENT_W - (per_row - 1) * 4 * mm) / per_row
    rows = []
    for start in range(0, len(items), per_row):
        chunk = items[start:start + per_row]
        cells = []
        for item in chunk:
            path = _resolve(item["path"], base_dir)
            block = []
            if path:
                block.append(_fit_image(path, cell_w - 4 * mm, 70 * mm))
            block.append(Paragraph(item.get("caption", ""), styles["caption"]))
            cells.append(block)
        cells += [""] * (per_row - len(chunk))
        rows.append(cells)

    table = Table(rows, colWidths=[cell_w] * per_row)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
    ]))
    return table


def _plain_table(columns, rows, styles):
    head = [Paragraph(c, styles["cellhead"]) for c in columns]
    body = [[Paragraph(str(v), styles["cell"]) for v in row] for row in rows]
    width = CONTENT_W / len(columns)
    table = Table([head] + body, colWidths=[width] * len(columns), repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
        ("INNERGRID", (0, 1), (-1, -1), 0.25, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _node_table(graph, styles):
    rows = [[Paragraph(h, styles["cellhead"]) for h in
             ("ノード", "タイプ", "デフォルトから変更したパラメータ")]]
    # 変更パラメータが多いノード（シミュレーションのソルバなど）は数百行になり、
    # 1ページに収まらず組版が失敗する。上限を決めて残りは件数だけ示す。
    limit = 12
    for node in graph["nodes"]:
        params = node.get("params") or {}
        if params:
            items = sorted(params.items())
            lines = [f"{k} = {v}" for k, v in items[:limit]]
            if len(items) > limit:
                lines.append(f"…ほか {len(items) - limit} 件")
            text = "<br/>".join(lines)
        else:
            text = "（変更なし）"
        rows.append([
            Paragraph(node["name"], styles["cell"]),
            Paragraph(node.get("type", ""), styles["cell"]),
            Paragraph(text, styles["cell"]),
        ])

    table = Table(rows, colWidths=[32 * mm, 34 * mm, CONTENT_W - 66 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
        ("INNERGRID", (0, 1), (-1, -1), 0.25, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _stats_table(stats, styles):
    fields = [
        ("ポイント数", stats.get("points")),
        ("プリミティブ数", stats.get("prims")),
        ("バウンディングボックス", f"{stats.get('bbox_min')} 〜 {stats.get('bbox_max')}"),
        ("ポイント属性", ", ".join(stats.get("point_attribs") or []) or "なし"),
        ("プリミティブ属性", ", ".join(stats.get("prim_attribs") or []) or "なし"),
        ("ディテール属性", ", ".join(stats.get("detail_attribs") or []) or "なし"),
    ]
    rows = [[Paragraph(k, styles["cellhead"]), Paragraph(str(v), styles["cell"])]
            for k, v in fields]
    table = Table(rows, colWidths=[45 * mm, CONTENT_W - 45 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), HEAD_BG),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _experiment_flow(spec, styles, base_dir):
    # 接続図が無い回もある（実験030の振り返り点検のように、
    # 1つのネットワークを作らずに複数の実験を測り直す回）。
    graph = _load(spec["graph"], base_dir) if spec.get("graph") else {}
    stats = _load(spec["stats"], base_dir) if spec.get("stats") else {}

    flow = [Paragraph(spec.get("title") or graph.get("title", "Houdini 実験ログ"), styles["title"])]

    meta = [
        datetime.date.today().isoformat(),
        f"Houdini {graph.get('houdini_version', '?')}" if graph else "",
        graph.get("network", ""),
        (f"ノード {len(graph['nodes'])} / 接続 {len(graph.get('edges', []))}"
         if graph.get("nodes") else ""),
    ]
    flow.append(Paragraph("　|　".join(m for m in meta if m), styles["meta"]))

    if spec.get("summary"):
        flow.append(Paragraph("何を作ったか", styles["h2"]))
        for para in spec["summary"].split("\n\n"):
            flow.append(Paragraph(para.strip(), styles["body"]))

    graph_img = _resolve(spec.get("graph_image"), base_dir)
    if graph_img:
        flow.append(Paragraph("ノードの接続", styles["h2"]))
        flow.append(_fit_image(graph_img, CONTENT_W, 120 * mm))
        flow.append(Paragraph("スクリプトが実際に構築したネットワーク。水色の点は表示フラグ。",
                              styles["caption"]))

    if graph.get("nodes"):
        flow.append(_node_table(graph, styles))

    for block in spec.get("comparisons", []):
        flow.append(Paragraph(block.get("label", "比較"), styles["h2"]))
        if block.get("note"):
            for para in block["note"].split("\n\n"):
                flow.append(Paragraph(para.strip(), styles["body"]))
        if block.get("images"):
            flow.append(_image_row(block["images"], styles, base_dir,
                                   block.get("per_row", 4)))
        if block.get("rows"):
            flow.append(_plain_table(block["columns"], block["rows"], styles))

    render_img = _resolve(spec.get("render"), base_dir)
    if render_img:
        flow.append(Paragraph("結果", styles["h2"]))
        flow.append(_fit_image(render_img, CONTENT_W, 115 * mm))
        flow.append(Paragraph(
            "OpenGL ROP による Smooth Wire Shaded 表示。ワイヤーフレームが乗っているため、"
            "ネットワークが生成したトポロジが確認できる。画像内のウォーターマークは "
            "Apprentice ライセンスによるもの。", styles["caption"]))

    if stats:
        flow.append(Paragraph("ジオメトリ", styles["h2"]))
        flow.append(_stats_table(stats, styles))

    if spec.get("notes"):
        flow.append(Paragraph("わかったこと", styles["h2"]))
        flow.extend(_bullets(spec["notes"], styles))

    if spec.get("next"):
        flow.append(Paragraph("次にやること", styles["h2"]))
        flow.extend(_bullets(spec["next"], styles))

    return flow, graph


def _document(out_pdf, title):
    return SimpleDocTemplate(
        out_pdf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=title, author="Houdini 実験室",
    )


def build(spec, out_pdf, base_dir="."):
    styles = _styles(_register_fonts())
    flow, graph = _experiment_flow(spec, styles, base_dir)
    _document(out_pdf, spec.get("title") or graph.get("title", "Houdini")).build(flow)
    return out_pdf


def build_bundle(spec_paths, out_pdf, title, intro=""):
    """One PDF holding several experiments.

    Gemini Notebook has a 300-source ceiling, so experiments go in as themed
    bundles that get replaced as they grow, rather than one source each."""
    styles = _styles(_register_fonts())

    titles = []
    bodies = []
    for spec_path in spec_paths:
        spec_path = os.path.abspath(spec_path)
        with open(spec_path, encoding="utf-8") as fp:
            spec = json.load(fp)
        flow, graph = _experiment_flow(spec, styles, os.path.dirname(spec_path))
        titles.append(spec.get("title") or graph.get("title", ""))
        bodies.append(flow)

    cover = [Paragraph(title, styles["title"])]
    cover.append(Paragraph(
        f'{datetime.date.today().isoformat()}　|　収録 {len(bodies)} 件', styles["meta"]))
    if intro:
        for para in intro.split("\n\n"):
            cover.append(Paragraph(para.strip(), styles["body"]))
    cover.append(Paragraph("収録している実験", styles["h2"]))
    cover.extend(_bullets(titles, styles))

    flow = cover
    for body in bodies:
        flow.append(PageBreak())
        flow.extend(body)

    _document(out_pdf, title).build(flow)
    return out_pdf


BUNDLE_INTRO = (
    "hython で実際にノードを組み、その結果を実測して記録したもの。"
    "数値はすべて実行して得た値で、推測は含まない。\n\n"
    "各実験は「何を作ったか」「ノードの接続」「変更したパラメータ」「結果」"
    "「わかったこと」「次にやること」の順で並んでいる。"
    "用語は別ソースの「用語集: Houdini 初心者向け」にまとめてある。"
)


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "--bundle":
        out_pdf, title, specs = sys.argv[2], sys.argv[3], sys.argv[4:]
        print(build_bundle(specs, out_pdf, title, BUNDLE_INTRO))
        return 0

    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    spec_path = os.path.abspath(sys.argv[1])
    with open(spec_path, encoding="utf-8") as fp:
        spec = json.load(fp)
    print(build(spec, sys.argv[2], base_dir=os.path.dirname(spec_path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
