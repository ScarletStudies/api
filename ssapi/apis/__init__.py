from flask_restplus import Api

from .course import api as ns1

api = Api(
    title='Scarlet Studies API',
    version='0.0.1',
    description='A description',
    # All API metadatas
)

api.add_namespace(ns1)


def init_app(app):
    api.init_app(app)
