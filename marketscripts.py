import pathlib
import datetime
import playhouse.sqlite_ext
import peewee
from marketparser import Sale, Item, Equip

def backupDatabase():
    backups_path = pathlib.Path('./backups/')
    backups_path.mkdir(exist_ok=True)
    filename = backups_path / ('market-backup-%s.db' % (datetime.date.today()))

    db = playhouse.sqlite_ext.CSqliteExtDatabase('market.db')
    db.backup_to_file(filename)

def getRunningAveragePrice(name):
    # given name --> find all sales with item name (name)
    # sort by date
    # then do a running average
    query = (Sale.select(Item.name, Sale.amount, Sale.cost).join(Item).where(Item.name == name, Sale.item_id == Item.id))
    for stuff in query:
        print(stuff.item)

getRunningAveragePrice("Diamond Ore")
