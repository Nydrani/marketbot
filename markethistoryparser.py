#!/usr/local/bin/python3

import pprint
import json
import re

class Item:
    def __init__(self, name, amount, cost):
        self.name = name
        self.amount = amount
        self.cost = cost

    def __str__(self):
        return self.name + " | " + str(self.amount) + " | " + str(self.cost) + " mesos"

    def __repr__(self):
        return str(self)

class Equip(Item):
    def __init__(self, name, amount, cost, stats, slots):
        super().__init__(name, amount, cost)
        self.stats = stats
        self.slots = slots

    def __str__(self):
        return super().__str__() + " | " + str(self.stats) + " | " + str(self.slots)

    def __repr__(self):
        return str(self)

def parseEquipContents(contents):
    slotRegex1 = re.compile('\((.* slots)\)')
    slotRegex2 = re.compile('\((\+\d+\/\d+)\)')
    statsRegex = re.compile('\(((?:[A-Z.]+ \+\d+ )+)\)')
    s = []
    regexList = [slotRegex1, slotRegex2, statsRegex]

    # split all matching (parenthises) pairs
    for e in contents.split('('):
        if ')' in e:
            e = '(' + e
        s.append(e)

    # cleanup items
    s = [e.strip() for e in s]

    slots = None
    stats = None

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
    name = ' '.join(s[:])

    return name, stats, slots 


itemList = []

with open('market_history.log', 'r') as f:
    for line in f:
        s = json.loads(line)

        if s['type'] != 'sold':
            print("ignore listing types")
            print(s)
            continue

        style1 = re.compile('\( *Channel +\d +FM +\d *\) \*\*I just sold a\(n\) (.*) to .* for (.*) mesos!\*\*')
        style2 = re.compile('\( *Channel +\d +FM +\d *\) \*\*I just sold a (.*) to .* for (.*) mesos!\*\*')
        style3 = re.compile('\( *Channel +\d +FM +\d *\) \*\*I just sold a (.*) for (.*) mesos!\*\*')
        regexList = [style1, style2, style3]

        for style in regexList:
            matched = style.match(s['content'])

            # found nothing --> try another
            if matched:
                break

        if matched is None:
            print("problem here (strange input format)")
            print(s)
            continue

        # split item and cost
        item = matched.group(1)
        cost = matched.group(2).replace(',', '')
        amount = 1
        name = None
        stats = None
        slots = None

        # code to item bunches
        bunchRegex = re.compile('(.*) \((\d+)\)$')
        m = bunchRegex.match(item)
        if m:
            # edge case for icarus cape
            if m.group(1) == 'Icarus Cape':
                pass
            else:
                # item was sold in a bunch
                amount = m.group(2)
                item = m.group(1)
    
        # code to match equips
        equipRegex = re.compile('.*\(.*\)')
        if equipRegex.match(item):
            # item is equip
            # parse equip
            #print("Weapon: " + item + " | " + cost)
            name, stats, slots = parseEquipContents(item)
            equip = Equip(name, amount, cost, stats, slots)

            itemList.append(equip)
            continue

        # code to match scrolls (useless for now)
        scrollRegex = re.compile('Scroll for .*')
        if scrollRegex.match(item):
            # item is scroll
            #print("Scroll: " + item + " | " + cost)
            obj = Item(item, amount, cost)
            itemList.append(obj)
            continue

        # others
        obj = Item(item, amount, cost)
        itemList.append(obj)

    # print everything
    pprint.pprint(itemList)

