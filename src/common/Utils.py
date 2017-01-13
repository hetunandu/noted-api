import logging
from functools import wraps

from flask import request
from src.common.Respond import Respond
from src.models.User import User
from google.appengine.ext import ndb
import datetime
import requests


def parse_json(passed_request):
	parsed = passed_request.get_json()
	logging.info('Request: %s' % parsed)
	return parsed


def get_user():
	token = request.headers.get('Authorization')
	user = User.from_token(token)
	if user is None:
		return False
	else:
		return user

def urlsafe_to_key(key):
	 return ndb.Key(urlsafe=key)

def date_from_ms(ms):
	return datetime.datetime.fromtimestamp(float(ms))



def send_mail(to, subject, message):
    requests.post(
        "https://api.mailgun.net/v3/mg.noted.study/messages",
        auth=("api", "key-d05bbfcd9406505468a659a0b7533dc2"),
        data={"from": "Noted Study <app@noted.study>",
              "to": [to.name, to.email],
              "subject": subject,
              "text": message})

    return True


def auth_required(original_function):
	@wraps(original_function)
	def wrapper_func(*args, **kwargs):
		token = request.headers.get('Authorization')
		if token is None:
			return Respond.error('Auth Required', 401)

		user = User.from_token(token)

		if user is None:
			return Respond.error('User not found', 400)
		else:
			return original_function(user, *args, **kwargs)

	return wrapper_func

def admin_required(original_function):
	@wraps(original_function)
	def wrapper_func(*args, **kwargs):
		token = request.headers.get('Authorization')

		if token is None:
			return Respond.error('Auth Required', 401)

		user = User.from_token(token)

		if user is None:
			return Respond.error('User not found', 400)
		elif user.type != "Admin":
			return Respond.error("User not an admin", 422)
		else:
			return original_function(user, *args, **kwargs)

	return wrapper_func

def creator_required(original_function):
	@wraps(original_function)
	def wrapper_func(*args, **kwargs):
		token = request.headers.get('Authorization')

		if token is None:
			return Respond.error('Auth Required', 401)

		user = User.from_token(token)
		if user is None:
			return Respond.error('User not found', 400)
		elif (user.type != 'Admin' and user.type != 'Creator'):
			return Respond.error("Permission Denied", 422)
		else:
			return original_function(user, *args, **kwargs)

	return wrapper_func