from google.appengine.ext import ndb

from src.models.Chapter import Chapter


class Subject(ndb.Model):
	course_key = ndb.KeyProperty(kind="Course")
	name = ndb.StringProperty(indexed=False)
	image = ndb.StringProperty(indexed=False)
	isDraft = ndb.BooleanProperty(default=True)
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)

	def query_chapters(self):
		chapters = []

		chapters_query = Chapter.query(ancestor=self.key).order(Chapter.created_at)

		for chapter in chapters_query:
			chapters.append(chapter.for_list())

		return chapters

	def dict_for_list(self):
		return {
			"key": self.key.urlsafe(),
			"name": self.name
		}
