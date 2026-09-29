#!/usr/bin/env python3
#
# End-to-end check of the build and the emulator setup: generates a tiny
# NROM test ROM, runs it in Azahar with both the .3dsx and the .cia (which
# gets installed first) and checks the colour on screen.
#
# The ROM fills the screen with palette colour $21 (light blue), and
# switches to $16 (red) while NES A is held. VirtuaNES maps 3DS A to NES A
# by default.
#
#   tools/build.sh && tools/azahar/smoketest.py
#
import os
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, '.azahar', 'smoketest')
APPS = ['virtuanes_3ds.3dsx', 'virtuanes_3ds.cia']


def assemble():
    base = 0xC000
    reset = bytearray([
        0x78,                   # sei
        0xD8,                   # cld
        0xA2, 0xFF,             # ldx #$ff
        0x9A,                   # txs
        0xA9, 0x00,             # lda #0
        0x8D, 0x00, 0x20,       # sta $2000
        0x8D, 0x01, 0x20,       # sta $2001
        0x2C, 0x02, 0x20,       # bit $2002   ; wait for two vblanks
        0x10, 0xFB,             # bpl -5
        0x2C, 0x02, 0x20,       # bit $2002
        0x10, 0xFB,             # bpl -5
        0xA9, 0x80,             # lda #$80    ; nmi on
        0x8D, 0x00, 0x20,       # sta $2000
        0xA9, 0x0A,             # lda #$0a    ; background on
        0x8D, 0x01, 0x20,       # sta $2001
        0x4C, 0x00, 0x00,       # jmp *
    ])
    reset[-2:] = struct.pack('<H', base + len(reset) - 3)

    nmi = bytes([
        0x48,                   # pha
        0xA9, 0x01,             # lda #1      ; strobe the controller
        0x8D, 0x16, 0x40,       # sta $4016
        0xA9, 0x00,             # lda #0
        0x8D, 0x16, 0x40,       # sta $4016
        0xA0, 0x21,             # ldy #$21    ; light blue
        0xAD, 0x16, 0x40,       # lda $4016   ; A button
        0x29, 0x01,             # and #1
        0xF0, 0x02,             # beq +2
        0xA0, 0x16,             # ldy #$16    ; red
        0xA9, 0x3F,             # lda #$3f    ; backdrop colour at $3f00
        0x8D, 0x06, 0x20,       # sta $2006
        0xA9, 0x00,             # lda #0
        0x8D, 0x06, 0x20,       # sta $2006
        0x8C, 0x07, 0x20,       # sty $2007
        0xA9, 0x00,             # lda #0      ; reset scroll
        0x8D, 0x05, 0x20,       # sta $2005
        0x8D, 0x05, 0x20,       # sta $2005
        0xA9, 0x80,             # lda #$80
        0x8D, 0x00, 0x20,       # sta $2000
        0x68,                   # pla
        0x40,                   # rti
    ])
    nmi_offset = 0x100

    prg = bytearray(0x4000)
    prg[0:len(reset)] = reset
    prg[nmi_offset:nmi_offset + len(nmi)] = nmi
    prg[0x3FFA:] = struct.pack('<HHH', base + nmi_offset, base, base)
    header = b'NES\x1a' + bytes([1, 1, 0, 0]) + bytes(8)   # NROM, 16K PRG, 8K CHR
    return header + bytes(prg) + bytes(0x2000)


def read_png(path):
    """Decodes an 8-bit RGB PNG (what run.sh writes) into a list of rows
    of bytes."""
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    pos, idat = 8, b''
    while pos < len(data):
        length, kind = struct.unpack('>I4s', data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        if kind == b'IHDR':
            width, height, depth, ctype = struct.unpack('>IIBB', chunk[:10])
            assert depth == 8 and ctype == 2, 'expected 8-bit RGB'
        elif kind == b'IDAT':
            idat += chunk
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * 3
    rows, prev = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        f, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = line[i - 3] if i >= 3 else 0
            b = prev[i]
            c = prev[i - 3] if i >= 3 else 0
            if f == 1:
                line[i] = (line[i] + a) & 0xFF
            elif f == 2:
                line[i] = (line[i] + b) & 0xFF
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
        rows.append(line)
        prev = line
    return rows


def pixel(out, name, x, y):
    rows = read_png(os.path.join(out, name + '.png'))
    return tuple(rows[y][x * 3:x * 3 + 3])


def check(app, rom):
    out = os.path.join(OUT, os.path.splitext(app)[1][1:])
    os.makedirs(out, exist_ok=True)
    # A at the ROM menu loads the only ROM on the SD card. Installing the
    # .cia adds the "Nintendo 3DS" folder, which is listed before it.
    select = ['key:down', 'wait:1'] if app.endswith('.cia') else []
    subprocess.run([
        os.path.join(ROOT, 'tools', 'azahar', 'run.sh'),
        '-a', os.path.join(ROOT, app), '-r', rom, '-o', out, '-t', '180', '--',
        'wait:10', 'shot:menu'] + select + ['key:a', 'wait:8', 'shot:idle',
        'down:a', 'wait:2', 'shot:pressed', 'up:a',
    ], check=True)

    # Middle of the NES picture on the top screen (256x240 centred in 400x240).
    idle, pressed = pixel(out, 'idle', 200, 120), pixel(out, 'pressed', 200, 120)
    print('%s: idle rgb%s (want light blue), pressed rgb%s (want red)' % (app, idle, pressed))
    ok = idle[2] > 150 and idle[0] < 150 and pressed[0] > 150 and pressed[2] < 100
    print('%s: %s - screenshots in %s' % (app, 'PASS' if ok else 'FAIL', out))
    return ok


def main():
    with tempfile.TemporaryDirectory() as tmp:
        rom = os.path.join(tmp, 'smoketest.nes')
        with open(rom, 'wb') as f:
            f.write(assemble())
        results = [check(app, rom) for app in APPS]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
