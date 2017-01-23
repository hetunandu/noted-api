from google.appengine.ext import ndb

class UserSession(ndb.Model):
	views = ndb.IntegerProperty(default=15)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)


	def as_dict(self):
		return {
			"views": self.views
			"created_at": self.created_at,
			"updated_at": self.updated_at
		}