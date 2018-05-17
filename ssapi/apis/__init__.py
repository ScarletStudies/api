from flask import jsonify
from flask_praetorian.exceptions import MissingTokenHeader
from flask_restplus import Api

from .course import api as ns1
from .category import api as ns2
from .post import api as ns3
from .semester import api as ns4
from .user import api as ns5
from .comment import api as ns6

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

api = Api(
    title='Scarlet Studies API',
    version='0.0.1',
    description='',
    authorizations=authorizations,
    security='apikey'
)

api.add_namespace(ns1)
api.add_namespace(ns2)
api.add_namespace(ns3)
api.add_namespace(ns4)
api.add_namespace(ns5)
api.add_namespace(ns6)


def init_app(app):
    api.init_app(app)

    @api.errorhandler(MissingTokenHeader)
    @app.errorhandler(MissingTokenHeader)
    def handle_authorization_error(e):
        return jsonify({'message': 'Unauthorized'}), 401
