#!/usr/bin/python

import cgi
from myfxbook import history
from myfxbook import account
from google.appengine.ext import db

print 'Content-Type: text/plain'
print ''

try:
    db.delete (history.MyFXHistoryRecord.all (keys_only = True).fetch (500))
except:
    print "Have entries to delete: %d" % history.MyFXHistoryRecord.all ().count ()
