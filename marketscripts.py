import pathlib
import datetime
import playhouse.sqlite_ext
import peewee
import sys
from marketparser import Sale, Item, Equip
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, WeekdayLocator, MO, DateFormatter
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


def running_mean(x, n):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[n:] - cumsum[:-n]) / float(n)

def getVolumeData(cost_list, bins):
    max_price = max(cost_list)
    min_price = min(cost_list)

    # get range within bins
    bin_range = (max_price - min_price) / bins
    bin_list = []

    for cost in cost_list:
        curPrice = min_price + bin_range / 2
        bin_number = 0
        while curPrice < cost:
            curPrice += bin_range
            bin_number += 1

        bin_list.append(bin_number)

    return bin_list

def getDailyAverage(cost_list, time_list):
    daily_price_list = []
    daily_time_list = []

    total_daily_price = 0
    total_daily_items = 0
    start_day = None
    for i in range(len(time_list)):
        # get all costs from one day --> calculate average (store in new list)
        cur_day = time_list[i]
        cur_price = cost_list[i]
        print(cur_day.strftime("%d-%B"))

        # edge case for start
        if start_day == None:
            total_daily_price = cur_price
            total_daily_items = 1
            start_day = cur_day
            continue

        # main loop
        if start_day.date() != cur_day.date():
            # different day -> save everything to daily price list
            print("cur day: " + cur_day.strftime("%d-%B"))
            print("start day: " + start_day.strftime("%d-%B"))
            daily_price_list.append(total_daily_price / total_daily_items)
            daily_time_list.append(start_day)

            # set initial stuff to this
            total_daily_price = cur_price
            total_daily_items = 1
            start_day = cur_day

        total_daily_price += cur_price
        total_daily_items += 1


    print(daily_price_list)
    print(daily_time_list)
    print(len(daily_price_list))
    print(len(daily_time_list))

    return daily_price_list, daily_time_list


def getPlotData(cool_name):

    # Exponential moving average
    cost = []
    time = []

    # given name --> find all sales with item name (name)
    # sort by date
    #for result in Sale.select(Sale.cost, Sale.time, Sale.amount).join(Item).where(Item.name == name, Sale.item_id == Item.id).order_by(Sale.time.asc()):
    for result in Sale.select(Sale.cost, Sale.time, Sale.amount).join(Item).where(Item.name == cool_name, Sale.item_id == Item.id).order_by(Sale.time.asc()):
        print(result.time)
        time.append(datetime.datetime.fromisoformat(result.time))
        cost.append(result.cost / result.amount)

    return cost, time

        

def plotAndGenerateImage(item_name, save_location):
    
    cost, time = getPlotData(item_name)
    # die on nothing
    if not cost:
        return False

    if not time:
        return False
    
    week = WeekdayLocator(byweekday=MO)        # major ticks on the mondays
    alldays = DayLocator()              	# minor ticks on the days
    formatter = DateFormatter("%Y-%m-%d")              	# minor ticks on the days
    
    daily_cost, daily_time = getDailyAverage(cost, time)
    mean_cost = running_mean(daily_cost, 5)
    mean_cost_10 = running_mean(daily_cost, 10)
    
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(week)
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_minor_locator(alldays)
    ax.plot(daily_time, daily_cost, label='daily_price')
    ax.plot(daily_time[2:-2], mean_cost, label='running mean (window 5)')
    ax.plot(daily_time[5:-4], mean_cost_10, label='running mean (window 10)')
    ax.set_ylim(bottom=0)
    
    
    plt.xlabel('date')
    plt.ylabel('meos')
    plt.margins(0)

    
    plt.title(item_name + " price")
    
    plt.legend()
    
    plt.savefig(save_location + '.png', bbox_inches='tight')

    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 marketscripts.py name_of_item save_location")
        sys.stdout.flush()
        sys.exit(1)
    
    success = plotAndGenerateImage(sys.argv[1], sys.argv[2])
    if not success:
        sys.exit(1)
