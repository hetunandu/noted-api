from flask import Blueprint, request
from google.appengine.api import urlfetch
from datetime import datetime, timedelta
import random
import logging
import simplejson as json

from src.common import Utils
from src.common.Respond import Respond

from src.models.Subject import Subject
from src.models.Chapter import Chapter
from src.models.Concept import Concept
from src.models.User import User
from src.models.UserConceptData import UserConceptData
from src.models.UserConcept import UserConcept
from src.models.UserTests import UserTests
from src.models.UserPointLog import UserPointLog
from src.models.SessionData import SessionData
from src.models.UserCodes import UserCodes


app_controller = Blueprint('app', __name__)

VIEWS_PER_SESSION = 10
RESET_COST = 25
SESSION_SECONDS = 18000

@app_controller.route('/login', methods=['POST'])
def app_login():
	"""
	Login via google
	With the id token get user details, if the user does not 
	exist then create it. 
	If the user is coming back then make a token and send it to the client
	"""
	post = Utils.parse_json(request)
	id_token = post['id_token']

	# TODO Verify token https://developers.google.com/identity/sign-in/web/backend-auth

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
	
	user = User.query(User.email == email).get()
	
	if user:
		# User already exists. Just make a token and return
		
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

@app_controller.route('/user')
@Utils.auth_required
def user_details(user):
	"""
	Send the details of the user via JWT token
	"""
	return Respond.success({
		"user": user.as_dict()
	})

@app_controller.route('/courses/<course_key>/subscribe', methods=['POST'])
@Utils.auth_required
def subscribe(user, course_key):
	"""
	Subscribe a course
	:param user:
	:param course_key:
	:return:
	"""
	post = Utils.parse_json(request)
	user.course = Utils.urlsafe_to_key(course_key)
	user.college = post['college']
	user.put()

	return Respond.success("Course subscribed by user")


@app_controller.route('/subjects')
@Utils.auth_required
def subjects(user):
	"""
	Get the list of subjects and user progress
	"""
	# Get user course
	course = user.course.get()

	# Get list of subjects
	subject_list = Subject.query(ancestor=course.key).fetch()

	subjects = map(Subject.dict_for_list, subject_list)

	for subject in subjects:
		key = Utils.urlsafe_to_key(subject['key'])
		session_data = SessionData.query(
			SessionData.subject == key,
			ancestor=user.key).order(-SessionData.created_at).get()

		if not session_data:

			session_data = SessionData(
					subject=key,
					views_available=VIEWS_PER_SESSION,
					parent=user.key
				)

			session_data.put()
		else:

			seconds_passed = (datetime.now() - session_data.created_at).seconds

			if seconds_passed > SESSION_SECONDS:

				# Refresh session
				session_data = SessionData(
						subject=key,
						views_available=VIEWS_PER_SESSION,
						parent=user.key
					)

				session_data.put()

		subject['views_available'] = session_data.views_available
		
		subject['session_ends'] = session_data.created_at + timedelta(seconds = SESSION_SECONDS)
		
		subject['total_concepts'] = Concept.query(ancestor=key).count()

		subject['reset_cost'] = RESET_COST
		
		subject['read_concepts'] = UserConcept.query(
			UserConcept.subject == key,
			ancestor=user.key).count()
	
	return Respond.success({"subjects": subjects})


@app_controller.route('/subjects/<subject_key>/reset')
@Utils.auth_required
def reset_session(user, subject_key):

	if user.getPoints() < RESET_COST:
		return Respond.error('User does not have enough points', error_code=400)

	user.subtractPoints(RESET_COST, "Skipped cooldown")

	session_data = SessionData(
			subject=Utils.urlsafe_to_key(subject_key),
			views_available=10,
			parent=user.key
		)

	session_data.put()

	response = {
		"views_available": session_data.views_available,
		"session_ends": session_data.created_at + timedelta(seconds = SESSION_SECONDS)
	}

	return Respond.success(response)


@app_controller.route('/subjects/<subject_key>/index')
@Utils.auth_required
def subject_index(user, subject_key):

	subject = Utils.urlsafe_to_key(subject_key).get()
	
	index = []
	chapters = Chapter.query(ancestor=subject.key).order(Chapter.srno)

	for chapter in chapters:
		
		concepts = []
		concepts_list = Concept.query(ancestor=chapter.key).order(Concept.srno)
		for concept in concepts_list:
			concepts.append({
				"key": concept.key,
				"name": concept.name
			})

		user_data = UserConcept.query(
			UserConcept.subject == subject.key,
			ancestor=user.key
			).fetch()

		for concept in concepts:
			for data in user_data:
				if data.concept == concept['key']:
					concept['read'] = data.read
					concept['important'] = data.important

			concept['key'] = concept['key'].urlsafe()


		index.append({
			"key": chapter.key.urlsafe(),
			"name": chapter.name,
			"concepts": concepts
		})

	return Respond.success({"index": index})


@app_controller.route('/concepts/<concept_key>')
@Utils.auth_required
def read_concept(user, concept_key):
	"""
	Send the concept to the user
	"""
	concept = Utils.urlsafe_to_key(concept_key).get()

	chapter = concept.key.parent()
	subject = chapter.parent()

	session_data = SessionData.query(
		SessionData.subject == subject,
		ancestor=user.key).order(-SessionData.created_at).get()

	if session_data.views_available < 1 :
		return Respond.error("Not enough views left", error_code=420)


	session_data.views_available = session_data.views_available - 1
	session_data.put()

	return Respond.success({
		"concept": concept.to_dict(),
		"views_available": session_data.views_available
		})




@app_controller.route('/subjects/<subject_key>/revise')
@Utils.auth_required
def subject_revise(user, subject_key):
	"""
	Send revision concepts
	"""
	# Find not read concepts
	# Fetch the first 5 from them
	# Send concepts

	subject = Utils.urlsafe_to_key(subject_key).get()

	session_data = SessionData.query(
		SessionData.subject == subject.key,
		ancestor=user.key).order(-SessionData.created_at).get()

	if session_data.views_available < 5 :
		return Respond.error("Not enough views left", error_code=420)
	

	user_concepts = UserConcept.query(
		UserConcept.subject == subject.key,
		ancestor=user.key
		).fetch()

	chapters = Chapter.query(ancestor=subject.key).order(Chapter.srno)

	revision_concepts = []

	for chapter in chapters:
		
		concepts = Concept.query(ancestor=chapter.key).order(Concept.srno).fetch()

		for concept in concepts:
			if len(revision_concepts) < 5:
				if any(x.concept == concept.key for x in user_concepts):
					pass
				else:
					revision_concepts.append(concept.to_dict())
			else:
				break


	if len(revision_concepts) is 0:
		return Respond.error("No concepts left to revise", error_code=400)


	session_data.views_available = session_data.views_available - len(revision_concepts)

	session_data.put()

	return Respond.success({
		"concepts": revision_concepts,
		"views_available": session_data.views_available
		})


@app_controller.route('/subjects/<subject_key>/revise/result', methods=['POST'])
@Utils.auth_required
def revision_result(user, subject_key):
	"""
	Save the result and calculate points
	"""
	subject = Utils.urlsafe_to_key(subject_key).get()
	post = Utils.parse_json(request)
	points_counter = 0


	for result in post['result']:

		if result['marked'] == "read":

			concept = Utils.urlsafe_to_key(result['key']).get()

			data = UserConcept.query(
				UserConcept.concept == concept.key,
				ancestor=user.key
				).get()

			if not data:
				data = UserConcept(
					parent=user.key,
					subject=subject.key,
					concept=concept.key
					)

			data.read += 1

			data.put()

			user.addPoints(1, "Read concept")
			points_counter += 1


	return Respond.success({"new_points": points_counter})



@app_controller.route('/subjects/<subject_key>/test')
@Utils.auth_required
def subject_test(user, subject_key):
	"""
	Send test concepts
	"""
	subject_key = Utils.urlsafe_to_key(subject_key)

	session_data = SessionData.query(
		SessionData.subject == subject_key,
		ancestor=user.key).order(-SessionData.created_at).get()

	if session_data.views_available < 5 :
		return Respond.error("Not enough views left", error_code=400)

	# Find revised concepts
	concepts = UserConcept.query(
		UserConcept.subject == subject_key,
		ancestor=user.key
		).fetch()

	# send 5 randomly

	if len(concepts) < 5:
		return Respond.error("Less than 5 concepts read", error_code=400)

	# Unique indices
	random_nums = random.sample(range(1, len(concepts)), 5)

	test_concepts = []

	for i in random_nums:
		test_concepts.append(concepts[i].concept.get().to_dict())


	session_data.views_available = session_data.views_available - 5
	session_data.put()

	return Respond.success({
		"concepts": test_concepts,
		"views_available": session_data.views_available
		})

@app_controller.route('/subjects/<subject_key>/test/result', methods=['POST'])
@Utils.auth_required
def test_result(user, subject_key):
	"""
	Save the result and calculate points
	"""
	subject = Utils.urlsafe_to_key(subject_key).get()
	post = Utils.parse_json(request)
	points_counter = 0


	for result in post['result']:

		if result['marked'] == "right":

			UserTests(
				concept=Utils.urlsafe_to_key(result['key']),
				right=True,
				parent=user.key
				).put()

			user.addPoints(3, "Answered correctly")
			points_counter += 3

		if result['marked'] == "wrong":
			UserTests(
				concept=Utils.urlsafe_to_key(result['key']),
				right=False,
				parent=user.key
				).put()

			user.addPoints(1, "Answered incorrectly")
			points_counter += 1


	return Respond.success({"new_points": points_counter})


@app_controller.route('/users/code/redeem', methods=['POST'])
@Utils.auth_required
def code_redeem(user):
	"""
	Check code for user and give points accordingly
	"""

	post = Utils.parse_json(request)

	code_data = UserCodes.query(UserCodes.code == post['code'], ancestor=user.key).get()

	if not code_data:
		return Respond.error('User does not have access to this code', error_code=400)


	user.addPoints(code_data.points, "Used code: " + code_data.code)

	return Respond.success({"new_points": code_data.points})



@app_controller.route('/users/<user_key>/code', methods=['POST'])
@Utils.admin_required
def add_code_for_user(user, user_key):
	"""
	Add a code for a user to user
	"""

	post = Utils.parse_json(request)

	UserCodes(
		parent=Utils.urlsafe_to_key(user_key),
		code=post['code'],
		points=post['points']
	).put()

	return Respond.success("Code added")












