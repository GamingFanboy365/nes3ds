#!/usr/bin/env python3
#
# Mapper tests: generates a small test ROM per mapper, runs each in Azahar
# and checks the result on screen.
#
# Every 8 KiB PRG bank starts with its bank number, and every 1 KiB CHR
# bank with its bank number. The test code (in the last PRG bank, fixed at
# $E000 on all the boards here) writes the mapper registers, then checks
# what the CPU sees at $8000-$FFFF, what the PPU reads from the pattern
# tables, and how the nametables are mirrored. The screen turns green if
# every check passes and red if one fails; the failing check's number is
# in the log.
#
#   tools/build.sh && tools/azahar/mappertest.py [MAPPER...]
#
import os
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from smoketest import read_png  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, '.azahar', 'mappertest')

PASS_COLOUR = 0x2A  # green
FAIL_COLOUR = 0x16  # red


class Asm:
    """A tiny 6502 assembler: just the instructions the tests use."""

    IMPLIED = {'sei': 0x78, 'cld': 0xD8, 'txs': 0x9A, 'rts': 0x60,
               'rti': 0x40, 'inx': 0xE8, 'dex': 0xCA, 'nop': 0xEA}
    IMMEDIATE = {'lda': 0xA9, 'ldx': 0xA2, 'ldy': 0xA0, 'cmp': 0xC9}
    ABSOLUTE = {'lda': 0xAD, 'sta': 0x8D, 'stx': 0x8E, 'sty': 0x8C,
                'bit': 0x2C, 'jmp': 0x4C, 'jsr': 0x20}
    BRANCH = {'bne': 0xD0, 'beq': 0xF0, 'bpl': 0x10, 'bmi': 0x30}

    def __init__(self, origin):
        self.origin = origin
        self.code = bytearray()
        self.labels = {}
        self.fixups = []  # (offset, label, kind)
        self.checks = 0

    @property
    def pc(self):
        return self.origin + len(self.code)

    def label(self, name):
        self.labels[name] = self.pc

    def op(self, name, arg=None):
        if arg is None:
            self.code.append(self.IMPLIED[name])
        elif isinstance(arg, str) and arg.startswith('#'):
            self.code += bytes([self.IMMEDIATE[name], int(arg[1:]) & 0xFF])
        elif name in self.BRANCH:
            self.code += bytes([self.BRANCH[name], 0])
            self.fixups.append((len(self.code) - 1, arg, 'rel'))
        elif isinstance(arg, str):
            self.code += bytes([self.ABSOLUTE[name], 0, 0])
            self.fixups.append((len(self.code) - 2, arg, 'abs'))
        else:
            self.code += bytes([self.ABSOLUTE[name]]) + struct.pack('<H', arg)

    def assemble(self):
        for offset, name, kind in self.fixups:
            target = self.labels[name]
            if kind == 'abs':
                self.code[offset:offset + 2] = struct.pack('<H', target)
            else:
                delta = target - (self.origin + offset + 1)
                assert -128 <= delta <= 127, name
                self.code[offset] = delta & 0xFF
        return bytes(self.code)

    # Test helpers ------------------------------------------------------

    def write(self, addr, value):
        self.op('lda', '#%d' % value)
        self.op('sta', addr)

    def expect_a(self, value):
        """Fails the test unless A == value."""
        self.checks += 1
        ok = 'ok%d' % self.checks
        self.op('cmp', '#%d' % value)
        self.op('beq', ok)
        self.op('ldx', '#%d' % self.checks)
        self.op('jmp', 'fail')
        self.label(ok)

    def expect(self, addr, value):
        self.op('lda', addr)
        self.expect_a(value)

    def ppu_addr(self, addr):
        self.op('bit', 0x2002)
        self.write(0x2006, addr >> 8)
        self.write(0x2006, addr & 0xFF)

    def ppu_write(self, addr, value):
        self.ppu_addr(addr)
        self.write(0x2007, value)

    def expect_ppu(self, addr, value):
        self.ppu_addr(addr)
        self.op('lda', 0x2007)  # the first read only fills the read buffer
        self.op('lda', 0x2007)
        self.expect_a(value)

    def expect_mirroring(self, kind):
        """kind: 'V', 'H' or '1' (one-screen)."""
        for i, nt in enumerate((0x2000, 0x2400, 0x2800, 0x2C00)):
            self.ppu_write(nt, 0x11 * (i + 1))
        expected = {'V': (0x33, 0x44, 0x33, 0x44),
                    'H': (0x22, 0x22, 0x44, 0x44),
                    '1': (0x44, 0x44, 0x44, 0x44)}[kind]
        for nt, value in zip((0x2000, 0x2400, 0x2800, 0x2C00), expected):
            self.expect_ppu(nt, value)

    def expect_one_screen_pages(self, select_0, select_1):
        """Checks that the two one-screen settings use different
        nametables. select_0/select_1 emit the code that selects them."""
        select_0()
        self.ppu_write(0x2000, 0xA5)
        select_1()
        self.ppu_write(0x2000, 0x5A)
        select_0()
        self.expect_ppu(0x2000, 0xA5)
        select_1()
        self.expect_ppu(0x2000, 0x5A)


def build_rom(mapper, prg_kib, chr_kib, test, battery=False,
              code_banks=None):
    """Builds an iNES ROM running test(asm) from $E000. code_banks lists the
    8 KiB PRG banks that hold the test code (default: the last one)."""
    asm = Asm(0xE010)
    asm.label('reset')
    asm.op('sei')
    asm.op('cld')
    asm.op('ldx', '#255')
    asm.op('txs')
    asm.write(0x2000, 0)
    asm.write(0x2001, 0)
    for n in range(2):  # the PPU needs two vblanks to warm up
        asm.label('vblank%d' % n)
        asm.op('bit', 0x2002)
        asm.op('bpl', 'vblank%d' % n)

    test(asm)

    asm.op('ldy', '#%d' % PASS_COLOUR)
    asm.op('jmp', 'show')
    asm.label('fail')
    asm.op('stx', 0x0000)  # failing check number
    asm.op('ldy', '#%d' % FAIL_COLOUR)
    asm.label('show')  # fills the whole palette with Y, turns on rendering
    asm.ppu_addr(0x3F00)
    asm.op('ldx', '#32')
    asm.label('palette')
    asm.op('sty', 0x2007)
    asm.op('dex')
    asm.op('bne', 'palette')
    asm.write(0x2006, 0)
    asm.write(0x2006, 0)
    asm.write(0x2005, 0)
    asm.write(0x2005, 0)
    asm.write(0x2001, 0x0A)
    asm.label('forever')
    asm.op('jmp', 'forever')
    asm.label('nmi')
    asm.op('rti')
    code = asm.assemble()

    banks = prg_kib // 8
    prg = bytearray()
    for bank in range(banks):
        data = bytearray(0x2000)
        data[0] = bank & 0xFF
        data[1] = ~bank & 0xFF
        prg += data
    for bank in code_banks or [banks - 1]:
        base = bank * 0x2000
        prg[base + 0x10:base + 0x10 + len(code)] = code
        prg[base + 0x1FFA:base + 0x2000] = struct.pack(
            '<HHH', asm.labels['nmi'], asm.labels['reset'], asm.labels['nmi'])

    chr_ = bytearray()
    for bank in range(chr_kib):
        data = bytearray(0x400)
        data[0] = bank & 0xFF
        chr_ += data

    flags6 = ((mapper & 0x0F) << 4) | (0x02 if battery else 0)
    flags7 = mapper & 0xF0
    header = b'NES\x1a' + bytes([prg_kib // 16, chr_kib // 8, flags6, flags7]) + bytes(8)
    return header + bytes(prg) + bytes(chr_), asm.checks


# The tests -----------------------------------------------------------------

def test_152(asm):
    # [MPPP CCCC]: one-screen select, 16 KiB PRG bank at $8000, 8 KiB CHR.
    asm.write(0x8000, 0x80 | (3 << 4) | 5)
    asm.expect(0x8000, 6)
    asm.expect(0xA000, 7)
    asm.expect_ppu(0x0000, 40)
    asm.expect_ppu(0x1C00, 47)
    asm.expect_mirroring('1')
    asm.expect_one_screen_pages(lambda: asm.write(0x8000, 0x00),
                                lambda: asm.write(0x8000, 0x80))


def test_153(asm):
    # LZ93D50 with SRAM: bit 0 of $8000-$8007 selects the 256 KiB half,
    # $8008 the 16 KiB bank at $8000; $C000 is the last bank of the half.
    for reg in range(8):
        asm.write(0x8000 + reg, 1)
    asm.write(0x8008, 3)
    asm.expect(0x8000, 32 + 6)
    asm.expect(0xA000, 32 + 7)
    asm.expect(0xC000, 62)
    asm.write(0x8009, 1)
    asm.expect_mirroring('H')
    asm.write(0x6000, 0x5A)
    asm.expect(0x6000, 0x5A)


def lz93d50_test(check_chr):
    def test(asm):
        asm.write(0x8008, 5)
        asm.expect(0x8000, 10)
        asm.expect(0xA000, 11)
        asm.expect(0xC000, 30)
        if check_chr:
            asm.write(0x8000, 9)
            asm.write(0x8003, 7)
            asm.expect_ppu(0x0000, 9)
            asm.expect_ppu(0x0C00, 7)
        asm.write(0x8009, 0)
        asm.expect_mirroring('V')
        asm.write(0x8009, 1)
        asm.expect_mirroring('H')
        asm.expect_one_screen_pages(lambda: asm.write(0x8009, 2),
                                    lambda: asm.write(0x8009, 3))
    return test


def test_154(asm):
    # Namcot 108: $8000 selects a register, $8001 writes it; bit 6 of any
    # write to $8000-$FFFF picks the one-screen nametable.
    asm.write(0x8000, 6)
    asm.write(0x8001, 3)
    asm.expect(0x8000, 3)
    asm.write(0x8000, 7)
    asm.write(0x8001, 4)
    asm.expect(0xA000, 4)
    asm.write(0x8000, 0)
    asm.write(0x8001, 4)
    asm.expect_ppu(0x0000, 4)
    asm.expect_ppu(0x0400, 5)
    asm.write(0x8000, 2)
    asm.write(0x8001, 5)
    asm.expect_ppu(0x1000, 0x40 | 5)
    asm.expect_mirroring('1')
    asm.expect_one_screen_pages(lambda: asm.write(0xC000, 0x00),
                                lambda: asm.write(0xC000, 0x40))


def mmc1_write(asm, addr, value):
    for bit in range(5):
        asm.write(addr, (value >> bit) & 1)


def test_155(asm):
    asm.write(0x8000, 0x80)  # reset the shift register
    mmc1_write(asm, 0x8000, 0x1E)  # 4 KiB CHR, fixed $C000, vertical
    mmc1_write(asm, 0xA000, 3)
    mmc1_write(asm, 0xC000, 5)
    # Bit 4 would disable WRAM on an MMC1B; the MMC1A ignores it.
    mmc1_write(asm, 0xE000, 0x10 | 2)
    asm.expect(0x8000, 4)
    asm.expect(0xA000, 5)
    asm.expect(0xC000, 14)
    asm.expect_ppu(0x0000, 12)
    asm.expect_ppu(0x1000, 20)
    asm.expect_mirroring('V')
    asm.write(0x6000, 0x5A)
    asm.expect(0x6000, 0x5A)
    mmc1_write(asm, 0x8000, 0x1F)
    asm.expect_mirroring('H')


def test_207(asm):
    asm.write(0x7EFA, 2)
    asm.expect(0x8000, 2)
    asm.write(0x7EFC, 3)
    asm.expect(0xA000, 3)
    asm.write(0x7EFE, 5)
    asm.expect(0xC000, 5)
    asm.write(0x7EF2, 9)
    asm.expect_ppu(0x1000, 9)
    # Bit 7 of $7EF0/$7EF1 picks the nametable for $2000-$27FF/$2800-$2FFF.
    asm.write(0x7EF0, 0x80 | 6)
    asm.write(0x7EF1, 0x00 | 8)
    asm.expect_ppu(0x0000, 6)
    asm.expect_ppu(0x0800, 8)
    asm.ppu_write(0x2000, 0xAA)
    asm.ppu_write(0x2800, 0xBB)
    asm.write(0x7EF6, 1)  # mapper 80's mirroring register must do nothing
    asm.expect_ppu(0x2400, 0xAA)
    asm.expect_ppu(0x2C00, 0xBB)
    asm.write(0x7EF0, 0x00 | 6)
    asm.write(0x7EF1, 0x80 | 8)
    asm.expect_ppu(0x2000, 0xBB)
    asm.expect_ppu(0x2800, 0xAA)


def namco_210_test(n340):
    def test(asm):
        asm.write(0xE000, 0x40 | 3)  # vertical on a 340
        asm.expect(0x8000, 3)
        asm.write(0xE800, 7)
        asm.expect(0xA000, 7)
        asm.write(0xF000, 9)
        asm.expect(0xC000, 9)
        asm.write(0x8000, 17)
        asm.write(0xB800, 13)
        asm.expect_ppu(0x0000, 17)
        asm.expect_ppu(0x1C00, 13)
        # A 175 keeps the header's mirroring (horizontal in these ROMs).
        asm.expect_mirroring('V' if n340 else 'H')
        asm.write(0xE000, 0x80 | 3)  # horizontal on a 340
        asm.expect_mirroring('H')
        if n340:
            asm.expect_one_screen_pages(lambda: asm.write(0xE000, 0x00 | 3),
                                        lambda: asm.write(0xE000, 0xC0 | 3))
        else:
            asm.write(0x6000, 0x5A)
            asm.expect(0x6000, 0x5A)
    return test


# (name, mapper, PRG KiB, CHR KiB, test, battery, banks holding the code)
TESTS = [
    ('152', 152, 128, 128, test_152, False, None),
    ('153', 153, 512, 0, test_153, True, [31, 63]),
    ('154', 154, 128, 128, test_154, False, None),
    ('155', 155, 128, 128, test_155, False, None),
    ('157', 157, 256, 0, lz93d50_test(False), False, None),
    ('159', 159, 256, 128, lz93d50_test(True), False, None),
    ('207', 207, 128, 128, test_207, False, None),
    ('210-n340', 210, 128, 128, namco_210_test(True), False, None),
    ('210-n175', 210, 128, 128, namco_210_test(False), True, None),
]


def main():
    wanted = sys.argv[1:]
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, mapper, prg, chr_, test, battery, code_banks in TESTS:
            if wanted and name not in wanted and str(mapper) not in wanted:
                continue
            rom, checks = build_rom(mapper, prg, chr_, test, battery, code_banks)
            path = os.path.join(tmp, 'mapper%s.nes' % name)
            with open(path, 'wb') as f:
                f.write(rom)
            out = os.path.join(OUT, name)
            os.makedirs(out, exist_ok=True)
            subprocess.run([
                os.path.join(ROOT, 'tools', 'azahar', 'run.sh'),
                '-r', path, '-o', out, '-t', '120', '--',
                'wait:10', 'key:a', 'wait:6', 'shot:result',
            ], check=True, stdout=subprocess.DEVNULL)
            rows = read_png(os.path.join(out, 'result.png'))
            r, g, b = rows[120][200 * 3:200 * 3 + 3]
            ok = g > 150 and r < 150
            print('mapper %-9s %s (%d checks, rgb(%d, %d, %d))' % (
                name, 'PASS' if ok else 'FAIL', checks, r, g, b))
            results.append(ok)
    print('%d/%d passed; screenshots in %s' % (sum(results), len(results), OUT))
    return 0 if results and all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
