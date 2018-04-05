# vim: ts=4:sw=4:expandtab

# Copyright (C) 2018 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#


#
# Collect email addresses from Git repositories for use with 2-avatar.py
#

WORKDIR=${WORKDIR:-/tmp/gource}
GITROOT=${GITROOT:-~/repos}


rm -f $WORKDIR/committer1

mkdir -p $WORKDIR

touch $WORKDIR/committer1

git_log () {
    if [ ! -d "$GITROOT/$1" ];then
        echo "ERROR: Repository does not exist: $GITROOT/$1"
        exit 1
    fi
    echo Repository: $1
    cd $GITROOT/$1
    git log "--pretty=format:%ae|%an" >> $WORKDIR/committer1
    echo " " >> $WORKDIR/committer1
}

git_log bleachbit
git_log bleachbit-misc
git_log cleanerml
git_log winapp2.ini

sort $WORKDIR/committer1 | sort | uniq | grep @ > $WORKDIR/committer2
