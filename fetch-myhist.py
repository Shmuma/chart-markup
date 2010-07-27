#!/usr/bin/python

import sys
import cgi
import pickle
from myfxbook import history
from myfxbook import account
from google.appengine.ext import db

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
    pairs = set ()
    try:
        print 'Got %d new orders, process them' % (count - acc.orders)
        for order in fetcher.orders[acc.orders:]:
            pair = fetcher.get ('symbol', order)
            rec = history.MyFXHistoryRecord (account = acc,
                                             open_at = history.parse_date (fetcher.get ('open date', order)),
                                             closed_at = history.parse_date (fetcher.get ('close date', order)),
                                             pair = pair,
                                             long = fetcher.get ('action', order) == "Buy",
                                             size = float (fetcher.get ('lots', order)),
                                             sl_price = float (fetcher.get ('sl', order)),
                                             tp_price = float (fetcher.get ('tp', order)),
                                             open_price = float (fetcher.get ('open price', order)),
                                             close_price = float (fetcher.get ('close price', order)),
                                             pips = float (fetcher.get ('pips', order)),
                                             profit = float (fetcher.get ('profit', order)),
                                             comment = fetcher.get ('comment', order))
            if not pair in pairs_map:
                pairs_map[pair] = 0
            rec.put ()
            pairs.add (pair)
            acc.orders += 1
            pairs_map[pair] += 1
    except:
        account.schedule_fetch (acc_id)
    acc.pairs_map = pickle.dumps (pairs_map)
    acc.put ()
    # wipe cache for affected pairs and update timestamp
    for pair in pairs:
        cache = history.HistoryDataCache (acc_id, pair)
        cache.delete ()
        account.set_last_update (acc_id, pair)
