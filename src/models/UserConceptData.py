from google.appengine.ext import ndb

class UserConceptData(ndb.Model):
	subject = ndb.KeyProperty(kind="Subject")
	concept = ndb.KeyProperty(kind="Concept")
	done = ndb.BooleanProperty(default=False)
	correct = ndb.BooleanProperty(default=False)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)
