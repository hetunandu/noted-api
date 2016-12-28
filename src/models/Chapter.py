from google.appengine.ext import ndb


class Chapter(ndb.Model):
	name = ndb.StringProperty()
	srno = ndb.IntegerProperty()
	index = ndb.JsonProperty(repeated=True)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)

	# Get the dict representation of a note
	def for_list(self):
		return {
			"name": self.name,
			"key": self.key.urlsafe(),
			"created_at": self.created_at,
			"updated_at": self.updated_at
		}

	def single_dic(self):
		return {
			"key": self.key.urlsafe(),
			"name": self.name,
			"index": self.index,
			"created_at": self.created_at,
			"updated_at": self.updated_at
		}

	def add_to_index(self, concept):
		self.index = self.index + [{
			"key": concept.key.urlsafe(),
			"name": concept.name
		}]
		self.put()
		return True
