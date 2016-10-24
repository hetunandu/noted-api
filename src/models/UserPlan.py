from google.appengine.ext import ndb
import datetime
from src.models.Concept import Concept
from src.models.UserStudyData import UserStudyData


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
        # concepts_in_portion = []
        # for chapter in self.portion:
        #     concepts = Concept.query(Concept.chapter_key == chapter.key).fetch()
        #     concepts_in_portion.append(concepts)
        

        # for concept in concepts_in_portion:
        #     concepts_with_data = UserStudyData.query(
        #                             UserStudyData.concept == concept.key,
        #                             ancestor=self.ancestor
        #                         ).count()
        return False
            

        

