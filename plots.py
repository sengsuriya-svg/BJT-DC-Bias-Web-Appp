"""Small SVG plot builder driven only by numeric ngspice results."""

from __future__ import annotations

import math
from html import escape

_WIDTH = 640
_HEIGHT = 260
_LEFT = 62
_RIGHT = 620
_TOP = 30
_BOTTOM = 220
_Y_LABEL_MID = (_TOP + _BOTTOM) / 2
_COLORS = ["#0c8176", "#c77a35", "#2563eb"]


def _freq_label(frequency: float) -> str:
    """Format a decade tick as 1, 10, 1k, 10k, 1M and so on."""
    if frequency >= 1e6:
        return f"{frequency / 1e6:g}M"
    if frequency >= 1e3:
        return f"{frequency / 1e3:g}k"
    return f"{frequency:g}"


def line_svg(points, x_label, y_label, title, series_labels=None, log_x=False):
    """Render one or more numeric series as an inline SVG string.

    ``log_x`` is for log-swept data such as ngspice's ``.ac dec`` output: the
    horizontal axis is drawn in log10 space and labelled in frequency decades.
    """
    numeric_rows = []
    for row in points:
        values = [float(value) for value in row[:3]]
        numeric_rows.append(values)

    if log_x:
        numeric_rows = [
            [math.log10(row[0]), *row[1:]]
            for row in numeric_rows
            if row[0] > 0
        ]

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
        f'<text x="18" y="{_Y_LABEL_MID:.1f}" '
        f'transform="rotate(-90 18 {_Y_LABEL_MID:.1f})" '
        f'text-anchor="middle" font-size="11" fill="#526c7f">'
        f'{escape(str(y_label))}</text>',
    ]

    if log_x:
        for decade in range(math.floor(x_min), math.ceil(x_max) + 1):
            tick_x = px(decade)
            parts.append(
                f'<line x1="{tick_x:.2f}" y1="{_TOP}" x2="{tick_x:.2f}" y2="{_BOTTOM}" '
                'stroke="#e6eef3"/>'
            )
            parts.append(
                f'<text x="{tick_x:.2f}" y="{_BOTTOM + 14}" text-anchor="middle" '
                f'font-size="10" fill="#526c7f">{escape(_freq_label(10 ** decade))}</text>'
            )

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
