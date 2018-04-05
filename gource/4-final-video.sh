# vim: ts=4:sw=4:expandtab

# Copyright (C) 2018 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#

#
# Add music, encode, and trim the video
#

WORKDIR=${WORKDIR:-/tmp/gource}

# Music: http://freemusicarchive.org/music/Chris_Zabriskie
# http://freemusicarchive.org/music/Chris_Zabriskie/Vendaface/05_-_Air_Hockey_Saloon

echo Download music
if [ ! -e "$WORKDIR/music.mp3" ]; then
    wget https://freemusicarchive.org/music/download/95af9859ee88ffce9a446e5896c4db8128b3d6a9 -O $WORKDIR/music.mp3
fi

echo Convert to mp4
rm -f $WORKDIR/video.mp4
time nice ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i $WORKDIR/video.ppm -i $WORKDIR/music.mp3 -vcodec libx264 -acodec copy -preset ultrafast -pix_fmt yuv420p -crf 1 -threads 0 -bf 0 $WORKDIR/video.mp4

echo Trim
rm -f $WORKDIR/video2.mp4
ffmpeg -i $WORKDIR/video.mp4 -to 03:30 -c copy $WORKDIR/video2.mp4

