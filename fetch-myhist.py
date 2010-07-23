#!/usr/bin/python

import cgi
import pickle
from myfxbook import history
from myfxbook import account

print 'Content-Type: text/plain'
print ''

if not 'id' in cgi.FieldStorage ():
    print 'Account id is required'
    exit ()

acc_id = cgi.FieldStorage ()['id'].value

# check for account existence
acc = account.by_id (acc_id)
if not acc:
    # not exists, create
    acc = account.MyFXAccount (id = acc_id)
    print "Account for %s created" % acc_id
    acc.put ()

# fetch and parse full history by CSV url
fetcher = history.FXBookHistoryFetcher (acc_id)
count = fetcher.fetch ()

if not acc.pairs_map:
    pairs_map = {}
else:
    pairs_map = pickle.loads (acc.pairs_map)
    if not pairs_map:
        pairs_map = {}

if count < acc.orders:
    print 'Something bad happened, we have more orders than MyFXBook returns.'
elif count == acc.orders:
    print 'No new data found, still have %d orders' % acc.orders
else:
    print 'Got %d new orders, process them' % (count - acc.orders)
    pairs = {}
    for order in fetcher.orders[acc.orders:]:
        pair = order[2]
        rec = history.MyFXHistoryRecord (account = acc,
                                         open_at = history.parse_date (order[0]),
                                         closed_at = history.parse_date (order[1]),
                                         pair = pair,
                                         long = order[3] == "Buy",
                                         size = float (order[4]),
                                         sl_price = float (order[5]),
                                         tp_price = float (order[6]),
                                         open_price = float (order[7]),
                                         close_price = float (order[8]),
                                         pips = float (order[11]),
                                         profit = float (order[12]),
                                         comment = order[13])
        rec.put ()
        if not pair in pairs_map:
            pairs_map[pair] = 0
        pairs[pair] = 1
        acc.orders += 1
        pairs_map[pair] += 1
    # wipe cache for affected pairs
    for pair in pairs.keys ():
        cache = history.HistoryDataCache (acc_id, pair)
        cache.delete ()
    if pairs:
        acc.pairs_map = pickle.dumps (pairs_map)
        acc.put ()
