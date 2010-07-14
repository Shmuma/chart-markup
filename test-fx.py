#!/usr/bin/python

import cgi
from myfxbook import history
from google.appengine.api.labs import taskqueue

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
parser = history.HistoryHtmlParser ()
parser.feed (hist.fetch ())
print parser.data

# schedule history processor of this account
try:
    q = taskqueue.Queue ("myfxhistory")
    q.add (taskqueue.Task (name = "myfx-%s" % account, method = "GET", url = "/myfxhistory?id=%s" % account, countdown = 30))
except:
    pass
