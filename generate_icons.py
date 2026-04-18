import struct, zlib, os, math

def write_png(path, size, draw_fn):
    img = [[(0, 0, 0, 0)] * size for _ in range(size)]
    draw_fn(img, size)
    rows = b''.join(b'\x00' + b''.join(struct.pack('BBBB', r, g, b, a) for r, g, b, a in row) for row in img)
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(rows))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)

def lerp(a, b, t): return a + (b - a) * t
def clamp(v, lo=0, hi=255): return max(lo, min(hi, int(v)))

def blend(base, r, g, b, a):
    br, bg, bb, ba = base
    t = a / 255
    return (
        clamp(lerp(br, r, t)),
        clamp(lerp(bg, g, t)),
        clamp(lerp(bb, b, t)),
        clamp(ba + a * (1 - ba / 255)),
    )

def circle_aa(img, cx, cy, radius, r, g, b, a=255):
    for y in range(max(0, int(cy - radius - 1)), min(len(img), int(cy + radius + 2))):
        for x in range(max(0, int(cx - radius - 1)), min(len(img[0]), int(cx + radius + 2))):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            alpha = clamp((radius - dist + 0.5) * 255)
            if alpha > 0:
                img[y][x] = blend(img[y][x], r, g, b, int(alpha * a / 255))

def rect_rounded(img, x1, y1, x2, y2, rad, r, g, b, a=255):
    for y in range(max(0, y1), min(len(img), y2)):
        for x in range(max(0, x1), min(len(img[0]), x2)):
            dx = max(x1 + rad - x, x - (x2 - rad), 0)
            dy = max(y1 + rad - y, y - (y2 - rad), 0)
            dist = math.sqrt(dx * dx + dy * dy)
            alpha = clamp((rad - dist + 0.5) * 255)
            if alpha > 0:
                img[y][x] = blend(img[y][x], r, g, b, int(alpha * a / 255))

def line_aa(img, x0, y0, x1, y1, w, r, g, b, a=255):
    dx, dy = x1 - x0, y1 - y0
    length = math.sqrt(dx * dx + dy * dy) or 1
    nx, ny = -dy / length, dx / length
    for y in range(len(img)):
        for x in range(len(img[0])):
            # distance to segment
            t = max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / (length * length)))
            px, py = x0 + t * dx, y0 + t * dy
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            alpha = clamp((w / 2 - dist + 0.5) * 255)
            if alpha > 0:
                img[y][x] = blend(img[y][x], r, g, b, int(alpha * a / 255))

def draw_icon(img, size):
    s = size / 128
    pad = 8 * s
    bg_r = 12 * s  # background rounded rect radius

    # Dark background with rounded corners
    rect_rounded(img, 0, 0, size, size, int(bg_r),
                 20, 20, 40, 255)

    # Subtle gradient overlay (top lighter)
    for y in range(size):
        alpha = int(30 * (1 - y / size))
        for x in range(size):
            img[y][x] = blend(img[y][x], 100, 120, 180, alpha)

    # Mouse body
    cx = size * 0.5
    body_top = size * 0.15
    body_bot = size * 0.82
    body_w = size * 0.38
    body_h = body_bot - body_top
    body_rx = int(body_w * 0.52)

    # Main mouse shape (teal)
    rect_rounded(img,
                 int(cx - body_w * 0.5), int(body_top),
                 int(cx + body_w * 0.5), int(body_bot),
                 body_rx,
                 0, 212, 170, 230)

    # Divider line between left/right click
    line_aa(img,
            cx, body_top + 2 * s,
            cx, body_top + body_h * 0.38,
            1.2 * s,
            20, 20, 40, 180)

    # Horizontal split line
    line_aa(img,
            cx - body_w * 0.5 + 2 * s, body_top + body_h * 0.38,
            cx + body_w * 0.5 - 2 * s, body_top + body_h * 0.38,
            1.2 * s,
            20, 20, 40, 160)

    # Scroll wheel (small rect)
    ww = body_w * 0.18
    wh = body_h * 0.16
    wx = cx - ww * 0.5
    wy = body_top + body_h * 0.14
    rect_rounded(img, int(wx), int(wy), int(wx + ww), int(wy + wh), int(ww * 0.45),
                 20, 20, 40, 200)

    # Haptic glow dot (side button area)
    circle_aa(img, int(cx - body_w * 0.52), int(body_top + body_h * 0.55),
              3.5 * s, 0, 255, 200, 220)
    circle_aa(img, int(cx - body_w * 0.52), int(body_top + body_h * 0.55),
              6 * s, 0, 212, 170, 60)

os.makedirs('icons', exist_ok=True)
for size in [16, 32, 48, 128]:
    write_png(f'icons/icon{size}.png', size, draw_icon)
    print(f'icons/icon{size}.png')

print('Done.')
