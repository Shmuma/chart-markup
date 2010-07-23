#!/usr/bin/python

from myfxbook import history
from myfxbook import account

print 'Content-Type: text/plain'
print ''

for acc in account.MyFXAccount.all ():
    account.schedule_fetch (acc.id)
    print 'Schedule update of %s account' % acc.id
