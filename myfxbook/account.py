import time

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue


# MyFXBook list of watched accounts
class MyFXAccount (db.Model):
    id = db.StringProperty (required = True)
    orders = db.IntegerProperty (default = 0)
    url = db.StringProperty ()
    pairs_map = db.BlobProperty ()
    delta_minutes = db.IntegerProperty (default = 0)


def by_id (id):
    return MyFXAccount.gql ("WHERE id=:1", id).get ()


def schedule_fetch (acc_id):
    q = taskqueue.Queue ("myfxhistory")
    q.add (taskqueue.Task (method = "GET", url = "/fetch-myhist?id=%s" % acc_id))


def get_last_update (acc_id):
    ts = memcache.get ("myfx-last-%s" % acc_id)
    if ts:
        return ts
    else:
        return "0"

def set_last_update (acc_id):
    memcache.set ("myfx-last-%s" % acc_id, int (time.time ()))
