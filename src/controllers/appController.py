from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.Subject import Subject
from src.models.Chapter import Chapter
from src.models.Concept import Concept
from src.models.UserConceptData import UserConceptData
# from datetime import datetime, timedelta
import random
# import logging

app_controller = Blueprint('app', __name__)

@app_controller.route('/subjects')
@Utils.auth_required
def subjects(user):
	"""
	Get the list of subjects and user progress
	"""
	
	# Get user course
	course = user.course.get()

	# Get list of subjects
	subject_list = course.query_subjects()

	response = []
	# Add it to the response array
	for subject in subject_list:
		response.append(subject.dict_for_list())

	# TODO Get the revised concept count

	Respond.success({"subjects": response})
	
	

@app_controller.route('/subjects/<subject_key>')
@Utils.auth_required
def subject_data(user, subject_key):
	"""
	Get the subject and its actions
	"""
	# Find subject from subject key
	subject = Utils.urlsafe_to_key(subject_key).get()

	# Fetch user data of concepts in index
	subject_index = UserSubjectIndex.query(
			UserConceptData.subject == subject.key,
			ancestor=user.key
		).fetch()

	index_with_data = []
	


	"""
	{
		"name": "Economics",
		"index": [
			{
				"chapter_name": "Micro Economics",
				concepts: [
					{
						"concept_id": "asdg323",
						"status": "locked"
					}
				]
			}
		]
	}

	"""


@app_controller.route('/subjects/<subject_key>/revise')
@Utils.auth_required
def subject_revise(user, subject_key):
	"""
	send revision concepts
	"""
	# Find not revised concepts
	# Fetch the first 5 from them
	# Save the revision
	# Send concepts
	"""
	{
		"revision_id": "hw7d23",
		"concepts": [
			{
				"id": "72basdad"
			}
		]
	}
	"""

@app_controller.route('/revise/<revision_key>/result', methods=['POST'])
@Utils.auth_required
def revision_result(user, revision_key):
	"""
	Save the result of the revison
	Charge the user
	"""
	"""
		POST:
		{
			"revison_id": "hw7d23",
			"result": [
				{
					"id": "72basdad",
					"revised": true,
					"skipped": false
				}
			]
		}
	"""
	# Save the result
	# Charge the user accrding to the revison id
	# return success

@app_controller.route('/subjects/<subject_key>/test')
@Utils.auth_required
def subject_test(user, subject_key):
	"""
	Send test concepts
	"""
	# Find revised concepts
	# Fetch 5 randomly
	# Save the test
	# Send concepts
	"""
	{
		"test_id": "asdas8ewfwe"
		"concepts": [
			{
				"id": "23123njad"
			}
		]
	}
	"""


@app_controller.route('/test/<test_key>/result', methods=['POST'])
@Utils.auth_required
def test_result(user, test_key):
	"""
	Save the result of the test
	"""
	"""
		POST:
		{
			"test_id": "asdas9ewfwe",
			"result": [
				{
					"id": "72basdad",
					"correct": true,
					"wrong": false,
					"skipped": false
				}
			]
		}
	"""


@app_controller.route('/concept/<concept_key>/revise')
@Utils.auth_required
def concept_revise(user, concept_key):
	"""
	Find the concept and status
	Save revision
	Send the concept
	"""
	"""
	{
		"concept": {
			"id": '2344234',
			"explanation": []
		}
	}
	"""














