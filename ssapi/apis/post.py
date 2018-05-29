import bleach
from flask import abort, request
from flask_praetorian import auth_required, current_user
from flask_restplus import Namespace, Resource, fields, reqparse, marshal
from sqlalchemy import desc

from ssapi.db import db, Post, Course, Category, Semester, Comment

from .category import category_marshal_model
from .comment import comment_marshal_model, new_comment_marshal_model
from .course import course_marshal_model
from .semester import semester_marshal_model
from .user import basic_user_marshal_model

api = Namespace('posts', description='Post related operations')

get_posts_parser = reqparse.RequestParser()

get_posts_parser.add_argument('courses[]',
                              action='append',
                              location='args',
                              help='Filter posts by specifying course ids')
get_posts_parser.add_argument('categories[]',
                              action='append',
                              location='args',
                              help='Filter posts by specifying category ids')
get_posts_parser.add_argument('query',
                              type=str,
                              location='args',
                              help='Search for posts containing query in content')
get_posts_parser.add_argument('limit',
                              type=int,
                              default=100,
                              location='args',
                              help='Limit number of returned results')
get_posts_parser.add_argument('offset',
                              type=int,
                              default=0,
                              location='args',
                              help='Starting offset of returned results')
get_posts_parser.add_argument('sort',
                              choices=('time', 'activity'),
                              default='time',
                              location='args',
                              help='Sort by time or latest activity')

new_post_marshal_model = api.model('New Post Model', {
    'title': fields.String(required=True, description='Post title'),
    'content': fields.String(required=True, description='Post content'),
    'category': fields.Nested(category_marshal_model, description='Only checking for id'),
    'course': fields.Nested(course_marshal_model, description='Only checking for id')
})

post_marshal_model = api.model('Post', {
    'id': fields.String(required=True,
                        description='The post id'),
    'title': fields.String(required=True,
                           description='The post title'),
    'content': fields.String(required=True,
                             description='The post content'),
    'cheers': fields.Nested(model=basic_user_marshal_model,
                            required=True,
                            description='Number of cheers'),
    'comments': fields.Nested(comment_marshal_model,
                              required=True,
                              description='List of comments for post'),
    'timestamp': fields.DateTime(required=True,
                                 description='Creation timestamp'),
    'is_archived': fields.Boolean(required=True,
                                  description='Whether post can be commented on'),
    'category': fields.Nested(model=category_marshal_model,
                              description='Post category'),
    'course': fields.Nested(model=course_marshal_model,
                            required=True,
                            description='Course to which post belongs'),
    'semester': fields.Nested(model=semester_marshal_model,
                              required=True,
                              description='Post semester'),
    'author': fields.Nested(model=basic_user_marshal_model,
                            required=True,
                            description='Post author'),
})


def linkify(attrs, new=False):
    attrs[(None, 'target')] = '_blank'
    attrs[(None, 'rel')] = 'nofollow'
    return attrs


@api.route('/')
class PostListResource(Resource):
    @api.doc('list_posts')
    @api.expect(get_posts_parser)
    @api.marshal_list_with(post_marshal_model)
    @auth_required
    def get(self):
        args = get_posts_parser.parse_args()
        filters = []

        if args['courses[]'] is not None:
            filters.append(Post.course_id.in_(args['courses[]']))

        if args['categories[]'] is not None:
            filters.append(Post.category_id.in_(args['categories[]']))

        if args['query'] is not None:
            filters.append(Post.content.like('%{}%'.format(args['query'])))

        # set with default
        limit = args['limit']
        offset = args['offset']

        if args['sort'] == 'activity':
            """
            select * from post
            left join comment on comment.post_id == post.id
            group by post.id
            order by max(post.timestamp, comment.timestamp) desc;

            if there has been comment activity, rank higher
            """
            return Post.query \
                .outerjoin(Comment) \
                .order_by(desc(Comment.timestamp), desc(Post.timestamp)) \
                .filter(*filters) \
                .limit(limit) \
                .offset(offset) \
                .all()

        # default sort by time
        return Post.query \
            .filter(*filters) \
            .order_by(desc(Post.timestamp)) \
            .limit(limit) \
            .offset(offset) \
            .all()

    @api.doc('new_post')
    @api.expect(new_post_marshal_model)
    @api.marshal_with(post_marshal_model)
    @auth_required
    def post(self):
        data = marshal(request.get_json(), new_post_marshal_model)

        title = data['title']
        content = data['content']

        content = bleach.clean(
            content,
            tags=[
                'p',
                'h1',
                'h2',
                'br',
                's',
                'u',
                *bleach.sanitizer.ALLOWED_TAGS
            ],
            strip=True
        )

        content = bleach.linkify(
            content
        )

        # validate data
        category = Category.query.get(data['category']['id'])
        if category is None:
            return abort(400, 'Category does not exist')

        course = Course.query.get(data['course']['id'])
        if course is None:
            return abort(400, 'Course does not exist')

        semester = Semester.query.order_by(desc(Semester.id)).first()

        post = Post(title=title,
                    content=content,
                    category=category,
                    course=course,
                    author=current_user(),
                    semester=semester)

        db.session.add(post)
        db.session.commit()

        return post, 201


@api.route('/<int:id>/comments/')
@api.param('id', 'The post id')
class CommentListResource(Resource):
    @api.doc('new_comment')
    @api.expect(new_comment_marshal_model)
    @api.marshal_with(post_marshal_model)
    @auth_required
    def post(self, id):
        post = Post.query.get(id)

        data = marshal(request.get_json(), new_comment_marshal_model)
        content = data['content']

        content = bleach.clean(
            content,
            tags=[
                'p',
                'h1',
                'h2',
                'br',
                's',
                'u',
                *bleach.sanitizer.ALLOWED_TAGS
            ],
            strip=True
        )

        content = bleach.linkify(
            content
        )

        comment = Comment(content=content,
                          post=post,
                          author=current_user())

        db.session.add(comment)
        db.session.commit()

        return post, 201


@api.route('/<int:id>/cheers/')
@api.param('id', 'The post id')
class CheerListResource(Resource):
    @api.doc('new_cheer')
    @api.marshal_with(post_marshal_model)
    @auth_required
    def post(self, id):
        post = Post.query.get(id)
        user = current_user()

        if user not in post.cheers:
            post.cheers.append(user)

        db.session.commit()

        return post, 201


@api.route('/<int:id>')
@api.param('id', 'The post id')
class PostResource(Resource):
    @api.doc('get_one_post')
    @api.marshal_with(post_marshal_model)
    @auth_required
    def get(self, id):
        return Post.query.get(id)
