from google.appengine.ext import ndb

class UserConcept(ndb.Model):
	subject = ndb.KeyProperty(kind="Subject")
	concept = ndb.KeyProperty(kind="Concept")
	read = ndb.IntegerProperty(default=0)
	important = ndb.BooleanProperty(default=False)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)
