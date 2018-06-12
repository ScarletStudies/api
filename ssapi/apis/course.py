import re
from flask_praetorian import auth_required
from flask_restplus import Namespace, Resource, fields, reqparse
from sqlalchemy import asc
from ssapi.db import Course


api = Namespace('courses', description='Course related operations')

parser = reqparse.RequestParser()

parser.add_argument('query',
                    type=str,
                    location='args',
                    help='Search for courses containing query in name')
parser.add_argument('limit',
                    type=int,
                    default=10,
                    location='args',
                    help='Limit number of returned results')

course_marshal_model = api.model('Course', {
    'id': fields.String(required=True, description='The course id'),
    'name': fields.String(required=True, description='The course name'),
    'offering_unit': fields.String(required=True,
                                   description='Typically the school and/or college'),
    'subject': fields.String(required=True, description='Course subject'),
    'course_number': fields.String(required=True, description='Individual course number')
})


@api.route('/')
class CourseListResource(Resource):
    @api.doc('list_courses')
    @api.expect(parser)
    @api.marshal_list_with(course_marshal_model)
    @auth_required
    def get(self):
        args = parser.parse_args()
        filters = []

        # courses are sorted by name by default
        order_by = asc(Course.name)

        if args['query'] is not None:
            result = re.match(r'(\d{1,2}):(\d{1,3}):(\d{1,3})', args['query'])

            if result:
                offering_unit, subject, course_number = result.group(1, 2, 3)

                filters.append(Course.course_number.like(course_number))
                filters.append(Course.offering_unit.like(offering_unit))
                filters.append(Course.subject.like(subject))
            else:
                filters.append(Course.name.like('%{}%'.format(args['query'])))

        # set with default
        limit = args['limit']

        return Course.query.filter(*filters).order_by(order_by).limit(limit).all()


@api.route('/<int:id>')
@api.param('id', 'The course id')
class CourseResource(Resource):
    @api.doc('get_one_course')
    @api.marshal_with(course_marshal_model)
    @auth_required
    def get(self, id):
        return Course.query.get_or_404(id)
