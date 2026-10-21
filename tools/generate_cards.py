"""Generate the animated SVG title cards used in the profile README."""

import random
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets"
BG = "#07070B"
PURPLE = "#3B2A6B"
TEAL = "#0F4A4F"
INK = "#E8E6F2"
RED = "#FF2A6D"
CYAN = "#05D9E8"
MONO = "JetBrains Mono, SFMono-Regular, Menlo, Consolas, Courier New, monospace"

# Hieroglyph-inspired glyphs drawn as strokes in a 40 x 56 box, so they render
# without relying on the viewer having an Egyptian-hieroglyph font installed.
GLYPHS = [
    "M4 28 Q20 12 36 28 Q20 40 4 28 Z M20 22 a5 5 0 1 0 0.1 0 M14 36 L10 50 M22 38 Q28 50 34 46",
    "M20 4 a9 11 0 1 0 0.1 0 M6 26 L34 26 M20 26 L20 54",
    "M20 54 L20 6 M20 12 Q30 14 32 4 M20 22 Q8 22 6 12 M20 32 Q32 32 34 22",
    "M4 14 l6 -6 l6 6 l6 -6 l6 6 l6 -6 M4 30 l6 -6 l6 6 l6 -6 l6 6 l6 -6 M4 46 l6 -6 l6 6 l6 -6 l6 6 l6 -6",
    "M8 40 Q12 20 26 16 Q34 14 36 20 L30 22 Q32 34 22 40 Z M14 40 L12 54 M22 40 L24 54",
    "M20 12 a14 14 0 1 0 0.1 0 M20 24 a2 2 0 1 0 0.1 0",
    "M20 4 L20 54 M8 12 L32 12 M8 20 L32 20 M8 28 L32 28 M12 54 L28 54",
    "M8 50 Q4 36 16 32 Q30 28 26 16 Q24 6 34 6 M34 6 L38 10 M30 4 L32 0",
    "M6 54 L20 6 L34 54 Z M13 32 L27 32",
    "M8 8 L32 8 L32 48 L8 48 Z M8 28 L32 28 M20 8 L20 48",
]


def dither_patterns():
    """Ordered-dither tiles (2 px pixels on an 8 px Bayer grid) at three densities."""
    bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    out = []
    for name, threshold, color in (("d1", 3, PURPLE), ("d2", 7, PURPLE), ("d3", 11, TEAL), ("d4", 5, TEAL)):
        cells = "".join(
            f'<rect x="{x * 2}" y="{y * 2}" width="2" height="2"/>'
            for y in range(4) for x in range(4) if bayer[y][x] < threshold
        )
        out.append(f'<pattern id="{name}" width="8" height="8" patternUnits="userSpaceOnUse">'
                   f'<g fill="{color}">{cells}</g></pattern>')
    return "".join(out)


def keytimes(intervals, total):
    """Discrete opacity animation that is visible only within the given (start, end) intervals."""
    points = {0.0: 0}
    for start, end in sorted(intervals):
        points[round(start / total, 4)] = 1
        points[round(end / total, 4)] = 0
    keys = sorted(points)
    values = [points[k] for k in keys]
    if keys[-1] < 1:
        keys.append(1.0)
        values.append(values[-1])
    return ";".join(f"{k:g}" for k in keys), ";".join(str(v) for v in values)


def opacity_anim(intervals, total):
    keys, values = keytimes(intervals, total)
    return (f'<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{keys}" values="{values}"/>')


def scramble_word(word, x0, y_mid, slot, size, total, seed, resolve_start, resolve_step,
                  glitch_start, glitch_end):
    """Letters cycle through glyphs, resolve left to right, glitch, then scramble again."""
    rng = random.Random(seed)
    step = 0.09
    parts = []
    scale = size / 56
    for i, ch in enumerate(word):
        x = x0 + i * slot
        resolve = resolve_start + i * resolve_step
        glyph_windows = {k: [] for k in range(len(GLYPHS))}
        t = 0.0
        while t < resolve - 1e-9:
            glyph_windows[rng.randrange(len(GLYPHS))].append((t, min(t + step, resolve)))
            t += step
        letter_windows = [(resolve, glitch_start)]
        t = glitch_start
        while t < glitch_end - 1e-9:
            if rng.random() < 0.5:
                letter_windows.append((t, t + 0.06))
            else:
                glyph_windows[rng.randrange(len(GLYPHS))].append((t, t + 0.06))
            t += 0.06
        t = glitch_end
        while t < total - 1e-9:
            glyph_windows[rng.randrange(len(GLYPHS))].append((t, min(t + step, total)))
            t += step
        for k, windows in glyph_windows.items():
            if not windows:
                continue
            gx = x + (slot - 40 * scale) / 2
            gy = y_mid - 28 * scale
            parts.append(
                f'<path d="{GLYPHS[k]}" transform="translate({gx:.1f} {gy:.1f}) scale({scale:.3f})" '
                f'fill="none" stroke="currentColor" stroke-width="{3 / scale:.2f}" stroke-linecap="round" '
                f'stroke-linejoin="round" opacity="0">{opacity_anim(windows, total)}</path>')
        if ch != " ":
            parts.append(
                f'<text x="{x + slot / 2:.1f}" y="{y_mid:.1f}" text-anchor="middle" dominant-baseline="central" '
                f'font-family="{MONO}" font-weight="800" font-size="{size}" fill="currentColor" opacity="0">'
                f'{escape(ch)}{opacity_anim(letter_windows, total)}</text>')
    return "".join(parts)


def glitch_layers(layer_id, total, bursts, width, height):
    """Red/cyan offset copies plus a displaced slice during short glitch bursts."""
    def jitter(amplitude, seed):
        rng = random.Random(seed)
        keys, values = [0.0], ["0 0"]
        for start, end in bursts:
            t = start
            while t < end:
                keys.append(round(t / total, 4))
                values.append(f"{rng.uniform(-amplitude, amplitude):.1f} {rng.uniform(-1.5, 1.5):.1f}")
                t += 0.05
            keys.append(round(end / total, 4))
            values.append("0 0")
        keys.append(1.0)
        values.append("0 0")
        return (f'<animateTransform attributeName="transform" type="translate" dur="{total}s" '
                f'repeatCount="indefinite" calcMode="discrete" keyTimes="{";".join(f"{k:g}" for k in keys)}" '
                f'values="{";".join(values)}"/>')

    slice_y = [(0.32, 0.12), (0.55, 0.08), (0.44, 0.1)]
    slices = "".join(
        f'<clipPath id="{layer_id}s{n}"><rect x="0" y="{height * y:.0f}" width="{width}" height="{height * h:.0f}"/></clipPath>'
        for n, (y, h) in enumerate(slice_y))
    slice_uses = "".join(
        f'<use href="#{layer_id}" clip-path="url(#{layer_id}s{n})" style="color:{INK}">{jitter(18, 40 + n)}</use>'
        for n in range(len(slice_y)))
    return (f'<defs>{slices}</defs>'
            f'<use href="#{layer_id}" style="color:{RED};mix-blend-mode:screen" opacity="0.8">{jitter(6, 1)}</use>'
            f'<use href="#{layer_id}" style="color:{CYAN};mix-blend-mode:screen" opacity="0.8">{jitter(6, 2)}</use>'
            f'<use href="#{layer_id}" style="color:{INK}"/>' + slice_uses)


def dither_bands(width, height, drift):
    """Dithered bands that thicken toward the top and bottom edges and drift slowly."""
    anim = (f'<animateTransform attributeName="patternTransform" type="translate" from="0 0" to="{drift} 0" '
            f'dur="12s" repeatCount="indefinite"/>') if drift else ""
    band = max(6, height // 10)
    rows = [("d3", 0, band), ("d2", band, band), ("d1", 2 * band, band),
            ("d1", height - 3 * band, band), ("d2", height - 2 * band, band), ("d4", height - band, band)]
    return "".join(f'<rect x="0" y="{y}" width="{width}" height="{h}" fill="url(#{p})"/>' for p, y, h in rows), anim


def glyph_row(x, y, scale, indices, color, gap=14):
    step = 40 * scale + gap
    return "".join(
        f'<path d="{GLYPHS[k]}" transform="translate({x + n * step:.1f} {y:.1f}) scale({scale})" fill="none" '
        f'stroke="{color}" stroke-width="{2 / scale:.2f}" stroke-linecap="round" stroke-linejoin="round"/>'
        for n, k in enumerate(indices))


def scanlines(width, height):
    return (f'<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
            f'<rect width="4" height="1" fill="#FFFFFF" opacity="0.035"/></pattern>'
            f'<rect width="{width}" height="{height}" fill="url(#scan)"/>')


def svg(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
            f'{body}</svg>\n')


def header():
    width, height, total = 1200, 300, 9.0
    word = "ARHM IQBAL"
    slot, size = 74, 76
    x0 = (width - slot * len(word)) / 2
    bands, _ = dither_bands(width, height, 0)
    letters = scramble_word(word, x0, height / 2, slot, size, total, 7, 0.7, 0.14, 7.2, 7.9)
    cursor_x = x0 + slot * len(word) + 8
    blocks = "".join(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{p})" opacity="0.9"/>'
        for x, y, w, h, p in ((70, 96, 120, 34, "d2"), (1010, 182, 140, 26, "d3"), (930, 70, 60, 18, "d1"),
                              (150, 200, 70, 20, "d4")))
    body = (
        f'<defs>{dither_patterns()}'
        f'<radialGradient id="vig" cx="50%" cy="50%" r="70%"><stop offset="55%" stop-color="#000" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="#000" stop-opacity="0.85"/></radialGradient>'
        f'<g id="name">{letters}</g></defs>'
        f'<rect width="{width}" height="{height}" fill="{BG}"/>{bands}{blocks}'
        + glitch_layers("name", total, [(0.0, 0.35), (3.6, 3.8), (7.2, 7.9)], width, height)
        + f'<rect x="{cursor_x:.0f}" y="{height / 2 - 34:.0f}" width="22" height="68" fill="{CYAN}">'
        f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" calcMode="discrete" dur="1s" repeatCount="indefinite"/></rect>'
        f'<text x="28" y="34" font-family="{MONO}" font-size="13" fill="#6C6A86" letter-spacing="2">[ ARHM-IQBAL ]</text>'
        f'<text x="{width - 28}" y="34" text-anchor="end" font-family="{MONO}" font-size="13" fill="#6C6A86" '
        f'letter-spacing="2">53.5461°N  113.4938°W</text>'
        + glyph_row(28, height - 40, 0.32, [0, 1, 4, 5, 6], "#4A4862")
        + scanlines(width, height)
        + f'<rect width="{width}" height="{height}" fill="url(#vig)"/>'
    )
    return svg(width, height, body)


def section(title, seed):
    width, height, total = 900, 64, 8.0
    slot, size = 22, 26
    x0 = 70
    letters = scramble_word(title, x0, height / 2, slot, size, total, seed, 0.3, 0.05, 6.6, 7.0)
    strip = "".join(
        f'<rect x="{x}" y="0" width="{w}" height="{height}" fill="url(#{p})"/>'
        for x, w, p in ((0, 18, "d3"), (18, 14, "d2"), (32, 12, "d1")))
    tail_x = x0 + slot * len(title) + 24
    body = (
        f'<defs>{dither_patterns()}<g id="t{seed}">{letters}</g></defs>'
        f'<rect width="{width}" height="{height}" fill="{BG}"/>{strip}'
        + glitch_layers(f"t{seed}", total, [(0.0, 0.25), (6.6, 7.0)], width, height)
        + f'<rect x="{tail_x}" y="{height / 2 - 1}" width="{width - tail_x - 20}" height="2" fill="url(#d3)"/>'
        f'<rect x="{tail_x}" y="{height / 2 + 5}" width="{(width - tail_x - 20) * 0.6:.0f}" height="2" fill="url(#d1)"/>'
        + scanlines(width, height)
    )
    return svg(width, height, body)


def footer():
    width, height = 1200, 90
    rows = [("d1", 0, 18), ("d2", 18, 18), ("d3", 36, 18), ("d2", 54, 18), ("d4", 72, 18)]
    body = (f'<defs>{dither_patterns()}</defs><rect width="{width}" height="{height}" fill="{BG}"/>'
            + "".join(f'<rect x="0" y="{y}" width="{width}" height="{h}" fill="url(#{p})"/>' for p, y, h in rows)
            + f'<rect x="{width / 2 - 230}" y="{height / 2 - 16}" width="460" height="32" fill="{BG}"/>'
            + glyph_row(width / 2 - 214, height / 2 - 9, 0.32, [0, 1], "#8C89A8", 10)
            + f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="{MONO}" font-size="13" fill="#8C89A8" letter-spacing="6">END OF TRANSMISSION</text>'
            + glyph_row(width / 2 + 176, height / 2 - 9, 0.32, [5, 6], "#8C89A8", 10)
            + scanlines(width, height))
    return svg(width, height, body)


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "header.svg").write_text(header())
    for name, title, seed in (("about", "ABOUT ME", 11), ("languages", "LANGUAGES", 12),
                              ("tools", "FRAMEWORKS & TOOLS", 13), ("activity", "ACTIVITY", 14)):
        (OUT / f"section_{name}.svg").write_text(section(title, seed))
    (OUT / "footer.svg").write_text(footer())


if __name__ == "__main__":
    main()
