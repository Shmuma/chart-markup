from google.appengine.ext import db


# MyFXBook list of watched accounts
class MyFXAccount (db.Model):
    id = db.IntegerProperty (required = True)
    last_page = db.IntegerProperty (default = 0)
    deals = db.IntegerProperty (default = 0)
    url = db.StringProperty ()
