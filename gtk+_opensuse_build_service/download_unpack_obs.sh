#!/bin/bash
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2010 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Download and unpack Windows binaries from openSUSE Build Service
#


REPOURL=http://download.opensuse.org/repositories/home:/andrew_z:/mingw32-gtk2/openSUSE_Factory/noarch/
REPOTMP=/tmp/repo.html
CACHEDIR=/tmp/gtk-obs/cache/
EXTRACTDIR=/tmp/gtk-obs/extract/

rm -f "$REPOTMP"
wget "$REPOURL" -nv -O - | grep -Eo \"m.*rpm\" | grep -Eo ming.*rpm | grep -vE '(debug|devel|gcc|glib|filesystem|cpp|gmp|mpfr|pixmap|runtime|termcap|pixman|headers|mingw32-jpeg)' > "$REPOTMP"

[[ -d "$EXTRACTDIR" ]] && rm -rf $EXTRACTDIR
mkdir -p $EXTRACTDIR
[[ -d "$CACHEDIR" ]] || mkdir -p $CACHEDIR

echo

echo cleaning up packages in cache that no longer exist online
for f in `ls "$CACHEDIR"`
do
    FOUND=0
    for f2 in `cat $REPOTMP`
    do
        if [ "$f" = "$f2" ]
        then
            FOUND=1
            break
        fi
    done
    if [[ "$FOUND" -eq "0" ]]
    then
        echo "$f no longer exists online: deleting"
        rm -rf "$CACHEDIR$f"
    fi
done

echo

for f in `cat "$REPOTMP"`
do
    echo "downloading and extracting $f"
    [[ -e "$CACHEDIR$f" ]] || wget "$REPOURL$f" -nv -O "$CACHEDIR$f"
    cd "$EXTRACTDIR"
    rpm2cpio "$CACHEDIR$f" | cpio -id
done

mv "${EXTRACTDIR}"usr/i686-pc-mingw32/sys-root/mingw/* "$EXTRACTDIR"
rm -rf "${EXTRACTDIR}usr"

echo

echo removing unnecessary
rm -rf "${EXTRACTDIR}"bin/*exe
rm -rf "${EXTRACTDIR}"bin/*manifest
rm -rf "${EXTRACTDIR}"bin/autopoint
rm -rf "${EXTRACTDIR}"bin/gettextize
rm -rf "${EXTRACTDIR}"bin/gtk-builder-convert
rm -rf "${EXTRACTDIR}"etc/fonts
rm -rf "${EXTRACTDIR}"include
rm -rf "${EXTRACTDIR}"lib/gettext
rm -rf "${EXTRACTDIR}"lib/pango
rm -rf "${EXTRACTDIR}"lib/*dll.a
rm -rf "${EXTRACTDIR}"share/{aclocal,doc,gettext,info,man}
rm -rf "${EXTRACTDIR}"share/themes/{Default,Emacs,Raleigh}
