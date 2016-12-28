from google.appengine.ext import ndb

class SessionData(ndb.Model):
	subject = ndb.KeyProperty(kind="Subject")
	views_available = ndb.IntegerProperty(default=10)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)
