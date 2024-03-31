#!/usr/bin/sh
DEST="pi@raspberrypi:/code/"
PASSWORD="raspberry"
echo "Pushing files to $DEST"
echo "..."
sshpass -p $PASSWORD scp pi.py pi.sh config.py requirements-pi.txt $DEST
sshpass -p $PASSWORD scp -r utils/ _pi/ $DEST
echo "Files pushed."
