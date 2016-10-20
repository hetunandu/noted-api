from google.appengine.ext import ndb

from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.Subject import Subject
from src.models.UserPlan import UserPlan

subjects_controller = Blueprint('subjects', __name__)


@subjects_controller.route('/', methods=['GET'])
@Utils.auth_required
def get(user):
    course = ndb.Key(urlsafe=user.course).get()
    if not course:
        return Respond.error("User not subscribed to a course", error_code=400)

    subjects = course.query_subjects()

    return Respond.success({"subjects": subjects})


@subjects_controller.route('/', methods=['POST'])
@Utils.admin_required
def store(user):
    """
    Store a subject. //TODO: Only admin users should be able to do this
    :param user:
    :return:
    """
    post = Utils.parse_json(request)
    subject = Subject(
        name=post['name'],
        course_key=ndb.Key(urlsafe=user.course)
    )

    if 'image' in post:
        subject.image = post['image']

    subject.put()

    return Respond.success(subject.dict_for_list())

@subjects_controller.route('/<subject_key>', methods=['GET'])
@Utils.auth_required
def view(user, subject_key):
    """
    Get the user progress of a subject and if they have paid for the notes of a subject
    """
    plan = _get_plan(user, subject_key)

    if len(plan) == 0:
        plan = False
    
    return Respond.success({
        "plan": plan[0].as_dict(),
        "paid": False
    })

@subjects_controller.route('/<subject_key>/plan', methods=['POST'])
@Utils.auth_required
def create_plan(user, subject_key):
    """
    Make a plan with the test date and portion
    """
    if len(_get_plan(user, subject_key)) > 0:
        return Respond.error("Plan already exists")
    
    post = Utils.parse_json(request)

    plan = UserPlan(
        subject=ndb.Key(urlsafe=subject_key),
        test_date=Utils.date_from_ms(post['test_date']),
        portion=map(Utils.urlsafe_to_key, post['portion']),
        parent=user.key
    )
    plan.put()

    return Respond.success("User plan created")


    


@subjects_controller.route('/<subject_key>/chapters', methods=['GET'])
@Utils.auth_required
def get_chapters(user, subject_key):

    subject = ndb.Key(urlsafe=subject_key).get()

    chapters = subject.query_chapters()

    return Respond.success({"chapters": chapters})


def _get_plan(user, subject_key):
    plan = UserPlan.query(
            UserPlan.subject == ndb.Key(urlsafe=subject_key),
            ancestor=user.key
        ).fetch()
    return plan
   