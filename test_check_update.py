#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

"""
Copyright (C) 2014-2025 by Andrew Ziem.  All rights reserved.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Verify the online update notification system returns the right version numbers
"""

import os
import sys
import time

dir_bb_root = os.path.abspath('../bleachbit')
os.chdir(dir_bb_root)
sys.path.append(dir_bb_root)

import bleachbit  # noqa: E402
import bleachbit.Update  # noqa: E402

LATEST_STABLE = '5.0.0'
LATEST_BETA = '5.0.1 (beta)'
# tuple in the format
# (current version sent, version returned 1, version returned 2)
TESTS = \
    (('3.0', LATEST_STABLE, None),
     ('3.1.0', LATEST_STABLE, None),
     ('3.2.0', LATEST_STABLE, None),
     ('3.9.0', LATEST_STABLE, None),
     ('3.9.2', LATEST_STABLE, None),
     ('4.0.0', LATEST_STABLE, None),
     ('4.1.0', LATEST_STABLE, None),
     ('4.2.0', LATEST_STABLE, None),
     ('4.4.0', LATEST_STABLE, None),
     ('4.4.2', LATEST_STABLE, None),
     ('4.5.0', LATEST_STABLE, None),
     ('4.6.0', LATEST_STABLE, None),
     ('4.6.2', LATEST_STABLE, None),
     ('5.0.0', LATEST_BETA, None),
     ('5.0.1', None, None))


def do_test(app_version, version1_expected, version2_expected, base_url=bleachbit.base_url):
    """Do a single test"""
    assert isinstance(base_url, str)
    assert base_url.startswith('http')
    print('\n', '*' * 10, app_version)
    bleachbit.APP_VERSION = app_version
    bleachbit.update_check_url = f'{base_url}/update/{bleachbit.APP_VERSION}'

    v1e = version1_expected  # e=expected
    v2e = version2_expected

    start_time = time.time()
    cu = bleachbit.Update.check_updates(True, False, None, None)
    elapsed_time_ms = (time.time() - start_time) * 1000

    print(f'returned={cu}, time={elapsed_time_ms:.2f}ms')

    test_success = True
    if cu == ():
        v1r = None  # r=returned
        v2r = None
    else:
        if cu[0]:
            v1r = cu[0][0]
        else:
            v1r = None
        if len(cu) > 1:
            v2r = cu[1][0]
        else:
            v2r = None
    if not v1e == v1r:
        print(
            f'ERROR: sent version {app_version}, expected v1={v1e}, returned v1={v1r}')
        test_success = False
    if not v2e == v2r:
        print(
            f'ERROR: sent version {app_version}, expected v2={v2e}, returned v2={v2r}')
        test_success = False

    return elapsed_time_ms, test_success


def main():
    """Main function"""
    base_url = bleachbit.base_url
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    times_ms = []
    test_count = 0
    success_count = 0
    error_count = 0

    for (app_version, version1_expected, version2_expected) in TESTS:
        elapsed_time_ms, test_success = do_test(
            app_version, version1_expected, version2_expected, base_url)
        test_count += 1
        times_ms.append(elapsed_time_ms)
        if test_success:
            success_count += 1
        else:
            error_count += 1

    print(
        f"\nTest summary: {test_count} total, {success_count} successful, {error_count} failed")
    if times_ms:
        min_time = min(times_ms)
        avg_time = sum(times_ms) / len(times_ms)
        max_time = max(times_ms)
        print(
            f"  min/avg/max = {min_time:.2f}/{avg_time:.2f}/{max_time:.2f} ms")


if __name__ == '__main__':
    main()
