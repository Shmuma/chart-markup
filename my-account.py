import os

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from myfxbook import account
from myfxbook import history
import pickle
import urllib
import sys

class MyFXAccount (webapp.RequestHandler):
    def expand_template (self, name, args):
        path = os.path.join (os.path.dirname (__file__), name)
        self.response.out.write (template.render (path, args))

    def get (self):
        if self.request.get ("delete"):
            self.delete_account (self.request.get ("delete"))
            return
        elif self.request.get ("add"):
            self.add_account (self.request.get ("id"), self.request.get ("url"), self.request.get ("delta_minutes"))
            return
        elif self.request.get ("update"):
            self.update_account (self.request.get ("update"), self.request.get ("url"), self.request.get ("delta_minutes"))
            return

        accounts = []
        for acc in account.MyFXAccount.all ():
            pairs = []
            if acc.pairs_map:
                pairs_map = pickle.loads (acc.pairs_map)
                for pair in pairs_map.keys ():
                    pairs.append ({'pair': pair, 'count': pairs_map[pair], 'url': "/fxbook?id=%s&pair=%s" % (acc.id, pair)})
            acc_info = { 'url': acc.url,
                         'id': acc.id,
                         'delta_minutes': acc.delta_minutes,
                         'orders': acc.orders,
                         'last_page': acc.last_page,
                         'key': acc.key (),
                         'pairs': pairs
                         }
            print acc_info
            accounts.append (acc_info)
        edit_key = self.request.get ("edit")
        if edit_key:
            acc = account.MyFXAccount.get (db.Key (edit_key))
            edit = { 'key': edit_key,
                     'delta_minutes': acc.delta_minutes,
                     'url': acc.url };
        else:
            edit = None
        self.expand_template ("tmpl/my-account.html", {"add_form": self.request.get ("add_form"),
                                                       "accounts": accounts,
                                                       "msg": self.request.get ("msg"),
                                                       "edit": edit})

    def delete_account (self, id):
        try:
            acc = account.MyFXAccount.get (db.Key (id))
        except:
            self.redirect_message ("Account deletion error: %s" % sys.exc_info ()[1])
            return
        acc_id = acc.id
        # the right way to remove account
        history.remove_account (acc)
        self.redirect_message ("Account '%s' removed" % acc_id)


    def redirect_message (self, msg):
        self.redirect (self.request.path + "?msg=" + urllib.quote_plus (msg))
        

    def add_account (self, id, url, delta_minutes):
        try:
            delta = int (delta_minutes)
        except:
            self.redirect_message ("Account deletion error: %s" % sys.exc_info ()[1])
            return

        if account.by_id (id):
            self.redirect_message ("Account %s already exists" % id)
            return
        acc = account.MyFXAccount (id = id, url = url, delta_minutes = delta)
        acc.put ()
        # schedule account fetch
        account.schedule_fetch (id, time=1)
        self.redirect_message ("Account %s created" % id)


    def update_account (self, key, url, delta_minutes):
        try:
            delta = int (delta_minutes)
            acc = account.MyFXAccount.get (db.Key (key))
        except:
            self.redirect_message ("Account deletion error: %s" % sys.exc_info ()[1])
            return

        acc.url = url
        acc.delta_minutes = delta
        acc.put ()
        history.cleanup_cache (acc)
        self.redirect_message ("Account updated")


app = webapp.WSGIApplication ([('/my-account', MyFXAccount)], debug=True)

def main ():
    run_wsgi_app (app)

if __name__ == "__main__":
    main ()
