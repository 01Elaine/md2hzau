"""Compose the README demo image: Typora screenshot → HZAU PDF cover side-by-side."""
from PIL import Image, ImageDraw, ImageFont
import pathlib

FIGURES = pathlib.Path(__file__).parent / "figures"
OUT     = pathlib.Path(__file__).parent / "docs" / "demo.png"

TARGET_H = 820
PADDING  = 48
GAP      = 160
LABEL_H  = 48
BG       = (248, 249, 250)
BLUE     = (52, 120, 246)
BLUE_PILL= (225, 235, 255)
LABEL_FG = (80, 80, 90)
SHADOW_C = (210, 213, 218)
CORNER   = 6


def load_scaled(path, h):
    img = Image.open(path).convert("RGBA")
    w0, h0 = img.size
    return img.resize((round(w0 * h / h0), h), Image.LANCZOS)


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


def draw_shadow(draw, box, shadow=SHADOW_C):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0+4, y0+6, x1+4, y1+6], radius=CORNER, fill=shadow)


def paste_rounded(canvas, panel, xy, radius=CORNER):
    x, y = xy
    w, h = panel.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w-1, h-1], radius=radius, fill=255)
    canvas.paste(panel.convert("RGBA"), (x, y), mask)


def draw_arrow(draw, cx, cy):
    arm, arm_h = 70, 12
    hw, hh = 28, 36
    x0 = cx - arm//2 - hw//2
    x1 = cx + arm//2 - hw//2
    draw.rounded_rectangle([x0, cy-arm_h//2, x1, cy+arm_h//2], radius=arm_h//2, fill=BLUE)
    draw.polygon([x1, cy-hh//2, x1+hw, cy, x1, cy+hh//2], fill=BLUE)


def main():
    left  = load_scaled(FIGURES / "example_md.png",      TARGET_H)
    right = load_scaled(FIGURES / "example_hzau_01.png", TARGET_H)

    lw, rw = left.width, right.width
    canvas_w = PADDING + lw + GAP + rw + PADDING
    canvas_h = PADDING + LABEL_H + TARGET_H + PADDING

    canvas = Image.new("RGB", (canvas_w, canvas_h), BG)
    draw   = ImageDraw.Draw(canvas)

    font_label = find_font(22, bold=True)
    font_cmd   = find_font(18)
    font_tip   = find_font(15)

    lx = PADDING
    rx = PADDING + lw + GAP
    iy = PADDING + LABEL_H

    # shadows
    draw_shadow(draw, [lx, iy, lx+lw, iy+TARGET_H])
    draw_shadow(draw, [rx, iy, rx+rw, iy+TARGET_H])

    # white panel bg
    draw.rounded_rectangle([lx, iy, lx+lw, iy+TARGET_H], radius=CORNER, fill=(255,255,255))
    draw.rounded_rectangle([rx, iy, rx+rw, iy+TARGET_H], radius=CORNER, fill=(255,255,255))

    # screenshots
    paste_rounded(canvas, left,  (lx, iy))
    paste_rounded(canvas, right, (rx, iy))

    # borders
    draw.rounded_rectangle([lx, iy, lx+lw, iy+TARGET_H], radius=CORNER, outline=(200,202,206), width=1)
    draw.rounded_rectangle([rx, iy, rx+rw, iy+TARGET_H], radius=CORNER, outline=(200,202,206), width=1)

    # labels above panels
    def label(text, x, w):
        bb = draw.textbbox((0,0), text, font=font_label)
        tw = bb[2]-bb[0]
        draw.text((x+(w-tw)//2, PADDING+(LABEL_H-22)//2), text, font=font_label, fill=LABEL_FG)

    label("Markdown 源文件", lx, lw)
    label("华农毕设 PDF",    rx, rw)

    # arrow
    arrow_cx = PADDING + lw + GAP // 2
    arrow_cy = iy + TARGET_H // 2
    draw_arrow(draw, arrow_cx, arrow_cy)

    # "一键转换" tip
    tip = "一键转换"
    bb = draw.textbbox((0,0), tip, font=font_tip)
    draw.text((arrow_cx-(bb[2]-bb[0])//2, arrow_cy-48), tip, font=font_tip, fill=(150,160,175))

    # badge
    cmd = "python md2hzau.py"
    bb  = draw.textbbox((0,0), cmd, font=font_cmd)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    px = 10
    bx0, bx1 = arrow_cx-tw//2-px, arrow_cx+tw//2+px
    by0 = arrow_cy + 32
    draw.rounded_rectangle([bx0, by0, bx1, by0+th+px], radius=6, fill=BLUE_PILL, outline=BLUE, width=1)
    draw.text((bx0+px, by0+px//2), cmd, font=font_cmd, fill=BLUE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, "PNG", optimize=True)
    print(f"Saved → {OUT}  ({canvas_w}×{canvas_h}px, {OUT.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
