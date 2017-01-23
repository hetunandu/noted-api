import logging
from google.appengine.ext import ndb
import jwt
from datetime import datetime, timedelta

from passlib.hash import pbkdf2_sha256
from src.models.UserPointLog import UserPointLog
from src.models.UserSession import UserSession

JWT_SECRET = "LrwHQ^ac;!Wld<v"
PER_SESSION_VIEWS = 15
RESET_COST = 20
SESSION_SECONDS = 21600 # 6 hours

class User(ndb.Model):
	# Basic Account Details
	name = ndb.StringProperty(required=True)
	email = ndb.StringProperty()
	password = ndb.StringProperty(indexed=False)
	# the uri where the profile picture is uploaded
	picture_uri = ndb.StringProperty(indexed=False)
	# Basic Course details
	course = ndb.KeyProperty(kind="Course")
	college = ndb.StringProperty()
	# Type of the user
	type = ndb.StringProperty(choices=["Student", "Creator", "Admin"], default="Student")
	# Model time properties
	created_at = ndb.DateTimeProperty(auto_now_add=True)
	updated_at = ndb.DateTimeProperty(auto_now=True)

	# Get the dict representation of a user
	def as_dict(self):
		return {
			"key": self.key.urlsafe(),
			"name": self.name,
			"email": self.email,
			"picture_uri": self.picture_uri,
			"course": self.course.urlsafe() if self.course else None,
			"college": self.college,
			"type": self.type,
			"points": self.getPoints(),
			"session": self.getSession(),
			"created_at": self.created_at,
			"updated_at": self.updated_at
		}

	# Make a JWT Token for the user
	def make_token(self):
		token = jwt.encode(
			{
				'key': self.key.urlsafe(),
				'iat': datetime.utcnow(),
				'exp': datetime.utcnow() + timedelta(days=7)
			},
			JWT_SECRET,
			algorithm='HS256'
		)

		return token

	# Get a user from the provided token
	@classmethod
	def from_token(cls, token):
		try:
			decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
		except jwt.ExpiredSignatureError:
			logging.error('JWT token expired')
			return None

		if decoded is not None:
			user_key = ndb.Key(urlsafe=decoded['key'])
			user = user_key.get()
			return user

	# Hash a password
	@staticmethod
	def hash_password(password):
		return pbkdf2_sha256.encrypt(password, rounds=5, salt_size=16)

	# Verify hashed password
	def verify_password(self, password):
		return pbkdf2_sha256.verify(password, self.password)


	def getPoints(self):
		latest = UserPointLog.query(ancestor=self.key).order(-UserPointLog.created_at).get()

		if not latest:
			return 0

		return latest.points

	def addPoints(self, points, action):
		old_points = self.getPoints()

		UserPointLog(
			parent=self.key,
			change=points,
			points=old_points + points,
			action=action
			).put()

		return True

	def subtractPoints(self, points, action):
		old_points = self.getPoints()

		UserPointLog(
			parent=self.key,
			change=-points,
			points=old_points - points,
			action=action
			).put()

		return True

	def getSession(self):
		session = UserSession.query(ancestor=self.key).order(-UserSession.created_at).get()

		if not session:
			session = self.createSession()

		seconds_passed = (datetime.now() - session.created_at).seconds

		if seconds_passed > SESSION_SECONDS:
			session = self.createSession()

		return {
			"views": session.views,
			"created_at": session.created_at,
			"updated_at": session.updated_at
		}


	def createSession(self):		
		session = UserSession(
			parent=self.key,
			views=PER_SESSION_VIEWS
			)

		session.put()

		return session


