from google.appengine.api import memcache
from google.appengine.api import urlfetch

class PagesCache:
    def __init__ (self, account):
        self.account = account

    def count_key (self):
        return "fxbook-%s-pages" % self.account

    def page_key (self, index):
        return "fxbook-%s-page-%d" % (self.account, index)

    def page_url (self, index):
        return 'http://www.myfxbook.com/paging.html?pt=4&p=%d&&id=%s&l=x&invitation=&sb=28&st=1&types=0,1,2,4&rand=0.22347837989218533'\
            % (index, self.account)

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
        res = urlfetch.fetch (self.page_url (index))
        if res.status_code == 200:
            return res.content
        return None


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
