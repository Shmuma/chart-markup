import os

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template


class MyFXAccount (webapp.RequestHandler):
    def expand_template (self, name, args):
        path = os.path.join (os.path.dirname (__file__), name)
        self.response.out.write (template.render (path, args))

    def get (self):
        self.expand_template ("tmpl/my-account.html", {})

app = webapp.WSGIApplication ([('/my-account', MyFXAccount)], debug=True)

def main ():
    run_wsgi_app (app)

if __name__ == "__main__":
    main ()
