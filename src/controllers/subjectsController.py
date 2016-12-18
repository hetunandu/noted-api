from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.Subject import Subject
from src.models.Chapter import Chapter
from src.models.Concept import Concept
from src.models.UserConceptData import UserConceptData
from datetime import datetime, timedelta
import random
import logging

subjects_controller = Blueprint('subjects', __name__)

FREE_CONCEPT_LIMIT = 10
FREE_WAIT_TIME = 21600

@subjects_controller.route('/', methods=['GET'])
@Utils.auth_required
def get(user):
	course = user.course.get()
	if not course:
		return Respond.error("User not subscribed to a course", error_code=400)

	subjects = course.query_subjects()

	for subject in subjects:
		subject_key = Utils.urlsafe_to_key(subject['key'])
		
		# Total number of concepts
		chapter_keys = Chapter.query(ancestor=subject_key).fetch(keys_only=True)
		subject['total_concepts'] = Concept.query(
			Concept.chapter_key.IN(chapter_keys)
		).count()

		concepts_data_query = UserConceptData.query(
			UserConceptData.subject == subject_key,
			ancestor=user.key
		).order(-UserConceptData.created_at)

		has_data_count = concepts_data_query.count()            
		if has_data_count > 0:

			# How many concepts have data stores
			subject['has_data_count'] = has_data_count
		
			# How many concepts have been marked done
			subject['is_done_count'] = concepts_data_query.filter(
				UserConceptData.done == True
			).count()

			# How many concepts are correct
			subject['is_right_count'] = UserConceptData.query(
				UserConceptData.subject == subject_key,
				UserConceptData.right > 0,
				ancestor=user.key
			).count()

			# How many concepts have been marked done as false 
			# Basically not done
			subject['is_skipped_count'] = concepts_data_query.filter(
				UserConceptData.done == False
			).count()

			# the free limit for the user
			subject['concept_limit'] = FREE_CONCEPT_LIMIT
		
			# When will the user get new concepts
			latest_data = concepts_data_query.get()
			subject['next_concepts_on'] = latest_data.created_at + timedelta(seconds=FREE_WAIT_TIME)

		else:
			subject['has_data_count'] = 0

	return Respond.success({"subjects": subjects})


@subjects_controller.route('/<subject_key>/revise')
@Utils.auth_required
def get_revision_concepts(user, subject_key):
	"""
	Fetch the DAILY_LIMIT concepts to be sent to the
	"""
	# Find the subject entity
	subject = Utils.urlsafe_to_key(subject_key).get()
	# Empty list to add the concepts
	todays_concepts = []
	
	# Find concepts with data present in the subject
	query_user_concepts = UserConceptData.query(
		UserConceptData.subject == subject.key,
		ancestor=user.key
	)
	# No data made before. First time
	if query_user_concepts.count() == 0:
	# Add DAILY_LIMIT concepts to the array and send

		# Find Chapters in the subject
		chapters = Chapter.query(ancestor=subject.key).order(Chapter.created_at).fetch()

		# Get the concepts in the index 
		for chapter in chapters:
			for concept in chapter.index:
				# Add only if the daily limit has reached
				if len(todays_concepts) < FREE_CONCEPT_LIMIT:
					# Create user data for the new concepts
					user_data = UserConceptData(
						subject=subject.key,
						concept=Utils.urlsafe_to_key(concept['key']),
						parent=user.key
					)
					user_data.put_async()
					# Add it to the array
					todays_concepts.append(concept['key'])
				else:
					break

	else:
		# Add the not understood concepts in the todays_concepts list
		for concept in query_user_concepts.filter(
				UserConceptData.done == False
			).order(UserConceptData.created_at):
			todays_concepts.append(concept.concept.urlsafe())

		# if less than DAILY_LIMIT are in todays_concepts
		if len(todays_concepts) < FREE_CONCEPT_LIMIT:
			# Check if 24 hours have passed since the last created data
			latest_data = query_user_concepts.order(-UserConceptData.created_at).get()
			timeElapsed = datetime.now() - latest_data.created_at
			if timeElapsed.seconds > FREE_WAIT_TIME:
				# get the reaming concepts from chapters
				chapters = Chapter.query(ancestor=subject.key).order(Chapter.created_at).fetch()
			
				# make a list of concepts with user data
				concepts_with_user_data = []
				for concept_data in query_user_concepts.order(UserConceptData.created_at):
					concepts_with_user_data.append(concept_data.concept.urlsafe())

				# Go through the chapter index to find out the next concepts to send them
				for chapter in chapters:
					for concept in chapter.index:
						if len(todays_concepts) < FREE_CONCEPT_LIMIT:
							# Check if concept_data has already been made
							if not concept['key'] in concepts_with_user_data:
								# Create user data for the new concepts
								user_data = UserConceptData(
									subject=subject.key,
									concept=Utils.urlsafe_to_key(concept['key']),
									parent=user.key
								)
								user_data.put_async()
								# Add it to the array
								todays_concepts.append(concept['key'])
						else:
							break

	concepts_with_data = []
	for concept in todays_concepts:
		data = Utils.urlsafe_to_key(concept).get().to_dict()
		concepts_with_data.append(data)

	return Respond.success({"concepts": concepts_with_data})

@subjects_controller.route('/<subject_key>/test')
@Utils.auth_required
def get_test_concepts(user, subject_key):
	"""
	Take 10 concepts in done randomly and send it to the user
	"""
	# Find the subject entity
	subject = Utils.urlsafe_to_key(subject_key).get()
	
	# Find concepts with concepts marked as done
	concepts_done_query = UserConceptData.query(
		UserConceptData.subject == subject.key,
		UserConceptData.done == True,
		ancestor=user.key,
	)

	# If questions less than 10, return error
	if concepts_done_query.count() < 10:
		return Respond.error("Less than 10 concepts marked done")

	# Fetch the concepts
	concepts_done = concepts_done_query.fetch(projection=[UserConceptData.concept])
	
	# Take random 10 random concepts
	
	# Empty list to add the concepts
	random_concepts = []
	# Set the daily limit
	LIMIT = 5

	N = 0
	for concept in concepts_done:
	        N += 1
	        if len( random_concepts ) < LIMIT:
	            random_concepts.append( concept )
	        else:
	            s = int(random.random() * N)
	            if s < LIMIT:
	                random_concepts[ s ] = concept

	# Get full entity
	full_concepts = []

	for concept_data in random_concepts:
		entity = concept_data.concept.get()
		full_concepts.append(entity.to_dict())

	# send them
	return Respond.success({"concepts": full_concepts})



@subjects_controller.route('/', methods=['POST'])
@Utils.creator_required
def store(user):
	"""
	Store a subject.
	:param user:
	:return:
	"""
	post = Utils.parse_json(request)
	subject = Subject(
		name=post['name'],
		course_key=user.course
	)

	if 'image' in post:
		subject.image = post['image']

	subject.put()

	return Respond.success(subject.dict_for_list())

@subjects_controller.route('/<subject_key>/chapters', methods=['GET'])
@Utils.auth_required
def get_chapters(user, subject_key):
	if user.type is "Student":
		if subject_key not in user.has_access:
			return Respond.error("User does not have access to the subject notes", error_code=403)

	subject = Utils.urlsafe_to_key(subject_key).get()

	chapters = subject.query_chapters()

	return Respond.success({"chapters": chapters})