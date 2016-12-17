from google.appengine.ext import ndb

class UserSubjectIndex(ndb.Model):
	subject = ndb.KeyProperty()
	index = ndb.JsonProperty(repeated=True)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)

	