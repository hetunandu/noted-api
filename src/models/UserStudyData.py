from google.appengine.ext import ndb

class UserStudyData(ndb.Model):
    subject = ndb.KeyProperty(kind="Subject")
    concept = ndb.KeyProperty(kind="Concept")
    action = ndb.StringProperty(choices=["understood", "not-understood", "wrong", "right"])
    created_at = ndb.DateTimeProperty(auto_now_add=True)

        