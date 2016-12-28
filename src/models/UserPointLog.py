from google.appengine.ext import ndb

class UserPointLog(ndb.Model):
	# Action taken by the user
	action = ndb.StringProperty()
	# The + or - Change of points becasue of the action
	change = ndb.IntegerProperty()
	# Final points after change
	points = ndb.IntegerProperty()
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	