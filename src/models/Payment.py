from google.appengine.ext import ndb

class Payment(ndb.Model):
	user=ndb.KeyProperty(kind="User")
	cost=ndb.IntegerProperty()
	points=ndb.IntegerProperty()
	request_id=ndb.StringProperty()
	request_url=ndb.StringProperty(indexed=False)
	payment_id=ndb.StringProperty(indexed=False)
	status=ndb.StringProperty()
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)
