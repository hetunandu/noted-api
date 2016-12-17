from google.appengine.ext import ndb

from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.Concept import Concept, References
from src.models.UserConceptData import UserConceptData

concepts_controller = Blueprint('concepts', __name__)


@concepts_controller.route('/', methods=['POST'])
@Utils.creator_required
def store(user):
	"""
	Store a concept.
	:param user:
	:return:
	"""
	post = Utils.parse_json(request)

	if 'name' not in post or 'chapter_key' not in post:
		return Respond.error("Input not valid", error_code=422)

	chapter_key = ndb.Key(urlsafe=post['chapter_key'])

	concept = Concept(
		name=post['name'],
		chapter_key=chapter_key
	)

	concept.put()

	chapter = chapter_key.get()

	chapter.add_to_index(concept)

	return Respond.success({'concept': concept.to_dict()})


@concepts_controller.route('/<concept_key>', methods=['PUT'])
@Utils.creator_required
def update(user, concept_key):
	"""
	Update a concept
	:param user:
	:param concept_key:
	:return: Updated concept
	"""
	concept = ndb.Key(urlsafe=concept_key).get()
	post = Utils.parse_json(request)

	if 'name' in post:
		concept.name = post['name']

	if 'explanation' in post:
		concept.explanation = post['explanation']

	if 'references' in post:
		references = []

		for ref in post['references']:
			reference = References(
				title=ref['title'],
				source=ref['source']
			)

			references.append(reference)

		concept.references = references

	if 'tips' in post:
		concept.tips = post['tips']

	if 'questions' in post:
		concept.questions = post['questions']

	concept.put()

	return Respond.success({'concept': concept.to_dict()})

@concepts_controller.route('/<concept_key>', methods=['DELETE'])
@Utils.creator_required
def delete(user, concept_key):
	"""
	Delete the concept. Remove from chapter index
	"""
	concept = ndb.Key(urlsafe=concept_key).get()
	chapter = concept.chapter_key.get()

	for concept_index in chapter.index:
		if concept_index['key'] == concept.key.urlsafe():
			chapter.index.remove(concept_index)
			print "Removed"


	chapter.put()

	concept.key.delete()

	return Respond.success({"deleted_key": concept_key})


@concepts_controller.route('/<concept_key>/done')
@Utils.auth_required
def done_concept(user, concept_key):
	"""
	Mark a concept as done
	"""
	# get the concept data entity
	concept_data = UserConceptData.query(
						UserConceptData.concept == Utils.urlsafe_to_key(concept_key),
						ancestor=user.key
					).get()
	if not concept_data:
		return Respond.error(error="No data of user for this concept")
	# mark it as understood
	concept_data.done = True
	concept_data.put()
	# return
	return Respond.success("Marked done")

@concepts_controller.route('/<concept_key>/right')
@Utils.auth_required
def right_concept(user, concept_key):
	"""
	Mark a concept as right
	"""
	# get the concept data entity
	concept_data = UserConceptData.query(
						UserConceptData.concept == Utils.urlsafe_to_key(concept_key),
						ancestor=user.key
					).get()
	if not concept_data:
		return Respond.error(error="No data of user for this concept")
	# increase right count
	concept_data.right = concept_data.right + 1
	concept_data.put()
	# return
	return Respond.success("Marked right")

@concepts_controller.route('/<concept_key>/wrong')
@Utils.auth_required
def wrong_concept(user, concept_key):
	"""
	Mark a concept as wrong
	"""
	# get the concept data entity
	concept_data = UserConceptData.query(
						UserConceptData.concept == Utils.urlsafe_to_key(concept_key),
						ancestor=user.key
					).get()
	if not concept_data:
		return Respond.error(error="No data of user for this concept")
	# mark done as false
	concept_data.done = False
	concept_data.put()
	# return
	return Respond.success("Marked wrong")
