# vim: ts=4:sw=4:expandtab

# Copyright (C) 2018 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

#
# ETL Git logs from multiple repositories for use in Gource
#

WORKDIR=${WORKDIR:-/tmp/gource}
GITROOT=${GITROOT:-~/repos}

mkdir -p $WORKDIR

echo Clearing old logs
rm -f $WORKDIR/*.log

git_log () {
    # parameters
    # 1: repository directory
    # 2: log name
    # 3: display name
    if [ ! -d "$GITROOT/$1" ];then
        echo ERROR: Repository does not exist: $GITROOT/$1
        exit 1
    fi
    echo Repository: $1
    gource --output-custom-log $WORKDIR/$2.log $GITROOT/$1 || exit 1
    sed -i -r "s#(.+)\|#\1|/$3#" $WORKDIR/core.log
}

echo Running Gource to extract logs from Git repositories
git_log bleachbit core Core
git_log bleachbit-misc misc misc
git_log cleanerml cleanerml CleanerML
git_log winapp2.ini winapp2 Winapp2.ini

echo Combining logs
rm -f $WORKDIR/combined.log
cat $WORKDIR/*log | sort -n > $WORKDIR/combined.log

echo Changing names
sed -i -E 's/\|([^|]*,[^|]*)\|/|Multiple translators|/g' $WORKDIR/combined.log
# combine two names for same person
sed -i -E 's/\|z\|/|Andrew Ziem|/g' $WORKDIR/combined.log
sed -i -E 's/\|rob\|/|Rob|/g' $WORKDIR/combined.log
sed -i -E 's/\|Jean Marc\|/|Jean-Marc|/g' $WORKDIR/combined.log
sed -i -E 's/\|mbrandis\|/|Mark Brandis|/g' $WORKDIR/combined.log
# unsupported characters
sed -i -E 's/அவினாஷ் Avinash/Avinash/g' $WORKDIR/combined.log
sed -i -E 's/☠//g' $WORKDIR/combined.log

echo Here are the names of contributors
cat $WORKDIR/combined.log | awk -F\| {'print  $2'} | sort | uniq | less




