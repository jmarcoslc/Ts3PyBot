#!/bin/bash

URL_MASTER="https://github.com/Aens/Ts3PyBot/archive/master.zip";
PY_NAME="Ts3PyBot";

wget $URL_MASTER;
unzip master.zip;

downloaded_version=`cat $PY_NAME-master/$PY_NAME.py | grep "INSTALLED_VERSION = " | cut -d\" -f2`;

if [ $1 -ne $downloaded_version ]; then
	service ts3bot.sh stop							# ts3bot.sh is not provided, as serveradmin you must to deploy your own script
	cp $PY_NAME-master/$PY_NAME.py ./$PY_NAME.py 	# take these three lines as an example
	service ts3bot.sh start -f 						# 
else
	rm -R $PY_NAME-master;
	rm master.zip;
fi