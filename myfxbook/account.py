from google.appengine.ext import db

# MyFXBook list of watched accounts
class MyFXAccount (db.Model):
    id = db.StringProperty (required = True)
    last_page = db.IntegerProperty (default = 0)
    orders = db.IntegerProperty (default = 0)
    url = db.StringProperty ()
    pairs_map = db.BlobProperty ()

def by_id (id):
    return MyFXAccount.gql ("WHERE id=:1", id).get ()
