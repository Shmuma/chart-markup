#!/usr/bin/python

from google.appengine.ext import db
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

acc = account.by_id (acc_id)

q = history.MyFXHistoryRecord.gql ("WHERE acc=:1 and pair=:2", acc, pair)
s = q.count ()

count = 0
for rec in q:
    count += 1
print s
print count

