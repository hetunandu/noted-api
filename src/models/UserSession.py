from google.appengine.ext import ndb
from src.common.consts import RESET_COST, PER_SESSION_VIEWS, SESSION_SECONDS, PRO_COST


class UserSession(ndb.Model):
	views = ndb.IntegerProperty(default=15)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)


	def as_dict(self):
		return {
			"views": self.views,
			"reset_cost": RESET_COST,
			"pro_cost": PRO_COST,
			"session_seconds": SESSION_SECONDS,
			"created_at": self.created_at,
			"updated_at": self.updated_at
		}

	
