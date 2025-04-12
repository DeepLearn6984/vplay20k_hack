import hashlib
import sys
import os

# Define read sizes in variables
TEST_PROGRAM_PRG_CHR_SIZE_IN_BYTES = 24576  # 24 KB
POKETRIS_CHR_SIZE_IN_BYTES = 8192  # 8 KB
POKETRIS_PRG_SIZE_IN_BYTES = 32768  # 32 KB
PACMAN_PRG_CHR_SIZE_IN_BYTES = 24576  # 24 KB
F22_PRG_CHR_SIZE_IN_BYTES = 262144  # 256 KB

def check_md5(filepath, expected_md5):
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

def create_test_program_nes(source_path, output_file):
    header = bytearray([
        0x4E, 0x45, 0x53, 0x1A,
        0x01, 0x01, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00
    ])
    with open(output_file, 'wb') as f:
        f.write(header)
        try:
            with open(source_path, 'rb') as src:
                src.seek(0x060000)
                pacman_data = src.read(TEST_PROGRAM_PRG_CHR_SIZE_IN_BYTES)
                f.write(pacman_data)
        except FileNotFoundError:
            print("Error: Source file not found.")
            return
    print(f"ROM '{output_file}' successfully extracted.")

def create_pacman_nes(source_path, output_file):
    header = bytearray([
        0x4E, 0x45, 0x53, 0x1A,
        0x01, 0x01, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00
    ])
    with open(output_file, 'wb') as f:
        f.write(header)
        try:
            with open(source_path, 'rb') as src:
                src.seek(0x0C0000)
                pacman_data = src.read(PACMAN_PRG_CHR_SIZE_IN_BYTES)
                f.write(pacman_data)
        except FileNotFoundError:
            print("Error: Source file not found.")
            return
    print(f"ROM '{output_file}' successfully extracted.")

def create_f22_nes(source_path, output_file):
    header = bytearray([
        0x4E, 0x45, 0x53, 0x1A,
        0x08, 0x10, 0x40, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00
    ])
    with open(output_file, 'wb') as f:
        f.write(header)
        try:
            with open(source_path, 'rb') as src:
                src.seek(0x080000)
                f22_data = src.read(F22_PRG_CHR_SIZE_IN_BYTES)
                f.write(f22_data)
        except FileNotFoundError:
            print("Error: Source file not found.")
            return
    print(f"ROM '{output_file}' successfully extracted.")

def create_harry_tetris_nes(source_path, output_file):
    header = bytearray([
        0x4E, 0x45, 0x53, 0x1A,
        0x02, 0x01, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00
    ])
    try:
        with open(source_path, 'rb') as src:
            src.seek(0x0C6000)
            chr_data = src.read(POKETRIS_CHR_SIZE_IN_BYTES)
            if len(chr_data) != POKETRIS_CHR_SIZE_IN_BYTES:
                print(f"Error: Incomplete CHR data. Expected {POKETRIS_CHR_SIZE_IN_BYTES} bytes.")
                return
            src.seek(0x0C8000)
            prg_data = src.read(POKETRIS_PRG_SIZE_IN_BYTES)
            if len(prg_data) != POKETRIS_PRG_SIZE_IN_BYTES:
                print(f"Error: Incomplete PRG data. Expected {POKETRIS_PRG_SIZE_IN_BYTES} bytes.")
                return
    except FileNotFoundError:
        print("Error: Source file not found.")
        return
    with open(output_file, 'wb') as f:
        f.write(header)
        f.write(prg_data)
        f.write(chr_data)
    print(f"ROM '{output_file}' successfully extracted.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_vape_dump.bin>")
        sys.exit(1)

    source_file = sys.argv[1]
    expected_md5 = "b92023df0dc4560240f550f27eb9b7b1"

    if not os.path.isfile(source_file):
        print(f"Error: File '{source_file}' does not exist.")
        sys.exit(1)

    if check_md5(source_file, expected_md5):
        print("MD5 is valid. Creating ROMs...")
        create_test_program_nes(source_file, "test_program.nes");
        create_harry_tetris_nes(source_file, "harry_tetris.nes")
        create_pacman_nes(source_file, "pacman.nes")
        create_f22_nes(source_file, "f22.nes")
    else:
        print("MD5 mismatch. ROMs were not extracted.")
