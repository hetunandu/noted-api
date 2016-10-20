from google.appengine.ext import ndb
import datetime
from src.models.Concept import Concept


class UserPlan(ndb.Model):
    subject = ndb.KeyProperty(kind="Subject")
    test_date = ndb.DateProperty(indexed=True)
    portion = ndb.KeyProperty(kind="Chapter", repeated=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def as_dict(self):
        return {
            "days_left": self._days_left(),
            "concepts_left": self._concepts_left()
        }


    def _days_left(self):
        delta = self.test_date - datetime.date.today()
        return delta.days

    def _concepts_left(self):
        return len(Concept.query(ancestor=self.key).fetch())