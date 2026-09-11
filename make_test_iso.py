#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
"""Build the CD-ROM test fixture .iso.

Creates a small ISO-9660 image (Joliet + Rock Ridge) whose files exercise
read-only filesystem handling in the test suite. The image is built
offline on Linux (requires xorriso), hosted on a web server, and
downloaded by CI, which mounts it as a virtual CD-ROM.

Usage: make_test_iso.py [output.iso]
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

VOLUME_LABEL = 'BLEACHBIT_TEST'

# For reproducible results, the mtime is frozen (based on BleachBit's
# original commit), and the full effect requires `--set_all_file_dates`.
MODIFICATION_DATE = '2008122120583100'
FIXED_MTIME = 1229893111  # 2008-12-21T20:58:31Z

# Text files: path relative to staging root -> content.
TEXT_FILES = {
    'BLEACHBIT_TEST_FIXTURE.txt': 'marker',

    # Nested paths
    'subdir/nested/nested.txt': 'nested\n',
    # ISO9660 has limit of eight levels.
    'eukaryota/animalia/arthropoda/sanguincendia/mechanicorpis/'
    'kleptogenidae/internecivus/raptus.txt':
        'A perfect organism. Its structural perfection is matched '
        'only by its hostility.\n',
    # Easy mode
    'basic/CONFIG.SYS': '8.3 filename',
    'basic/come as you are.tmp': 'spaces\n',
    'basic/MiXeD_CaSe.bak': 'mixed case\n',
    # Exactly at the 64-character Joliet name limit.
    'basic/' + 'a' * 55 + '_long.txt': 'Or am I 64-characters "short"?\n',
    # Collision if handled case insensitivity.
    # Corporate needs you to find the differences.
    'case_sensitivity/OFFICE.txt': 'illustrated dinosaur\n',
    'case_sensitivity/office.txt': 'triangle\n',
    # ASCII that Windows doesn't like
    'char/stove|hat': 'pipe',
    'char/angle<bracket>': '',
    'char/"laser"': 'in essence, a sophisticated heat beam',
    # Windows should not return 8.3 filenames for Unicode.
    'charset/café.txt': 'unicode name\n',
    'charset/猿も木から落ちる.txt': 'unicode name\n',
    # Legal on Joliet but unopenable through normal Windows APIs.
    'not_windows_friendly/aux.txt': 'reserved name regardless of extension\n',
    'not_windows_friendly/com1.txt': 'reserved name',
    'not_windows_friendly/con.txt': 'reserved ',
    'not_windows_friendly/nul.txt': 'reserved',
    'not_windows_friendly/prn.txt': 'reserved',
    'not_windows_friendly/trailingdot.': 'trailing dot\n',
    'not_windows_friendly/trailingspace ': 'trailing space\n',

}


# Exact size in bytes of the known-size fixture file: 256 KiB.
KNOWN_SIZE_BYTES = 262144


def build_staging(root):
    """Populate the staging directory and return its path."""
    staging = os.path.join(root, 'staging')
    for relpath, content in TEXT_FILES.items():
        path = os.path.join(staging, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    # Zero-byte edge case, and a file of known size for getsize() tests.
    # The payload is every byte value repeated, so a test that reads the
    # file back can detect offset or ordering errors that uniform filler
    # such as b'A' * n would hide.
    os.makedirs(os.path.join(staging, 'names'))
    open(os.path.join(staging, 'names', 'zero_byte.bin'), 'wb').close()
    with open(os.path.join(staging, 'names', '256KiB.bin'), 'wb') as f:
        f.write(bytes(range(256)) * (KNOWN_SIZE_BYTES // 256))
    for dirpath, dirnames, filenames in os.walk(staging):
        for name in dirnames + filenames:
            os.utime(os.path.join(dirpath, name), (FIXED_MTIME, FIXED_MTIME))
    # The walk above stamps only children, so stamp the root too: its
    # timestamp becomes the ISO root directory's record date.
    os.utime(staging, (FIXED_MTIME, FIXED_MTIME))
    return staging


def make_iso(staging, iso_path):
    """Invoke xorriso to write the image."""
    if not shutil.which('xorriso'):
        sys.exit('xorriso not found; install it (e.g., apt install xorriso)')
    subprocess.run([
        'xorriso', '-as', 'mkisofs',
        '-V', VOLUME_LABEL,
        '-J',  # Joliet: what Windows reads
        '-R',  # Rock Ridge: POSIX names if mounted on Linux
        '--modification-date=' + MODIFICATION_DATE,
        # Copy each file's fixed mtime over its atime and ctime in the
        # Rock Ridge record, which otherwise captures the ctime of the
        # staging files and makes the image non-reproducible.
        '--set_all_file_dates', 'set_to_mtime',
        '-o', iso_path,
        staging,
    ], check=True)


def verify_iso(iso_path):
    """Check the image contains every expected fixture path.

    Catches silent fixture corruption that would otherwise surface only
    as confusing test failures: xorriso changing how it handles long or
    reserved names, or a case-insensitive build host collapsing the
    CasePair.txt/CASEPAIR.txt pair into one file.
    """
    expected = set(TEXT_FILES) | {'names/zero_byte.bin', 'names/256KiB.bin'}
    result = subprocess.run(
        ['xorriso', '-indev', iso_path, '-find', '/'],
        capture_output=True, text=True, check=True)
    found = {line.strip().strip("'").lstrip('/')
             for line in result.stdout.splitlines()}
    missing = expected - found
    if missing:
        sys.exit(f'{iso_path} is missing expected files: {sorted(missing)}')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Build the CD-ROM test fixture .iso')
    parser.add_argument('iso_path', nargs='?', default='bleachbit_test.iso')
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        staging = build_staging(tmpdir)
        make_iso(staging, args.iso_path)

    verify_iso(args.iso_path)

    with open(args.iso_path, 'rb') as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    size = os.path.getsize(args.iso_path)
    print(f'wrote {args.iso_path} ({size} bytes)')
    # sha256sum format, so CI can use this line in a checksum file.
    print(f'{digest}  {os.path.basename(args.iso_path)}')


if __name__ == '__main__':
    main()
