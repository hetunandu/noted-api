from google.appengine.ext import ndb

class UserConceptData(ndb.Model):
	subject = ndb.KeyProperty(kind="Subject")
	concept = ndb.KeyProperty(kind="Concept")
	skip = ndb.IntegerProperty(default=0)
	read = ndb.IntegerProperty(default=0)
	right = ndb.IntegerProperty(default=0)
	wrong = ndb.IntegerProperty(default=0)
	star = ndb.BooleanProperty(default=False)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)
