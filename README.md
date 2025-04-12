# 🔧 vplay20k-hack

> A deep dive into reverse-engineering of **VPlay20K** handheld platform – an unexpected fusion of **vape** and **NES-on-a-chip** technology. Part vape mod, part gaming console, all curiosity-driven hacking.


## 📦 Specs & Components

### 📺 Display
- **Type**: 1.77" TFT LCD  
- **Resolution**: 128x160 pixels  
- **Interface**: 20-pin parallel MCU  
- **Driver IC**: ST7735  
- **Operating Voltage**: 2.6V ~ 3.0V  
- **Datasheet**: [hicenda.com](https://www.hicenda.com/product/0177-inch-tft-display.html)

### 💾 Memory
- **Model**: Winbond W25Q32JV  
- **Capacity**: 32M-bit (4MB)  
- **Interface**: Dual/Quad SPI  
- **Operating Voltage**: 3V  
- **Datasheet**: [winbond.com](https://www.winbond.com/hq/support/documentation/downloadV2022.jsp?__locale=en&xmlPath=/support/resources/.content/item/DA00-W25Q32JV_1.html&level=1)

### 🔋 Power
- **Battery Type**: 18650 Li-ion  
- **Capacity**: 850mAh  
- **Charging Circuit**: Unknown (Currently reverse-engineering 🔍)

### 🧠 Core system
- **Main Chip**: NES-on-a-chip variant (likely an NOAC)  
- **Microcontroller**: Manages:
  - Vape functionality (still unclear how)  
  - LCD display driving  
  - Audio output through small speaker  
  - Potential microphone input

## 🚧 Current status

- [x] Display pinout successfully identified  
- [x] SPI Flash dump from W25Q32 extracted
- [X] Extract 3 base ROMS
- [ ] Recover the other assets in the dump
- [ ] Determine how NES mappers are implemented in flash to support every possible NES ROM


## 📸 SPI dump
- The SPI dump was obtained by desoldering the chip with a hot air gun and then reading the flash using an Arduino UNO.

## 📸 SPI Flash mapping

    (0x000000, 0x05FFFF, "Unknown data 1"),
    (0x060000, 0x065FFF, "Test program"),
    (0x066000, 0x07FFFF, "Unknown data 2"),
    (0x080000, 0x0BFFFF, "F-22 hacked ROM", 262144),
    (0x0C0000, 0x0C5FFF, "Pac-Man hacked ROM", 24576),
    (0x0C6000, 0x0C7FFF, "Harry Tetris hack CHR ROM", 8192)
    (0x0C8000, 0x0CFFFF, "Harry Tetris hack PGR ROM", 32768)
    (0x0C6000, 0x3FFFFF, "Unknown data 3")

## Roms mappers
### 0. **Test program (Mapper 0)**
- **Mapper**: NROM (0)
- **PRG-ROM**: 16 KB
- **CHR-ROM**: 8 KB
- **Mirroring**: Horizontal
- Hidden test rom: test input, screen and speaker
  
### 1. **F-22 (Mapper 4)**
- **Mapper**: CNROM (4)
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

## Rom extractor

This tool will assist in extracting ROMs from the dump and creating the correct iNES header to be fully playable with emulators.

### Usage

Run the script with `vplay20k_dump.bin` as an argument:

    python vplay_rom_extractor.py /path/to/vplay20k_dump.bin

The script will check the MD5 hash of the SPI dump and generate the following ROM files if the hash matches:
- test_program.nes
- f22.nes
- pacman.nes
- harry_tetris.nes

## Rom injector

This tool allows you to replace the 3 original games of the **VPlay20K** vape dump, preserving the original structure of the file. The tool ensures the correct placement of PRG and CHR data, with the appropriate iNES headers for NES compatibility.
Please report to rom[X]_compatibility.txt for compatibility list.

### Usage

Run the script with `vplay20k_dump.bin` and the three ROMs you wish to inject as arguments:

    python vplay_rom_injector.py /path/to/vplay20k_dump.bin /path/to/rom1.nes /path/to/rom2.nes /path/to/rom3.nes

