import hashlib
import sys
import os

EXPECTED_MD5 = "b92023df0dc4560240f550f27eb9b7b1"
DUMP_SIZE = 0x400000  # 4 MB (W25Q32)

# iNES header: PRG count (16 KB units), CHR count (8 KB units), flags 6
def ines_header(prg_16k, chr_8k, flags6=0x00):
    return bytes([0x4E, 0x45, 0x53, 0x1A, prg_16k, chr_8k, flags6, 0x00]) + bytes(8)

# NES 2.0 header for the whole dump: mapper 256 (OneBus), extended console type
def onebus_header(size, console_type):
    prg_units = size // 0x4000
    return bytes([
        0x4E, 0x45, 0x53, 0x1A,
        prg_units & 0xFF, 0x00,     # PRG size LSB, no CHR (graphics live in PRG space)
        0x00, 0x0B,                 # mapper 0 low nibbles, NES 2.0 + extended console
        0x01,                       # mapper 256
        (prg_units >> 8) & 0x0F,    # PRG size MSB
        0x00, 0x00, 0x00,
        console_type,               # 0x0A = VT369
        0x00, 0x01                  # standard controller
    ])

# (output file, header, [(offset, size), ...]) -- chunks are written in order
ROMS = [
    ("test_program.nes", ines_header(1, 1), [(0x060000, 0x6000)]),
    ("f22.nes",          ines_header(8, 16, 0x40), [(0x080000, 0x40000)]),   # MMC3
    ("pacman.nes",       ines_header(1, 1), [(0x0C0000, 0x6000)]),
    ("harry_tetris.nes", ines_header(2, 1), [(0x0C8000, 0x8000),             # PRG
                                             (0x0C6000, 0x2000)]),           # CHR
]

# Menu graphics: 8bpp tiles (64 bytes/tile), one block per 32 KB slice (start, used size)
TILE_BLOCKS = [
    (0x000000, 0xF840), (0x010000, 0x6340), (0x018000, 0x5100), (0x020000, 0x5100),
    (0x028000, 0x3840), (0x030000, 0x3EC0), (0x038000, 0x2640), (0x040000, 0xA700),
    (0x050000, 0x4780), (0x058000, 0x5100),
]

# Boot status patch: make the two "LDA $41EB" reads at $EF79/$EF82 (fixed bank, file 0x7C000 = $C000)
# return a constant, so the menu boots straight into the vape screen as if the MCU had asked for it.
# 0x22 = status, mode bit 3 = 0 (BEAST); 0x2A = mode bit 3 = 1 (REGULAR).
# Also preload battery/e-liquid ($D205: LDA #$FF -> LDA #$05) so the screen doesn't wait for the MCU.
TEST_ROMS = [("vape_test_beast.nes", 0x22), ("vape_test_regular.nes", 0x2A)]

def cpu_to_file(addr):
    return 0x7C000 + (addr - 0xC000)

def patched_dump(dump, status):
    data = bytearray(dump)
    for addr in (0xEF79, 0xEF82):
        o = cpu_to_file(addr)
        assert data[o:o + 3] == b'\xAD\xEB\x41', f"unexpected code at ${addr:04X}"
        data[o:o + 3] = bytes([0xA9, status, 0xEA])      # LDA #status / NOP
    o = cpu_to_file(0xD205)
    assert data[o:o + 2] == b'\xA9\xFF', "unexpected code at $D205"
    data[o + 1] = 0x05
    return bytes(data)

def write_tile_sheets(dump, out_dir, cols=32, scale=2):
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        print("numpy/Pillow not installed: tile sheets skipped.")
        return
    for start, size in TILE_BLOCKS:
        tiles = np.frombuffer(dump[start:start + size], np.uint8).reshape(-1, 8, 8)
        rows = (len(tiles) + cols - 1) // cols
        sheet = np.zeros((rows * 8, cols * 8), np.uint8)
        for i, t in enumerate(tiles):
            sheet[(i // cols) * 8:(i // cols) * 8 + 8, (i % cols) * 8:(i % cols) * 8 + 8] = t
        path = os.path.join(out_dir, f"tiles_8bpp_{start:06X}.png")
        Image.fromarray(sheet).resize((cols * 8 * scale, rows * 8 * scale), Image.NEAREST).save(path)
        print(f"Tile sheet '{path}' written (greyscale, palette not applied).")

def md5_of(data):
    return hashlib.md5(data).hexdigest()

def write_rom(path, header, data):
    with open(path, 'wb') as f:
        f.write(header)
        f.write(data)
    print(f"ROM '{path}' successfully extracted ({len(data) // 1024} KB).")

def extract_all(dump, out_dir):
    for name, header, chunks in ROMS:
        data = b''.join(dump[off:off + size] for off, size in chunks)
        write_rom(os.path.join(out_dir, name), header, data)

    # Whole flash with the menu (VAPE MODE / GAME MODE); runs in NintendulatorNRS
    write_rom(os.path.join(out_dir, "vape_full_vt369.nes"), onebus_header(len(dump), 0x0A), dump)

    for name, status in TEST_ROMS:
        try:
            data = patched_dump(dump, status)
        except AssertionError as e:
            print(f"Skipping '{name}': {e} (menu code differs from the original dump).")
            continue
        write_rom(os.path.join(out_dir, name), onebus_header(len(dump), 0x0A), data)

    write_tile_sheets(dump, out_dir)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--no-md5"]
    check_md5 = "--no-md5" not in sys.argv[1:]

    if len(args) not in (1, 2):
        print("Usage: python vplay_rom_extractor.py [--no-md5] <path_to_vape_dump.bin> [output_dir]")
        print("  --no-md5  skip the MD5 check (e.g. on a dump modified by vplay_rom_injector.py)")
        sys.exit(1)

    source_file = args[0]
    out_dir = args[1] if len(args) == 2 else "."

    if not os.path.isfile(source_file):
        print(f"Error: File '{source_file}' does not exist.")
        sys.exit(1)

    with open(source_file, 'rb') as f:
        dump = f.read()

    if len(dump) != DUMP_SIZE:
        print(f"Error: dump is {len(dump)} bytes, expected {DUMP_SIZE} (4 MB). ROMs were not extracted.")
        sys.exit(1)

    actual_md5 = md5_of(dump)
    print(f"MD5 of {source_file}: {actual_md5}")
    if actual_md5 == EXPECTED_MD5:
        print("MD5 is valid. Creating ROMs...")
    elif check_md5:
        print("MD5 mismatch. ROMs were not extracted (use --no-md5 for a modified dump).")
        sys.exit(1)
    else:
        print("MD5 mismatch ignored (--no-md5). Creating ROMs...")

    os.makedirs(out_dir, exist_ok=True)
    extract_all(dump, out_dir)
