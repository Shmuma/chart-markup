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

hist = history.FXBookHistory (account, pair)
print hist.csv ()
