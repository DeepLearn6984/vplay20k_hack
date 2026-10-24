# 🔧 vplay20k-hack

> A deep dive into reverse-engineering of **VPlay20K** handheld platform – an unexpected fusion of **vape** and **NES-on-a-chip** technology. Part vape mod, part gaming console, all curiosity-driven hacking.

> ⚠️ No copyrighted data is distributed here: no flash dump, no ROMs, no screenshots, no graphics.
> Everything is generated locally from **your own dump** of the W25Q32.


## 📦 Specs & Components

### 📺 Display
- **Type**: 1.77" TFT LCD
- **Resolution**: 128x160 pixels (mounted portrait, the menu draws everything rotated 90°)
- **Interface**: 20-pin parallel MCU
- **Driver IC**: sold as ST7735, but the init sequence uses registers the ST7735 doesn't have (0x52, 0x63, 0x82–0x99, 0xB4…) – likely a GC9106-style controller (to confirm)
- **Color mode**: 16-bit (`3A = 55`), window 160x128
- **Operating Voltage**: 2.6V ~ 3.0V
- **Datasheet**: [hicenda.com](https://www.hicenda.com/product/0177-inch-tft-display.html)

### 💾 Memory
- **Model**: Winbond W25Q32JV
- **Capacity**: 32M-bit (4MB)
- **Interface**: Dual/Quad SPI
- **Operating Voltage**: 3V (⚠️ don't use an unmodified 5V CH341A)
- **Datasheet**: [winbond.com](https://www.winbond.com/hq/support/documentation/downloadV2022.jsp?__locale=en&xmlPath=/support/resources/.content/item/DA00-W25Q32JV_1.html&level=1)
- **Expected dump MD5**: `b92023df0dc4560240f550f27eb9b7b1`

### 🔋 Power
- **Battery Type**: 18650 Li-ion
- **Capacity**: 850mAh
- **Charging Circuit**: Unknown (Currently reverse-engineering 🔍) – probably handled by the vape MCU, which reports battery level to the VT369

### 🧠 Core system
- **Main Chip**: **VT369** (V.R. Technology OneBus NES-on-a-chip)
  - Confirmed by the menu code, which uses VT369-only registers (`$41B3`, `$4165`, `$41E4`–`$41EB`)
  - Menu graphics use the 8bpp / 256-colour tile mode
  - Drives the LCD and the speaker
- **Vape MCU** (separate chip, firmware NOT in the W25Q32): handles
  - Heating coil / power (BEAST MODE = 25W)
  - Puff detection
  - Battery & e-liquid levels
  - Stores the selected vape mode
- **I2C chip at address 0x40** (8-bit 0x80): challenge-response check at boot, looks like an anti-clone / authentication chip (could also be the vape MCU)
- **Firmware vendor string**: `Wellminds Technology`

## 🚧 Current status

- [x] Display pinout successfully identified
- [x] SPI Flash dump from W25Q32 extracted
- [X] Extract 3 base ROMS
- [x] Identify the main chip (VT369) and run the full dump in an emulator
- [x] Locate menu graphics (8bpp) and menu code
- [x] Find how the vape mode is sent to the MCU
- [ ] Decode the menu's game table (to add games of any size)
- [ ] Extract every menu screen as PNG (tiles + layout + palette)
- [ ] Identify the vape MCU and the I2C 0x40 chip on the PCB
- [ ] Identify the data in `0x0F0000–0x3BFFFF`
- [ ] Determine how NES mappers are implemented in flash to support every possible NES ROM


## 📸 SPI dump
- The SPI dump was obtained by desoldering the chip with a hot air gun and then reading the flash using an Arduino UNO.

## 🗺️ SPI Flash mapping

See [`mapping.tex`](mapping.tex) / [`mapping.pdf`](mapping.pdf) for the full diagram.

| Range | Content |
|---|---|
| `0x000000–0x05FFFF` | Menu graphics, 8bpp tiles (64 bytes/tile), one block per 32 KB, 0xFF padded |
| `0x060000–0x065FFF` | Test program (24 KB) |
| `0x066000–0x07BFFF` | Menu code banks |
| `0x07C000–0x07FFFF` | Menu fixed bank (`$C000–$FFFF`), vectors at `0x7FFFA`: NMI `$D520`, RESET `$EEFB`, IRQ `$D6AA` |
| `0x080000–0x0BFFFF` | F-22 hacked ROM (256 KB, MMC3) |
| `0x0C0000–0x0C5FFF` | Pac-Man hacked ROM (24 KB, NROM) |
| `0x0C6000–0x0C7FFF` | Harry Tetris hack CHR ROM (8 KB) |
| `0x0C8000–0x0CFFFF` | Harry Tetris hack PRG ROM (32 KB) |
| `0x0D0000–0x0EFFFF` | Empty (0xFF) |
| `0x0F0000–0x3BFFFF` | Unknown data, no 6502 code (audio?) |
| `0x3C0000–0x3FFFFF` | Empty (0xFF) |

### ROM ↔ CPU addresses

The VT369 maps the flash in 8 KB banks, like an MMC3:

| CPU window | Bank |
|---|---|
| `$8000–$9FFF` | register `$4107` |
| `$A000–$BFFF` | register `$4108` |
| `$C000–$DFFF` | fixed, second-to-last bank |
| `$E000–$FFFF` | fixed, last bank (vectors) |

`flash_offset = bank × 0x2000 + (cpu_address & 0x1FFF)`

In the menu (`$4100 = 0`, 512 KB window), the fixed banks are `0x3E` / `0x3F`, so for `$C000–$FFFF`:

`flash_offset = 0x70000 + cpu_address` (add `0x10` inside a `.nes` file with header)

`$4100` (outer bank) and `$410B` (bank size) are changed by the game launcher so each game sees its own area as a cartridge.

## Roms mappers
### 0. **Test program (Mapper 0)**
- **Mapper**: NROM (0)
- **PRG-ROM**: 16 KB
- **CHR-ROM**: 8 KB
- **Mirroring**: Horizontal
- Hidden test rom: test input, screen and speaker

### 1. **F-22 (Mapper 4)**
- **Mapper**: MMC3 (4)
- **PRG-ROM**: 128 KB
- **CHR-ROM**: 128 KB
- **Mirroring**: Horizontal

### 2. **Pac-Man (Mapper 0)**
- **Mapper**: NROM (0)
- **PRG-ROM**: 16 KB
- **CHR-ROM**: 8 KB
- **Mirroring**: Horizontal

### 3. **Harry Tetris (Mapper 0)**
- **Mapper**: NROM (0)
- **PRG-ROM**: 32 KB
- **CHR-ROM**: 8 KB
- **Mirroring**: Horizontal
- Note: On this ROM, the CHR ROM is swapped with the PRG ROM, which is uncommon.

## 🎮 Running the whole dump in an emulator

The whole dump runs **as-is** in **NintendulatorNRS**: just prepend a 16-byte NES 2.0 header, no byte is moved or changed (the extractor does it for you, see `vape_full_vt369.nes`).

```
4E 45 53 1A  00 00 00 0B  01 01 00 00  00 0A 00 01
```

- Mapper 256 (OneBus), PRG = 4 MB, no CHR
- Console type `0x0A` = VT369
- Boots to the **VAPE MODE / GAME MODE** menu

Menu flow: **VAPE MODE → BEAST MODE / REGULAR MODE → CONFIRM? YES / NO** (Start validates).

To flash a modified image back, strip the 16-byte header to get a plain 4 MB `.bin`.

## 🔌 VT369 ↔ Vape MCU link

The vape setting goes through the VT369 GPIO port **`$41EA` / `$41EB`** (not I2C).

| Direction | Bits | Meaning |
|---|---|---|
| VT369 → MCU | bit 6 | Mode: **0 = BEAST (25W)**, 1 = REGULAR |
| VT369 → MCU | bit 7 | Unknown (`$0D27`) |
| MCU → VT369 | bits 5–4 = `01`, bits 3–0 = value | Battery level 0–5 (`$0D30`) |
| MCU → VT369 | bits 5–4 = `11`, bits 3–0 = value | E-liquid level 0–10 (`$0D2F`) |
| MCU → VT369 | bit 5 set at boot | Device status, bit 3 = saved mode |

Inputs are read 8 times in a row until stable (debounce).

The **25W / 3.5V / 0.5Ω** shown on the BEAST screen are fixed images: the real power is decided by the MCU, the VT369 only sends one mode bit.

## 🧩 Menu code

The menu is a state machine: the main loop (`$EF37`) jumps through the table at `$F19D`, indexed by `$50`.

| `$50` | Address | Screen |
|---|---|---|
| 0 | `$CB94` | Main menu VAPE MODE / GAME MODE |
| 1 | `$CD56` | VAPE menu: BEAST / REGULAR choice |
| 2 | `$CEFE` | GAME MODE (likely the game list) |
| 3–6 | `$D01E`, `$D07F`, `$D0E7`, `$D178` | Picked at boot from the MCU status (unknown yet) |
| 7 | `$D18A` | BEAST vape screen (25W, gauges) |
| 8 | `$D262` | REGULAR vape screen |
| 9 | `$D383` | Picked at boot from MCU status 2/3/7 (charging / low battery?) |
| 10 | `$D3A9` | BEAST confirmation (port bit 6 = 0) |
| 11 | `$D44C` | REGULAR confirmation (port bit 6 = 1) |

Other key routines (fixed bank):

| Address | Role |
|---|---|
| `$F113` | Game launcher (sets banks `$4107–$410A`, jumps to a RAM stub) |
| `$DD07` + table `$DB08` | LCD init sequence |
| `$E189–$E35A` | Bit-banged I2C on `$4150`/`$4152` (bit0 SCL, bit1 SDA, read `$4153`) |
| `$CC11` + table `$E372` | I2C challenge-response; 10 failures → crash/reset |
| `$EF74` | Reads MCU status at boot and picks the start screen |
| `$D0CC` | Power-down: `$4175 = $19` then infinite loop |

## Rom extractor

This tool checks the MD5 hash of the SPI dump, then generates everything with the correct headers to be fully playable with emulators.

### Usage

Run the script with `vplay20k_dump.bin` as an argument (output directory is optional):

    python vplay_rom_extractor.py [--no-md5] /path/to/vplay20k_dump.bin [output_dir]

`--no-md5` skips the MD5 check, for a modified dump (e.g. after `vplay_rom_injector.py`). The dump must still be 4 MB.

Generated files:
- `test_program.nes`, `f22.nes`, `pacman.nes`, `harry_tetris.nes` – the games, with iNES headers
- `vape_full_vt369.nes` – the whole flash with the menu (NES 2.0 header, VT369)
- `vape_test_beast.nes`, `vape_test_regular.nes` – patched copies that boot straight into the vape screens (simulated MCU status)
- `tiles_8bpp_XXXXXX.png` – raw 8bpp menu tiles, one sheet per block (greyscale, palette not applied; needs numpy + Pillow)

## Rom injector

This tool allows you to replace the 3 original games of the **VPlay20K** vape dump, preserving the original structure of the file. The tool ensures the correct placement of PRG and CHR data, with the appropriate iNES headers for NES compatibility.
Please report to rom[X]_compatibility.txt for compatibility list.

### Usage

Run the script with `vplay20k_dump.bin` and the three ROMs you wish to inject as arguments:

    python vplay_rom_injector.py /path/to/vplay20k_dump.bin /path/to/rom1.nes /path/to/rom2.nes /path/to/rom3.nes

Test the result in NintendulatorNRS before flashing it back. The injected dump no longer matches the original MD5, so run the extractor with `--no-md5`, then open the generated `vape_full_vt369.nes`:

    python vplay_rom_extractor.py --no-md5 /path/to/vplay20k_dump.bin [output_dir]
