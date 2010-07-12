#!/usr/bin/python

import cgi
from myfxbook import history

print 'Content-Type: text/plain'
print ''

if not 'id' in cgi.FieldStorage ():
    print 'Account id is required'
    exit ()

if not 'page' in cgi.FieldStorage ():
    print 'Page index is required'
    exit ()

account = cgi.FieldStorage ()['id'].value
page = int (cgi.FieldStorage ()['page'].value)

hist = history.FXBookHistoryFetcher (account, page)
filter = history.FXBookHistoryFilter (hist.fetch ())

print filter.csv ()
