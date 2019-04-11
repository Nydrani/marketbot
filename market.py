import discord
import json
import os
import peewee
import marketparser

test_sold_id = 564623272226848784
test_listings_id = 564623286898655262
test_server_id = 564606128688726021

osm_server_id = 496611148850921475
osm_sold_id = 553996752273801217
osm_listings_id = 553996579531653120

my_token = '***REMOVED***'

# TODO probably write a complete timeout if i get no legit messages for a day
# pretty much means i dont have permissions (or parsing is incorrect)

class MyClient(discord.Client):
    hasPermissions = False

    def __init__(self, log_location, server_id, sold_id, listings_id):
        super().__init__()
        self.log_location = log_location
        self.server_id = server_id
        self.sold_id = sold_id
        self.listings_id = listings_id

    def __enter__(self):
        self.log_file = open(self.log_location, "a+")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log_file.close()

    def updatePermissions(self):
        market_server = self.get_guild(self.server_id)
        if market_server is None:
            self.hasPermissions = False
            return

        sold_channel = self.get_channel(self.sold_id)
        if sold_channel is None:
            self.hasPermissions = False
            return

        listings_channel = self.get_channel(self.listings_id)
        if listings_channel is None:
            self.hasPermissions = False
            return

        server_me = market_server.me

        channel_perms = sold_channel.permissions_for(server_me)
        if not channel_perms.read_messages:
            self.hasPermissions = False
            return

        channel_perms = listings_channel.permissions_for(server_me)
        if not channel_perms.read_messages:
            self.hasPermissions = False
            return

        self.hasPermissions = True

    async def on_guild_available(self, guild):
        self.updatePermissions()
        print('on_guild_available')
        print(self.hasPermissions)

    async def on_guild_unavailable(self, guild):
        self.updatePermissions()
        print('on_guild_unavailable')
        print(self.hasPermissions)

    async def on_guild_join(self, guild):
        self.updatePermissions()
        print('on_guild_remove')
        print(self.hasPermissions)

    async def on_guild_remove(self, guild):
        self.updatePermissions()
        print('on_guild_remove')
        print(self.hasPermissions)

    async def on_guild_channel_update(self, before, after):
        self.updatePermissions()
        print('on_guild_channel_update')
        print(self.hasPermissions)

    async def on_resumed(self):
        self.updatePermissions()
        print('on_rsume')
        print(self.hasPermissions)

    async def on_ready(self):
        self.updatePermissions()
        print('on_ready')
        print(self.hasPermissions)

        print('Logged on as', self.user)
        print(client.guilds)

    async def on_message(self, message):
        # check i have permissions
        if not self.hasPermissions:
            return

        self.parseMessage(message)

    def parseMessage(self, message):
        # check correct channel
        if message.channel.id != self.sold_id and message.channel.id != self.listings_id:
            return

        # prepare message
        prep_message = {}
        prep_message["content"] = message.content.strip()
        prep_message["author"] = message.author.display_name.strip()
        prep_message["created_at"] = message.created_at.isoformat()
        if message.channel.id == self.sold_id:
            prep_message["type"] = "sold"
        elif message.channel.id == self.listings_id:
            prep_message["type"] = "listing"

        print(prep_message)

        # load into db
        marketparser.loadDatabase(prep_message)

        json_string = json.dumps(prep_message)
        self.log_file.write(json_string + '\n')
        self.log_file.flush()
        os.fsync(self.log_file.fileno())


test_mode = False

if test_mode:
    cur_server_id = test_server_id
    cur_sold_id = test_sold_id
    cur_listings_id = test_listings_id
else:
    cur_server_id = osm_server_id
    cur_sold_id = osm_sold_id
    cur_listings_id = osm_listings_id

with MyClient("market.log", cur_server_id, cur_sold_id, cur_listings_id) as client:
    client.run(my_token, bot=False)
