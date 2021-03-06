#!/bin/bash

# Copyright (C) 2012 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Convert SVG to a Windows application icon
#


DIR=/tmp/

function svg2ico {
        echo svg2ico $1
        rm -f $DIR/icon.png $DIR/bleachbit_$1.png
        convert -filter Box -background none bleachbit.svg -resize $1x$1 $DIR/icon.png
        optipng -quiet -o7 $DIR/icon.png
        pngcrush -rem allb -reduce -brute -q $DIR/icon.png $DIR/bleachbit_$1.png
}

svg2ico 16
svg2ico 32
svg2ico 48
svg2ico 128

png2ico $DIR/bleachbit.ico $DIR/bleachbit_{128,48,32,16}.png

