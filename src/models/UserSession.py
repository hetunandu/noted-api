from google.appengine.ext import ndb

class UserSession(ndb.Model):
	views = ndb.IntegerProperty(default=10)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)
