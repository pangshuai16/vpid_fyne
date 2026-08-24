#!/usr/bin/env python3
# 生成程序图标：USB 图案（超采样抗锯齿，杜绝模糊）
#   - resources/app.ico  : Windows 多尺寸 BMP 形式 ICO（16/24/32/48/64，兼容 XP）
#   - resources/app_icon.h: Linux 内嵌 128x128 RGBA PNG 字节数组
import struct, zlib, os

USB_BLUE = (0x00, 0x7A, 0xFF)

# USB 三叉符号的若干多边形（归一化坐标 0..1），构成近似 USB 标志
def usb_polys():
    return [
        # 顶部横杠
        [(0.16, 0.10), (0.84, 0.10), (0.84, 0.22), (0.70, 0.22),
         (0.70, 0.30), (0.30, 0.30), (0.30, 0.22), (0.16, 0.22)],
        # 中央竖杆（收窄进入）
        [(0.44, 0.30), (0.56, 0.30), (0.56, 0.46), (0.44, 0.46)],
        # 左腿（斜向下分叉，加粗）
        [(0.44, 0.42), (0.52, 0.44), (0.40, 0.82), (0.26, 0.82)],
        # 右腿（斜向下分叉）
        [(0.48, 0.44), (0.56, 0.42), (0.74, 0.82), (0.60, 0.82)],
    ]

def in_poly(x, y, poly):
    n = len(poly); inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def sample_alpha(dx, dy, polys, size, sx, sy):
    # (dx,dy) 为目标像素在尺寸 size 内的坐标
    scale = 8  # 超采样倍率
    hit = 0; total = scale * scale
    x0 = dx / size; y0 = dy / size
    for yy in range(scale):
        for xx in range(scale):
            px = x0 + (xx + 0.5) / size / scale
            py = y0 + (yy + 0.5) / size / scale
            for p in polys:
                if in_poly(px, py, p):
                    hit += 1; break
    a = hit * 255 // total
    return a

def render_rows(size):
    """返回 bottom-up 的 32bpp [BGRA] 行（实际只含蓝与透明）。"""
    polys = usb_polys()
    rows = []
    for dy in range(size - 1, -1, -1):   # ICO XOR 自底向上
        row = bytearray()
        for dx in range(size):
            a = sample_alpha(dx, dy, polys, size, sx=1, sy=1)
            row += bytes((USB_BLUE[2], USB_BLUE[1], USB_BLUE[0], a))  # BGRA
        rows.append(bytes(row))
    return rows

def ico_and_mask(size):
    mask_row_bytes = ((size + 31) // 32) * 4
    mask = []
    for _ in range(size):
        mask.append(bytes(mask_row_bytes))  # 全部 0 -> 不透明
    return mask

def build_ico(sizes):
    count = len(sizes)
    entries = []
    idata = b""
    for s in sizes:
        rows = render_rows(s)
        xor = b"".join(rows)
        mask = b"".join(ico_and_mask(s))
        bi = struct.pack('<IiiHHIIiiII', 40, s, s * 2, 1, 32, 0, len(xor) + len(mask), 0, 0, 0, 0)
        off_in_file = 6 + 16 * count + len(idata)
        entries.append(struct.pack('<BBBBHHII', s, s, 0, 0, 1, 32, len(xor) + len(mask), off_in_file))
        idata += bi + xor + mask
    header = struct.pack('<HHH', 0, 1, count)
    return header + b"".join(entries) + idata

def build_png(width, height, get_pixel):
    """构造 8bpp RGBA PNG，get_pixel(x,y) -> (r,g,b,a)。"""
    raw = b""
    stride = width * 4
    for y in range(height):
        raw += b"\x00" + b"".join(bytes(get_pixel(x, y)) for x in range(width))
    def chunk(typ, data):
        c = typ + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(raw, 9))
            + chunk(b'IEND', b''))

def render_png_pixel(size):
    polys = usb_polys()
    def p(x, y):
        a = sample_alpha(x, y, polys, size, 1, 1)
        return (USB_BLUE[0], USB_BLUE[1], USB_BLUE[2], a)
    return p

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sizes = [16, 32, 48]   # 精简体积，48px 兼顾清晰
    with open(os.path.join(here, 'app.ico'), 'wb') as f:
        f.write(build_ico(sizes))
    print('app.ico', os.path.getsize(os.path.join(here, 'app.ico')), 'bytes')

    # PNG 128x128 -> .h
    png = build_png(128, 128, render_png_pixel(128))
    lines = []
    for i in range(0, len(png), 24):
        lines.append('  ' + ','.join('0x%02x' % b for b in png[i:i + 24]) + ',')
    body = '\n'.join(lines).rstrip(',') + '\n'
    hdr = ('#pragma once\n'
           '// 自动生成：内嵌 128x128 RGBA PNG（USB 图案）\n'
           'namespace vpid {\n'
           'static const unsigned char kAppIconPng[] = {\n'
           + body +
           '};\n'
           'static const unsigned int kAppIconPngLen = sizeof(kAppIconPng);\n'
           '}\n')
    with open(os.path.join(here, 'app_icon.h'), 'w') as f:
        f.write(hdr)
    print('app_icon.h bytes:', len(png))

    with open(os.path.join(here, 'app.rc'), 'w') as f:
        f.write('1 ICON "app.ico"\n')
    print('app.rc written')

if __name__ == '__main__':
    main()