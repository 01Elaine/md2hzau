"""Compose the README demo image."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pathlib

FIGURES = pathlib.Path(__file__).parent / "figures"
OUT     = pathlib.Path(__file__).parent / "docs" / "demo.png"

# ── palette ────────────────────────────────────────────────────────────────
BG_TOP    = (235, 239, 246)
BG_BOT    = (220, 226, 237)
BLUE      = (41, 98, 220)
BLUE_PILL = (219, 231, 255)
LABEL_FG  = (90, 100, 118)
WHITE     = (255, 255, 255)
BORDER    = (200, 205, 215)

# ── layout ─────────────────────────────────────────────────────────────────
TARGET_H  = 760   # final panel height
PADDING   = 56    # outer margin
GAP       = 170   # arrow zone width
FOOT_H    = 42    # label area below panels
CORNER    = 8


def load_crop_scale(path, target_h, crop_bottom_frac=1.0):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    crop_h = int(h * crop_bottom_frac)
    img = img.crop((0, 0, w, crop_h))
    scale = target_h / crop_h
    return img.resize((round(w * scale), target_h), Image.LANCZOS)


def find_font(size, bold=False):
    for p in (
        [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf"]
        if bold else
        [r"C:\Windows\Fonts\msyh.ttc",   r"C:\Windows\Fonts\arial.ttf"]
    ):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def soft_shadow(canvas, box, radius=CORNER, blur=18, strength=55):
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        [x0+5, y0+7, x1+5, y1+7], radius=radius, fill=(0, 0, 0, strength))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def paste_rounded(canvas, img, xy, radius=CORNER):
    x, y = xy
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w-1, h-1], radius=radius, fill=255)
    canvas.paste(img.convert("RGBA"), (x, y), mask)


def draw_arrow_badge(draw, cx, cy, font):
    # shaft
    arm = 52
    draw.rounded_rectangle(
        [cx-arm, cy-7, cx+arm, cy+7], radius=7, fill=BLUE)
    # head
    draw.polygon([cx+arm, cy-19, cx+arm+22, cy, cx+arm, cy+19], fill=BLUE)

    # badge below
    cmd = "python md2hzau.py"
    bb  = draw.textbbox((0, 0), cmd, font=font)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    px, py2 = 11, 6
    bx0 = cx - tw//2 - px
    bx1 = cx + tw//2 + px
    by0 = cy + 30
    by1 = by0 + th + py2*2
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=6,
                            fill=BLUE_PILL, outline=BLUE, width=2)
    draw.text((bx0+px, by0+py2), cmd, font=font, fill=BLUE)


def main():
    # Crop Typora screenshot to top 55% so height ratio matches A4 cover better
    left  = load_crop_scale(FIGURES / "example_md.png",      TARGET_H, 0.55)
    right = load_crop_scale(FIGURES / "example_hzau_01.png", TARGET_H, 1.00)

    lw, rw = left.width, right.width
    canvas_w = PADDING + lw + GAP + rw + PADDING
    canvas_h = PADDING + TARGET_H + FOOT_H + PADDING

    # ── gradient background ────────────────────────────────────────────────
    base = Image.new("RGBA", (canvas_w, canvas_h))
    for y in range(canvas_h):
        t = y / canvas_h
        r = int(BG_TOP[0] + (BG_BOT[0]-BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1]-BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2]-BG_TOP[2]) * t)
        ImageDraw.Draw(base).line([(0, y), (canvas_w, y)], fill=(r, g, b, 255))

    lx = PADDING
    rx = PADDING + lw + GAP
    py = PADDING

    # ── shadows ────────────────────────────────────────────────────────────
    soft_shadow(base, [lx, py, lx+lw, py+TARGET_H])
    soft_shadow(base, [rx, py, rx+rw, py+TARGET_H])

    # ── white panel backgrounds ────────────────────────────────────────────
    wl = Image.new("RGBA", base.size, (0,0,0,0))
    ImageDraw.Draw(wl).rounded_rectangle(
        [lx, py, lx+lw, py+TARGET_H], radius=CORNER, fill=(255,255,255,255))
    ImageDraw.Draw(wl).rounded_rectangle(
        [rx, py, rx+rw, py+TARGET_H], radius=CORNER, fill=(255,255,255,255))
    base.alpha_composite(wl)

    # ── paste screenshots ──────────────────────────────────────────────────
    paste_rounded(base, left,  (lx, py))
    paste_rounded(base, right, (rx, py))

    # ── thin border ────────────────────────────────────────────────────────
    bl = Image.new("RGBA", base.size, (0,0,0,0))
    ImageDraw.Draw(bl).rounded_rectangle(
        [lx, py, lx+lw, py+TARGET_H], radius=CORNER,
        outline=(*BORDER, 180), width=1)
    ImageDraw.Draw(bl).rounded_rectangle(
        [rx, py, rx+rw, py+TARGET_H], radius=CORNER,
        outline=(*BORDER, 180), width=1)
    base.alpha_composite(bl)

    # ── flatten to RGB for drawing text / arrow ────────────────────────────
    rgb = Image.new("RGB", base.size, WHITE)
    rgb.paste(base.convert("RGB"))

    draw = ImageDraw.Draw(rgb)
    font_label = find_font(19, bold=False)
    font_cmd   = find_font(16, bold=False)

    arrow_cx = PADDING + lw + GAP // 2
    arrow_cy = py + TARGET_H // 2

    draw_arrow_badge(draw, arrow_cx, arrow_cy, font_cmd)

    # ── labels below panels ────────────────────────────────────────────────
    def foot_label(text, x, w):
        bb = draw.textbbox((0,0), text, font=font_label)
        tw = bb[2]-bb[0]
        draw.text((x + (w-tw)//2, py + TARGET_H + 12),
                  text, font=font_label, fill=LABEL_FG)

    foot_label("Markdown 源文件", lx, lw)
    foot_label("华农毕设 PDF", rx, rw)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(OUT, "PNG", optimize=True)
    print(f"Saved → {OUT}  ({canvas_w}×{canvas_h}px, {OUT.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
