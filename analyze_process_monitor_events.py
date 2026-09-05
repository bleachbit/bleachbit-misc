#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2016,2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.
"""
Analyze a Process Monitor CSV export to determine which files BleachBit
actually read during a capture session, and diff that against the
contents of the build's `dist` directory to produce keep/remove lists.

This is a rewrite of the original analyze_process_monitor_events.py
(https://github.com/bleachbit/bleachbit-misc) with the following fixes:

  * Uses csv.DictReader instead of hardcoded column indices, so it is
    robust to ProcMon CSV format changes.
  * Skips ProcMon's leading metadata/title line.
  * Filters by Process Name (default: bleachbit.exe, python.exe) so the
    whitelist is not polluted by other processes on the machine.
  * Filters by Operation (CreateFile / ReadFile) and Result (SUCCESS),
    instead of paper-cutting registry/windows paths after the fact.
  * Drops QueryDirectory wildcard enumerations, which mark directories
    as touched without any file actually being read.
  * Normalizes paths safely (no crash on empty strings).

Usage:

    python -m windows.analyze_process_monitor_events \\
        --csv windows/procmon_trace.csv \\
        --base "C:\\path\\to\\dist" \\
        --compare dist

Outputs (in --outdir):
  * build-accessed.txt - files under --base that were read during the trace
  * build-keep.txt     - files in --compare that appear in build-accessed.txt
  * build-remove.txt   - files in --compare that were never read
"""

import argparse
import csv
import os

# Operations that indicate a file was actually opened for reading.
# CreateFile with SUCCESS is how GTK/gdk-pixbuf opens a pixbuf; a
# follow-up ReadFile is not required for the "is this asset referenced"
# question, but we accept both.
READ_OPERATIONS = {'CreateFile', 'ReadFile'}

# Process names whose file access we care about.  Add more as needed
# (e.g. a helper process spawned by the app).
DEFAULT_PROCESS_NAMES = {'bleachbit.exe', 'bleachbit_console.exe',
                         'python.exe', 'pythonw.exe', 'python3.exe'}


def write_list(items, fn):
    """Write a sorted list of strings to a file, one per line."""
    with open(fn, 'w', encoding='utf-8') as f:
        for item in sorted(items):
            f.write(f'{item}\n')
    print(f'Wrote {len(items)} entries to {fn}')


def normalize_path(path, base_path):
    """Lowercase, swap / for \\, strip the base directory prefix.

    Returns None if the path is empty or not under base_path.
    """
    if not path:
        return None
    # Normalize separators and collapse runs of backslashes (ProcMon normally
    # emits single backslashes, but be defensive against escaped/doubled ones).
    p = path.replace('/', '\\')
    while '\\\\' in p:
        p = p.replace('\\\\', '\\')
    p = p.lower()
    base = base_path.replace('/', '\\').lower()
    while '\\\\' in base:
        base = base.replace('\\\\', '\\')
    while base.endswith('\\'):
        base = base[:-1]
    if p.startswith(base + '\\'):
        p = p[len(base) + 1:]
    elif p == base:
        p = ''
    return p


def is_asset_path(rel_path):
    """True if the normalized relative path looks like a shipped asset.

    Keeps the analyzer focused even though --compare may include the
    whole dist tree; non-asset files (DLLs, .pyc, locale mo, etc.) are
    still tracked in the whitelist but flagged separately for review.
    """
    if not rel_path:
        return False
    low = rel_path.lower()
    return (low.startswith('share\\icons\\') or
            low.startswith('share\\themes\\') or
            low.startswith('themes\\'))


def parse_csv(csv_path, base_path, process_names):
    """Return the set of normalized relative paths that were read."""
    whitelist = set()
    seen_header = False
    with open(csv_path, newline='', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            # ProcMon CSV begins with a title line like
            #   "Process Monitor,Version 3.96,..."  (single column)
            # followed by the real header.  Detect and skip both.
            if not seen_header:
                if len(row) == 1 and 'process monitor' in row[0].lower():
                    continue
                if any(c.lower() == 'path' for c in row):
                    # Build a column map and switch to DictReader-style access.
                    header = [c.lower().strip() for c in row]
                    idx = {name: i for i, name in enumerate(header)}
                    seen_header = True
                    continue
                # Unexpected row before header; skip defensively.
                continue
            # Now parse data rows by header index.
            op = _get(row, idx, 'operation')
            result = _get(row, idx, 'result')
            proc = _get(row, idx, 'process name')
            path = _get(row, idx, 'path')
            detail = _get(row, idx, 'detail')
            if op not in READ_OPERATIONS:
                continue
            if result != 'SUCCESS':
                continue
            if proc.lower() not in process_names:
                continue
            if op == 'CreateFile' and path and path.endswith('\\*'):
                # QueryDirectory-style enumeration; not a real file read.
                continue
            if op == 'CreateFile' and 'Options: Directory' in detail:
                # GTK opens directories with CreateFile to enumerate them;
                # these are not file reads and would pollute the whitelist
                # with directory paths.
                continue
            rel = normalize_path(path, base_path)
            if rel:
                whitelist.add(rel)
    return whitelist


def _get(row, idx, name):
    """Safely fetch a column from a row by header name."""
    i = idx.get(name)
    if i is None or i >= len(row):
        return ''
    return row[i].strip()


def walk_compare(compare_path):
    """Yield normalized relative paths of every file under compare_path."""
    for root, _dirs, files in os.walk(compare_path):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, compare_path).replace('/', '\\')
            yield rel.lower()


# Icon size directories under share\icons\<theme>\ that GTK selects based
# on the requested pixel size and display DPI.  If one size was read, the
# others would be read at a different DPI, so we keep them all.
ICON_SIZE_DIRS = ('16x16', '24x24', '32x32', '48x48', '64x64', '96x96',
                  '256x256')


def expand_variants(keep, compare_files):
    """Expand the keep set to include DPI/size variants of kept assets.

    Two patterns:
      1. Icon size variants: if 16x16\\actions\\edit-delete.png was read,
         also keep 24x24\\actions\\edit-delete.png, 32x32\\..., etc.
         (GTK loads the size matching the display DPI.)
      2. @2 high-DPI variants: if checkbox-checked.png was read, also
         keep checkbox-checked@2.png.

    Does NOT expand to scalable\\*.svg — proven never read from disk
    (GTK 3 uses its internal GResource for symbolic icons).
    """
    expanded = set(keep)
    for path in keep:
        parts = path.split('\\')
        # Pattern 1: icon size variants under share\icons\<theme>\<size>\...
        # e.g. share\icons\adwaita\16x16\actions\edit-delete.png
        if (len(parts) >= 5 and parts[0] == 'share' and parts[1] == 'icons'
                and parts[3] in ICON_SIZE_DIRS):
            size_dir = parts[3]
            filename = '\\'.join(parts[4:])
            theme = parts[2]
            for alt_size in ICON_SIZE_DIRS:
                if alt_size == size_dir:
                    continue
                candidate = f'share\\icons\\{theme}\\{alt_size}\\{filename}'
                if candidate in compare_files:
                    expanded.add(candidate)
        # Pattern 2: @2 high-DPI variants in themes\windows10\assets\
        # e.g. checkbox-checked.png -> checkbox-checked@2.png
        if path.endswith('.png') and '@2' not in path:
            base, ext = path[:-4], path[-4:]
            candidate = f'{base}@2{ext}'
            if candidate in compare_files:
                expanded.add(candidate)
    return expanded


def main():
    parser = argparse.ArgumentParser(
        description='Diff a ProcMon CSV against the dist tree to find unused files.')
    parser.add_argument('--csv', required=True, help='ProcMon CSV export path.')
    parser.add_argument('--base', required=True,
                        help='Base directory of the app while it was traced '
                             '(e.g. C:\\\\path\\\\to\\\\dist).  Paths in the CSV '
                             'are made relative to this.')
    parser.add_argument('--compare', required=True,
                        help='Directory to diff against (e.g. dist).')
    parser.add_argument('--process', default=','.join(DEFAULT_PROCESS_NAMES),
                        help='Comma-separated process names to include '
                             '(default: bleachbit/python).')
    parser.add_argument('--outdir', default='.',
                        help='Where to write build-keep.txt/build-remove.txt/'
                             'build-accessed.txt.')
    args = parser.parse_args()

    process_names = {p.strip().lower() for p in args.process.split(',') if p.strip()}
    raw_whitelist = parse_csv(csv_path=args.csv, base_path=args.base,
                              process_names=process_names)

    # Build the set of files that actually exist under --compare so we can
    # (a) diff keep/remove and (b) filter the whitelist down to real files,
    # dropping directory paths that GTK opened with CreateFile.
    compare_files = set(walk_compare(args.compare))
    accessed = raw_whitelist & compare_files
    write_list(accessed, os.path.join(args.outdir, 'build-accessed.txt'))

    # Expand the keep set to include DPI/size variants of assets that were
    # read (e.g. 24x24 icon if 16x16 was read, @2 PNG if 1x was read).
    keep = expand_variants(accessed, compare_files)
    remove = compare_files - keep
    write_list(keep, os.path.join(args.outdir, 'build-keep.txt'))
    write_list(remove, os.path.join(args.outdir, 'build-remove.txt'))

    # Asset-focused summary, since pruning share\\icons / themes is the
    # primary motivation.  Print to stdout for quick inspection.
    asset_keep = {p for p in keep if is_asset_path(p)}
    asset_remove = {p for p in remove if is_asset_path(p)}
    print()
    print(f'Asset files kept:   {len(asset_keep)}')
    print(f'Asset files removed: {len(asset_remove)}')
    if asset_remove:
        sample = sorted(asset_remove)[:10]
        print('Sample removable assets:')
        for p in sample:
            print(f'  {p}')
        if len(asset_remove) > len(sample):
            print(f'  ... and {len(asset_remove) - len(sample)} more (see build-remove.txt)')


if __name__ == '__main__':
    main()
