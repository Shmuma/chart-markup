#!/usr/bin/python

import cgi
from myfxbook import history
from myfxbook import account

from google.appengine.api.labs import taskqueue

print 'Content-Type: text/plain'
print ''

if not 'id' in cgi.FieldStorage ():
    print 'Account id is required'
    exit ()

acc_id = cgi.FieldStorage ()['id'].value

# check for account existence
acc = account.by_id (acc_id)
if not acc:
    # not exists, create
    acc = account.MyFXAccount (id = acc_id)
    print "Account for %s created" % acc_id
    acc.put ()

# trying to fetch next page of data. If data is obtained, schedule next page
# immediately. If page is empty, schedule next check in 10 minutes.
acc.last_page += 1
fetcher = history.FXBookHistoryFetcher (acc_id, acc.last_page)
parser = history.HistoryHtmlParser ()
parser.feed (fetcher.fetch ())

check_existence = history.have_history_records (acc, acc.last_page)

count = len (parser.data)
for entry in parser.data:
    # make MyFXHistoryRecord instance
    rec = history.MyFXHistoryRecord (account = acc, page = acc.last_page,
                                     pair = entry['pair'],
                                     open_at = history.parse_date (entry['open_at']),
                                     closed_at = history.parse_date (entry['closed_at']),
                                     long = entry['action'] == "Buy",
                                     size = float (entry['size']),
                                     sl_price = float (entry['sl_price']),
                                     tp_price = float (entry['tp_price']),
                                     open_price = float (entry['open_price']),
                                     close_price = float (entry['close_price']),
                                     pips = float (entry['pips']),
                                     profit = float (entry['profit']),
                                     comment = entry['comment'])
    valid = not (check_existence and history.record_exists (rec))
    if valid:
        rec.put ();
        acc.orders += 1

# If page is empty, we'll check it later
if count == 0:
    acc.last_page -= 1
acc.put ()

if count == 0:
    countdown = 10*60
else:
    countdown = 1

try:
    q = taskqueue.Queue ("myfxhistory")
    q.add (taskqueue.Task (method = "GET", url = "/fetch-myhist?id=%s" % acc_id, countdown = countdown))
except:
    pass

print 'ok, countdown = %d' % countdown
