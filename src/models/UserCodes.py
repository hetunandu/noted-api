from google.appengine.ext import ndb

class UserCodes(ndb.Model):
	srno=ndb.IntegerProperty()
	code=ndb.StringProperty()
	points=ndb.IntegerProperty()
	repName=ndb.StringProperty()
	activated=ndb.BooleanProperty(default=False)
	activatedBy=ndb.KeyProperty(kind='User')