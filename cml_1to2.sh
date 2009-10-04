#!/bin/bash

# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Convert from CleanerML version 1 to version 2.
# Version 2 introduced in BleachBit version 0.7.0.
#


for f in cleaners/*.xml
do
        sed -i 's/type="children" directories="false">\([^<]*\)<\/action/command="delete" search="walk.files" path="\1"\//g' $f
        sed -i 's/type="children" directories="true">\([^<]*\)<\/action/command="delete" search="walk.all" path="\1"\//g' $f
        sed -i 's/type="\(file\|glob\)">\([^<]*\)<\/action/command="delete" search="\1" path="\2" \//g' $f
        sed -i 's/type="sqlite.vacuum">\([^<]*\)<\/action/command="sqlite.vacuum" search="glob" path="\1" \//g' $f
        sed -i 's/type="winreg" name="\(.*\)">\([^<]*\)<\/action/command="winreg" path="\2" name="\1" \//g' $f
        sed -i 's/type="winreg">\([^<]*\)<\/action/command="winreg" path="\1" \//g' $f
        sed -i 's/type="\(apt.autoremove\|apt.autoclean\|yum.clean_all\)"/command="\1"/g' $f
done

