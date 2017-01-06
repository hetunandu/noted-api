from google.appengine.ext import ndb

class Payment(ndb.Model):
	user=ndb.KeyProperty(kind="User")
	cost=ndb.IntegerProperty()
	points=ndb.IntegerProperty()
	request_id=ndb.StringProperty()
	request_url=ndb.StringProperty()
