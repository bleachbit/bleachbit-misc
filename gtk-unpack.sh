#!/bin/bash

# Copyright (C) 2010 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Unpack GTK+ Windows binaries, dependencies, and SQLite and prepare for use
#

echo pre-clean
rm -rf bin etc lib manifest share zlib-1.?.? sqlite3.dll

echo unzip
unzip -q atk_*zip
unzip -q cairo*.zip
unzip -q expat*.zip
unzip -q fontconfig*.zip
unzip -q freetype*.zip
unzip -q gdk-pixbuf_*zip
unzip -q gettext-runtime*zip
unzip -q glib*zip
unzip -q gtk+_2*zip
unzip -q libpng_1.2*zip
unzip -q libpng_1.4*zip
unzip -q pango*zip
unzip -q sqlitedll-*zip sqlite3.dll
unzip -q zlib*zip zlib-1.?.?/zlib1.dll # zlib 1.2.4
unzip -q zlib*zip bin/zlib1.dll # zlib 1.2.5

echo move/copy
mv zlib-1.?.?/zlib1.dll bin # zlib 1.2.4
cp gtkrc etc/gtk-2.0/
rm -rf zlib-1.?.?

echo remove unnecessary
find \( -name atk10.mo -o -name glib20.mo -o -name gtk20-properties.mo \) -exec rm -f \{\} \+
#find lib/gtk-2.0/2.10.0/loaders/ | grep dll$ | grep -v png | xargs rm -f 
rm -f bin/*exe
rm -f bin/libtiff-3.dll
rm -f bin/libtiffxx-3.dll
rm -f etc/gtk-2.0/gtk.immodules
rm -f lib/charset.alias
rm -f lib/gtk-2.0/2.10.0/engines/libpixmap.dll
rm -rf etc/pango/
rm -rf manifest
rm -rf share/doc
rm -rf share/themes/{Default,Emacs,Raleigh}/
rm -rf share/local/*/LC_MESSAGES/gdk-pixbuf.mo


echo strip
# warning: do not strip zlib1.dll or *.pyd
# do not strip (?) sqlite3.dll because of http://bleachbit.sourceforge.net/forum/074-fails-errors
i686-pc-mingw32-strip --preserve-dates bin/intl.dll bin/lib*dll
find lib \( -iname '*dll' -o -iname '*exe' \) -exec i686-pc-mingw32-strip --strip-debug --discard-all --preserve-dates  -v \{\} \+

echo compress UPX
find \( -iname '*dll' -o -iname '*exe' \) -exec upx --best --crp-ms=999999 --nrv2e \{\} \+

echo setup theme
echo 'gtk-theme-name = "MS-Windows"' > etc/gtk-2.0/gtkrc
