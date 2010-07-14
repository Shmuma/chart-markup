import os

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from myfxbook import account
from myfxbook import history
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

        self.expand_template ("tmpl/my-account.html", {"accounts": account.MyFXAccount.all (),
                                                       "msg": self.request.get ("msg")})

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
        

app = webapp.WSGIApplication ([('/my-account', MyFXAccount)], debug=True)

def main ():
    run_wsgi_app (app)

if __name__ == "__main__":
    main ()
