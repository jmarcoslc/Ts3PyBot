HOST = "" #Address to connect
USER = "" #Username of serverquery client
PASS = "" #Password of serverquery client
nickname = "" #Public nickname
channel_to_join = sys.argv[1] #Default channel name to join. If you don't use sys.argv[1] the clone command won't work.
channel_password = "" #Password to join that channel
PORT = 17845 #Port to connect
SID = 1 #virtual server ID
super_admins = [""] #add database IDs that will be able to run python code on-the-fly using Test command
admins_groups_ids = [""] #add server_group ids that will have permissions for every bot command, except Test
ignore_group_id = "" #a server_group id that will be used to track when the bot ignores you
welcome_message = "" #say this when you log in
