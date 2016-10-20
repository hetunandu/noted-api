from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.Course import Course

courses_controller = Blueprint('courses', __name__)


@courses_controller.route('/', methods=['POST'])
@Utils.auth_required
def store(user):
    """
    Store a course. //TODO: Only admin users should be able to do this
    :param user:
    :return:
    """
    post = Utils.parse_json(request)
    course = Course(name=post['name'])
    course.put()

    return Respond.success(course.single_dic())

@courses_controller.route('/<course_key>/subscribe', methods=['POST'])
@Utils.auth_required
def subscribe(user, course_key):
    """
    Subscribe a course
    :param user:
    :param course_key:
    :return:
    """
    user.course = course_key
    user.put()

    return Respond.success("Course subscribed by user")