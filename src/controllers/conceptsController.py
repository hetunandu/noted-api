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
	Store a concept. //TODO: Only admin users should be able to do this
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


@concepts_controller.route('/<concept_key>/understood')
@Utils.auth_required
def understand_concept(user, concept_key):
	"""
	Mark a concept as understood
	"""
	# get the concept data entity
	concept_data = UserConceptData.query(
						UserConceptData.concept == Utils.urlsafe_to_key(concept_key),
						ancestor=user.key
					).get()
	if not concept_data:
		return Respond.error(error="No data of user for this concept")
	# mark it as understood
	concept_data.understood = True
	concept_data.put()
	# return
	return Respond.success("Marked understood")
