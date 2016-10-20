from flask import Blueprint
from src.common import Utils
from src.common.Respond import Respond

deck_controller = Blueprint('deck', __name__)


@deck_controller.route('/', methods=['POST'])
@Utils.auth_required
def get_deck(user):
    """
    Get the concepts for user
    :param user:
    :return:
    """

    pass
