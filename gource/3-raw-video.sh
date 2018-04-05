# vim: ts=4:sw=4:expandtab

# Copyright (C) 2018 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#

#
# Invoke Gource to produce the video
#

WORKDIR=${WORKDIR:-/tmp/gource}
GITROOT=${GITROOT:-~/repos}

rm -f $WORKDIR/video.ppm

gource  \
    --title "History of BleachBit code (2008 to 2018)" \
    --date-format "%Y-%m-%d" \
    --font-size 20 \
    --caption-file caption.psv \
    --caption-duration 5 \
    --auto-skip-seconds 1 \
    --seconds-per-day 0.04 \
    --highlight-dirs \
    --hide mouse,progress \
    --key \
    --stop-at-end \
    --hide-root \
    --logo $GITROOT/bleachbit/bleachbit.png \
    --user-image-dir $WORKDIR/avatar/ \
    --multi-sampling \
    -1920x1080 \
    --output-framerate 60 \
    --output-ppm-stream $WORKDIR/video.ppm \
    $WORKDIR/combined.log
