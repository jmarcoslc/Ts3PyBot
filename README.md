# Ts3PyBot
This is a working spanish Ts3 Bot programmed to use for Guild Wars 2 events and API integration.

It uses py-ts3 as a library: https://github.com/benediktschmitt/py-ts3

The bot uses Python 3.4 and it connects to the server as a ServerQuery, joins a channel and then monitorizes whatever it's in that channel. It's able to answer back to chat commands.

More info is in: http://www.guildwars2-spain.com/foro/ayuda-y-soporte-tecnico/37402-bot-o-tron-nuestro-bot-en-teamspeak

So... what you need to run this bot?

0. Put the Ts3PyBot file and the login_data_file files in the same folder.
0. Create an empty subfolder named "databases".
0. Download the py-ts3 library and put it inside its own ts3 folder.
0. Everything should look like this: http://prntscr.com/c870pa
0. Now create a ServerQuery user with admin permissions to which the bot will connect and whitelist it so it can make multiple connections.
0. Edit the login_data_file file so nothing is empty
0. Then finally just launch the ts3pybot file :D

Create an issue if you find any :P
