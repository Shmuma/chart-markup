#!/usr/bin/python

import cgi
from myfxbook import history

print 'Content-Type: text/plain'
print ''

if not 'id' in cgi.FieldStorage ():
    print 'Account id is required'
    exit ()

if not 'pair' in cgi.FieldStorage ():
    print 'Currency pair is required'
    exit ()

account = cgi.FieldStorage ()['id'].value
pair = cgi.FieldStorage ()['pair'].value

cache = history.HistoryDataCache (account, pair)

res = cache.csv ()

if res:
    print res
else:
    hist = history.FXBookHistory (account, pair)
    res = hist.csv ()
    cache.set_csv (res)
    print res

