from google.appengine.ext import db


# MyFXBook list of watched accounts
class MyFXAccount (db.Model):
    id = db.StringProperty (required = True)
    last_page = db.IntegerProperty (default = 0)
    orders = db.IntegerProperty (default = 0)
    url = db.StringProperty ()


def by_id (id):
    return MyFXAccount.gql ("WHERE id=:1", id).get ()


def remove (acc):
    try:
        while True:
            hist = acc.myfxhistoryrecord_set.all (keys_only = True).fetch (100)
            if not hist:
                break
            db.delete (hist)
    except:
        pass
    acc.delete ()
