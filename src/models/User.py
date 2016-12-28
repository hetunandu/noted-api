import logging
from google.appengine.ext import ndb
import jwt
import datetime
from passlib.hash import pbkdf2_sha256
from src.models.UserPointLog import UserPointLog


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

	_secret = "LrwHQ^ac;!Wld<v"  # Used for JWT TOKEN

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
			"created_at": self.created_at,
			"updated_at": self.updated_at
		}

	# Make a JWT Token for the user
	def make_token(self):
		token = jwt.encode(
			{
				'key': self.key.urlsafe(),
				'iat': datetime.datetime.utcnow(),
				'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
			},
			self._secret,
			algorithm='HS256'
		)

		return token

	# Get a user from the provided token
	@classmethod
	def from_token(cls, token):
		try:
			decoded = jwt.decode(token, User._secret, algorithms=['HS256'])
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

