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

if not 'pair' in cgi.FieldStorage ():
    print 'Currency pair is required'
    exit ()

count_mode = 'count' in cgi.FieldStorage ()

acc_id = cgi.FieldStorage ()['id'].value
pair = cgi.FieldStorage ()['pair'].value

# In count_mode we just display count of orders by given currency pair and account id
if count_mode:
    acc = account.by_id (acc_id)
    if not acc.pairs_map:
        print '0'
    else:
        pairs_map = pickle.loads (acc.pairs_map)
        if pair in pairs_map:
            print pairs_map[pair]
        else:
            print '0'
else:
    cache = history.HistoryDataCache (acc_id, pair)
    res = cache.csv ()
    if res:
        print res
    else:
        hist = history.FXBookHistory (acc_id, pair)
        res = hist.csv ()
        cache.set_csv (res)
        print res

