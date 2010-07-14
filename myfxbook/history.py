from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import db

from HTMLParser import HTMLParser

import account
import datetime

class MyFXHistoryRecord (db.Model):
    account = db.ReferenceProperty (account.MyFXAccount)
    page = db.IntegerProperty (required = True)
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


class PagesCache:
    def __init__ (self, account):
        self.account = account

    def count_key (self):
        return "fxbook-%s-pages" % self.account

    def page_key (self, index):
        return "fxbook-%s-page-%d" % (self.account, index)

    def count (self):
        pages = memcache.get (self.count_key ())
        if pages:
            return pages
        else:
            return 0

    def new_count (self, count):
        memcache.set (self.count_key (), count)

    def page (self, index):
        data = memcache.get (self.page_key (index))
        if data:
            return data
        return FXBookHistoryFetcher (self.account, index)


class FXBookHistory:
    def __init__ (self, acc_id, pair):
        self.account = account.MyFXAccount.gql ("WHERE id = :1", acc_id).get ()
        self.pair = pair

    def csv (self, header = True):
        """ Return history data as CSV text
        """
        res = 'open_date,close_date,long,lots,sl,tp,open_price,close_price,pips,profit\n'
        recs = MyFXHistoryRecord.gql ("WHERE account=:1 and pair=:2", self.account, self.pair)
      
        for rec in recs:
            res += "%s,%s,%s,%s,%s\n" % (rec.open_at, rec.closed_at, rec.long, rec.size, rec.sl_price)

        return res


# Class downloads given history page from myfxbook account
class FXBookHistoryFetcher:
    def __init__ (self, account, page):
        self.account = account
        self.page = page

    def page_url (self):
        return 'http://www.myfxbook.com/paging.html?pt=4&p=%d&&id=%s&l=x&invitation=&sb=28&st=1&types=0,1,2,4&rand=0.22347837989218533'\
            % (self.page, self.account)

    def fetch (self):
        res = urlfetch.fetch (self.page_url ())
        if res.status_code == 200:
            return res.content
        return None



# Parser of history data. Returns list of hashes with orders performed.
class HistoryHtmlParser (HTMLParser):
    def reset (self):
        HTMLParser.reset (self)
        self.data = []
        self.entry = {}
        self.res = ""
        self.in_tr = False
        self.in_td = False
        self.td_index = 0

    def has_class (self, attrs):
        for a,b in attrs:
            if a == "class":
                return True
        return False

    def handle_starttag (self, tag, attrs):
        if tag == "tr" and self.has_class (attrs):
            self.in_tr = True
            return
        if not self.in_tr:
            return
        if tag == "td":
            self.td_index += 1
            self.in_td = True

    def handle_data (self, data):
        txt = data.strip ()
        if self.in_tr and self.in_td and txt:
            if self.td_index == 1:
                self.res += "\n"
            self.entry[self.index2key (self.td_index)] = txt
            self.res += "%d: %s\n" % (self.td_index, txt)

    def handle_endtag (self, tag):
        if tag == "tr":
            self.in_tr = False
            self.in_td = False
            self.td_index = 0
            if self.entry:
                # filter out deposits
                if 'pair' in self.entry:
                    if not 'comment' in self.entry:
                        self.entry['comment'] = ""
                    self.data.append (self.entry)
                self.entry = {}
        elif tag == "td":
            self.in_td = False

    def index2key (self, index):
        map = {
            1: 'open_at',
            2: 'closed_at',
            3: 'pair',
            4: 'action',
            5: 'size',
            6: 'sl_price',
            7: 'tp_price',
            8: 'open_price',
            9: 'close_price',
            10: 'pips',
            11: 'profit',
            12: 'comment'}

        if index in map:
            return map[index]
        else:
            return 'unknown'

# parse '05.12.2010 20:50' to datetime
def parse_date (str):
    date,time = str.split (' ')
    mon,day,year = date.split ('.')
    hr,min = time.split (':')
    return datetime.datetime (int (year), int (mon), int (day),
                              int (hr), int (min))

# check that such record exists. Use pair, account, open@, close@ as a key
def record_exists (hist):
    return MyFXHistoryRecord.gql ("WHERE account = :1 and pair = :2 and open_at = :3 and closed_at = :4",
                                  hist.account, hist.pair, hist.open_at, hist.closed_at).count (1) > 0

def have_history_records (acc, page):
    return MyFXHistoryRecord.gql ("WHERE account = :1 and page = :2", acc, page).count (1) > 0
