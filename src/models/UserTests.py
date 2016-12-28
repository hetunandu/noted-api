from google.appengine.ext import ndb

class UserTests(ndb.Model):
	concept = ndb.KeyProperty(kind="Concept")
	right = ndb.BooleanProperty()
	created_at = ndb.DateTimeProperty(auto_now_add=True)
