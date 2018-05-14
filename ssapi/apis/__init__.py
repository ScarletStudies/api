from flask_restplus import Api

from .course import api as ns1
from .category import api as ns2
from .post import api as ns3
from .semester import api as ns4
from .user import api as ns5

api = Api(
    title='Scarlet Studies API',
    version='0.0.1',
    description='',
    # All API metadatas
)

api.add_namespace(ns1)
api.add_namespace(ns2)
api.add_namespace(ns3)
api.add_namespace(ns4)
api.add_namespace(ns5)


def init_app(app):
    api.init_app(app)
