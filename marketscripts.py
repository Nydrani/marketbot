import pathlib
import datetime
import playhouse.sqlite_ext
import peewee
import sys
import io
import base64
from marketparser import Sale, Item, Equip
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, MO, DateFormatter, MonthLocator
from matplotlib.ticker import FuncFormatter
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

    total_daily_price = cost_list[0]
    total_daily_items = 1
    start_day = time_list[0]

    cur_day = None
    cur_price = None

    for i in range(1, len(time_list)):
        # get all costs from one day --> calculate average (store in new list)
        cur_day = time_list[i]
        cur_price = cost_list[i]
        #print(cur_day.strftime("%d-%B"))

        # main loop
        if start_day.date() != cur_day.date():
            # different day -> save everything to daily price list
            #print("cur day: " + cur_day.strftime("%d-%B"))
            #print("start day: " + start_day.strftime("%d-%B"))
            daily_price_list.append(total_daily_price / total_daily_items)
            daily_time_list.append(start_day)

            # set initial stuff to this
            total_daily_price = cur_price
            total_daily_items = 1
            start_day = cur_day
        else:
            total_daily_price += cur_price
            total_daily_items += 1

    # always add last day
    daily_price_list.append(total_daily_price / total_daily_items)
    daily_time_list.append(start_day)


    #print(daily_price_list)
    #print(daily_time_list)
    #print(len(daily_price_list))
    #print(len(daily_time_list))

    return daily_price_list, daily_time_list


def getPlotData(cool_name):

    # Exponential moving average
    cost = []
    time = []

    # given name --> find all sales with item name (name)
    # sort by date
    #for result in Sale.select(Sale.cost, Sale.time, Sale.amount).join(Item).where(Item.name == name, Sale.item_id == Item.id).order_by(Sale.time.asc()):
    for result in Sale.select(Sale.cost, Sale.time, Sale.amount).join(Item).where(Item.name == cool_name, Sale.item_id == Item.id).order_by(Sale.time.asc()):
        #print(result.time)
        time.append(datetime.datetime.fromisoformat(result.time))
        cost.append(result.cost / result.amount)

    return cost, time

def formatCost(num, pos):
    magnitude = 0
    while abs(num) >= 1000 and magnitude < 3:
        magnitude += 1
        num /= 1000.0

    if magnitude <= 1:
        return '%.f%s' % (num, ['', 'k', 'mil', 'bil'][magnitude])

    return '%.1f%s' % (num, ['', 'k', 'mil', 'bil'][magnitude])


def is_outlier(points, thresh=100):
    """
    Returns a boolean array with True if points are outliers and False 
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 
    """
    # custom no outliers if not enough data
    if points.shape[0] < 10:
        return [False for i in range(points.shape[0])]

    if len(points.shape) == 1:
        points = points[:,None]

    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)
    modified_z_score = 0.6745 * diff / med_abs_deviation
    return modified_z_score > thresh

def plotAndGenerateImage(item_name, save_location):
    
    cost, time = getPlotData(item_name)
    # die on nothing
    if not cost:
        return False

    if not time:
        return False

    #print(cost)
    #print(time)
    

    np_cost = np.array(cost)
    outliers = is_outlier(np_cost)
    #for i, val in enumerate(outliers):
    #    if val:
    #        print(np_cost[i])

    filtered_cost = [res for (res, check) in zip(cost, outliers) if not check]
    filtered_time = [res for (res, check) in zip(time, outliers) if not check]
    
    alldays = DayLocator()              	# minor ticks on the days
    month = MonthLocator(bymonthday=15)         # major ticks on the month
    formatter = DateFormatter("%Y-%m-%d")
    
    daily_cost, daily_time = getDailyAverage(filtered_cost, filtered_time)
    mean_cost = running_mean(daily_cost, 7)
    #mean_cost_14 = running_mean(daily_cost, 14)

    #print(daily_cost)
    #print(daily_time)
    
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    ax.yaxis.set_major_formatter(FuncFormatter(formatCost))
    ax.xaxis.set_major_locator(month)
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_minor_locator(alldays)

    if len(daily_cost) == 1:
        ax.plot(daily_time, daily_cost, '#7ba5ed', marker='o', label='daily average price', alpha=0.8)
    else:
        ax.plot(daily_time, daily_cost, '#7ba5ed', label='daily average price', alpha=0.8)
        ax.plot(daily_time[3:-3], mean_cost, '#e24f4f', label='running mean (window 7)')
        #ax.plot(daily_time[7:-6], mean_cost_14, label='running mean (fortnight)')

    ax.grid(True, 'major', 'y', linestyle='--', alpha=0.5)
    new_bot = ax.get_ybound()[0] * 0.9
    new_top = ax.get_ybound()[1] * 1.1
    ax.set_ylim(top=new_top, bottom=new_bot)
    
    plt.xlabel('date')
    plt.ylabel('mesos')
    plt.margins(0)

    plt.title(item_name + " price")
    plt.legend()
    plt.savefig(save_location + '.png', bbox_inches='tight')

    # also create zero_anchored image
    ax.set_ylim(bottom=0)
    plt.savefig(save_location + 'zeroanchored.png', bbox_inches='tight')

    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 marketscripts.py name_of_item save_location")
        sys.stdout.flush()
        sys.exit(1)
    
    success = plotAndGenerateImage(sys.argv[1], sys.argv[2])
    if not success:
        sys.exit(1)

