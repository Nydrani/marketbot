import peewee
import json
import re

db = peewee.SqliteDatabase('market.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Item(BaseModel):
    name = peewee.CharField(unique=True, max_length=64)


class Sale(BaseModel):
    item_id = peewee.ForeignKeyField(Item)
    amount = peewee.SmallIntegerField()
    cost = peewee.IntegerField()
    time = peewee.DateTimeField()


class Equip(BaseModel):
    item_id = peewee.ForeignKeyField(Item)
    sale_id = peewee.ForeignKeyField(Sale)
    stats = peewee.CharField(max_length=128)
    slots = peewee.CharField(max_length=16)


db.connect()
db.create_tables([Item, Sale, Equip])


def parseEquipContents(contents):
    slotRegex1 = re.compile(r'\((.* slots)\)')
    slotRegex2 = re.compile(r'\((\+\d+\/\d+)\)')
    statsRegex = re.compile(r'\(((?:[A-Z.]+ \+\d+ )+)\)')
    s = []

    skip = False

    # split all matching (parenthises) pairs
    for e in contents.split('('):
        if ')' in e:
            e = '(' + e
        s.append(e)

    # cleanup items
    s = [e.strip() for e in s]

    slots = "Clean"
    stats = "Clean"

    # find the stats and slots sections
    for e in s[:]:
        m = slotRegex1.match(e)
        if m:
            # slots are bla
            slots = m.group(1)
            s.remove(m.group(0))
            continue

        m = slotRegex2.match(e)
        if m:
            slots = m.group(1)
            s.remove(m.group(0))
            continue

        m = statsRegex.match(e)
        if m:
            stats = m.group(1)
            s.remove(m.group(0))
            continue

    # merge everything else into the name
    # equips are not stackable, so amount would not be merged into the name
    name = ' '.join(s[:])

    return name, stats, slots

def loadDatabase(s):
    # ignoring listings for now
    if s['type'] != 'sold':
        return

    style1 = re.compile(r'^\(Channel +\d +FM +\d\) \*\*I just sold a\(n\) (.*) to .* for (.*) mesos!\*\*$')
    style2 = re.compile(r'^\(Channel +\d +FM +\d\) \*\*I just sold a (.*) to .* for (.*) mesos!\*\*$')
    style3 = re.compile(r'^\(Channel +\d +FM +\d\) \*\*I just sold a (.*) for (.*) mesos!\*\*$')
    regexList = [style1, style2, style3]

    for style in regexList:
        matched = style.match(s['content'])

        # found nothing --> try another
        if matched:
            break

    if matched is None:
        with open("problem.log", "a") as err:
            err.write("problem here (strange input format): %s" % s['content'])

        print("problem here (strange input format) check problem logs")
        print(s)
        return

    # split item and cost
    item = matched.group(1)
    cost = matched.group(2).replace(',', '')
    amount = 1
    time = s['created_at']
    name = None
    stats = None
    slots = None

    # code to item bunches
    bunchRegex = re.compile(r'(.*) \((\d+)\)$')
    m = bunchRegex.match(item)
    if m:
        # edge case for icarus cape
        if m.group(1) == 'Icarus Cape':
            pass
        else:
            # item was sold in a bunch
            amount = m.group(2)
            item = m.group(1)

    name = item

    # code to match equips
    # for now ignore equips
    # (since they fluctuate based on price and slots)
    equipRegex = re.compile(r'.*\(.*\)')
    if equipRegex.match(item):
        # parse equip
        name, stats, slots = parseEquipContents(item)

    # code to match scrolls
    # old style scrolls are useless (since they miss the %)
    scrollRegex = re.compile('^Scroll for .*[^%]$')
    if scrollRegex.match(item):
        # item is old style scroll
        return

    # load sale into db
    # WARNING: Race conditions may happen when multithreaded
    obj, created = Item.get_or_create(name=name)

    #print("found " + name)
    # WARNING: Race conditions may happen when multithreaded
    sale, created = Sale.get_or_create(item_id=obj, amount=amount, cost=cost, time=time)
    if not created:
        # seems like the sale was already created. quit
        print("Already created")
        print(s)
        return

    if stats is not None and slots is not None:
        Equip.create(item_id=obj, sale_id=sale, stats=stats, slots=slots)


# parse entire market_history from this
if __name__ == '__main__':
    with open('market_history.log', 'r') as f:
        for i in f:
            loadDatabase(json.loads(i))
