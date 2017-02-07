from flask import Blueprint, request
from google.appengine.api import urlfetch
import random
import logging
import simplejson as json

from src.common import Utils
from src.common.Respond import Respond
from src.common.consts import PER_SESSION_VIEWS, RESET_COST, PRO_COST

from src.models.Subject import Subject
from src.models.Chapter import Chapter
from src.models.Concept import Concept
from src.models.User import User
from src.models.UserConcept import UserConcept
from src.models.UserTests import UserTests
from src.models.UserSession import UserSession
from src.models.UserCodes import UserCodes

app_controller = Blueprint('app', __name__)


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


@app_controller.route('/user/points')
@Utils.auth_required
def user_points(user):
    """
    Send the points of the user
    """
    return Respond.success({
        "points": user.getPoints()
    })


@app_controller.route('/courses/<course_key>/subscribe', methods=['POST'])
@Utils.auth_required
def subscribe(user, course_key):
    """
    Subscribe a course
    :param user:
    :param course_key:
    :return: Response
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
    Get the list of subjects and their index
    """

    # Get user course
    course = user.course.get()

    # Get list of subjects
    subject_list = Subject.query(Subject.isDraft == False, ancestor=course.key).fetch()

    user_data = UserConcept.query(ancestor=user.key).fetch()

    response = []

    for subject in subject_list:
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

        response.append({
            "key": subject.key.urlsafe(),
            "name": subject.name,
            "index": index
        })

    return Respond.success({"subjects": response})


@app_controller.route('/session/reset')
@Utils.auth_required
def reset_session(user):
    if user.getPoints() < RESET_COST:
        return Respond.error('User does not have enough points', error_code=400)

    user.subtractPoints(RESET_COST, "Skipped cooldown")

    session = UserSession(
        views=PER_SESSION_VIEWS,
        parent=user.key
    )

    session.put()

    return Respond.success({"session": session.as_dict(), "balance": user.getPoints()})


# @app_controller.route('/subjects/<subject_key>/progress')
# @Utils.auth_required
# def user_progress(user):
# 	subject = Utils.urlsafe_to_key(subject_key)

# 	total_concepts = Concept.query(ancestor=subject.key).count()

# 	read_concepts = UserConcept.query(
# 		UserConcept.subject == subject.key,
# 		UserConcept.read >= 1,
# 		ancestor=user.key).count()


@app_controller.route('/subjects/<subject_key>/index')
@Utils.auth_required
def subject_index(user, subject_key):
    subject = Utils.urlsafe_to_key(subject_key).get()

    index = []
    chapters = Chapter.query(ancestor=subject.key).order(Chapter.srno)

    # user_data = UserConcept.query(
    #     UserConcept.subject == subject.key,
    #     ancestor=user.key
    # ).fetch()

    for chapter in chapters:

        concepts = []
        concepts_list = Concept.query(ancestor=chapter.key).order(Concept.srno)
        for concept in concepts_list:
            concepts.append({
                "key": concept.key,
                "name": concept.name
            })

        for concept in concepts:
            # for data in user_data:
            #     if data.concept == concept['key']:
            #         concept['read'] = data.read
            #         concept['important'] = data.important

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

    if not user_has_views(user, 1):
        return Respond.error('Not enough views left', error_code=420)

    concept = Utils.urlsafe_to_key(concept_key).get()

    return Respond.success({"concept": concept.to_dict()})


@app_controller.route('/concepts/batch', methods=['POST'])
@Utils.auth_required
def get_batch_concepts(user):
    """
    Send concepts required by in the request
    :param user:
    :return:
    """

    post = Utils.parse_json(request)

    concepts = post['concepts']

    if not user_has_views(user, len(concepts)):
        return Respond.error('Not enough views left', error_code=420)

    response = []

    for concept in concepts:
        entity = Utils.urlsafe_to_key(concept).get()
        response.append(entity.to_dict())

    return Respond.success({"concepts": response})


@app_controller.route('/concepts/<concept_key>/important')
@Utils.auth_required
def mark_concept_important(user, concept_key):
    """
    Mark a concept as important
    """

    concept = Utils.urlsafe_to_key(concept_key).get()

    # Get the user data for the concept
    user_data = UserConcept.query(UserConcept.concept == concept.key, ancestor=user.key).get()

    if not user_data:

        subject = concept.key.parent().parent()

        user_data = UserConcept(
            subject=subject,
            concept=concept.key,
            important=True,
            parent=user.key
        )

        user_data.put()

    else:
        if user_data.important:
            return Respond.error('Concept already marked important')

        user_data.important = True
        user_data.put()

    return Respond.success('Concept marked important')


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

    session_data = user.getSession()

    if session_data['views'] < 5:
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

    user.subtractSessionViews(len(revision_concepts))

    return Respond.success({
        "concepts": revision_concepts,
        "session_data": user.getSession()
    })


@app_controller.route('/concepts/result', methods=['POST'])
@Utils.auth_required
def save_result(user):
    """
    Save the result for the user
    :param user:
    :return:
    """

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
                    concept=concept.key
                )

            data.read += 1

            data.put()

            user.addPoints(1, "Read concept")
            points_counter += 1

    user.subtractSessionViews(len(post['result']))

    return Respond.success({
        "new_points": points_counter,
        "balance": user.getPoints(),
        "session": user.getSession()
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

    return Respond.success({"new_points": points_counter, "balance": user.getPoints()})


@app_controller.route('/subjects/<subject_key>/test')
@Utils.auth_required
def subject_test(user, subject_key):
    """
    Send test concepts
    """
    subject_key = Utils.urlsafe_to_key(subject_key)

    session_data = user.getSession()

    if session_data['views'] < 5:
        return Respond.error("Not enough views left", error_code=400)

    # Find revised concepts
    concepts = UserConcept.query(
        UserConcept.subject == subject_key,
        ancestor=user.key
    ).fetch()

    # select 5 randomly

    if len(concepts) < 5:
        return Respond.error("Less than 5 concepts read", error_code=400)

    # Unique indices
    random_nums = random.sample(range(1, len(concepts)), 5)

    test_concepts = []

    for i in random_nums:
        test_concepts.append(concepts[i].concept.get().to_dict())

    user.subtractSessionViews(5)

    return Respond.success({
        "concepts": test_concepts,
        "session_data": user.getSession()
    })


@app_controller.route('/subjects/<subject_key>/test/result', methods=['POST'])
@Utils.auth_required
def test_result(user, subject_key):
    """
    Save the result and calculate points
    """

    # subject = Utils.urlsafe_to_key(subject_key).get()

    post = Utils.parse_json(request)

    points_counter = 0

    for result in post['result']:

        if result['marked'] == "right":
            UserTests(
                concept=Utils.urlsafe_to_key(result['key']),
                right=True,
                parent=user.key
            ).put()

            user.addPoints(1, "Answered correctly")
            points_counter += 1

        if result['marked'] == "wrong":
            UserTests(
                concept=Utils.urlsafe_to_key(result['key']),
                right=False,
                parent=user.key
            ).put()

            user.addPoints(1, "Answered incorrectly")
            points_counter += 1

    return Respond.success({"new_points": points_counter, "balance": user.getPoints()})


@app_controller.route('/users/code/redeem', methods=['POST'])
@Utils.auth_required
def code_redeem(user):
    """
    Check code for user and give points accordingly
    """

    post = Utils.parse_json(request)

    code_data = UserCodes.query(UserCodes.code == post['code'], UserCodes.activated == False).get()

    if not code_data:

        promo_data = UserCodes.query(UserCodes.code == post['code'], ancestor=user.key).get()

        if not promo_data:
            return Respond.error('No code found', error_code=400)

        user.addPoints(promo_data.points, "Used code: " + promo_data.code)

        return Respond.success({"new_points": promo_data.points, "balance": user.getPoints()})

    code_data.activated = True
    code_data.activatedBy = user.key

    code_data.put()

    user.addPoints(code_data.points, "Used code: " + code_data.code)

    return Respond.success({"new_points": code_data.points, "balance": user.getPoints()})


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


@app_controller.route('/users/pro', methods=['POST'])
@Utils.auth_required
def activate_pro(user):
    """
    Activate pro usage for the user
    :param user:
    :return: Response
    """

    # Perform checks

    if user.getPoints() < PRO_COST:
        return Respond.error('Low balance', error_code=420)

    if user.pro:
        return Respond.error('User already a pro', error_code=410)

    post = Utils.parse_json(request)

    users_with_device = User.query(User.device == post['device']).fetch()

    if len(users_with_device) > 0:
        return Respond.error('Device already registered by another user')

    # Activate Pro for user on this device

    user.subtractPoints(PRO_COST, 'Activated Pro')

    user.pro = True
    user.device = post['device']

    user.put()

    return Respond.success('Activated pro for user')


@app_controller.route('/subjects/<subject_key>/download')
@Utils.auth_required
def save_data_offline(user, subject_key):
    """
    Send a json file to download all concept data of the subject
    """

    if not user.pro:
        return Respond.error('User not a pro', error_code=410)

    subject = Utils.urlsafe_to_key(subject_key).get()

    index = []

    user_data_list = UserConcept.query(UserConcept.subject == subject.key, ancestor=user.key).fetch()

    user_data = {}
    for data in user_data_list:
        user_data[data.concept.urlsafe()] = {
            'important': data.important,
            'read': data.read
        }

    chapters = Chapter.query(ancestor=subject.key).order(Chapter.srno)

    for chapter in chapters:
        concepts = []
        concept_list = Concept.query(ancestor=chapter.key).order(Concept.srno)

        for concept in concept_list:
            concept_data = concept.to_dict()
            key = concept_data['key']

            if key in user_data:
                concept_data.update(user_data[key])

            concepts.append(concept_data)

        index.append({
            "name": chapter.name,
            "key": chapter.key.urlsafe(),
            "concepts": concepts
        })

    return Respond.success(index)


def user_has_views(user, views):
    if user.pro:
        return True

    session = user.getSession()

    if session['views'] < views:
        return False

    else:
        return True