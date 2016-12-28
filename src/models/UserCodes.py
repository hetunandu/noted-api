from google.appengine.ext import ndb

class UserCodes(ndb.Model):
	code=ndb.StringProperty()
	points=ndb.IntegerProperty()
	uses=ndb.IntegerProperty()
