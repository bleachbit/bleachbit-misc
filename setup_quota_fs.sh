#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Andrew Ziem.
#
# Create a small loopback ext4 filesystem with a tight user quota so that
# tests can exercise code paths that handle errno.EDQUOT (Disk quota
# exceeded), as used by bleachbit.Wipe.wipe_path().
#
# Default layout:
#   backing file:  /tmp/bleachbit-quota.XXXXXX.img   (1 GiB, sparse, unique name)
#   mount point:   /mnt/bleachbit-quota
#   quota:         100 MiB soft / 100 MiB hard for the invoking user
#
# Usage:
#   sudo ./scripts/setup_quota_fs.sh             # create + mount
#   sudo ./scripts/setup_quota_fs.sh --cleanup   # unmount + remove
#   sudo ./scripts/setup_quota_fs.sh --status    # show current state
#   sudo BB_QUOTA_LIMIT_MB=50 ./scripts/setup_quota_fs.sh # pass environment variable
#
# Environment overrides:
#   BB_QUOTA_IMG        backing file path
#   BB_QUOTA_MNT        mount point
#   BB_QUOTA_SIZE_MB    filesystem size in MiB (default 1024)
#   BB_QUOTA_LIMIT_MB   user hard quota in MiB (default 100)
#   BB_QUOTA_USER       user to apply the quota to (default: SUDO_USER or $USER)

set -euo pipefail

IMG="${BB_QUOTA_IMG:-$(mktemp -u /tmp/bleachbit-quota.XXXXXX.img)}"
MNT="${BB_QUOTA_MNT:-/mnt/bleachbit-quota}"
SIZE_MB="${BB_QUOTA_SIZE_MB:-1024}"
LIMIT_MB="${BB_QUOTA_LIMIT_MB:-100}"
# Prefer the user who invoked sudo, so the quota applies to the test runner.
QUOTA_USER="${BB_QUOTA_USER:-${SUDO_USER:-${USER:-}}}"

log()  { printf '[quota-fs] %s\n' "$*"; }
die()  { printf '[quota-fs] error: %s\n' "$*" >&2; exit 1; }

require_root() {
    if [[ $EUID -ne 0 ]]; then
        die "must be run as root (try: sudo $0 $*)"
    fi
}

require_tools() {
    local missing=()
    for t in mkfs.ext4 tune2fs mount umount setquota quota; do
        command -v "$t" >/dev/null 2>&1 || missing+=("$t")
    done
    if (( ${#missing[@]} )); then
        die "missing required tools: ${missing[*]} (apt install quota e2fsprogs)"
    fi
}

is_mounted() {
    mountpoint -q "$MNT"
}

do_cleanup() {
    require_root
    if is_mounted; then
        log "unmounting $MNT"
        umount "$MNT"
    else
        log "$MNT is not mounted"
    fi
    if [[ -e "$IMG" ]]; then
        log "removing backing file $IMG"
        rm -f "$IMG"
    fi
    if [[ -d "$MNT" ]]; then
        rmdir "$MNT" 2>/dev/null || log "leaving $MNT in place (not empty?)"
    fi
    log "cleanup complete"
}

do_status() {
    log "backing file: $IMG ($([ -e "$IMG" ] && echo present || echo absent))"
    log "mount point:  $MNT ($([ -d "$MNT" ] && echo exists || echo missing))"
    if is_mounted; then
        log "mounted:      yes"
        if [[ -n "$QUOTA_USER" ]]; then
            # -l limits output to local filesystems. The "Cannot stat()
            # mounted device tmpfs" warning is a cosmetic quirk of the
            # quota tools iterating /proc/mounts; filter it from stderr.
            quota -l -u "$QUOTA_USER" 2> >(grep -v 'Cannot stat() mounted device tmpfs' >&2) || true
        fi
    else
        log "mounted:      no"
    fi
}

do_setup() {
    require_root
    require_tools

    [[ -n "$QUOTA_USER" ]] || die "could not determine target user; set BB_QUOTA_USER"
    id "$QUOTA_USER" >/dev/null 2>&1 || die "unknown user: $QUOTA_USER"

    # Tear down any previous instance so re-running is idempotent.
    if is_mounted || [[ -e "$IMG" ]]; then
        log "existing instance found; cleaning up first"
        do_cleanup
    fi

    log "creating $SIZE_MB MiB sparse backing file at $IMG"
    truncate -s "${SIZE_MB}M" "$IMG"

    log "formatting ext4 (this may take a moment)"
    mkfs.ext4 -q "$IMG"

    # Enable the journaled ext4 quota feature. This is the modern,
    # non-deprecated approach: quotas are stored in the journal and
    # enforced automatically on mount, so quotacheck/quotaon/aquota.user
    # are not needed (and would otherwise emit "Cannot stat() mounted
    # device tmpfs" warnings while scanning unrelated mounts).
    log "enabling ext4 journaled quota feature"
    tune2fs -O quota "$IMG" >/dev/null

    log "creating mount point $MNT"
    mkdir -p "$MNT"

    # Mount with usrquota so the journaled user quota is enforced.
    log "mounting with usrquota"
    mount -o loop,usrquota "$IMG" "$MNT"

    # setquota blocks are in 1 KiB units.
    local blocks=$((LIMIT_MB * 1024))
    log "setting ${LIMIT_MB} MiB quota for user '$QUOTA_USER'"
    # The quota tools iterate /proc/mounts and stat() each "device" field;
    # tmpfs entries have no real device path, producing a cosmetic
    # "Cannot stat() mounted device tmpfs" warning on stderr. Filter it
    # out so genuine errors remain visible.
    setquota -u "$QUOTA_USER" "$blocks" "$blocks" 0 0 "$MNT" 2> >(grep -v 'Cannot stat() mounted device tmpfs' >&2)

    # Make the mount point writable by the test user so they can actually
    # trigger EDQUOT by writing files there.
    chmod 0770 "$MNT"
    chown "$QUOTA_USER":"$(id -gn "$QUOTA_USER")" "$MNT"

    cat <<EOF

[quota-fs] setup complete.

  Mount point : $MNT
  Filesystem  : $SIZE_MB MiB ext4 (loopback on $IMG)
  User        : $QUOTA_USER
  Quota       : ${LIMIT_MB} MiB soft/hard

To trigger errno.EDQUOT as $QUOTA_USER, write more than ${LIMIT_MB} MiB:
    dd if=/dev/zero of="$MNT/big.bin" bs=1M count=$((LIMIT_MB + 5))

To verify the quota:
    quota -l -u "$QUOTA_USER"

To tear down:
    sudo $0 --cleanup

EOF
}

case "${1:-}" in
    --cleanup) do_cleanup ;;
    --status)  do_status  ;;
    ""|--setup) do_setup  ;;
    *) die "unknown option: $1 (use --setup, --cleanup, or --status)" ;;
esac
