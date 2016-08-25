#!/usr/bin/python3.4

# The MIT License (MIT)
# 
# Copyright (c) 2016 Alejandro Gutierrez Almansa <https://github.com/Aens>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#Libraries
import ts3
import datetime
import time
import json
import textwrap
import sys
import subprocess
import urllib
import re
from urllib import request
from random import choice, sample
from bs4 import BeautifulSoup
from login_data_file import *

INSTALLED_VERSION = "5.5"
VERSION_COMMENTS = "Web-Scrapping hecho con BeautifulSoup :D ahora todo es más chachi."

#################
# Main bot Code #
#################
def bot_principal(ts3conn):
    global my_channel, my_name
    my_channel = get_channel_id(channel_to_join)
    try:
        ts3conn.clientupdate(client_nickname=nickname)
    except ts3.query.TS3QueryError:  # Get random numeric nicknames just in case your desired nickname is taken
        keep_trying = True
        while keep_trying == True:
            try:
                ts3conn.clientupdate(client_nickname=nickname + str(sample(range(100), 1))[1:-1])
                keep_trying = False
                break
            except:
                print(str(datetime.datetime.now())[:19]+" Name Taken, I will use Another.")
                continue
    my_own_info = get_my_data()
    move_user_to_channel(my_channel, my_own_info["client_id"], channel_password)
    my_name = my_own_info["client_nickname"] #update this, just in case the name was taken and changed
    subscribe_to_event("server", None)
    subscribe_to_event("textchannel", my_channel)
    subscribe_to_event("channel", my_channel)
    subscribe_to_event("textprivate", None)
    print("--- Bot started. Now I'm monitorizing channel: "+channel_to_join+" ---")
    if not welcome_message == "":
        send_text_to_channel(my_channel, welcome_message)
    #Create Main Loop
    while True:
        ts3conn.send_keepalive() 
        try:
            event = ts3conn.wait_for_event(timeout=550) #Send a message each X seconds or the bot will disconnect due to inactivity at 600 seconds
        except ts3.query.TS3TimeoutError:
            print("TIMED OUT")
        else:
            event_handler(event)
        
#################
# TS3 Commandss #
#################
def get_my_data():
    answer_from_server = ts3conn.whoami()
    return answer_from_server.parsed[0]
    
def get_channel_id(name):
    answer_from_server = ts3conn.channelfind(pattern=ts3.escape.TS3Escape.unescape(name))
    return answer_from_server.parsed[0]["cid"]
        
def move_user_to_channel(channel_id, user_id, channel_password=None):
    ts3conn.clientmove(cid=channel_id, clid=user_id, cpw=channel_password)

def subscribe_to_event(event_type, channel_id):
    if channel_id == None:
        ts3conn.servernotifyregister(event=event_type)
    else:
        ts3conn.servernotifyregister(event=event_type, id_=channel_id)

def get_all_users(): 
    answer_from_server = ts3conn.clientlist()
    return answer_from_server

def get_channels_list():
    answer_from_server = ts3conn.channellist(secondsempty=True)
    return answer_from_server.parsed
    
def send_poke(clientid, message):
    ts3conn.clientpoke(msg=message, clid=clientid)
    
def get_channel_info(channel_id):
    answer_from_server = ts3conn.channelinfo(cid=channel_id)
    return answer_from_server

def get_client_info(clientid):
    answer_from_server = ts3conn.clientinfo(clid=clientid)
    return answer_from_server

def get_database_id(userid):
    answer_from_server = get_client_info(userid).parsed[0]['client_database_id']
    return answer_from_server

def get_database_info(clientdbid):
    answer_from_server = ts3conn.clientdbinfo(cldbid=clientdbid)
    return answer_from_server

def add_to_group(group_id, client_dbid):
    ts3conn.servergroupaddclient(sgid=group_id, cldbid=client_dbid)

def delete_from_group(group_id, client_dbid):
    ts3conn.servergroupdelclient(sgid=group_id, cldbid=client_dbid)

def change_description(iduser, new_value):
    ts3conn.clientedit(clid=iduser, client_description=new_value)

def send_text_to_channel(channel_id, message, color="purple"):
    if len(message) < 950:
        ts3conn.sendtextmessage(targetmode=2, target=channel_id, msg="[color="+color+"]"+message+"[/color]")
    else: 
        parts = too_much_letters(message)
        for i in parts:
            while i.startswith("[/"): #TBD this needs to be done better to catch up broken formatting bugs
                i = i.split("]",1)[1]
            ts3conn.sendtextmessage(targetmode=2, target=channel_id, msg=i)
    
def send_text_to_user(userid, message, color="purple"):
    ts3conn.sendtextmessage(targetmode=1, target=userid, msg="[color="+color+"]"+message+"[/color]")

####################
# Common functions #
####################

def too_much_letters(big_text):
    return textwrap.wrap(big_text, 950)

def get_command(message):
    divided_message = message.split(" ",1)
    if len(divided_message) > 1:
        text_after_command = divided_message[1]
    else:
        text_after_command = ""
    return divided_message[0], text_after_command

def resubscribe_to_everything():
    ts3conn.servernotifyunregister()
    subscribe_to_event("server", None)
    subscribe_to_event("textchannel", my_channel)
    subscribe_to_event("channel", my_channel)
    subscribe_to_event("textprivate", None)

def check_if_superadmin(userid):
    user_database_id = get_database_id(userid)
    if user_database_id in super_admins:
        return True
    else:
        return False
    
def check_if_admin(user, userid, command):
    user_data = get_client_info(userid)
    user_servergroups = user_data[0]["client_servergroups"].split(",")
    is_admin = False
    for i in user_servergroups:
        if i in admins_groups_ids:
            is_admin = True
            break
    if is_admin == True:
        return True
    else:
        send_text_to_channel(my_channel, "No tienes permisos para usar el comando [/color][color=green]"+command+"[/color][color=red], "+user, "red")
        return False

def parse_time_in_hours(unparsed_time):
    try:
        if int(unparsed_time) > 60:
            minutes = int(unparsed_time) / 60
            minutes = int(minutes)
            if int(minutes) > 60:
                hours = int(minutes) / 60
                hours = int(hours)
                unparsed_time = str(hours)+" horas"
            else:
                unparsed_time = str(minutes)+" minutos"
        else:
            unparsed_time = unparsed_time+" segundos"
        return unparsed_time
    except ValueError:
        return "Error"

def parse_time_in_days(unparsed_time):
    unparsed_time = ((int(time.time()) - int(unparsed_time)) / 3600) /24
    unparsed_time = int(unparsed_time)
    if unparsed_time < 2:
        return "menos de dos días"
    else:
        return str(unparsed_time) + " días"
        
def parse_ip(ip):
    s = str(request.urlopen("http://ip-api.com/json/"+ip).read())
    region = web_scrap(s, ',"regionName":"', '","')
    town = web_scrap(s, ',"city":"', '","')
    country = web_scrap(s, '"country":"', '","')
    if country == "": #just in case
        return "Error de localización."
    else:
        return town.replace("\xf1","ñ")+" ("+region+", "+country+")"

def get_target_nicknames(uniqueid, target_ip):
    nicknames_list = []
    with open("databases/localusers.txt", 'r') as readingnicks:
        for line in readingnicks:
            line_loaded = json.loads(line)
            if line_loaded[0] == uniqueid:
                nicknames_list.append("[b]"+line_loaded[1]+"[/b] (Coincide por UniqueID)")
            elif line_loaded[6] == target_ip:
                nicknames_list.append("[b]"+line_loaded[1]+"[/b] (Coincide por IP)")
        readingnicks.close()
    if len(nicknames_list) > 1:
        return ", ".join(nicknames_list)
    else:
        return "[color=red][b]Ninguno[/b][/color]"

def capture_user_data(event):
    try:
        user_database_id = event.parsed[0]['client_database_id']
        user_name = event.parsed[0]['client_nickname']
        user_uniqueid = event.parsed[0]['client_unique_identifier']
        user_description = event.parsed[0]['client_description']
        user_groups = event.parsed[0]['client_servergroups']
        user_channel = event.parsed[0]['ctid']
        save_time = str(datetime.datetime.now())[:19]
        user_ip = get_client_info(event.parsed[0]['clid'])[0]['connection_client_ip']
    except Exception as e:
        print("Error for the programmer: "+str(e)+" ------ en:"+str(event.parsed))
    else:
        if not "from 127.0.0.1" in user_name: #TBD this is to whitelist localhost bots, must find a better way
            data = []
            user_exists = False
            with open("databases/localusers.txt", 'r+') as f:
                for line in f:
                    data_line = json.loads(line)
                    if data_line[0] == user_uniqueid:
                        if data_line[1] == user_name:
                            data_line[0] = user_uniqueid
                            data_line[1] = user_name
                            data_line[2] = user_database_id
                            data_line[3] = user_description
                            data_line[4] = user_groups
                            data_line[5] = user_channel
                            data_line[6] = user_ip
                            data_line[7] = save_time
                            user_exists = True
                    data.append(data_line)
                f.seek(0)
                f.writelines(["%s\n" % json.dumps(i) for i in data])
                f.truncate()
                f.close()
            if user_exists == False:
                writing = open("databases/localusers.txt", 'a')
                writing.write(json.dumps([user_uniqueid, user_name, user_database_id, user_description, user_groups, user_channel, user_ip, save_time])+"\n")
                writing.close()

def get_users_in_channel():
    requested_data = get_all_users()
    users_in_channel = []
    for i in requested_data:
        if i["cid"] == my_channel:
            if not i["client_nickname"] == my_name: #As usual, we ignore the bot
                users_in_channel.append(i["client_nickname"])
    return users_in_channel

def get_target_id(text_after_command):
    try: #catch serverqueries error
        requested_data = ts3conn.clientfind(pattern=text_after_command)
        target_id = requested_data[0]["clid"] 
    except:
        target_id = "Error"
    return target_id

def enable_bot(event):
    global bot_disabled
    user = event.parsed[0]['invokername']
    message = event.parsed[0]['msg']
    targetmode = event.parsed[0]['targetmode']
    userid = event.parsed[0]['invokerid']
    if targetmode == "2":
        command = get_command(message)[0]
        if check_if_admin(user, userid, command) == True:
            if command == "!enciendete":
                bot_disabled = False
                send_text_to_channel(my_channel, "[b]BOT ENCENDIDO[/b]", "green")
                
def get_description(userid):
    return get_client_info(userid).parsed[0]['client_description']

def characters_regex(text_after_command):
    weird_character = False
    for i in text_after_command:
        if not re.match("[a-zA-Z0-9 ïäëöüËÏÜÖÄáéíúóÁÉÍÓÚÀÈÌÒÙàèìòùñÑ]", i):
            weird_character = True
            break
    return weird_character

def web_scrap(text, start, end):
    _,_,rest = text.partition(start)
    result,_,_ = rest.partition(end)
    return result

#################
# Handle events #
#################

def event_handler(event):
    global nickname
    event_type = event.event
    if bot_disabled == False:
        if event_type == "notifytextmessage":
            is_a_bot = event.parsed[0]['invokername'].startswith(nickname)
            if not is_a_bot:
                messages_handler(event)
        elif event_type == "notifyclientleftview":
            leaves_server(event)
        elif event_type == "notifycliententerview":
            joins_server(event)
        elif event_type == "notifyclientmoved":
            someone_moves_in_or_out_from_channel(event)
        elif event_type == "notifychanneledited":
            channel_edited(event)
        elif event_type == "notifychanneldescriptionchanged":
            pass #TBD it's handled inside channel_edited
        else:
            send_text_to_channel(my_channel, "ERROR: EVENTO DESCONOCIDO - "+event_type, "red")
    else:
        if event_type == "notifytextmessage":
            enable_bot(event)

def channel_edited(event):
    try: 
        user = event.parsed[0]['invokername']
        channel_name = event.parsed[0]['channel_name']
    except KeyError: #TBD need to find a better way to do this, because the server sends a double event if the description is changed.
        channel_description_changed(event) 

def channel_description_changed(event):
    pass

def joins_server(event):
    if my_name == nickname: #Only 1 bot instance runs this code.
        capture_user_data(event)

def leaves_server(event):
    if event[0]['cfid']:
        leaves_channel(event)

def someone_moves_in_or_out_from_channel(event):
    if event[0]['ctid'] == my_channel:
        joins_channel(event)
    else:
        leaves_channel(event)

def joins_channel(event):
    pass

def leaves_channel(event):
    if event[0]['clid'] in channel_signed_users:
        signed_user_leaves_channel(event[0]['clid'])

def signed_user_leaves_channel(clid):
    global channel_signed_users
    deleted = channel_signed_users.pop(clid, None)
    send_text_to_channel(my_channel, "[b]"+deleted[1]+"[/b] eliminado como taxi porque [color=green]"+deleted[0]+"[/color] se ha ido del canal.", "red")
    
def messages_handler(event):
    try:
        user = event.parsed[0]['invokername']
        message = event.parsed[0]['msg']
        targetmode = event.parsed[0]['targetmode']
        userid = event.parsed[0]['invokerid']
        uniqueid = event.parsed[0]['invokeruid']
    except KeyError:
        send_text_to_channel(my_channel, "Error trying to get your message data.", "red")
    else:
        time.sleep(0.3) #This delay is to prevent an issue in the chat where the bot would appear that answers before you send a command.
        if targetmode == "1":
            private_message_handler(user, message, userid, uniqueid)
        elif targetmode == "2":
            channel_message_handler(user, message, userid, uniqueid)

def private_message_handler(user, message, userid, uniqueid):
    message_divided = get_command(message)
    command =  message_divided[0]
    text_after_command =  message_divided[1]
    time.sleep(0.2) #This delay is to prevent an issue in the chat where the bot would appear that answers before you send a command.
    if command.lower() == "!say":
        command_say(userid, text_after_command)
    elif command.lower() == "!ignorame":
        command_ignore(userid, text_after_command)
    elif command.lower() == "!avisame":
        command_avisame(userid, text_after_command)
    elif command.lower() == "!api":
        api_store_key(text_after_command, userid, uniqueid)
    elif command.lower() == "!asocia":
        command_asocia(text_after_command, userid)
    else:
        send_text_to_user(userid, "[b]Error: Eso no es un comando valido.[/b] \nEstás hablando por privado a un robot programado para ayudar a este TeamSpeak, "
                    +"si tienes alguna duda ponte en contacto con mi creador [color=green]Aens[/color] que suele estar en los canales de su clan YOLO", "red")

def channel_message_handler(user, message, userid, uniqueid):
    message_divided = get_command(message)
    command =  message_divided[0]
    text_after_command =  message_divided[1]

    #SuperAdmin Permissions required
    if command == "!test":
        command_test(user, text_after_command, userid, uniqueid)
    elif command == "!patchday": 
        command_patchday(text_after_command, userid)
    elif command == "!clon": 
        command_clone(text_after_command, userid)
    elif command == "!actualizarbot":
    	command_botupdate(userid)

    #Admin Permissions required
    elif command == "!global": 
        command_global(user, text_after_command, userid, command)
    elif command == "!track": 
        command_track(user, text_after_command, userid, command)
    elif command == "!entra": 
        command_entra(user, text_after_command, userid, command)
    elif command == "!mueve": 
        command_mueve(user, text_after_command, userid, command)
    elif command == "!trae": 
        command_trae(user, text_after_command, userid, command)
    elif command == "!apagate": 
        command_apagate(user, userid, command)
    elif command == "!devtracker": 
        command_devtracker(user, text_after_command, userid, command)
        
    #These don't require permissions
    elif command == "!version": 
        command_version()
    elif command == "!cuentacanales": 
        command_cuentacanales()
    elif command == "!wiki": 
        command_wiki(text_after_command)
    elif command == "!tiempo": 
        command_tiempo()
    elif command == "!userinfo": 
        command_userinfo(user, userid, uniqueid)
    elif command == "!rng": 
        command_rng()
    elif command == "!drop": 
        command_drop(user)
    elif command == "!copia": 
        command_copia(user, text_after_command, uniqueid)
    elif command == "!pega": 
        command_pega(user, text_after_command)
    elif command == "!claves": 
        command_claves()
    elif command == "!borra": 
        command_borra(user, text_after_command, uniqueid)
    elif command == "!api": 
        command_api(user, text_after_command, userid, uniqueid)
    elif command == "!busca": 
        command_busca(text_after_command)
    elif command == "!grupos": 
        command_grupos(user, userid)
    elif command == "!potato": 
        command_potato(user)
    elif command == "!ayuda": 
        command_ayuda()
    elif command == "!youtube": 
        command_youtube(user, text_after_command)
    elif command == "!bot": 
        command_bot(user, text_after_command, userid, uniqueid)
    elif command == "!calcula": 
        command_calcula(text_after_command)
    elif command == "!sierpes": 
        command_sierpes(user, text_after_command, userid, uniqueid)
    elif command == "!kick":
        command_kick(user, text_after_command, userid, uniqueid)
    elif command == "+taxi": 
        command_plustaxi(user, text_after_command, userid)
    elif command == "-taxi": 
        command_minustaxi(user, userid)
    elif command == "taxi": 
        command_taxies()
    elif command == "!recuento": 
        command_recuento(text_after_command)
    elif poll_status == True: 
        if_poll_is_active(user, uniqueid, command)

############
# Commands #
############

def command_sierpes(user, text_after_command, userid, uniqueid):
    send_text_to_channel(my_channel, "Error: Comando sin programar, requiere de planificación.", "red")
    #TBD To be Done

def command_bot(user, text_after_command, userid, uniqueid):
    send_text_to_channel(my_channel, "Error: No tengo inteligencia artificial todavía, soy un potato.", "red")
    #TBD long-term project, AI for the bot to answer common questions.

def readable_formatting(text):
    result = text.replace("<p>", "").replace("</p>", "").replace("</div>", "")
    return result

def command_devtracker(user, text_after_command, userid, command):
    if check_if_admin(user, userid, command) == True:
        if len(text_after_command) == 1 and text_after_command.startswith(("1", "2", "3", "4", "5", "6", "7", "8", "9")):
            send_text_to_channel(my_channel, "Un momento, por favor...")
            webpage_url = "https://forum-en.guildwars2.com/forum/info/devtracker"
            webpage_request = request.urlopen(webpage_url)
            status_code = webpage_request.getcode()
            if status_code == 200:
                list_of_posts = []
                html = BeautifulSoup(webpage_request, "html.parser")
                posts = html.find_all('div',{'class':'arenanet post'})
                for i,post in enumerate(posts):
                    author = post.find('a', {'class' : 'member arenanet'}).getText()
                    date = post.find('time', {'class' : 'changeabletime'}).getText()
                    content = post.find('div', {'class' : 'message-content'}).getText()
                    if len(list_of_posts) < int(text_after_command):
                        list_of_posts.append("[b]"+date+" - "+author+"[/b]"+content)
                for i in list_of_posts:
                    send_text_to_channel(my_channel, i)
            else:
                send_text_to_channel(my_channel, "Error: Status Code: " + str(status_code), "red")
        else:
            send_text_to_channel(my_channel, "Error: Parametro no valido, escribe del 1 al 9 cuantos posts quieres que lea. Ejemplo: !devtracker 4", "red")

def command_botupdate(userid):
    if check_if_superadmin(userid):
        send_text_to_channel(my_channel, "Actualizando BOT")
        try:
            subprocess.call(["./bot_update.sh", str(INSTALLED_VERSION)])
        except Exception as e:
            send_text_to_channel(my_channel, "[b]Error:[/b] "+str(e), "red")
        else:
            send_text_to_channel(my_channel, "No hay actualización disponible") #If reach this line, there is no update available.

def command_kick(user, text_after_command, userid, uniqueid):
    global kicker_on_cooldown
    if kicker_on_cooldown == uniqueid:
        send_text_to_channel(my_channel, "[b]Error:[/b] estás en cooldown,"+user+", no acepto más kicks tuyos.", "red")
    else:
        chance_of_backfire = sample(range(100), 1)[0]
        if chance_of_backfire > 50:
            kick_id = userid
        else:
            kick_id = get_target_id(text_after_command)
        try:
            target_info =  get_client_info(kick_id)
            target_channel = target_info.parsed[0]['cid']
            target_name = target_info.parsed[0]['client_nickname']
            if target_channel == my_channel:
                if target_name == my_name:
                    send_text_to_channel(my_channel, "No me voy a kickear a mi mismo, gilipollas xD", "red")
                elif userid == kick_id:
                    send_text_to_channel(my_channel, "No quiero, te echo a ti mismo :D")
                    ts3conn.clientkick(reasonid=4, reasonmsg="Uso el comando !kick contra "+target_name+" por petición de "+user, clid=kick_id)
                else:
                    ts3conn.clientkick(reasonid=4, reasonmsg="Uso el comando !kick contra "+target_name+" por petición de "+user, clid=kick_id)
                    send_text_to_channel(my_channel, "[b]"+target_name+"[/b] ha sido kickeado por el comando !kick de [b]"+user+"[/b]")
                kicker_on_cooldown = uniqueid
            else:
                send_text_to_channel(my_channel, "[b]Error:[/b] "+target_name+" no esta en el canal.", "red")
        except Exception as e:
            send_text_to_channel(my_channel, "[b]Error:[/b] "+str(e), "red")
        
def command_plustaxi(user, text_after_command, userid):
    global channel_signed_users
    description = get_description(userid)
    if description == "":
        send_text_to_user(userid, "[b]Error: Parece que no tienes ningún personaje asociado a este TeamSpeak.[/b] Si deseas asociar uno, escribeme: [/color][color=purple]!asocia tunombredepersonaje", "red")
    else:
        if not userid in channel_signed_users:
            channel_signed_users[userid] = [user, description]
            send_text_to_channel(my_channel, "[b]"+description+"[/b][/color][color=purple] añadido a la lista de Taxistas - [color=gray](personaje de "+user+").[/color]", "green")
        else:
            send_text_to_channel(my_channel, "[b]Error: [/b]"+user+", ya eres Taxista.", "red")

def command_minustaxi(user, userid):
    global channel_signed_users
    if userid in channel_signed_users:
        description_was = channel_signed_users[userid][1]
        channel_signed_users.pop(userid, None)
        send_text_to_channel(my_channel, "[b]"+description_was+"[/b][/color][color=purple] eliminado de la lista de Taxistas - [color=gray](personaje de "+user+").", "green")
    else:
        send_text_to_channel(my_channel, "[b]Error: [/b]"+user+", no eres Taxista.", "red")

def command_taxies():
    if channel_signed_users:
        list_of_taxies = []
        for i in channel_signed_users.values():
            list_of_taxies.append(i[1])
        send_text_to_channel(my_channel, "\n[b]Escribe alguno de estos comandos en el chat del juego para unirte a esas personas:[/b] [/color]\n[color=green]/squadjoin "
                             +"\n /squadjoin ".join(list_of_taxies)
                             +"\n[/color][color=purple]El comando [b]/squadjoin[/b] sirve para unirse a escuadras, si la persona a la que te quieres unir no está en una escuadra, utiliza [b]/join[/b].")
    else:
        send_text_to_channel(my_channel, "Lo siento, no he encontrado Taxistas disponibles.", "red")

def command_asocia(text_after_command, userid):
    if text_after_command == "":
        send_text_to_user(userid, "[b]Error: [/b]"+usuario+", has olvidado decirme el nombre del personaje.", "red")
    else:
        if characters_regex(text_after_command) == False:
            try:
                change_description(userid, text_after_command)
            except Exception as e:
                send_text_to_user(userid, "Error inesperado: "+str(e), "red")
            else:
                send_text_to_user(userid, "Exito: [/color][color=green]"+text_after_command+"[/color][color=purple] ha sido asociado a tu cuenta de TeamSpeak. Puedes cambiarlo siempre que quieras, ya conoces el proceso.")
        else:
            send_text_to_user(userid, "No admito alguno de esos simbolos raros")
            
def command_clone(text_after_command, userid):
    if check_if_superadmin(userid) == True:
        if not text_after_command == "":
            try:
                channel_id = get_channel_id(text_after_command)
            except Exception as e:
                send_text_to_channel(my_channel, "[b]No encuentro ningún canal llamado así:[/b] "+str(e), "red")
            else:
                subprocess.Popen(["python3.4", sys.argv[0], text_after_command])
                send_text_to_channel(my_channel, "[b]Clon creado con exito en el canal con ID[/b] "+str(channel_id))

def command_calcula(text_after_command):
    if text_after_command == "":
        send_text_to_channel(my_channel, "Error: Tienes que decirme qué calcular", "red")
    else:
        if "**" in text_after_command:
            send_text_to_channel(my_channel, "Error: No se admiten dobles asteriscos, que peto por falta de memoria xD.", "red")
        elif "[" in text_after_command:
            send_text_to_channel(my_channel, "Error: No se admiten calculos de listas con corchetes [].", "red")        
        else:
            weird_character = False
            for i in text_after_command:
                if re.match("[a-zA-Z]", i):
                    weird_character = True
                    break
            if weird_character == False:
                try:
                    result = eval(text_after_command)
                except Exception as e:
                    result = "Error: "+str(e)
                send_text_to_channel(my_channel, "[b]Resultado:[/b] "+str(result))
            else:
                send_text_to_channel(my_channel, "Error: No se admiten letras.", "red")

def command_apagate(user, text_after_command, userid, command):
    global bot_disabled
    if check_if_admin(user, userid, command) == True:
        bot_disabled = True
        send_text_to_channel(my_channel, "[b]BOT APAGADO[/b]", "red")

def command_youtube(user, text_after_command):
    if text_after_command == "":
        send_text_to_channel(my_channel, "Error, "+user+": Tienes que decirme qué buscar.", "red")
    else:
        webpage_url = "http://www.youtube.com/results?search_query=" + text_after_command.replace(" ","+")
        webpage_url = urllib.parse.quote(webpage_url, safe='/:?+=', encoding="utf-8", errors="strict")
        webpage_request = request.urlopen(webpage_url)
        status_code = webpage_request.getcode()
        if status_code == 200:
            list_of_videos = []
            html = BeautifulSoup(webpage_request, "html.parser")
            videos = html.find_all('div',{'class':'yt-lockup-content'})
            for i,video in enumerate(videos):
                if len(list_of_videos) < 5:
                    title = video.find('a')['title']
                    lenght = video.find('span', {'class' : 'accessible-description'}).getText()
                    link = video.find('a')['href']
                    formatted_text = link = "[url=http://www.youtube.com" + link + "]"+title+"[/url]"+lenght
                    list_of_videos.append(formatted_text)
            send_text_to_channel(my_channel, "[b]Buscando [/b][/color][color=green][b]"+text_after_command+"[/b][/color][color=purple][b] en Youtube he encontrado esto:\n"+ "\n".join(list_of_videos))
        else:
            send_text_to_channel(my_channel, "Error: Status Code: " + str(status_code), "red")

def command_patchday(text_after_command, userid):
    if check_if_superadmin(userid):
        ###Read old Database
        send_text_to_channel(my_channel, "[b]Leyendo base de datos local desactualizada.[/b]")
        reading = open("databases/api_items_database.txt", 'r')
        old_database = reading.read()[1:-1]
        reading.close()
        old_database = old_database.split(',')
        if not len(old_database) == 1:
            old_database = [int(i) for i in old_database]
        ###Read new Database
        send_text_to_channel(my_channel, "[b]Leyendo base de datos de Anet.[/b]")
        web_reading = request.urlopen("https://api.guildwars2.com/v2/items").read().decode('utf8')
        new_database = json.loads(web_reading)
        ###Find differences
        send_text_to_channel(my_channel, "[b]Comparando datos.[/b]")
        differences = set(new_database) - set(old_database)
        differences = list(differences)
        list.sort(differences)
        send_text_to_channel(my_channel, str(len(differences))+"[/color] [color=purple][b]diferencias encontradas.[/b]", "green")
        ###Try to make it readable
        send_text_to_channel(my_channel, "[b]Generando codigos.[/b]")
        for i in differences:
            web_reading = request.urlopen("https://api.guildwars2.com/v2/items/"+str(i)+"?lang=es").read().decode('utf8')
            this_item = json.loads(web_reading)
            send_text_to_channel(my_channel, this_item['chat_link']+" - "+this_item['name']+"[/color][color=purple] - Icono: [url="+this_item['icon']+
                                   "]Icono[/url] - Web: [url=https://api.guildwars2.com/v2/items/"+str(i)+"]https://api.guildwars2.com/v2/items/"+str(i)+"[/url]", "green")
        ###Update local(old) Database
        if "update" in text_after_command:
            send_text_to_channel(my_channel, "[b]Actualizando base de datos local.")
            with open('databases/api_items_database.txt', 'w') as local_file:
                json.dump(new_database, local_file)
            send_text_to_channel(my_channel, "[b]Base de datos actualizada.[/b]")
        send_text_to_channel(my_channel, "[b]Comando Finalizado.[/b]")              
    
def command_ayuda():
    send_text_to_channel(my_channel, "Todo mi funcionamiento está en el foro: "
                         +"[url=http://www.guildwars2-spain.com/foro/comunidad/37402-bot-o-tron-nuestro-bot-del-teamspeak]Click Aqui[/url]. "
                         +"(Si necesitas ayuda, postea allí)")

def command_track(user, text_after_command, userid, command):
    if check_if_admin(user, userid, command) == True: #TBD clean some code
        if text_after_command == "":
            send_text_to_channel(my_channel, "Error: No me has dicho a quien.", "red")
        else:
            try:
                found = False
                requested_data = ts3conn.clientfind(pattern=text_after_command)
                if len(requested_data) == 1:
                    found = True
                else:
                    for i in requested_data:
                        if i["client_nickname"].lower() == text_after_command.lower():
                            requested_data = i
                            found = True
                            break
            except:
                send_text_to_channel(my_channel, "Error: No encuentro a nadie con esa busqueda.", "red")
            else:
                if found == False:
                    send_text_to_channel(my_channel, "Error: Aparecen varias personas con esa busqueda, dime el nombre [u]exactamente[/u].", "red")
                else:
                    try:
                        target_id = requested_data[0]["clid"] #catch serverqueries error 
                        requested_data = get_client_info(target_id)
                    except:
                        send_text_to_channel(my_channel, "Error: No he logrado obtener información del usuario.", "red")
                    else:
                        target_age = parse_time_in_days(requested_data[0]["client_created"])
                        target_uniqueid = requested_data[0]["client_unique_identifier"]
                        target_system = requested_data[0]["client_platform"]
                        target_connections = requested_data[0]["client_totalconnections"]
                        target_database_id = requested_data[0]["client_database_id"]
                        target_name = requested_data[0]["client_nickname"]
                        target_online = parse_time_in_hours(str(requested_data[0]['connection_connected_time'])[:-3])
                        target_ip = requested_data[0]['connection_client_ip']
                        target_geolocalization = parse_ip(target_ip)
                        target_nicknames = get_target_nicknames(target_uniqueid, target_ip)
                        send_text_to_channel(my_channel, "Okay \n La ID de [color=red][b]"+target_name+"[/b][/color] es [color=red][b]"+target_id+"[/b][/color].\n"+
                        "Su UniqueId es [b][color=red]"+target_uniqueid+"[/color][/b] y la DatabaseID es [b][color=red]"+target_database_id+"[/color][/b].\n "+
                        "Entró por primera vez hace [color=red][b]"+target_age+"[/b][/color] y se ha conectado [color=red][b]"+target_connections+"[/b][/color] veces a este TeamSpeak. \n"+
                        "Está usando [b][color=red]"+target_system+"[/color][/b] y lleva [b][color=red]"+target_online+"[/color][/b] conectado/a \n "+
                        "Su IP es [b][color=green]"+target_ip+"[/color][/b] y le he localizado en [b][color=green]"+target_geolocalization+"[/color][/b]\n "+
                        "Otros nicks que ha usado son: [color=blue]"+target_nicknames+"[/color]")

def command_say(userid, text_after_command):
    if check_if_superadmin(userid) == True:
        send_text_to_channel(my_channel, text_after_command)
    else:
        send_text_to_user(userid, "[b]Error: No tienes permiso para usar ese comando.", "red")
        
def command_ignore(userid, text_after_command):
    user_data = get_client_info(userid)
    user_servergroups = user_data[0]["client_servergroups"].split(",")
    user_database_id = user_data[0]["client_database_id"]
    if ignore_group_id in user_servergroups:
        send_text_to_user(userid, "[b]Error: [/b]Ya estas añadido a la lista de ignorados del bot.", "red")
    else:
        add_to_group(ignore_group_id, user_database_id)
        send_text_to_user(userid, "[b]Hecho:[/b] A partir de ahora intentaré no molestarte.")

def command_avisame(userid, text_after_command):
    user_data = get_client_info(userid)
    user_servergroups = user_data[0]["client_servergroups"].split(",")
    user_database_id = user_data[0]["client_database_id"]
    if ignore_group_id in user_servergroups:
        delete_from_group(ignore_group_id, user_database_id)
        send_text_to_user(userid, "[b]Hecho:[/b] A partir de ahora recibirás mensajes mios.")
    else:
        send_text_to_user(userid, "[b]Error: [/b]No estás en la lista de ignorados del bot.", "red")

def command_global(user, text_after_command, userid, command):
    if check_if_admin(user, userid, command) == True:
        send_text_to_channel(my_channel, "[b]Vale, avisando a todo el servidor...[/b]")
        count_yes = count_no = 0
        requested_data = ts3conn.clientlist(groups=True)
        for i in requested_data:
            if not i["client_nickname"].startswith(nickname): #if it's not a bot instance (very important to not mess up your bots)
                user_groups = i["client_servergroups"].split(",")
                if ignore_group_id in user_groups:
                    count_no = count_no + 1
                else:
                    sender_text = " [/color][color=gray]- Este ha sido un mensaje enviado por [b]"+user+"[/b]. Si no quieres recibir mensajes de este bot, escribe: !ignorame"
                    try:
                        send_text_to_user(i["clid"], text_after_command + sender_text)
                        count_yes = count_yes + 1
                    except ts3.query.TS3QueryError:
                        send_text_to_channel(my_channel, "ERROR al intentar enviar mensaje a:" +str(i), "red")
        send_text_to_channel(my_channel, "[b]He avisado a [/b][/color][color=blue][b]"+str(count_yes)+" personas[/b][/color] - [color=gray]("+str(count_no)+" personas no quieren avisos)")

def command_mueve(user, text_after_command, userid, command):
    if check_if_admin(user, userid, command) == True:
        send_text_to_channel(my_channel, "Vale, os muevo.")
        try:
            target_channel = get_channel_id(text_after_command)
        except Exception as e:
            send_text_to_channel(my_channel, "[b]No encuentro ningún canal llamado así, o tiene contraseña:[/b] "+str(e), "red")
        else:
            requested_data = get_all_users()
            for i in requested_data:
                if not i["client_nickname"].startswith(nickname): #if it's not a bot instance (very important to not mess up your bots)
                    if i["cid"]: 
                        if my_channel == i["cid"]:
                            try:
                                move_user_to_channel(target_channel, i["clid"], "")
                            except:
                                send_text_to_channel(my_channel, "[b]Error, no he logrado mover a:[/b] "+i["client_nickname"], "red")
            resubscribe_to_everything()
            
def command_trae(user, text_after_command, userid, command):
    if check_if_admin(user, userid, command) == True:
        send_text_to_channel(my_channel, "De acuerdo, un momento...")
        try:
            target_channel = get_channel_id(text_after_command)
        except:
            send_text_to_channel(my_channel, "[b]Nombre de canal erroneo (no olvides tildes o mayusculas)[/b]", "red")
        else:
            requested_data = get_all_users()
            count = 0
            for i in requested_data:
                if i["cid"]:
                    if not i["client_nickname"].startswith(nickname): #if it's not a bot instance (very important to not mess up your bots)
                        if target_channel == i["cid"]:
                            try:
                                move_user_to_channel(my_channel, i["clid"])
                                count = count + 1
                            except:
                                send_text_to_channel(my_channel, "[b]Error, no he logrado mover a:[/b] "+i["client_nickname"], "red")
            send_text_to_channel(my_channel, "He traido a [b]"+str(count)+"[/b] personas del canal [b]"+text_after_command+"[/b] a petición de [b]"+user+"[/b]")

def command_entra(user, text_after_command, userid, command):
    global my_channel #it's needed to call it global to update it
    if check_if_admin(user, userid, command) == True:
        try:
            my_channel = get_channel_id(text_after_command)
            send_text_to_channel(my_channel, "[b]Me marcho al canal "+text_after_command+". ¡Nos vemos![/b]")
            my_own_id = get_my_data()["client_id"]
            move_user_to_channel(my_channel, my_own_id)
            send_text_to_channel(my_channel, "¡Hola!, [b]"+ user + "[/b] me acaba de pedir que entre en este canal :D")
        except Exception as e:
            send_text_to_channel(my_channel, "[b]No encuentro ningún canal llamado así, o tiene contraseña:[/b] "+str(e), "red")
        else:
            resubscribe_to_everything()

def command_grupos(user, userid):
    user_data = get_client_info(userid)
    user_servergroups = user_data[0]["client_servergroups"].split(",")
    servergroups_list = ts3conn.servergrouplist()
    user_servergroups_parsed = []
    for i in user_servergroups:
        for j in servergroups_list:
            if i == j["sgid"]:
                user_servergroups_parsed.append(i + ":" + j["name"])
    send_text_to_channel(my_channel, "[b]"+user+"[/b] tiene los grupos: [/color][color=green]"+", ".join(user_servergroups_parsed))
    
def command_borra(user, text_after_command, uniqueid):
    if text_after_command == "":
        send_text_to_channel(my_channel, "Error, "+user+": Tienes que decirme qué clave borrar.", "red")
    else:
        data = []
        with open("databases/personalsaves.txt", 'r+') as f:
            for line in f:
                data_line = json.loads(line)
                if data_line[3] == text_after_command: #if savename is found
                    if data_line[0] == uniqueid: #and uniqueid matches, don't save it (a trick to delete)
                        send_text_to_channel(my_channel, "[b]Texto de la clave [/b][/color][color=green]"+text_after_command+"[/color][color=purple][b] borrado[/b]")
                    else: #but if user doesn't matches, re-write that line again
                        data.append(data_line)
                        send_text_to_channel(my_channel, "Lo siento "+user+", pero no puedes borrar textos de otras personas. "+text_after_command+" pertenece a "+data_line[1]+".", "red")
                else:
                    data.append(data_line)
            f.seek(0)
            f.writelines(["%s\n" % json.dumps(i) for i in data])
            f.truncate()
            f.close()

def command_pega(user, text_after_command):
    if text_after_command == "":
        send_text_to_channel(my_channel, "Error, "+user+": Tienes que decirme qué pegar.", "red")
    else:
        found_text = found_time = "Error"
        with open("databases/personalsaves.txt", 'r') as readinglineas:
            for line in readinglineas:
                readingStats = json.loads(line)
                if readingStats[3] == text_after_command:
                    found_user = readingStats[1]
                    found_time = readingStats[2]
                    found_text = readingStats[4]
                    send_text_to_channel(my_channel, found_time+" - [b]"+found_user+"[/b]: [/color][color=green]"+found_text)
        if found_text == "Error":
            send_text_to_channel(my_channel, "Lo siento, no puedo encontrar esa clave (asegurate de que la has escrito bien)", "red")

def command_claves():
    list_of_savenames = []
    with open("databases/personalsaves.txt", 'r+') as f:
        for line in f:
            data_line = json.loads(line)
            list_of_savenames.append(data_line[3])
    list_of_savenames.sort()
    send_text_to_channel(my_channel, "[b]Lista de todos los textos guardados: [/b][/color][color=green]"+", ".join(list_of_savenames))

def command_copia(user, text_after_command, uniqueid):
    if not text_after_command == "":
        save_time = str(datetime.datetime.now())[:19]
        message_divided = get_command(text_after_command)
        savename =  message_divided[0]
        text_to_copy =  message_divided[1]
        if len(savename) < 21:
            if len(text_to_copy) < 900:
                if len(text_to_copy) > 1:
                    #open database
                    data = []
                    status = "not found"
                    with open("databases/personalsaves.txt", 'r+') as f:
                        for line in f:
                            data_line = json.loads(line)
                            if data_line[3] == savename: #if savename is found
                                if data_line[0] == uniqueid: #and same uniqueid
                                    data_line[0] = uniqueid
                                    data_line[1] = user
                                    data_line[2] = save_time
                                    data_line[3] = savename
                                    data_line[4] = text_to_copy
                                    status = "replaced"
                                else: #if is found but is wrong uniqueid
                                    status = "found but wrong user"
                                    send_text_to_channel(my_channel, "Lo siento, [b]"+user+"[/b], pero no puedes reemplazar textos de otra persona. [b]"+savename+"[/b] pertenece a [b]"+data_line[1]+"[/b].", "red")
                            data.append(data_line)
                        f.seek(0)
                        f.writelines(["%s\n" % json.dumps(i) for i in data])
                        f.truncate()
                        f.close()
                    if status == "not found": #if savename was never found
                        writing = open("databases/personalsaves.txt", 'a')
                        writing.write(json.dumps([uniqueid, user, save_time, savename, text_to_copy])+"\n")
                        writing.close()
                    if not status == "found but wrong user":
                        send_text_to_channel(my_channel, "Tu texto ha sido guardado, [b]"+user+"[/b], puedes pegarlo usando el comando:[/color][color=green] !pega "+savename+"")
                else:
                    send_text_to_channel(my_channel, "Error: Tienes que decirme qué copiar", "red")
            else:
                send_text_to_channel(my_channel, "Error: El texto no puede ser tan largo.", "red")
        else:
            send_text_to_channel(my_channel, "Error: La clave no puede ser tan larga.", "red")
    else:
        send_text_to_channel(my_channel, "Error, "+user+": Tienes que decirme un nombre clave con el que guardar el texto, y tras eso el texto.", "red")

def command_test(user, text_after_command, userid, uniqueid):
    global super_admins #To allow a super_admin to add or remove other superadmins without resetting the bot. Delete this line if you don't want the risk of being removed as superadmin
    if check_if_superadmin(userid) == True:
        try:
            message_result = eval(text_after_command)
        except NameError:
            message_result = "[color=red]Error: esa variable no existe.[/color]"
        except TypeError:
            message_result = "[color=red]Error de Tipo, el resultado no es una string - Crash evitado.[/color]"
        except SyntaxError:
            message_result = "[color=red]Error de sintaxis,[/color] "+user
        except UnboundLocalError:
            message_result = "[color=red]UnboundLocallError O,o ¿WTF? ¿referencia a una variable que no existe?[/color]"
        except ValueError as e:
            message_result = "[color=red]Error de valor, algo falla ahí.[/color]"
        except IndexError:
            message_result = "[color=red]Error, ese item no existe en esa lista.[/color]"
        except AttributeError:
            message_result = "[color=red]Ese atributo no existe.[/color]"
        except KeyError:
            message_result = "[color=red]Esa Key no existe.[/color]"
        except ZeroDivisionError:
            message_result = "[color=red]No voy a dividir por cero ¬¬[/color]"
        except ts3.query.TS3QueryError as e:
            message_result = "[color=red]Error de TeamSpeak:[/color][color=green "+str(e)
        send_text_to_channel(my_channel, "Result: "+str(message_result))

def command_userinfo(user, userid, uniqueid):
    user_database_id = get_database_id(userid)
    send_text_to_channel(my_channel, "Vale, estos son tus datos:"
        +"\n[b]Nick: [/b][color=green]" + user
        +"\n[/color][b]User ID: [/b][color=green]" + userid
        +"\n[/color][b]Database ID: [/b][color=green]" + user_database_id
        +"\n[/color][b]Unique ID: [/b][color=green]" + uniqueid)

def command_tiempo():
    time_now = datetime.datetime.now()
    send_text_to_channel(my_channel, "Desde las [/color]"+str(start_time)[:19]
    +"(Hora del Servidor)[color=purple], llevo conectado [b][color=green]"+str(time_now - start_time)[:-7].replace("day", "día")
    +" [/color][/b]Horas/Minutos/Segundos.")

def command_version():
    send_text_to_channel(my_channel, "[b]Version {}: [/b]{}".format(INSTALLED_VERSION, VERSION_COMMENTS))

def command_rng():
    send_text_to_channel(my_channel, "Numero al azar: [b]" + str(sample(range(1000), 1))[1:-1] + "[/b]")

def command_wiki(text_after_command):
    if text_after_command == "":
        send_text_to_channel(my_channel, "[b]Error, no me has dicho qué buscar.[/b]", "red")
    else:
        text_after_command = text_after_command.replace(" ", "_")
        send_text_to_channel(my_channel, "[url=http://wiki.guildwars2.com/wiki/" + text_after_command + "]Enlace wiki al articulo ingles: [b]"+text_after_command+"[/b][/url]")

def command_potato(user):
    send_text_to_channel(my_channel, "[b]"+user+"[/b] tiene "+str(sample(range(101), 1))[1:-1]+" potatos.")

def command_cuentacanales():
    stored_channels = get_channels_list() 
    total_channels = 0
    for i in stored_channels:
        total_channels = total_channels + 1
    send_text_to_channel(my_channel, "Hay "+str(total_channels)+" canales.")

def command_drop(user):
    decto_number = sample(range(100), 1)[0] #The dectoplasm is an inside joke of the YOLO guild.
    if decto_number < 10:
        if not "Detouc" in user:
            send_text_to_channel(my_channel, "[b]"+user+"[/b], te ha salido el [/color][color=orange][b]Dectoplasma[/b]")
        else:
            send_text_to_channel(my_channel, "[b]"+user+"[/b], te ha salido [/color][color=gray][b]un Cofre vacio sin Dectoplasma[/b].")
    else:
        number_chosen = sample(range(10000), 1)[0]
        level = choice(["80", "79", "78", "77", "76"])
        weapons = choice(["Espada", "Mandoble", "Hacha", "Escudo", "Lanza", "Tridente", "Arco Largo", "Arco Corto", "Daga", "Foco", "Báculo", "Cuerno", "Maza", "Cetro", "Antorcha", "Martillo", "Cañón de Arpón", "Rifle", "Pistola"])
        if number_chosen < 2:
            weapon_chosen = "[color=purple][b]"+weapons+" Prelegendario[/b][/color][color=purple]. ¡QUÉ SUERTE!"
        elif number_chosen < 200:
            weapon_chosen = "[color=orange][b]"+weapons+" Exotico[/b][/color][color=purple] de nivel "+level+"."
        elif number_chosen < 2000:
            weapon_chosen = "[color=#BFB331][b]"+weapons+" Amarillo[/b][/color][color=purple] de nivel "+level+"."
        elif number_chosen < 6000:
            weapon_chosen = "[color=green][b]"+weapons+" Verde[/b][/color][color=purple] de nivel "+level+"."
        else:
            weapon_chosen = "[color=blue][b]"+weapons+" Azul[/b][/color][color=purple] de nivel "+level+"."
        send_text_to_channel(my_channel, "("+str(number_chosen * 100 / 10000)+"%)[/color][color=green] - [b]"+user+"[/b], te ha salido [/color]"+weapon_chosen)
        
def command_busca(text_after_command):
    if len(text_after_command) > 2:
        try:
            requested_data = ts3conn.clientfind(pattern=text_after_command)
        except Exception as e:
            requested_data = []
        finally:
            if len(requested_data) == 1:
                user_found = requested_data[0]["client_nickname"]
                user_data = get_client_info(requested_data[0]["clid"])
                user_channel_id = user_data[0]["cid"]
                channel_name = get_channel_info(user_channel_id).parsed[0]['channel_name']
                send_text_to_channel(my_channel, "He encontrado a [b]"+str(user_found)+"[/b] en el canal [b]"+channel_name+"[/b].")
            elif len(requested_data) > 1:
                users_found = []
                for i in requested_data:
                    users_found.append(i["client_nickname"])
                send_text_to_channel(my_channel, "He encontrado todos estos conectados: [b]"+str(users_found)[2:-2]+"[/b].")
            elif len(requested_data) == 0:
               send_text_to_channel(my_channel, "[b]No hay nadie conectado con esta busqueda:[/b] "+text_after_command+".", "red")
    else:
        send_text_to_channel(my_channel, "[b]Error: necesito más de 2 letras para buscar a alguien.[/b]", "red")
            
def command_api(user, text_after_command, userid, uniqueid):
    message_divided = get_command(text_after_command)
    option =  message_divided[0]
    option_data =  message_divided[1]
    if option == "guarda": 
        send_text_to_channel(my_channel, "Las APIs se deben guardar por privado para evitar que terceras personas puedan verla. Haz click en mi nombre y abreme una charla privada.", "red")
    else:
        api_key = read_api_key_from_database(uniqueid)
        if not api_key == "error":
            try:
                if option == "cartera":
                    api_wallet(api_key, user)
                elif option == "cuenta":
                    api_account(api_key)
                elif option == "personajes":
                    api_characters(api_key, user)
                elif option == "build":
                   api_build(api_key)
            except Exception as e:
                send_text_to_channel(my_channel, "[b]Imposible conseguir datos -[/b] Error: "+str(e), "red")
            
###################
# GW2 API related #
###################

def api_build(api_key):#TBD To be Done
    send_text_to_channel(my_channel, "Proximamente :D", "blue")

def api_characters(api_key, user):
    api_permissions_data = api_get_permissions(api_key)
    api_permissions = api_permissions_data["permissions"]
    if "characters" in api_permissions:
        send_text_to_channel(my_channel, "[b]Leyendo datos de tus personajes, [color=green]"+user+"[/color]...[/b]\n")
        webpage_stored = request.urlopen("https://api.guildwars2.com/v2/characters?access_token="+api_key).read().decode('utf8')
        api_characters_name = json.loads(webpage_stored)
        send_text_to_channel(my_channel, "[b]Personajes: [/b][color=green]"+", ".join(api_characters_name)+"[/color]")
        total_deaths = 0
        total_hours = 0
        for i in api_characters_name:
            webpage_stored = "https://api.guildwars2.com/v2/characters/"+i+"?access_token="+api_key
            webpage_stored = urllib.parse.quote(webpage_stored, safe='/:=', encoding="utf-8", errors="strict")
            webpage_stored = request.urlopen(webpage_stored).read().decode('utf8')
            this_character = json.loads(webpage_stored)
            #Localized texts
            GeneroPersonaje = this_character['gender'].replace("Male", "Masculino").replace("Female", "Femenino")
            RazaPersonaje = this_character['race'].replace("Human", "Humano")
            ProfesionPersonaje = this_character['profession'].replace("Elementalist", "Elementalista").replace("Mesmer", "Hipnotizador").replace("Guardian", "Guardián").replace("Necromancer", "Nigromante").replace("Thief", "Ladrón").replace("Warrior", "Guerrero").replace("Engineer", "Ingeniero").replace("Revenant", "Retornado").replace("Ranger", "Guardabosques")
            #deaths
            character_deaths = this_character['deaths']
            total_deaths = total_deaths + character_deaths
            #hours
            character_hours = (this_character['age'] / 60) / 60
            if character_hours < 1:
                character_hours = 1
            character_hours = int(character_hours)
            total_hours = total_hours + character_hours
            #send to chat
            send_text_to_channel(my_channel, "[b]"+this_character['name']+": [/b]"+RazaPersonaje+
                                 " ("+GeneroPersonaje+"), [/color][color=green]"+ProfesionPersonaje+" de nivel [b]"+str(this_character['level'])+"[/b][/color]"+
                                 " - [color=blue]Lo has jugado [b]"+str(character_hours)+"[/b] horas y lleva [b]"+
                                 str(character_deaths)+"[/b] Muertes[/color][color=gray] ([b]"+str(character_deaths / character_hours)[:4]+"[/b] cada hora)")
        send_text_to_channel(my_channel, "[b]No hay más personajes.[/b][/color] - [color=blue]Muertes en total: [b]"+str(total_deaths)+
                             "[/b]. Horas en total:[b] "+str(total_hours)+"[/b].[/color] - "+
                             "[color=gray]Tienes una media de [b]"+str(total_deaths / total_hours)[:4]+"[/b] muertes por hora.", "green")
    else:
        send_text_to_channel(my_channel, "[b]No tengo permiso para ver datos de personajes.[/b]", "red")

def api_wallet(api_key, user):
    api_permissions_data = api_get_permissions(api_key)
    api_permissions = api_permissions_data["permissions"]
    if "wallet" in api_permissions:
        send_text_to_channel(my_channel, "[b]Leyendo datos de tu cartera, [color=green]"+user+"[/color]...[/b]\n")
        webpage_stored = request.urlopen("https://api.guildwars2.com/v2/account/wallet?access_token="+api_key).read().decode('utf8')
        api_wallet = json.loads(webpage_stored)
        for i in api_wallet:
            webpage_stored = request.urlopen("https://api.guildwars2.com/v2/currencies/"+str(i['id'])+"?lang=es").read().decode('utf8')
            api_currency_type = json.loads(webpage_stored)
            if api_currency_type['name'] == "Moneda":
                i['value'] = i['value'] / 10000
                api_currency_type['name'] = "Oro"
            send_text_to_channel(my_channel, "[b]"+api_currency_type['name']+": [/b][/color][color=green]"+str(i['value']))
        send_text_to_channel(my_channel, "No hay más datos.", "green")
    else:
        api_without_permission(api_name)

def api_account(api_key):
    api_permissions_data = api_get_permissions(api_key)
    api_permissions = api_permissions_data["permissions"]
    api_name = api_permissions_data["name"]
    if "account" in api_permissions:
        webpage_stored = request.urlopen("https://api.guildwars2.com/v2/account?access_token="+api_key).read().decode('utf8')
        api_data = json.loads(webpage_stored)
        #fractal
        api_fractal_level = "[color=red]Error, falta el permiso Progression.[/color]"
        if "progression" in api_permissions:
            api_fractal_level = str(api_data['fractal_level'])
        #WvsW
        api_server = api_get_server(api_data['world'])
        #commander tag
        api_has_tag = "No"
        if api_data['commander'] == True:
            api_has_tag = "Sí"
        #account type
        api_account_type = api_data['access']
        #age
        api_age = api_data['created'][:-10]
        #envia los datos
        send_text_to_channel(my_channel, "\n[b]Nombre de cuenta: [/b][/color][color=green]"+api_data['name']+"[/color]"
                               +"\n[color=purple][b]Tipo de cuenta: [/b][/color][color=green]"+api_account_type+"[/color]"
                               +"\n[color=purple][b]Cuenta creada desde: [/b][/color][color=green]"+api_age+"[/color]"
                               +"\n[color=purple][b]Servidor de Mundo contra Mundo: [/b][/color][color=green]"+api_server+"[/color]"
                               +"\n[color=purple][b]Tiene chapa de Comandante: [/b][/color][color=green]"+api_has_tag+"[/color]"
                               +"\n[color=purple][b]Nivel de fractal Máximo: [/b][/color][color=green]"+api_fractal_level)
    else:
        api_without_permission(api_name)

def api_without_permission(api_name):
    send_text_to_channel(my_channel, "[b]Tu clave [/b]"+api_name+"[b] no puede acceder a esa información. Tendrás que crear una diferente.[/b] - Error: "+str(e), "red")
    
def api_get_permissions(api_key):
    webpage_stored = request.urlopen("https://api.guildwars2.com/v2/tokeninfo?access_token="+api_key).read().decode('utf8')
    return json.loads(webpage_stored)

def api_get_server(server_id):
    webpage_stored = request.urlopen("https://api.guildwars2.com/v2/worlds/"+str(server_id)+"?lang=es").read().decode('utf8')
    return json.loads(webpage_stored)["name"]

def api_store_key(key_submitted, userid, uniqueid):
    if not len(key_submitted) == 72:
        send_text_to_user(userid, "API no valida, "+str(len(key_submitted))+" caracteres. Deberían ser 72, asi que comprueba que la escribes bien, sin espacios al comienzo o al final.", "red")
    else:
        try:
            webpage_stored = request.urlopen("https://api.guildwars2.com/v2/tokeninfo?access_token="+key_submitted).read().decode('utf8')
            api_permissions = json.loads(webpage_stored)
        except Exception as e:
            send_text_to_user(userid, "[b]Api erronea, falla alguna letra[/b] - "+str(e), "red")
        else:
            send_text_to_user(userid, "Permisos de clave detectados: [/color][color=green]"+", ".join(api_permissions['permissions']))
            save_time = str(datetime.datetime.now())[:19]
            data = []
            user_exists = False
            with open("databases/apikeys.txt", 'r+') as f:
                for line in f:
                    data_line = json.loads(line)
                    if data_line[0] == uniqueid:
                        data_line[0] = uniqueid
                        data_line[1] = key_submitted
                        data_line[2] = save_time
                        user_exists = True
                    data.append(data_line)
                f.seek(0)
                f.writelines(["%s\n" % json.dumps(i) for i in data])
                f.truncate()
                f.close()
            if user_exists == False:
                writing = open("databases/apikeys.txt", 'a')
                writing.write(json.dumps([uniqueid, key_submitted, save_time])+"\n")
                writing.close()
            send_text_to_user(userid, "[b]Bien, tu clave API ha sido guardada en la base de datos.[/b]")
    
def read_api_key_from_database(uniqueid):
    api_key = "error"
    with open("databases/apikeys.txt", 'r') as f:
        for line in f:
            data_line = json.loads(line)
            if data_line[0] == uniqueid:
                api_key = data_line[1]
    f.close()
    if api_key == "error":
        send_text_to_channel(my_channel, "Error: no tienes ninguna clave API guardada en mi base de datos.", "red")
    return api_key

#########
# Polls #
#########

def command_recuento(text_after_command):
    options = text_after_command.split(" ")
    if options[0].lower() == "apagado":
        if poll_status == True:
            command_recuento_apagado()
        else:
            send_text_to_channel(my_channel, "[b]Error:[/b] El recuento no está activo.", "red")
    elif options[0].lower() == "resultado":
        if poll_status == True:
            command_recuento_resultado()
        else:
            send_text_to_channel(my_channel, "[b]Error:[/b] El recuento no está activo.", "red")
    elif len(options) > 1:
        if poll_status == True:
            send_text_to_channel(my_channel, "[b]Error:[/b] El recuento ya está activo.", "red")
        else:
            command_recuento_encendido(options)
    else:
        send_text_to_channel(my_channel, "[b]Error:[/b] Esas opciones no son validas", "red")

def command_recuento_encendido(options):
    global poll_status, poll_options
    if len(options) < 10:
        for i in options:
            if len(i) < 25:
                if not i in poll_options:
                    poll_options.append(i.lower())
                else:
                    send_text_to_channel(my_channel, "Aviso: La palabra [b]"+i+" [/b]queda ignorada porque está repetida.", "red")
            else:
                send_text_to_channel(my_channel, "Aviso: [b]"+i+"[/b] es una palabra demasiado larga, la ignoro.", "red")
        poll_status = True
        send_text_to_channel(my_channel, "[b]Recuento activado. Opciones disponibles: [/b][/color][color=green] "+", ".join(poll_options))
    else:
        send_text_to_channel(my_channel, "[b]Error: [/b]Solo se permiten menos de 10 opciones.", "red")

def command_recuento_apagado():
    global poll_status, poll_options, poll_results
    poll_status = False
    poll_results = []
    poll_options = []
    send_text_to_channel(my_channel, "[b]Vale, recuento borrado y desactivado.[/b]")

def command_recuento_resultado():
    for i in poll_options:
        count = 0
        option_users = []
        for j in poll_results:
            if j[0] == i:
                option_users.append(j[1])
                count = count + 1
        send_text_to_channel(my_channel, "[b]Recuento de[/b][/color] [color=green]"+i+":[/color] [color=blue]"+str(count)+"[/color] [color=gray] "+", ".join(option_users))
    send_text_to_channel(my_channel, "[b]Total: [/b][/color][color=blue]"+str(len(poll_results))+" votos.")
    users_in_channel = get_users_in_channel()
    users_unpolled = []
    for i in poll_results:
        if not i[1] in users_in_channel:
            users_unpolled.append(i[1])
    if len(users_unpolled) > 0:
        send_text_to_channel(my_channel, "[b]Estas personas aun no han votado: [/b][/color][color=brown]"+", ".join(users_unpolled)+".")

def if_poll_is_active(user, uniqueid, option):
    global poll_results
    if option.lower() in poll_options:
        user_found = False
        for i in poll_results:
            if uniqueid in i[2]:
                send_text_to_channel(my_channel, "Error: [b]"+user+"[/b], tu ya has votado.", "red")
                user_found = True
                break
        if user_found == False:
            poll_results.append((option, user, uniqueid))
            send_text_to_channel(my_channel, "[b]"+user+"[/b] vota la opción: [b]"+option+"[/b]", "green")
                                    
###############
# Initializer #
###############

def generate_database_files():
    #TBD Note: will fail if folder doesnt exists
    open('databases/apikeys.txt', 'a').close()
    open('databases/personalsaves.txt', 'a').close()
    open('databases/localusers.txt', 'a').close()
    open('databases/api_items_database.txt', 'a').close()
    
if __name__ == "__main__":
    generate_database_files()
    
    #######################################################################################
    ## The next code is to store temporary variables, this is not the configuration file ##
    #######################################################################################
    my_channel = "" #channel where I am, always
    my_name = "" #var to store my name
    start_time = datetime.datetime.now() #start time
    poll_status = False #status for polls
    poll_options = [] #list to store poll options
    poll_results = [] #list to store poll results
    bot_disabled = False #store the status of the bot
    channel_signed_users = {} #list to store a global dict to store people that signed in for an specific task
    kicker_on_cooldown = "" #var to store the uniqueid of the last person using the kick command

    with ts3.query.TS3Connection(HOST, PORT) as ts3conn:
        ts3conn.login(client_login_name=USER, client_login_password=PASS)
        ts3conn.use(sid=SID)
        bot_principal(ts3conn)


#TODOLIST
    #All the TBD in the files are things to be done later or that would need to be improved
    #TBD - descript on android users yields an error
