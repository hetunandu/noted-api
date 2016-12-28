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


@subjects_controller.route('/', methods=['GET'])
@Utils.auth_required
def get(user):
	course = user.course.get()
	if not course:
		return Respond.error("User not subscribed to a course", error_code=400)

	subjects = map(Subject.dict_for_list, Subject.query(ancestor=course.key).fetch())

	return Respond.success({"subjects": subjects})

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
		parent=user.course
	)

	subject.put()

	return Respond.success(subject.dict_for_list())

@subjects_controller.route('/<subject_key>/chapters', methods=['GET'])
@Utils.auth_required
def get_chapters(user, subject_key):

	subject = Utils.urlsafe_to_key(subject_key).get()

	chapters = map(Chapter.for_list, Chapter.query(ancestor=subject.key).order(Chapter.srno).fetch())

	return Respond.success({"chapters": chapters})





