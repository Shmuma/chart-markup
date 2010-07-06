#!/usr/bin/python

import cgi
from myfxbook import history

print 'Content-Type: text/plain'
print ''

if not 'id' in cgi.FieldStorage ():
    print 'Account id is required'
    exit ()

account = cgi.FieldStorage ()['id'].value

hist = history.FXBookHistory (account)
print hist.csv ()
