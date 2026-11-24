"""Small SVG plot builder driven only by numeric ngspice results."""

from __future__ import annotations

from html import escape

_WIDTH = 640
_HEIGHT = 260
_LEFT = 62
_RIGHT = 620
_TOP = 30
_BOTTOM = 220
_COLORS = ["#0c8176", "#c77a35", "#2563eb"]


def line_svg(points, x_label, y_label, title, series_labels=None):
    """Render one or more numeric series as an inline SVG string."""
    numeric_rows = []
    for row in points:
        values = [float(value) for value in row[:3]]
        numeric_rows.append(values)

    if not numeric_rows:
        return '<svg viewBox="0 0 640 260" role="img"><text x="20" y="30">No data</text></svg>'

    series_count = max(len(row) for row in numeric_rows) - 1
    if series_count < 1:
        return '<svg viewBox="0 0 640 260" role="img"><text x="20" y="30">No series</text></svg>'

    x_values = [row[0] for row in numeric_rows]
    y_values = [value for row in numeric_rows for value in row[1:]]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    if x_max == x_min:
        x_max = x_min + 1.0
    if y_max == y_min:
        y_min -= 0.5
        y_max += 0.5

    def px(x):
        return _LEFT + (x - x_min) / (x_max - x_min) * (_RIGHT - _LEFT)

    def py(y):
        return _BOTTOM - (y - y_min) / (y_max - y_min) * (_BOTTOM - _TOP)

    labels = list(series_labels or [])
    parts = [
        f'<svg viewBox="0 0 {_WIDTH} {_HEIGHT}" role="img" '
        'style="width:100%;height:auto;font-family:Tahoma,Arial,sans-serif">',
        f'<rect x="0" y="0" width="{_WIDTH}" height="{_HEIGHT}" fill="#f9fcfd" '
        'stroke="#dce7ee" rx="6"/>',
        f'<text x="{_LEFT}" y="18" font-size="13" fill="#103658" font-weight="700">'
        f'{escape(str(title))}</text>',
        f'<line x1="{_LEFT}" y1="{_BOTTOM}" x2="{_RIGHT}" y2="{_BOTTOM}" '
        'stroke="#9cb2c2"/>',
        f'<line x1="{_LEFT}" y1="{_TOP}" x2="{_LEFT}" y2="{_BOTTOM}" '
        'stroke="#9cb2c2"/>',
        f'<text x="{_RIGHT}" y="{_HEIGHT - 8}" text-anchor="end" font-size="11" '
        f'fill="#526c7f">{escape(str(x_label))}</text>',
        f'<text x="{_LEFT}" y="{_TOP - 10}" font-size="11" fill="#526c7f">'
        f'{escape(str(y_label))}</text>',
    ]

    for index in range(series_count):
        coords = " ".join(f"{px(row[0]):.2f},{py(row[index + 1]):.2f}" for row in numeric_rows)
        color = _COLORS[index % len(_COLORS)]
        label = labels[index] if index < len(labels) else f"Series {index + 1}"
        parts.append(
            f'<polyline points="{coords}" fill="none" stroke="{color}" '
            'stroke-width="2.2" stroke-linejoin="round"/>'
        )
        parts.append(
            f'<rect x="{_LEFT + index * 110}" y="8" width="10" height="10" fill="{color}"/>'
            f'<text x="{_LEFT + index * 110 + 14}" y="17" font-size="11" fill="#526c7f">'
            f'{escape(str(label))}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)
