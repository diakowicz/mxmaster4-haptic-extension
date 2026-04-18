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

    # Dark background
    rect_rounded(img, 0, 0, size, size, int(14 * s), 18, 18, 36, 255)

    # Mouse body — centered, clean proportions
    cx   = size * 0.5
    bw   = size * 0.42        # body width
    bt   = size * 0.13        # body top
    bb   = size * 0.87        # body bottom
    bh   = bb - bt
    brad = int(bw * 0.5)      # fully rounded top

    rect_rounded(img,
                 int(cx - bw * 0.5), int(bt),
                 int(cx + bw * 0.5), int(bb),
                 brad,
                 0, 212, 170, 255)

    # Horizontal split (top buttons vs palm area)
    split_y = bt + bh * 0.36
    line_aa(img,
            cx - bw * 0.5 + 1.5 * s, split_y,
            cx + bw * 0.5 - 1.5 * s, split_y,
            1.5 * s, 18, 18, 36, 200)

    # Vertical divider (left / right button)
    line_aa(img,
            cx, bt + 1.5 * s,
            cx, split_y,
            1.5 * s, 18, 18, 36, 200)

    # Scroll wheel — pill shape, centered, in top half
    ww = bw * 0.16
    wh = bh * 0.18
    wx = cx - ww * 0.5
    wy = bt + bh * 0.10
    rect_rounded(img,
                 int(wx), int(wy),
                 int(wx + ww), int(wy + wh),
                 int(ww * 0.5),
                 18, 18, 36, 220)

os.makedirs('icons', exist_ok=True)
for size in [16, 32, 48, 128]:
    write_png(f'icons/icon{size}.png', size, draw_icon)
    print(f'icons/icon{size}.png')

print('Done.')
