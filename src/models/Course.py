from google.appengine.ext import ndb

from src.models.Subject import Subject


class Course(ndb.Model):
    name = ndb.StringProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def single_dic(self):
        return {
            "key": self.key.urlsafe(),
            "name": self.name
        }

    def query_subjects(self):
        subjects = []
        subjects_query = Subject.query(Subject.course_key == self.key).order(Subject.created_at)

        for subject in subjects_query:
            subjects.append(subject.dict_for_list())

        return subjects
