"""Generate the animated black-and-white SVG title cards used in the profile README."""

import random
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets"
BLACK = "#000000"
WHITE = "#F2F2F2"
SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "SFMono-Regular, Menlo, Consolas, Courier New, monospace"
NOISE = "0123456789#$%&@*+=/<>?!"
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither_fade(width, y, height, levels=6, pixel=2):
    """White ordered dither that gets denser toward the bottom edge."""
    tile = pixel * 4
    defs, rects = [], []
    step = height / levels
    for n in range(levels):
        threshold = 1 + n * 2
        cells = "".join(f'<rect x="{x * pixel}" y="{yy * pixel}" width="{pixel}" height="{pixel}"/>'
                        for yy in range(4) for x in range(4) if BAYER[yy][x] < threshold)
        defs.append(f'<pattern id="d{n}" width="{tile}" height="{tile}" patternUnits="userSpaceOnUse">'
                    f'<g fill="{WHITE}">{cells}</g></pattern>')
        rects.append(f'<rect x="0" y="{y + n * step:.1f}" width="{width}" height="{step + 0.5:.1f}" fill="url(#d{n})"/>')
    return "".join(defs), "".join(rects)


def opacity_anim(intervals, total):
    points = {0.0: 0}
    for start, end in sorted(intervals):
        points[round(start / total, 4)] = 1
        points[round(end / total, 4)] = 0
    keys = sorted(points)
    values = [points[k] for k in keys]
    if keys[-1] < 1:
        keys.append(1.0)
        values.append(values[-1])
    return (f'<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{";".join(f"{k:g}" for k in keys)}" values="{";".join(str(v) for v in values)}"/>')


def decode(word, cx, baseline, size, spacing, total, seed, hold_until):
    """Letters flicker through random characters for a moment, then lock in left to right."""
    rng = random.Random(seed)
    step, settle, stagger = 0.04, 0.25, 0.04
    width = len(word) * spacing
    parts = []
    for i, ch in enumerate(word):
        if ch == " ":
            continue
        x = cx - width / 2 + (i + 0.5) * spacing
        resolve = settle + i * stagger
        noise = {}
        for start, end in ((0.0, resolve), (hold_until + i * stagger * 0.5, total)):
            t = start
            while t < end - 1e-9:
                noise.setdefault(rng.choice(NOISE), []).append((t, min(t + step, end)))
                t += step
        for glyph, windows in noise.items():
            parts.append(f'<text x="{x:.1f}" y="{baseline}" text-anchor="middle" font-family="{MONO}" '
                         f'font-size="{size * 0.8:.0f}" fill="{WHITE}" opacity="0">{escape(glyph)}'
                         f'{opacity_anim(windows, total)}</text>')
        parts.append(f'<text x="{x:.1f}" y="{baseline}" text-anchor="middle" font-family="{SANS}" font-weight="700" '
                     f'font-size="{size}" fill="{WHITE}" opacity="0">{escape(ch)}'
                     f'{opacity_anim([(resolve, hold_until + i * stagger * 0.5)], total)}</text>')
    return "".join(parts)


def svg(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}">{body}</svg>\n')


def header():
    width, height = 1200, 240
    defs, fade = dither_fade(width, 180, 60)
    body = (f'<defs>{defs}</defs><rect width="{width}" height="{height}" fill="{BLACK}"/>{fade}'
            + decode("ARHM IQBAL", width / 2, 135, 84, 72, 12.0, 3, 11.4))
    return svg(width, height, body)


def section(title, seed):
    width, height = 900, 60
    body = (f'<rect width="{width}" height="{height}" fill="{BLACK}"/>'
            + decode(title, 20 + len(title) * 13, 40, 26, 26, 12.0, seed, 11.4)
            + f'<rect x="0" y="{height - 2}" width="{width}" height="2" fill="{WHITE}" opacity="0.25"/>')
    return svg(width, height, body)


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "header.svg").write_text(header())
    for n, (name, title) in enumerate((("about", "ABOUT"), ("languages", "LANGUAGES"),
                                       ("tools", "TOOLS"), ("activity", "ACTIVITY"))):
        (OUT / f"section_{name}.svg").write_text(section(title, 20 + n))
    footer = OUT / "footer.svg"
    if footer.exists():
        footer.unlink()


if __name__ == "__main__":
    main()
