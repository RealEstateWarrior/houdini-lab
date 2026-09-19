"""PIL だけで描く折れ線グラフ（matplotlib が入っていないため）。

目盛りと線は同じ1つの換算で置く。ラベルは線が実際に届く範囲の値だけ出す。

    from pil_chart import line_chart
    line_chart("out/x.png", series, x_label="秒", y_label="高さ", ...)

series は [{"label": str, "points": [(x, y), ...], "color": (r, g, b), "dash": bool}, ...]
"""

import math

from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/meiryo.ttc"
INK = (29, 29, 31)
DIM = (120, 120, 128)
GRID = (232, 232, 237)
GROUND = (255, 255, 255)
PALETTE = [(0, 102, 204), (214, 96, 30), (46, 139, 87), (160, 60, 150), (120, 120, 128)]


def _font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def _ticks(lo, hi, count=5):
    span = hi - lo
    raw = span / count
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), default=mag * 10)
    first = math.ceil(lo / step) * step
    out = []
    value = first
    while value <= hi + 1e-9:
        out.append(round(value, 10))
        value += step
    return out


def line_chart(path, series, title="", x_label="", y_label="", size=(1000, 560),
               x_range=None, y_range=None, markers=()):
    """markers は [(x, y, "文字")] で、点に小さな注記を付ける。"""
    width, height = size
    left, right, top, bottom = 92, 30, 70 if title else 30, 120
    image = Image.new("RGB", size, GROUND)
    draw = ImageDraw.Draw(image)
    xs = [x for s in series for x, _ in s["points"]]
    ys = [y for s in series for _, y in s["points"]]
    x0, x1 = x_range or (min(xs), max(xs))
    y0, y1 = y_range or (min(ys), max(ys))
    pad = (y1 - y0) * 0.05 or 1.0
    if not y_range:
        y0, y1 = y0 - pad, y1 + pad

    def px(x):
        return left + (x - x0) / (x1 - x0) * (width - left - right)

    def py(y):
        return height - bottom - (y - y0) / (y1 - y0) * (height - top - bottom)

    f_small, f_mid, f_title = _font(15), _font(17), _font(24)
    if title:
        draw.text((left, 22), title, font=f_title, fill=INK)
    for t in _ticks(y0, y1):
        draw.line([left, py(t), width - right, py(t)], fill=GRID)
        label = f"{t:g}"
        w = draw.textlength(label, font=f_small)
        draw.text((left - 10 - w, py(t) - 9), label, font=f_small, fill=DIM)
    for t in _ticks(x0, x1, 6):
        draw.line([px(t), top, px(t), height - bottom], fill=GRID)
        label = f"{t:g}"
        w = draw.textlength(label, font=f_small)
        draw.text((px(t) - w / 2, height - bottom + 8), label, font=f_small, fill=DIM)
    draw.rectangle([left, top, width - right, height - bottom], outline=(200, 200, 206))
    if x_label:
        w = draw.textlength(x_label, font=f_mid)
        draw.text(((left + width - right) / 2 - w / 2, height - bottom + 32), x_label,
                  font=f_mid, fill=DIM)
    if y_label:
        draw.text((10, top - 26 if not title else top - 24), y_label, font=f_mid, fill=DIM)

    for index, s in enumerate(series):
        color = s.get("color") or PALETTE[index % len(PALETTE)]
        pts = [(px(x), py(y)) for x, y in s["points"]]
        if s.get("dash"):
            # 線分ごとに 6px 描いて 5px 空ける。点の数に関係なく同じ見た目になる
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                length = max(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5, 1e-6)
                pos = 0.0
                while pos < length:
                    end = min(pos + 6.0, length)
                    draw.line([(ax + (bx - ax) * pos / length, ay + (by - ay) * pos / length),
                               (ax + (bx - ax) * end / length, ay + (by - ay) * end / length)],
                              fill=color, width=2)
                    pos += 11.0
        else:
            draw.line(pts, fill=color, width=3, joint="curve")
    for x, y, text in markers:
        draw.ellipse([px(x) - 4, py(y) - 4, px(x) + 4, py(y) + 4], fill=INK)
        draw.text((px(x) + 8, py(y) - 22), text, font=f_small, fill=INK)

    # 凡例は下にまとめる
    lx, ly = left, height - 46
    for index, s in enumerate(series):
        if not s.get("label"):
            continue
        color = s.get("color") or PALETTE[index % len(PALETTE)]
        if s.get("dash"):
            for k in range(0, 28, 8):
                draw.line([lx + k, ly + 10, lx + k + 4, ly + 10], fill=color, width=2)
        else:
            draw.line([lx, ly + 10, lx + 28, ly + 10], fill=color, width=3)
        draw.text((lx + 36, ly), s["label"], font=f_small, fill=INK)
        lx += 36 + draw.textlength(s["label"], font=f_small) + 28
    image.save(path)
    return path
