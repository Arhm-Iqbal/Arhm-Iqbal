"""Generate the monochrome SVG header used in the GitHub profile README."""

from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets"
BACKGROUND = "#0D1117"
WHITE = "#F0F6FC"
MUTED = "#919BA8"
LINE = "#30363D"
SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "SFMono-Regular, Menlo, Consolas, monospace"


def svg(width, height, title, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-labelledby="title">\n'
        f'<title id="title">{escape(title)}</title>\n{body}\n</svg>\n'
    )


def header():
    # Keep the dither motif in a restrained, decorative panel. All text is visible
    # without animation support; reduced-motion viewers get the static design.
    dots = "\n".join(
        f'<circle cx="{x}" cy="{y}" r="1" opacity="{0.12 + (x - 700) / 1400:.2f}"/>'
        for y in range(24, 240, 12)
        for x in range(700, 988, 12)
    )
    body = f'''<defs>
  <clipPath id="frame"><rect x="1" y="1" width="998" height="246" rx="18"/></clipPath>
</defs>
<style>
  .intro {{ animation: appear 700ms ease-out both; }}
  @keyframes appear {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{ .intro {{ animation: none; }} }}
</style>
<rect x="1" y="1" width="998" height="246" rx="18" fill="{BACKGROUND}" stroke="{LINE}"/>
<g clip-path="url(#frame)">
  <g fill="{MUTED}">{dots}</g>
  <g fill="none" stroke="{LINE}" stroke-width="1.5">
    <circle cx="840" cy="124" r="72"/>
    <circle cx="840" cy="124" r="104"/>
    <path d="M768 124H912M840 52V196M789 73L891 175M789 175L891 73"/>
  </g>
  <circle cx="840" cy="124" r="42" fill="{BACKGROUND}" stroke="{MUTED}"/>
  <path d="M826 113L815 124L826 135M854 113L865 124L854 135M844 108L836 140"
        fill="none" stroke="{WHITE}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <g fill="{WHITE}">
    <circle cx="840" cy="52" r="4"/>
    <circle cx="891" cy="175" r="4"/>
    <circle cx="768" cy="124" r="4"/>
  </g>
</g>
<g class="intro">
  <text x="48" y="51" font-family="{MONO}" font-size="13" letter-spacing="2.5" fill="{MUTED}">NEUROSCIENCE / CODE</text>
  <text x="44" y="133" font-family="{SANS}" font-weight="700" font-size="76" letter-spacing="-2" fill="{WHITE}">ARHM IQBAL</text>
  <text x="48" y="176" font-family="{SANS}" font-size="19" fill="{MUTED}">Honours Neuroscience · University of Alberta</text>
  <path d="M48 209H74" stroke="{WHITE}" stroke-width="2"/>
  <text x="86" y="213" font-family="{MONO}" font-size="12" letter-spacing="1.7" fill="{MUTED}">EDMONTON, AB</text>
</g>'''
    return svg(1000, 248, "Arhm Iqbal — neuroscience and code", body)


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "header.svg").write_text(header(), encoding="utf-8")


if __name__ == "__main__":
    main()
