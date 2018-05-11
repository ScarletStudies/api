from flask import abort
from flask_restplus import Namespace, Resource, fields, reqparse
from sqlalchemy import desc

from ssapi.db import Post
from ssapi.apis.category import category_marshal_model
from ssapi.apis.course import course_marshal_model

api = Namespace('posts', description='Post related operations')

parser = reqparse.RequestParser()

parser.add_argument('courses[]',
                    action='append',
                    location='args',
                    help='Filter posts by specifying course ids')
parser.add_argument('categories[]',
                    action='append',
                    location='args',
                    help='Filter posts by specifying category ids')
parser.add_argument('query',
                    type=str,
                    location='args',
                    help='Search for posts containing query in content')
parser.add_argument('limit',
                    type=int,
                    default=100,
                    location='args',
                    help='Limit number of returned results')
parser.add_argument('offset',
                    type=int,
                    default=0,
                    location='args',
                    help='Starting offset of returned results')
parser.add_argument('sort',
                    choices=('time',),
                    default='time',
                    location='args',
                    help='Sort by time (desc)')

post_marshal_model = api.model('Post', {
    'id': fields.String(required=True, description='The post id'),
    'content': fields.String(required=True, description='The post content'),
    'timestamp': fields.DateTime(required=True,
                                 description='Creation timestamp'),
    'is_archived': fields.Boolean(required=True,
                                  description='Whether post can be commented on'),
    'category': fields.Nested(model=category_marshal_model,
                              description='Post category'),
    'course': fields.Nested(model=course_marshal_model,
                            required=True,
                            description='Course to which post belongs')
})


@api.route('/')
class PostListResource(Resource):
    @api.doc('list_posts')
    @api.expect(parser)
    @api.marshal_list_with(post_marshal_model)
    def get(self):
        args = parser.parse_args()
        filters = []

        if args['courses[]'] is not None:
            filters.append(Post.course_id.in_(args['courses[]']))

        if args['categories[]'] is not None:
            filters.append(Post.category_id.in_(args['categories[]']))

        if args['query'] is not None:
            filters.append(Post.content.like(args['query']))

        # set with default
        limit = args['limit']
        offset = args['offset']

        if args['sort'] == 'time':
            order_by = desc(Post.timestamp)

        return Post.query \
                   .filter(*filters) \
                   .order_by(order_by) \
                   .limit(limit) \
                   .offset(offset) \
                   .all()


@api.route('/<int:id>')
@api.param('id', 'The post id')
@api.response(404, 'Post not found')
class PostResource(Resource):
    @api.doc('get_post')
    @api.marshal_with(post_marshal_model)
    def get(self, id):
        post = Post.query.filter_by(id=id).first()

        if post is not None:
            return post

        abort(404, "Post {} doesn't exist".format(id))
