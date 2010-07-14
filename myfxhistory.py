#!/usr/bin/python

import cgi
from myfxbook import history
from google.appengine.api.labs import taskqueue

print 'Content-Type: text/plain'
print ''

if not 'id' in cgi.FieldStorage ():
    print 'Account id is required'
    exit ()

account = cgi.FieldStorage ()['id'].value

print 'ok'
