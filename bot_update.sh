#!/bin/bash

URL_MASTER="https://github.com/jmarcoslc/Ts3PyBot/archive/master.zip";
PY_NAME="Ts3PyBot";
SHELL_SCRIPT_NAME="bot_update";

wget $URL_MASTER;
unzip master.zip;

downloaded_version=`cat $PY_NAME-master/$PY_NAME.py | grep "INSTALLED_VERSION = " | cut -d\" -f2`;

if [ "$1" != "$downloaded_version" ]; then
	service ts3bot.sh stop												# ts3bot.sh is not provided, as serveradmin you must to deploy your own script
	cp $PY_NAME"-master"/$PY_NAME.py ./$PY_NAME.py 						# take these lines as an example
	cp $PY_NAME"-master"/$SHELL_SCRIPT_NAME.sh ./$SHELL_SCRIPT_NAME.sh
	service ts3bot.sh start -f
fi

rm -R $PY_NAME"-master";
rm master.zip;
