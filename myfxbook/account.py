from google.appengine.ext import db
from google.appengine.api.labs import taskqueue


# MyFXBook list of watched accounts
class MyFXAccount (db.Model):
    id = db.StringProperty (required = True)
    last_page = db.IntegerProperty (default = 0)
    orders = db.IntegerProperty (default = 0)
    url = db.StringProperty ()
    pairs_map = db.BlobProperty ()


def by_id (id):
    return MyFXAccount.gql ("WHERE id=:1", id).get ()


def schedule_fetch (acc_id, time):
    q = taskqueue.Queue ("myfxhistory")
    q.add (taskqueue.Task (method = "GET", url = "/fetch-myhist?id=%s" % acc_id, countdown = time))

