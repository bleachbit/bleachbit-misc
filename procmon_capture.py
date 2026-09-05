#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.
"""
Automate Microsoft Process Monitor (ProcMon) to record which files
BleachBit reads during a session.  The resulting CSV is consumed by
analyze_process_monitor_events.py to build a keep/remove list for the
py2exe build.

ProcMon is downloaded on first run from Sysinternals and cached under
windows/procmon/.  It is driven entirely from the command line:

    python -m windows.procmon_capture --launch dist/bleachbit.exe -- --gui --no-uac
    python -m windows.procmon_capture --pytest -- tests/TestGui.py

The script:
  1. Ensures procmon64.exe (or procmon.exe) is available locally.
  2. Starts it (minimized) with a backing .pml file.
  3. Runs the chosen workload (launch the app, or run a command).
  4. Stops ProcMon.
  5. Exports the trace to CSV.

Notes:
  * ProcMon requires administrator privileges to capture file I/O.
    Run this script from an elevated shell (e.g. a terminal opened with
    "Run as administrator"), or each procmon invocation will trigger a
    separate UAC prompt (one for the capture start, one for /Terminate,
    and one for /OpenLog /SaveAs).  An elevated shell suppresses all of
    them.
  * ProcMon keeps a running instance; start_capture auto-terminates any
    stale instance before starting a fresh one.  Use `--stop` to clean up
    a leftover instance without starting a new capture.
"""

import argparse
import os
import subprocess
import sys
import time
import urllib.request
import zipfile

PROCMON_URL = 'https://download.sysinternals.com/files/ProcessMonitor.zip'
HERE = os.path.dirname(os.path.abspath(__file__))
PROCMON_DIR = os.path.join(HERE, 'procmon')
DEFAULT_PML = os.path.join(HERE, 'procmon_trace.pml')
DEFAULT_CSV = os.path.join(HERE, 'procmon_trace.csv')


def procmon_exe():
    """Return the path to procmon64.exe, falling back to procmon.exe."""
    for name in ('procmon64.exe', 'procmon.exe'):
        path = os.path.join(PROCMON_DIR, name)
        if os.path.exists(path):
            return path
    return None


def ensure_procmon():
    """Download and extract ProcMon if not already cached. Returns exe path."""
    exe = procmon_exe()
    if exe:
        return exe
    os.makedirs(PROCMON_DIR, exist_ok=True)
    zip_path = os.path.join(PROCMON_DIR, 'ProcessMonitor.zip')
    print(f'Downloading {PROCMON_URL} -> {zip_path}')
    urllib.request.urlretrieve(PROCMON_URL, zip_path)
    print(f'Extracting {zip_path}')
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(PROCMON_DIR)
    os.remove(zip_path)
    exe = procmon_exe()
    if not exe:
        raise RuntimeError('ProcMon executable not found after extraction')
    print(f'Using {exe}')
    return exe


def run_procmon(args, check=False):
    """Invoke procmon with the given args list."""
    exe = ensure_procmon()
    cmd = [exe] + args
    print(' '.join(cmd))
    # ProcMon may return non-zero for benign reasons (e.g. /Terminate when
    # nothing is running), so check is opt-in.
    return subprocess.run(cmd, check=check)


def start_capture(pml_path):
    """Start a ProcMon capture writing to pml_path.

    ProcMon with /BackingFile starts capturing and stays resident (it does
    NOT exit until /Terminate is sent), so we must launch it with Popen and
    return immediately.  /Quiet suppresses the startup filter dialog;
    /Minimized starts the window minimized.  There is no true headless mode
    for the capturing instance, so a minimized window is expected.

    A stale ProcMon instance from a previous crashed run can ignore the new
    /BackingFile, so we /Terminate first to ensure a clean start.
    """
    # Clean up any leftover instance so it can't hijack the new capture.
    # Only attempt this if ProcMon is already cached, to avoid forcing a
    # download on the very first run.
    if procmon_exe():
        run_procmon(['/Terminate'])
    if os.path.exists(pml_path):
        os.remove(pml_path)
    exe = ensure_procmon()
    cmd = [exe, '/AcceptEula', '/Quiet', '/Minimized',
           '/BackingFile', pml_path]
    print(' '.join(cmd))
    subprocess.Popen(cmd)
    # Give the driver a moment to install its filter before the workload runs.
    time.sleep(2)


def stop_capture(pml_path, csv_path):
    """Stop ProcMon and export the trace to CSV."""
    run_procmon(['/Terminate'])
    if not os.path.exists(pml_path):
        # The capture never produced a backing file — most likely ProcMon
        # failed to start (e.g. UAC declined, not elevated).  Don't try to
        # /OpenLog a nonexistent file; that just fails opaquely.
        print(f'ERROR: no trace file to export: {pml_path}', file=sys.stderr)
        print('ProcMon likely failed to start. Run from an elevated shell.',
              file=sys.stderr)
        return
    if os.path.exists(csv_path):
        os.remove(csv_path)
    # /SaveAs exports the .pml to a multi-column CSV (the format
    # analyze_process_monitor_events.py expects).
    run_procmon(['/OpenLog', pml_path, '/SaveAs', csv_path])
    if os.path.exists(csv_path):
        size = os.path.getsize(csv_path)
        print(f'Wrote {csv_path} ({size:,} bytes)')
    else:
        print(f'WARNING: {csv_path} was not written', file=sys.stderr)


EXERCISE_CHECKLIST = [
    "1. Start `bleachbit_console.exe --debug --gui --no-uac`",
    "2. Toggle arrows in the cleaner tree viewer",
    "3. Type something in the cleaner search box",
    "4. Click the spinbox controls in the chaff dialog",
    "5. Open the About dialog and expand the license",
    "6. Maximize the window, then restore it",
    "7. Toggle Windows 10 theme vs standard/Adwaita",
    "8. In preferences, view the keep list and custom pages",
    "9. Disable expert mode",
    "10. Toggle a cleaner like Chrome that triggers expert mode restriction",
    "11. Repeat from step 2",
]


def run_workload(cmd, cwd=None):
    """Run the workload command and wait for it to exit."""
    print(f'Running workload: {" ".join(cmd)}')
    proc = subprocess.run(cmd, cwd=cwd)
    print(f'Workload exited with code {proc.returncode}')


def main():
    parser = argparse.ArgumentParser(
        description='Capture file-read activity with Sysinternals Process Monitor.')
    parser.add_argument('--pml', default=DEFAULT_PML,
                        help=f'Backing PML path (default: {DEFAULT_PML})')
    parser.add_argument('--csv', default=DEFAULT_CSV,
                        help=f'Output CSV path (default: {DEFAULT_CSV})')
    parser.add_argument('--stop', action='store_true',
                        help='Only stop a running ProcMon instance and exit.')
    work = parser.add_mutually_exclusive_group(required=False)
    work.add_argument('--launch', metavar='EXE',
                      help='Path to the executable to launch (e.g. dist/bleachbit.exe).')
    work.add_argument('--pytest', action='store_true',
                      help='Run a pytest command as the workload. Remaining args '
                           'after "--" are passed to pytest.')
    parser.add_argument('--pytest-bin', default=sys.executable,
                        help='Python/pytest binary to invoke (default: current interpreter).')
    parser.add_argument('--cwd', default=None,
                        help='Working directory for the workload.')
    args, extra = parser.parse_known_args()
    # parse_known_args keeps the "--" separator in extras; drop it so it
    # isn't forwarded to the workload as a literal argument.
    extra = [a for a in extra if a != '--']

    if args.stop:
        # Don't force a download just to terminate nothing.
        if procmon_exe():
            run_procmon(['/Terminate'])
        else:
            print('ProcMon not cached; nothing to stop.')
        return

    if not (args.launch or args.pytest):
        parser.error('one of --launch, --pytest, or --stop is required')

    # Validate the workload before starting ProcMon, so a bad path doesn't
    # waste a capture (and a multi-MB CSV of unrelated events).
    if args.launch:
        launch_path = args.launch
        if not os.path.isabs(launch_path):
            launch_path = os.path.abspath(launch_path)
        if not os.path.exists(launch_path):
            print(f'ERROR: workload not found: {launch_path}', file=sys.stderr)
            print('Build dist first (python -m windows.setup) or pass an '
                  'absolute path.', file=sys.stderr)
            sys.exit(2)
    elif args.pytest:
        if not os.path.exists(args.pytest_bin):
            print(f'ERROR: pytest binary not found: {args.pytest_bin}',
                  file=sys.stderr)
            sys.exit(2)

    start_capture(args.pml)
    try:
        if args.launch:
            # Extra args after "--" are forwarded to the launched exe
            # (e.g. -- --gui --no-uac).
            if args.launch:
                print()
                print('=== Exercise checklist ===')
                for item in EXERCISE_CHECKLIST:
                    print(f'  {item}')
                print()
            run_workload([args.launch] + extra, cwd=args.cwd)
        elif args.pytest:
            # Anything after "--" on the command line is forwarded to pytest.
            cmd = [args.pytest_bin, '-m', 'pytest'] + extra
            run_workload(cmd, cwd=args.cwd)
    finally:
        # Always stop ProcMon so a crashed workload doesn't leave it running.
        stop_capture(args.pml, args.csv)
        if os.path.exists(args.csv):
            print()
            print('=== Next step ===')
            print('Analyze the trace to build the keep/remove lists:')
            print('  python -m windows.analyze_process_monitor_events \\')
            print(f'      --csv "{args.csv}" \\')
            print(f'      --base "{os.path.abspath(args.cwd or ".")}\\dist" \\')
            print('      --compare dist --outdir windows')


if __name__ == '__main__':
    main()
