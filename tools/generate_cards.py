"""Generate the animated black-and-white SVG title cards used in the profile README."""

import random
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets"
BLACK = "#000000"
WHITE = "#F2F2F2"
GREY = "#8A8A8A"
DIM = "#4D4D4D"
SERIF = "Times New Roman, Times, Georgia, serif"
MONO = "JetBrains Mono, SFMono-Regular, Menlo, Consolas, Courier New, monospace"
NOISE = "0123456789#$%&@*+=/\\<>?!{}[]^~:;"
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither_defs(pixel=3, levels=(1, 3, 5, 7, 9, 11, 13)):
    """Ordered-dither tiles in white at increasing density, named dither1..N."""
    tile = pixel * 4
    out = []
    for n, threshold in enumerate(levels, start=1):
        cells = "".join(
            f'<rect x="{x * pixel}" y="{y * pixel}" width="{pixel}" height="{pixel}"/>'
            for y in range(4) for x in range(4) if BAYER[y][x] < threshold)
        out.append(f'<pattern id="dither{n}" width="{tile}" height="{tile}" patternUnits="userSpaceOnUse">'
                   f'<g fill="{WHITE}">{cells}</g></pattern>')
    return "".join(out)


def dither_gradient(x, y, width, height, levels, horizontal=True, reverse=False):
    """Step through dither densities to fake a gradient: sparse to dense (or reversed)."""
    order = list(range(1, levels + 1))
    if reverse:
        order.reverse()
    step = (width if horizontal else height) / levels
    rects = []
    for i, level in enumerate(order):
        if horizontal:
            rects.append(f'<rect x="{x + i * step:.1f}" y="{y}" width="{step + 0.5:.1f}" height="{height}" fill="url(#dither{level})"/>')
        else:
            rects.append(f'<rect x="{x}" y="{y + i * step:.1f}" width="{width}" height="{step + 0.5:.1f}" fill="url(#dither{level})"/>')
    return "".join(rects)


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


def decode_word(word, x0, baseline, slot, size, total, seed, resolve_start, resolve_step,
                rescramble_start, serif=True, condense=0.82):
    """Each letter flickers through random numbers/symbols, then locks in, left to right."""
    rng = random.Random(seed)
    step = 0.055
    parts = []
    for i, ch in enumerate(word):
        if ch == " ":
            continue
        cx = x0 + i * slot + slot / 2
        resolve = resolve_start + i * resolve_step
        rescramble = rescramble_start + i * resolve_step * 0.5
        noise = {}
        for start, end in ((0.0, resolve), (rescramble, total)):
            t = start
            while t < end - 1e-9:
                noise.setdefault(rng.choice(NOISE), []).append((t, min(t + step, end)))
                t += step
        for glyph, windows in noise.items():
            parts.append(
                f'<text x="{cx:.1f}" y="{baseline:.1f}" text-anchor="middle" font-family="{MONO}" '
                f'font-weight="700" font-size="{size * 0.62:.0f}" fill="currentColor" opacity="0">'
                f'{escape(glyph)}{opacity_anim(windows, total)}</text>')
        font = SERIF if serif else MONO
        parts.append(
            f'<text transform="translate({cx:.1f} {baseline:.1f}) scale({condense} 1.12)" text-anchor="middle" '
            f'font-family="{font}" font-weight="900" font-size="{size}" fill="currentColor" opacity="0">'
            f'{escape(ch)}{opacity_anim([(resolve, rescramble)], total)}</text>')
    return "".join(parts)


def glitch(layer_id, total, bursts, width, height):
    """Monochrome glitch: a grey ghost and horizontally displaced slices during short bursts."""
    def jitter(amplitude, seed):
        rng = random.Random(seed)
        keys, values = [0.0], ["0 0"]
        for start, end in bursts:
            t = start
            while t < end:
                keys.append(round(t / total, 4))
                values.append(f"{rng.uniform(-amplitude, amplitude):.1f} 0")
                t += 0.05
            keys.append(round(end / total, 4))
            values.append("0 0")
        keys.append(1.0)
        values.append("0 0")
        return (f'<animateTransform attributeName="transform" type="translate" dur="{total}s" repeatCount="indefinite" '
                f'calcMode="discrete" keyTimes="{";".join(f"{k:g}" for k in keys)}" values="{";".join(values)}"/>')

    bands = [(0.30, 0.10), (0.52, 0.07), (0.68, 0.09)]
    clips = "".join(f'<clipPath id="{layer_id}c{n}"><rect x="0" y="{height * y:.0f}" width="{width}" '
                    f'height="{height * h:.0f}"/></clipPath>' for n, (y, h) in enumerate(bands))
    return (f'<defs>{clips}</defs>'
            f'<use href="#{layer_id}" style="color:{DIM}">{jitter(8, 1)}</use>'
            f'<use href="#{layer_id}" style="color:{WHITE}"/>'
            + "".join(f'<use href="#{layer_id}" clip-path="url(#{layer_id}c{n})" style="color:{WHITE}">'
                      f'{jitter(22, 10 + n)}</use>' for n in range(len(bands))))


def scanlines(width, height):
    return (f'<pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse">'
            f'<rect width="3" height="1" fill="{BLACK}" opacity="0.35"/></pattern>'
            f'<rect width="{width}" height="{height}" fill="url(#scan)"/>')


def label(x, y, text, size=12, fill=GREY, anchor="start", spacing=3):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{MONO}" font-size="{size}" '
            f'fill="{fill}" letter-spacing="{spacing}">{escape(text)}</text>')


def svg(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}">{body}</svg>\n')


def header():
    width, height, total = 1200, 340, 10.0
    size, slot = 128, 104
    rows = ""
    rows += decode_word("ARHM", 70, 158, slot, size, total, 3, 0.5, 0.13, 8.2)
    rows += decode_word("IQBAL", 70, 292, slot, size, total, 4, 1.0, 0.13, 8.5)
    body = (
        f'<defs>{dither_defs()}<g id="name">{rows}</g></defs>'
        f'<rect width="{width}" height="{height}" fill="{BLACK}"/>'
        + dither_gradient(640, 0, 560, height, 7)
        + f'<rect x="700" y="40" width="440" height="260" fill="{BLACK}"/>'
        + dither_gradient(700, 40, 440, 260, 7, horizontal=False, reverse=True)
        + f'<rect x="716" y="56" width="408" height="228" fill="{BLACK}"/>'
        + f'<rect x="716" y="56" width="408" height="228" fill="none" stroke="{WHITE}" stroke-width="1"/>'
        + label(736, 92, "PROFILE:01", 14, WHITE, spacing=4)
        + f'<rect x="736" y="106" width="368" height="1" fill="{GREY}"/>'
        + label(736, 140, "SUBJECT ....... ARHM IQBAL")
        + label(736, 166, "AFFILIATION ... U OF ALBERTA")
        + label(736, 192, "LOCATION ...... EDMONTON, AB")
        + label(736, 218, "STATUS ........ ONLINE")
        + f'<rect x="1080" y="206" width="12" height="14" fill="{WHITE}">'
          f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" calcMode="discrete" dur="1s" '
          f'repeatCount="indefinite"/></rect>'
        + dither_gradient(736, 246, 368, 18, 7)
        + label(70, 40, "// ARHM-IQBAL", 12, GREY)
        + f'<rect x="70" y="312" width="540" height="2" fill="{WHITE}"/>'
        + glitch("name", total, [(0.0, 0.3), (4.4, 4.6), (8.2, 8.7)], width, height)
        + scanlines(width, height)
    )
    return svg(width, height, body)


def section(index, title, seed):
    width, height, total = 900, 72, 9.0
    size, slot = 38, 30
    x0 = 92
    letters = decode_word(title, x0, 52, slot, size, total, seed, 0.25, 0.05, 7.6, condense=0.86)
    tail = x0 + slot * len(title) + 24
    body = (
        f'<defs>{dither_defs(pixel=2)}<g id="t{seed}">{letters}</g></defs>'
        f'<rect width="{width}" height="{height}" fill="{BLACK}"/>'
        + label(16, 46, f"{index:02d}", 22, WHITE, spacing=2)
        + f'<rect x="66" y="14" width="2" height="44" fill="{WHITE}"/>'
        + glitch(f"t{seed}", total, [(0.0, 0.2), (7.6, 8.0)], width, height)
        + (dither_gradient(tail, 20, width - tail - 16, 32, 7) if tail < width - 60 else "")
        + scanlines(width, height)
    )
    return svg(width, height, body)


def footer():
    width, height = 1200, 48
    body = (f'<defs>{dither_defs()}</defs><rect width="{width}" height="{height}" fill="{BLACK}"/>'
            + dither_gradient(0, 0, width, height, 4, horizontal=False))
    return svg(width, height, body)


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "header.svg").write_text(header())
    for index, (name, title) in enumerate((("about", "ABOUT"), ("languages", "LANGUAGES"),
                                           ("tools", "TOOLS"), ("activity", "ACTIVITY")), start=1):
        (OUT / f"section_{name}.svg").write_text(section(index, title, 20 + index))
    (OUT / "footer.svg").write_text(footer())


if __name__ == "__main__":
    main()
