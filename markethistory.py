import discord
import json
import datetime
import os


test_server_id = 564606128688726021
test_sold_id = 564623272226848784

osm_server_id = 496611148850921475
osm_sold_id = 553996752273801217

my_token = '***REMOVED***'

# TODO probably write a complete timeout if i get no legit messages for a day
# pretty much means i dont have permissions (or parsing is incorrect)
class MyClient(discord.Client):

    def __init__(self, log_location, server_id, sold_id):
        super().__init__()
        self.log_location = log_location
        self.server_id = server_id
        self.sold_id = sold_id

    def __enter__(self):
        self.log_file = open(self.log_location, "w")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log_file.close()


    async def on_ready(self):
        print("Ready")

        market_server = self.get_guild(self.server_id)
        if market_server is None:
            print("Server doesnt exist")
            await client.logout()
            return

        print("Getting sold channel")
        sold_channel = client.get_channel(self.sold_id)

        print("Checking perms")
        if sold_channel is None:
            print("Channel doesnt exist")
            await client.logout()
            return

        channel_perms = sold_channel.permissions_for(market_server.me)
        if not channel_perms.read_message_history:
            print("Dont have channel permissions")
            await client.logout()
            return

        print("Reading history")
        today = datetime.datetime.now()
        month_delta = datetime.timedelta(days=30)
        last_month = today - month_delta
        count = 0
        async for message in sold_channel.history(limit=None, after=last_month):
            self.parseMessage(message)
            count += 1

        print(count)
        print("Logging out")
        await client.logout()


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
     
        json_string = json.dumps(prep_message)
        self.log_file.write(json_string + '\n')
        self.log_file.flush()
        os.fsync(self.log_file.fileno())
            

test_mode = True

if test_mode:
    cur_server_id = test_server_id
    cur_sold_id = test_sold_id
else:
    cur_server_id = osm_server_id
    cur_sold_id = osm_sold_id

with MyClient("market_history.log", cur_server_id, cur_sold_id) as client:
    client.run(my_token, bot=False)

