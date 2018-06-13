import bleach
from datetime import datetime, timedelta
from flask import abort, request, current_app
from flask_praetorian import auth_required, current_user
from flask_restplus import Namespace, Resource, fields, reqparse, marshal
from sqlalchemy import desc, or_

from ssapi.db import db, Post, Course, Category, Semester, Comment, User

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
get_posts_parser.add_argument('page',
                              type=int,
                              default=1,
                              location='args',
                              help='Pagination')
get_posts_parser.add_argument('sort',
                              choices=('time', 'activity'),
                              default='time',
                              location='args',
                              help='Sort by time or latest activity')
get_posts_parser.add_argument('start_date',
                              location='args',
                              help='Return posts on or after given date')
get_posts_parser.add_argument('end_date',
                              location='args',
                              help='Return posts before and not on given date')

new_post_marshal_model = api.model('New Post Model', {
    'title': fields.String(required=True, description='Post title'),
    'content': fields.String(required=True, description='Post content'),
    'due_date': fields.Date(required=False, description='The post due date'),
    'category': fields.Nested(category_marshal_model, description='Only checking for id'),
    'course': fields.Nested(course_marshal_model, description='Only checking for id')
})

post_marshal_model = api.model('Post', {
    'id': fields.String(required=True,
                        description='The post id'),
    'title': fields.String(required=True,
                           description='The post title'),
    'due_date': fields.Date(required=False,
                            description='The post due date, if it makes sense'),
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

paginated_post_marshal_model = api.model('Paginated Post', {
    'items': fields.List(fields.Nested(post_marshal_model)),
    'total': fields.Integer()
})


def linkify(attrs, new=False):
    attrs[(None, 'target')] = '_blank'
    attrs[(None, 'rel')] = 'nofollow'
    return attrs


@api.route('/')
class PostListResource(Resource):
    @api.doc('list_posts')
    @api.expect(get_posts_parser)
    @api.marshal_with(paginated_post_marshal_model)
    @auth_required
    def get(self):
        args = get_posts_parser.parse_args()
        filters = []

        if args['courses[]'] is not None:
            filters.append(Post.course_id.in_(args['courses[]']))

        if args['categories[]'] is not None:
            filters.append(Post.category_id.in_(args['categories[]']))

        if args['query'] is not None:
            filters.append(
                or_(
                    Post.content.like('%{}%'.format(args['query'])),
                    Post.title.like('%{}%'.format(args['query']))
                )
            )

        if args['start_date'] is not None:
            # because >= does not appear to work correctly, use > with a day before
            start_date = datetime.strptime(args['start_date'], '%Y-%m-%d') \
                - timedelta(days=1)
            filters.append(Post.due_date > start_date)

        if args['end_date'] is not None:
            end_date = datetime.strptime(args['end_date'], '%Y-%m-%d')
            filters.append(Post.due_date < end_date)

        # pagination
        page = args['page']

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
                .paginate(page)

        # default sort by time
        return Post.query \
            .filter(*filters) \
            .order_by(desc(Post.timestamp)) \
            .paginate(page)

    @api.doc('new_post')
    @api.expect(new_post_marshal_model)
    @api.marshal_with(post_marshal_model)
    @auth_required
    def post(self):
        data = marshal(request.get_json(), new_post_marshal_model)

        title = data['title']
        content = data['content']
        due_date = data['due_date']

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

        if due_date:
            due_date = datetime.strptime(due_date, '%Y-%m-%d')

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
                    due_date=due_date,
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


@api.route('/<int:post_id>/comments/<int:comment_id>')
@api.param('post_id', 'The post id')
@api.param('comment_id', 'The comment id')
class CommentResource(Resource):
    @api.doc('delete_one_post')
    @api.marshal_with(post_marshal_model)
    @auth_required
    def delete(self, post_id, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        user = current_user()

        if comment.author.id != user.id:
            return 'Not Comment Owner', 403

        deleted_user = User.query.filter_by(
            email=current_app.config['DELETED_ACCOUNT_EMAIL']).one()

        comment.content = '<p>[deleted]</p>'
        comment.author = deleted_user

        db.session.commit()

        return Post.query.get(post_id)


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
        return Post.query.get_or_404(id)

    @api.doc('delete_one_post')
    @api.marshal_with(post_marshal_model)
    @auth_required
    def delete(self, id):
        post = Post.query.get_or_404(id)
        user = current_user()

        if post.author.id != user.id:
            return 'Not Post Owner', 403

        deleted_user = User.query.filter_by(
            email=current_app.config['DELETED_ACCOUNT_EMAIL']).one()

        post.content = '<p>[deleted]</p>'
        post.author = deleted_user

        db.session.commit()

        return post
