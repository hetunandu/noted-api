from flask import jsonify
import logging


class Respond:
    def __init__(self):
        pass

    @staticmethod
    def _respond(response, http_code=200):
        logging.info('Response: %s' % response)
        resp = jsonify(response)
        resp.status_code = http_code

        return resp

    @staticmethod
    def success(message):
        return Respond._respond({
            'success': True,
            'message': message
        })

    @staticmethod
    def error(error, error_code=500):
        return Respond._respond({
            'success': False,
            'error': error
        }, error_code)

    @staticmethod
    def not_found(message="The request resource was not found"):
        return Respond.error(message, 404)

    @staticmethod
    def json(json):
        return Respond._respond(json)
