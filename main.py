#!/usr/bin/env python3
"""The World in One Page - 17 November 2026.

Draws a one-page newspaper front page summing up Tuesday 17 November
2026 world news, as a 1024x1024 PNG, using only the Python standard
library. No network, no randomness, no clock: two runs write identical
bytes.

Everything here is drawn from scratch: a bitmap font, a small raster
canvas (rectangles, circles, lines, triangles) and a minimal PNG
encoder (IHDR / IDAT with zlib / IEND, CRC32 checksums).
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------- font ----
# A 5x7 pixel font, drawn by hand. Each glyph is 7 rows of 5 bits.
# Only the characters this page needs are defined.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}

# -------------------------------------------------------------- canvas ----
class Canvas:
    """A plain RGB pixel buffer with tiny drawing primitives."""

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.buf = bytearray(background * (width * height))

    def _set(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.buf[i:i + 3] = color

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                self.buf[base:base + 3] = color
                base += 3

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - dx, cy + dy, dx * 2 + 1, 1, color)

    def disc_outline(self, cx, cy, r, color, thick=2):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            for t in range(thick):
                self._set(cx - dx + t, cy + dy, color)
                self._set(cx + dx - t, cy + dy, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line, with a square brush of side `thick`."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.rect(x0 - half, y0 - half, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def triangle(self, ax, ay, bx, by, cx, cy, color):
        """Filled triangle, scanline by scanline."""
        ys = sorted(((ay, ax), (by, bx), (cy, cx)))
        (y0, x0), (y1, x1), (y2, x2) = ys
        if y0 == y2:
            return
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = x0 + (x1 - x0) * (y - y0) / max(1, y1 - y0)
                xb = x0 + (x2 - x0) * (y - y0) / max(1, y2 - y0)
            else:
                xa = x1 + (x2 - x1) * (y - y1) / max(1, y2 - y1)
                xb = x0 + (x2 - x0) * (y - y0) / max(1, y2 - y0)
            lo, hi = int(min(xa, xb)), int(max(xa, xb))
            self.rect(lo, y, hi - lo + 1, 1, color)

    # ------------------------------------------------------------ text ----
    def glyph(self, ch, x, y, scale, color):
        rows = FONT.get(ch)
        if rows is None:
            return
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    self.rect(x + c * scale, y + r * scale, scale, scale, color)

    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def text(self, text, x, y, scale, color):
        text = text.upper()
        cx = x
        for ch in text:
            self.glyph(ch, cx, y, scale, color)
            cx += 6 * scale
        return cx

    def text_centered(self, text, cx, y, scale, color):
        self.text(text, cx - self.text_width(text, scale) // 2, y, scale, color)

    def wrap(self, text, max_width, scale):
        """Greedy word wrap; returns a list of lines that fit max_width."""
        words = text.split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if self.text_width(trial, scale) <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def paragraph(self, text, x, y, max_width, scale, color, line_gap=4):
        lines = self.wrap(text, max_width, scale)
        for i, line in enumerate(lines):
            self.text(line, x, y + i * (7 * scale + line_gap), scale, color)
        return y + len(lines) * (7 * scale + line_gap)

# -------------------------------------------------------------- colors ----
PAPER = bytes((247, 243, 232))
INK = bytes((17, 17, 17))
RED = bytes((178, 34, 34))
BLUE = bytes((30, 80, 140))
SKY = bytes((140, 190, 220))
SEA = bytes((24, 90, 130))
SAND = bytes((222, 196, 140))
GREEN = bytes((46, 120, 70))
GREY = bytes((120, 120, 115))
LIGHT = bytes((232, 226, 210))
ORANGE = bytes((230, 120, 30))
GOLD = bytes((214, 164, 32))
DARK = bytes((40, 44, 52))
WHITE = bytes((255, 255, 255))
TEAL = bytes((20, 110, 110))

# ----------------------------------------------------------------- png ----
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    row_len = WIDTH * 3
    for y in range(HEIGHT):
        raw.append(0)  # filter: none
        start = y * row_len
        raw += canvas.buf[start:start + row_len]
    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# --------------------------------------------------------- illustrations ----
def draw_gulf(c, x, y, w, h):
    """Strait of Hormuz: sea, a tanker, fire and a missile streak."""
    c.rect(x, y, w, h, SKY)
    c.rect(x, y + h - 46, w, 46, SEA)
    # tanker hull and deck
    c.rect(x + 40, y + h - 78, w - 110, 34, DARK)
    c.rect(x + 60, y + h - 96, 46, 18, DARK)
    c.rect(x + 210, y + h - 92, 14, 14, RED)
    # fire plume from the tanker
    c.triangle(x + 300, y + h - 78, x + 330, y + 8, x + 356, y + h - 78, ORANGE)
    c.triangle(x + 312, y + h - 78, x + 328, y + 34, x + 344, y + h - 78, GOLD)
    # missile streak across the sky
    c.line(x + 20, y + 22, x + 150, y + 52, INK, 4)
    c.circle(x + 156, y + 54, 5, RED)
    # waves
    for wx in range(x + 8, x + w - 8, 44):
        c.line(wx, y + h - 22, wx + 22, y + h - 14, WHITE, 3)


def draw_bridge(c, x, y, w, h):
    """Kerch Bridge: an arched road bridge over water, span broken."""
    c.rect(x, y, w, h, SKY)
    c.circle(x + w - 60, y + 22, 18, GOLD)
    c.rect(x, y + h - 30, w, 30, SEA)
    # bridge deck in two pieces with a gap in the middle
    c.rect(x + 8, y + 34, 168, 10, DARK)
    c.rect(x + w - 176, y + 34, 168, 10, DARK)
    # arch ribs
    c.line(x + 20, y + 44, x + 90, y + h - 8, DARK, 5)
    c.line(x + w - 20, y + 44, x + w - 90, y + h - 8, DARK, 5)
    # broken span falling into the water
    c.line(x + 196, y + 40, x + 232, y + 74, DARK, 7)
    c.line(x + 232, y + 74, x + 268, y + 64, DARK, 7)
    # smoke over the gap
    c.circle(x + 228, y + 30, 12, GREY)
    c.circle(x + 248, y + 20, 15, GREY)
    c.circle(x + 214, y + 18, 10, GREY)
    # support pillars
    c.rect(x + 60, y + 44, 12, h - 74, DARK)
    c.rect(x + w - 72, y + 44, 12, h - 74, DARK)


def draw_manila(c, x, y, w, h):
    """Manila skyline at dusk, flags flying over the summit."""
    c.rect(x, y, w, h, bytes((250, 200, 120)))
    c.circle(x + 60, y + 34, 22, GOLD)
    # skyline blocks
    c.rect(x + 20, y + 66, 70, h - 66, DARK)
    c.rect(x + 110, y + 44, 56, h - 44, TEAL)
    c.rect(x + 186, y + 80, 84, h - 80, DARK)
    c.rect(x + 290, y + 56, 60, h - 56, BLUE)
    c.rect(x + 368, y + 86, 76, h - 86, TEAL)
    # lit windows
    for wx, wy in ((36, 76), (58, 88), (124, 58), (142, 78), (206, 84),
                   (232, 90), (306, 68), (330, 86), (384, 90), (412, 92)):
        c.rect(x + wx, y + wy, 10, 7, GOLD)
    # three flags on poles
    for fx, col in ((x + 96, RED), (x + 220, BLUE), (x + 356, GREEN)):
        c.vline(fx, y + 8, 44, INK, 3)
        c.rect(fx + 3, y + 8, 34, 20, col)
        c.rect(fx + 3, y + 8, 34, 7, WHITE)


def draw_measles(c, x, y, w, h):
    """Red virus dots with spikes, and a white shield with a cross."""
    c.rect(x, y, w, h, LIGHT)
    # virus dots with spike lines
    for vx, vy, r in ((70, 40, 20), (170, 30, 14), (290, 38, 18),
                      (330, 64, 12), (120, 70, 11), (250, 68, 12)):
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, -1), (-1, 1), (1, 1)):
            c.line(x + vx, y + vy, x + vx + dx * (r + 9), y + vy + dy * (r + 9),
                   RED, 3)
        c.circle(x + vx, y + vy, r, RED)
        c.circle(x + vx - 5, y + vy - 5, 5, WHITE)
    # shield with a cross
    sx, sy = x + w - 104, y + 8
    c.triangle(sx, sy + 30, sx + 38, sy, sx + 76, sy + 30, WHITE)
    c.rect(sx, sy + 28, 76, 28, WHITE)
    c.triangle(sx, sy + 56, sx + 38, sy + 80, sx + 76, sy + 56, WHITE)
    c.rect(sx + 30, sy + 16, 14, 44, RED)
    c.rect(sx + 15, sy + 30, 44, 14, RED)


def draw_mongolia(c, x, y, w, h):
    """Steppe, mountains and a ger (round tent) under a big sun."""
    c.rect(x, y, w, h, SKY)
    c.circle(x + w - 70, y + 30, 24, GOLD)
    # mountains
    c.triangle(x + 10, y + h - 40, x + 130, y + 18, x + 250, y + h - 40, TEAL)
    c.triangle(x + 180, y + h - 40, x + 300, y + 30, x + 420, y + h - 40, BLUE)
    # steppe
    c.rect(x, y + h - 40, w, 40, GREEN)
    # ger: round wall, cone roof, door
    gx, gy = x + 150, y + h - 78
    c.rect(gx, gy + 34, 130, 34, SAND)
    c.triangle(gx - 8, gy + 36, gx + 65, gy, gx + 138, gy + 36, RED)
    c.rect(gx + 56, gy + 40, 18, 28, DARK)
    c.vline(gx + 65, gy - 6, 12, INK, 3)


def draw_jets(c, x, y, w, h):
    """Two fighter jets under a rising sun, over the sea."""
    c.rect(x, y, w, h, SKY)
    c.circle(x + w // 2, y + 34, 30, RED)
    c.rect(x, y + h - 26, w, 26, SEA)
    # jet 1 (upper left) and jet 2 (lower right): fuselage + swept wings
    for jx, jy, s in ((x + 80, y + 26, 1), (x + 260, y + 56, -1)):
        c.line(jx, jy, jx + 110 * s, jy + 10, DARK, 8)
        c.triangle(jx + 30 * s, jy, jx + 70 * s, jy - 22, jx + 78 * s, jy + 4,
                   DARK)
        c.triangle(jx + 30 * s, jy + 8, jx + 70 * s, jy + 28, jx + 78 * s,
                   jy + 10, DARK)
        c.line(jx + 110 * s, jy + 10, jx + 128 * s, jy + 12, ORANGE, 4)
    # speed lines
    for sx, sy in ((x + 30, y + 48), (x + 60, y + 66), (x + 220, y + 80)):
        c.line(sx, sy, sx + 44, sy + 6, WHITE, 3)

# -------------------------------------------------------------- stories ----
# Six verified stories from Tuesday 17 November 2026, across regions and
# beats. Sources: Reuters / AP / Al Jazeera / PAHO via Profile News,
# Level Headlines, Peek-a-Daily, Asas Press and the ABC World News
# Tonight episode of the day.
STORIES = [
    ("MIDDLE EAST", "US STRIKES IRAN",
     "US warplanes hit a missile site on Qeshm Island after attacks on "
     "ships in the Strait of Hormuz. Tankers burned; a dirty-bomb scare "
     "was denied by Tehran.", draw_gulf),
    ("EUROPE", "KERCH BRIDGE HIT",
     "Ukraine struck the bridge linking Russia to Crimea. A road span "
     "collapsed into the water, and Russia vowed to rebuild it.",
     draw_bridge),
    ("ASIA", "TRUMP LANDS IN MANILA",
     "Trump arrived in the Philippines for the ASEAN summit, opening a "
     "three-day Asia trip that ends in talks with Xi and Putin.",
     draw_manila),
    ("HEALTH", "US LOSES MEASLES STATUS",
     "The US lost its measles elimination status after a year of "
     "nonstop spread, the first time since 2000, health officials said.",
     draw_measles),
    ("ASIA", "MONGOLIA PRESIDENT QUITS",
     "President Khurelsukh resigned after accusations of embezzlement "
     "from a railway project. Parliament must accept it to take effect.",
     draw_mongolia),
    ("ASIA", "JAPAN SCRAMBLES JETS",
     "Japan sent fighter jets up and protested after two suspected "
     "Russian aircraft entered its airspace near Okinoshima.",
     draw_jets),
]


# -------------------------------------------------------------- layout ----
def draw_masthead(c):
    c.hline(0, 10, WIDTH, INK, 4)
    c.text_centered("THE WORLD IN ONE PAGE", WIDTH // 2, 26, 7, INK)
    c.text_centered("SIX STORIES THAT MADE TUESDAY", WIDTH // 2, 84, 3, RED)
    c.hline(0, 118, WIDTH, INK, 3)
    c.text_centered("TUESDAY 17 NOVEMBER 2026", WIDTH // 2, 130, 5, INK)
    c.hline(0, 172, WIDTH, INK, 4)
    c.hline(0, 178, WIDTH, INK, 2)


def draw_story(c, story, x, y, w, h):
    kicker, headline, summary, art = story
    c.rect(x, y, w, h, WHITE)
    c.rect(x, y, w, h, INK)  # placeholder, overwritten below
    c.rect(x + 2, y + 2, w - 4, h - 4, WHITE)
    # picture
    art(c, x + 14, y + 12, w - 28, 96)
    # kicker
    c.text(kicker, x + 14, y + 118, 2, RED)
    # headline, up to two lines
    lines = c.wrap(headline, w - 28, 3)
    hy = y + 140
    for line in lines[:2]:
        c.text(line, x + 14, hy, 3, INK)
        hy += 7 * 3 + 3
    # summary
    c.paragraph(summary, x + 14, hy + 6, w - 28, 2, INK, line_gap=3)


def draw_page():
    c = Canvas(WIDTH, HEIGHT, PAPER)
    draw_masthead(c)
    # 2 columns x 3 rows of stories
    gx, gy = 16, 190
    cw, ch = 488, 240
    gap = 12
    for i, story in enumerate(STORIES):
        col = i % 2
        row = i // 2
        draw_story(c, story, gx + col * (cw + gap), gy + row * (ch + gap),
                   cw, ch)
    # footer
    fy = gy + 3 * ch + 2 * gap + 6
    c.hline(16, fy, WIDTH - 32, INK, 2)
    c.text_centered("THE WORLD IN ONE PAGE  -  TUESDAY 17 NOVEMBER 2026  -  "
                    "ONE DAY, ONE PAGE", WIDTH // 2, fy + 10, 2, INK)
    return c


# ----------------------------------------------------------------- main ----
def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    canvas = draw_page()
    write_png(canvas, path)
    print("wrote %s (%d bytes)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main()
