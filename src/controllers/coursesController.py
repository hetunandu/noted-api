from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.Course import Course
from google.appengine.ext import ndb

courses_controller = Blueprint('courses', __name__)


@courses_controller.route('/', methods=['GET'])
@Utils.auth_required
def get(user):
	"""
	Get all the available courses
	"""
	courses = map(Course.as_dict, Course.query().fetch())

	return Respond.success({"courses": courses})


@courses_controller.route('/', methods=['POST'])
@Utils.creator_required
def store(user):
	"""
	Store a course.
	:param user:
	:return:
	"""
	post = Utils.parse_json(request)
	course = Course(name=post['name'])
	course.put()

	return Respond.success(Course.as_dict(course))

