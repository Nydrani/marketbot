import pathlib
import datetime
import playhouse.sqlite_ext
import peewee
from marketparser import Sale, Item, Equip
import matplotlib.pyplot as plt
import numpy as np

def backupDatabase():
    backups_path = pathlib.Path('./backups/')
    backups_path.mkdir(exist_ok=True)
    filename = backups_path / ('market-backup-%s.db' % (datetime.date.today()))

    db = playhouse.sqlite_ext.CSqliteExtDatabase('market.db')
    db.backup_to_file(filename)

def calcSMA(average, time, cost):
    # time = 1 day --> anything with less than 1 day --> delay less --> otherwise decay more
    decay = 0.9
    result = average * decay + cost * (1 - decay)
    return result

def calcEMA(average, time, cost):
    mult = 2 / (time + 1)
    result = (cost - average) * mult + average
    average = average * decay + cost * (1 - decay)
    return result

def calcWMA(average, time, cost):
    decay = 0.95
    result = average * decay + cost * (1 - decay)
    return result


def getPlotData(name):

    # Exponential moving average
    cost = []
    time = []

    # given name --> find all sales with item name (name)
    # sort by date
    for result in Sale.select(Sale.cost, Sale.time).join(Item).where(Item.name == name, Sale.item_id == Item.id):
        time.append(result.time)
        cost.append(result.cost)


    return cost, time

        


#getRunningAveragePrice("Opal")

cost, time = getPlotData("Diamond Ore")
plt.scatter(time, cost, label='average price')

plt.xlabel('time')
plt.ylabel('cost')
plt.gcf().autofmt_xdate()

plt.title("Simple Plot")

plt.legend()

plt.show()
