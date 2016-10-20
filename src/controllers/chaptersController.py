from google.appengine.ext import ndb
from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.Chapter import Chapter
from src.models.Concept import Concept

chapters_controller = Blueprint('chapters', __name__)


@chapters_controller.route('/', methods=['POST'])
@Utils.admin_required
def store(user):
    """
    Store a chapter
    :param user:
    :return:
    """
    post = Utils.parse_json(request)

    subject = ndb.Key(urlsafe=post['subject_key'])

    chapter = Chapter(name=post['name'], parent=subject)
    chapter.put()

    return Respond.success(chapter.single_dic())


@chapters_controller.route('/<chapter_key>')
@Utils.auth_required
def get_concepts(user, chapter_key):
    """
    Get the concepts of a chapter
    :param chapter_key:
    :param user:
    :return:
    """
    chapter = ndb.Key(urlsafe=chapter_key).get().single_dic()

    chapter['concepts'] = []
    for concept in chapter['index']:
        full_concept = ndb.Key(urlsafe=concept['key']).get()
        if full_concept:
            chapter['concepts'].append(full_concept.to_dict())

    return Respond.success({
        'chapter': chapter
    })


@chapters_controller.route('/<chapter_key>', methods=['PUT'])
@Utils.admin_required
def edit_chapter(user, chapter_key):
    """
    Edit the chapter
    :param user:
    :param chapter_key:
    :return:
    """
    chapter = ndb.Key(urlsafe=chapter_key).get()

    post = Utils.parse_json(request)
    chapter.name = post['name']
    chapter.put()

    return Respond.success(chapter.for_list())


@chapters_controller.route('/<chapter_key>', methods=['DELETE'])
@Utils.admin_required
def delete_chapter(user, chapter_key):
    """
    Delete the chapter and remove link from the other concepts
    :param user:
    :param chapter_key:
    :return:
    """
    chapter = ndb.Key(urlsafe=chapter_key).get()

    concepts = Concept.query(Concept.chapter_key == chapter.key)

    for concept in concepts:
        concept.chapter_key = None
        concept.put()

    chapter.key.delete()

    return Respond.json({
        "success": True,
        "message": "Chapter deleted successfully",
        "deleted_key": chapter_key
    })
