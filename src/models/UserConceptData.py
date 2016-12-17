from google.appengine.ext import ndb

class UserConceptData(ndb.Model):
	subject = ndb.KeyProperty(kind="Subject")
	concept = ndb.KeyProperty(kind="Concept")
	done = ndb.BooleanProperty(default=False)
	right = ndb.IntegerProperty(default=0)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)
