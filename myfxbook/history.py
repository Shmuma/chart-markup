from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import db

from HTMLParser import HTMLParser

import account

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
    def __init__ (self, account):
        self.account = account

        # get history data
        pc = PagesCache (account)
        pages = pc.count ()
        if pages:
            for page in xrange (0, pages-1):
                print page
        else:
            page = 0
            while True:
                data = pc.page (page)
                if not data:
                    break
                print data
                page += 1
            pc.new_count (page)

    def csv (header = True):
        """ Return history data as CSV text
        """
        res = ['open_date,close_date,symbol,action,lots,sl,tp,open_price,close_price,pips,profit']

        return '\n'.join (res)


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

