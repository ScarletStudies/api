from flask_restplus import Namespace, fields

from .user import basic_user_marshal_model

api = Namespace('comments', description='Comment related operations')

comment_marshal_model = api.model('Comment', {
    'id': fields.String(required=True,
                        description='The comment id'),
    'content': fields.String(required=True,
                             description='The comment content'),
    'timestamp': fields.String(required=True,
                               description='The comment timestamp'),
    'author': fields.Nested(model=basic_user_marshal_model,
                            required=True,
                            description='Comment author'),
})

new_comment_marshal_model = api.model('Comment', {
    'content': fields.String(required=True,
                             description='The comment content'),
})
