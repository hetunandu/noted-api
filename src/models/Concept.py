from google.appengine.ext import ndb


class References(ndb.Model):
    title = ndb.StringProperty()
    source = ndb.StringProperty()

    @staticmethod
    def ref_to_dict(ref):
        return{
            "title": ref.title,
            "source": ref.source
        }


class Concept(ndb.Model):
    name = ndb.StringProperty(required=True)
    chapter_key = ndb.KeyProperty(kind="Chapter", required=True)
    isDraft = ndb.BooleanProperty(default=False)
    explanation = ndb.JsonProperty()
    references = ndb.StructuredProperty(References, repeated=True)
    tips = ndb.StringProperty(repeated=True)
    questions = ndb.StringProperty(repeated=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def to_dict(self):
        return {
            "name": self.name,
            "key": self.key.urlsafe(),
            "explanation": self.explanation or [],
            "references": map(References.ref_to_dict, self.references),
            "tips": self.tips,
            "questions": self.questions
        }
