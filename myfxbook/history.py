from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import db

import account
import datetime
import pickle
import csv

class MyFXHistoryRecord (db.Model):
    account = db.ReferenceProperty (account.MyFXAccount)
    pair = db.StringProperty (required = True)
    open_at = db.DateTimeProperty (required = True)
    closed_at = db.DateTimeProperty (required = True)
    long = db.BooleanProperty (required = True)
    size = db.FloatProperty (required = True)
    sl_price = db.FloatProperty ()
    tp_price = db.FloatProperty ()
    open_price = db.FloatProperty (required = True)
    close_price = db.FloatProperty (required = True)
    pips = db.FloatProperty (required = True)
    profit = db.FloatProperty (required = True)
    comment = db.StringProperty ()


class HistoryDataCache:
    def __init__ (self, account, pair):
        self.account = account
        self.pair = pair

    def csv_key (self):
        return "myfx-history-csv-%s-%s" % (self.account, self.pair)

    def csv (self):
        return memcache.get (self.csv_key ())

    def delete (self):
        memcache.delete (self.csv_key ())

    def set_csv (self, csv, time = 0):
        memcache.set (self.csv_key (), csv, time = time)


class FXBookHistory:
    def __init__ (self, acc_id, pair):
        self.account = account.MyFXAccount.gql ("WHERE id = :1", acc_id).get ()
        self.pair = pair

    def csv (self, header = True):
        """ Return history data as CSV text
        """
        res = 'open_date,close_date,long,lots,sl,tp,open_price,close_price,pips,profit,comment\n'
        recs = MyFXHistoryRecord.gql ("WHERE account=:1 and pair=:2 ORDER BY open_at ASC", self.account, self.pair)

        delta = datetime.timedelta (minutes = self.account.delta_minutes)
        for rec in recs:
            res += "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (rec.open_at + delta, rec.closed_at + delta, rec.long, rec.size,
                                                           rec.sl_price, rec.tp_price, rec.open_price, rec.close_price,
                                                           rec.pips, rec.profit, rec.comment)
        return res


# Class downloads given history page from myfxbook account
class FXBookHistoryFetcher:
    def __init__ (self, account):
        self.account = account
        self.orders = []

    def history_url (self):
        return 'http://www.myfxbook.com/statements/%s/statement.csv' % self.account

    def fetch (self):
        res = urlfetch.fetch (self.history_url ())
        if res.status_code == 200:
            # parse csv data
            reader = csv.reader (res.content.split ('\n'))
            block = 0
            for row in reader:
                if not len (row):
                    continue
                if row[0] == 'Open Date':
                    block += 1
                    if block > 1:
                        break
                    self.keys = dict (zip (map (lambda (s): s.lower (), row), xrange (len (row))))
                    continue
                if len (row) < 4:
                    continue
                if not row[3] in ['Buy', 'Sell']:
                    continue;
                # we insert in front, because data is sorted descending open timestamp
                self.orders.insert (0, row)
        return len (self.orders)

    def get (self, key, arr):
        if not key in self.keys:
            return "0"
        else:
            return arr[self.keys[key]]

# parse '05/13/2010 20:50' to datetime
def parse_date (str):
    date,time = str.split (' ')
    mon,day,year = date.split ('/')
    hr,min = time.split (':')
    return datetime.datetime (int (year), int (mon), int (day),
                              int (hr), int (min))

# check that such record exists. Use pair, account, open@, close@ as a key
def record_exists (hist):
    return MyFXHistoryRecord.gql ("WHERE account = :1 and pair = :2 and open_at = :3 and closed_at = :4",
                                  hist.account, hist.pair, hist.open_at, hist.closed_at).count (1) > 0


def have_history_records (acc, page):
    return MyFXHistoryRecord.gql ("WHERE account = :1 and page = :2", acc, page).count (1) > 0


def remove_account (acc):
    while True:
        hist = MyFXHistoryRecord.gql ("WHERE account = :1", acc).fetch (100)
        if not hist:
            break
        db.delete (hist)
    acc.delete ()


def cleanup_cache (acc):
    pairs_map = pickle.loads (acc.pairs_map)
    for pair in pairs_map.keys ():
        HistoryDataCache (acc.id, pair).delete ()
        account.set_last_update (acc.id, pair)
