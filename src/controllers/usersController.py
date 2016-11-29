from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.User import User
from google.appengine.api import urlfetch
import logging
import simplejson as json

users_controller = Blueprint('users', __name__)


@users_controller.route('/admin/register', methods=['POST'])
@Utils.admin_required
def admin_register(user):
	"""
	Get the post variables and register the user
	:return: User token
	"""
	# parse the json request
	post = Utils.parse_json(request)

	# Check if basic account info is in the post
	if 'name' not in post or 'email' not in post or 'password' not in post:
		return Respond.error("Validation Error", error_code=422)

	# Check if email has not registered before
	if User.query(User.email == post['email']).count() > 0:
		return Respond.error("User account with this email already registered", 401)

	# Create a user model
	user = User(
		name=post['name'],
		email=post['email'],
		password=User.hash_password(post['password']),
		type=post['type']
	)

	# Add other properties of the user if sent
	if 'year' in post:
		user.year = post['year']
	if 'course' in post:
		user.course = post['course']
	if 'college' in post:
		user.college = post['college']
	if 'picture_uri' in post:
		user.picture_uri = post['picture_uri']

	# Save the user
	user.put()

	# Make a token for the user
	token = user.make_token()

	# Respond with the token
	return Respond.success({
		"token": token,
		"user" : user.as_dict()
	})


@users_controller.route('/login', methods=['POST'])
def admin_login():
	"""
	Login a user
	:return:
	"""
	# Pass the post details
	post = Utils.parse_json(request)

	# Check if email and password in the post
	if 'email' not in post or 'password' not in post:
		return Respond.error("Email password not found", error_code=422)

	# Find the user with that email
	user = User.query(User.email == post['email']).get()

	# If user not found
	if user is None:
		return Respond.error("User not found with the provided email", error_code=404)

	if user.type is not "Admin" or user.type is not "Creator":
		return Respond.error("Login with password not allowed", error_code=422)

	# If password not correct
	if not user.verify_password(post['password']):
		return Respond.error("Password incorrect")

	# Make token
	token = user.make_token()

	# Respond with user and token
	return Respond.success({
		"token": token,
		"user": user.as_dict()
	})

@users_controller.route('/social', methods=['POST'])
def social_login():
	"""
	Login via google
	With the id token get user details, if the user does not 
	exist then create it. If the user is coming back then just save the id token 
	Then make a token and send it to the client
	"""
	post = Utils.parse_json(request)
	id_token = post['id_token']

	url = 'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token=%s' % id_token

	try:
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			result = json.loads(result.content)
			name = result['name']
			email = result['email']
			picture = result['picture']
		else:
			error = 'Status code: {} , Response: {}'.format(result.status_code, result.content)
			logging.error(error)
			return Respond.error('Error getting user info from google.')
	except urlfetch.Error:
		logging.exception('Caught exception fetching url')
		return Respond.error('Error getting user info from google.')
	
	users = User.query(User.email == email).fetch()
	
	if len(users) > 1:
		return Respond.error("There was an error", error_code=422)
	
	elif len(users) == 1:
		# User already exists. Just make a token and return
		user = users[0]
		
		# Make token
		token = user.make_token()

		# Respond with user and token
		return Respond.success({
			"token": token,
			"user": user.as_dict()
		})
	else:
		# New User. Create and send token
		user = User(
			name=name,
			email=email,
			picture_uri=picture
		)
		user.put()

		# Make token
		token = user.make_token()

		# Respond with user and token
		return Respond.success({
			"token": token,
			"user": user.as_dict()
		})

@users_controller.route('/details')
@Utils.auth_required
def user_details(user):
	"""
	Send the details of the user via JWT token
	"""
	return Respond.success({
		"user": user.as_dict()
	})
