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

rm -f "$REPOTMP"
wget "$REPOURL" -nv -O - | grep -Eo \"m.*rpm\" | grep -Eo ming.*rpm | grep -vE '(debug|devel|gcc|glib|filesystem|cpp|gmp|mpfr|pixmap|runtime|termcap|pixman|headers|mingw32-jpeg|iconv|mingw32-tiff|mingw32-jasper)' > "$REPOTMP"

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
    echo "downloading $f"
    [[ -e "$CACHEDIR$f" ]] || wget "$REPOURL$f" -nv -O "$CACHEDIR$f"
done


