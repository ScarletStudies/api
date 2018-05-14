from flask import abort
from flask_restplus import Namespace, Resource, fields, reqparse
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
    def get(self):
        args = parser.parse_args()
        filters = []

        if args['query'] is not None:
            filters.append(Course.name.like('%{}%'.format(args['query'])))

        # set with default
        limit = args['limit']

        return Course.query.filter(*filters).limit(limit).all()


@api.route('/<int:id>')
@api.param('id', 'The course id')
@api.response(404, 'Course not found')
class CourseResource(Resource):
    @api.doc('get_course')
    @api.marshal_with(course_marshal_model)
    def get(self, id):
        course = Course.query.filter_by(id=id).first()

        if course is not None:
            return course

        abort(404, "Course {} doesn't exist".format(id))
