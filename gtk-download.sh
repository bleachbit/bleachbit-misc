#!/bin/bash

# Copyright (C) 2010 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Download Windows binaries: SQLite, GTK+, and dependencies
#

wget \
	http://ftp.acc.umu.se/pub/gnome/binaries/win32/glib/2.22/glib_2.22.5-1_win32.zip \
	http://ftp.acc.umu.se/pub/gnome/binaries/win32/gtk+/2.16/gtk+_2.16.6-2_win32.zip \
	http://ftp.gnome.org/pub/gnome/binaries/win32/atk/1.30/atk_1.30.0-1_win32.zip \
	http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/cairo_1.8.8-1_win32.zip \
	http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/gettext-runtime-0.17-1.zip \
	http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/libpng_1.2.40-1_win32.zip \
	http://ftp.gnome.org/pub/gnome/binaries/win32/dependencies/libpng_1.4.0-1_win32.zip \
	http://ftp.gnome.org/pub/gnome/binaries/win32/pango/1.24/pango_1.24.2-1_win32.zip \ 
	http://www.sqlite.org/sqlitedll-3_6_23_1.zip \
	http://zlib.net/zlib124-dll.zip

# The following require freetype6.dll, which is large, so use older verisons.
#  cairo_1.8.8-2_win32.zip
#  cairo_1.8.8-4_win32.zip
#  pango_1.24.2-1_win32.zip
#  pango_1.26.0-1_win32.zip

# GTK 2.16.6 requires libpng14 while cairo requires libpng12 but shipping two libpngs
# is smaller than shipping freetype
