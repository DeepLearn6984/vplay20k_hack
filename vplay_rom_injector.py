import hashlib
import sys
import os
import shutil  # For copying the file

# Define read sizes for each ROM
HARRY_TETRIS_CHR_SIZE_IN_BYTES = 8192  # 8 KB
HARRY_TETRIS_PRG_SIZE_IN_BYTES = 32768  # 32 KB
PACMAN_PRG_CHR_SIZE_IN_BYTES = 24576  # 24 KB
F22_PRG_CHR_SIZE_IN_BYTES = 262144  # 256 KB

# Header of each ROM to be preserved
HEADER_PACMAN =       bytearray([0x4E, 0x45, 0x53, 0x1A, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
HEADER_F22 =          bytearray([0x4E, 0x45, 0x53, 0x1A, 0x08, 0x10, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
HEADER_HARRY_TETRIS = bytearray([0x4E, 0x45, 0x53, 0x1A, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

def check_md5(filepath, expected_md5):
    """Check if the file MD5 hash matches the expected one."""
    try:
        with open(filepath, 'rb') as f:
            md5_hash = hashlib.md5()
            while chunk := f.read(8192):
                md5_hash.update(chunk)
            actual_md5 = md5_hash.hexdigest()
            print(f"MD5 of {filepath}: {actual_md5}")
            return actual_md5 == expected_md5
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return False

def check_header(rom_path, expected_header):
    """Check if the ROM has the expected iNES header."""
    with open(rom_path, 'rb') as rom:
        header = rom.read(16)
        if header != expected_header:
            print(f"Error: ROM '{rom_path}' does not have the correct header. Injection aborted.")
            print(f"Expected header: {' '.join(f'{byte:02X}' for byte in expected_header)}")
            print(f"Actual header: {' '.join(f'{byte:02X}' for byte in header)}")
            return False
        return True

def inject_rom(source_path, dump_path, rom_offset, rom_size):
    """Inject the PRG/CHR data from the ROM into the vape dump at the given offset."""
    try:
        with open(dump_path, 'r+b') as dump:
            dump.seek(rom_offset)
            with open(source_path, 'rb') as rom:
                # Skip the first 16 bytes (iNES header) and read the rest
                rom.read(16)  # Skip the header
                rom_data = rom.read(rom_size)
                dump.write(rom_data)
                print(f"Injected {source_path} into dump at offset {hex(rom_offset)}")
                return True
    except FileNotFoundError:
        print(f"Error: File '{source_path}' or '{dump_path}' not found.")
        return False

def inject_f22(dump_path, rom_path):
    """Inject the F22 ROM data into the vape dump."""
    if check_header(rom_path, HEADER_F22):
        return inject_rom(rom_path, dump_path, 0x080000, F22_PRG_CHR_SIZE_IN_BYTES)
    return False

def inject_pacman(dump_path, rom_path):
    """Inject the Pac-Man ROM data into the vape dump."""
    if check_header(rom_path, HEADER_PACMAN):
        return inject_rom(rom_path, dump_path, 0x0C0000, PACMAN_PRG_CHR_SIZE_IN_BYTES)
    return False

def inject_harry_tetris(dump_path, rom_path):
    """Inject the Harry Tetris ROM (with reversed PRG/CHR data) into the vape dump."""
    if check_header(rom_path, HEADER_HARRY_TETRIS):  # Check the header before injecting
        try:
            with open(rom_path, 'rb') as rom:
                rom.read(16)  # Skip the header
                prg_data = rom.read(HARRY_TETRIS_PRG_SIZE_IN_BYTES)
                chr_data = rom.read(HARRY_TETRIS_CHR_SIZE_IN_BYTES)

                if len(prg_data) != HARRY_TETRIS_PRG_SIZE_IN_BYTES or len(chr_data) != HARRY_TETRIS_CHR_SIZE_IN_BYTES:
                    print(f"Error: ROM '{rom_path}' does not have the correct PRG/CHR size. Injection aborted.")
                    return False

                # Inject CHR data to PRG location in dump (0x0C6000)
                inject_rom_data(dump_path, 0x0C6000, chr_data)
                # Inject PRG data to CHR location in dump (0x0C8000)
                inject_rom_data(dump_path, 0x0C8000, prg_data)
                print(f"Injected '{os.path.basename(rom_path)}' into the dump at the correct PRG/CHR locations.")
                return True
        except FileNotFoundError:
            print(f"Error: File '{rom_path}' not found.")
            return False
        except Exception as e:
            print(f"Error injecting Harry Tetris ROM from '{rom_path}': {str(e)}")
            return False
    return False

def inject_rom_data(dump_path, offset, data):
    """Inject raw data into the dump at the given offset."""
    try:
        with open(dump_path, 'r+b') as dump:
            dump.seek(offset)
            dump.write(data)
        return True
    except FileNotFoundError:
        print(f"Error: File '{dump_path}' not found.")
        return False

def backup_dump(dump_file):
    """Create a backup of the vape dump file with a .bak extension."""
    try:
        backup_file = dump_file + '.bak'
        shutil.copy(dump_file, backup_file)
        print(f"Backup created at '{backup_file}'")
    except FileNotFoundError:
        print(f"Error: File '{dump_file}' not found. Backup failed.")
        sys.exit(1)

# ============ ENTRY POINT ============
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python vplay_rom_injector.py <vplay20k_dump.bin> <rom1> <rom2> <rom3>")
        sys.exit(1)

    dump_file = sys.argv[1]
    rom1 = sys.argv[2]
    rom2 = sys.argv[3]
    rom3 = sys.argv[4]

    expected_md5 = "b92023df0dc4560240f550f27eb9b7b1"

    if not os.path.isfile(dump_file):
        print(f"Error: File '{dump_file}' does not exist.")
        sys.exit(1)

    # Step 1: Backup the vape dump file
    backup_dump(dump_file)

    # Step 2: Check MD5 and proceed with injections
    if check_md5(dump_file, expected_md5):
        print("MD5 is valid. Injecting ROMs...")
        
        # Track injection status
        injection_successful = True

        # Perform injections and check each result
        if not inject_f22(dump_file, rom1):
            print(f"Error injecting F22 ROM from '{rom1}'.")
            injection_successful = False

        if not inject_pacman(dump_file, rom2):
            print(f"Error injecting Pac-Man ROM from '{rom2}'.")
            injection_successful = False

        if not inject_harry_tetris(dump_file, rom3):
            print(f"Error injecting Harry Tetris ROM from '{rom3}'.")
            injection_successful = False

        # Final message based on success or failure
        if injection_successful:
            print("ROM injection complete. Enjoy your vape!")
        else:
            print("ROM injection failed. Please check the error messages above.")
    else:
        print("MD5 mismatch. ROMs were not injected.")
