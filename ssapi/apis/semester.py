from flask_praetorian import auth_required
from flask_restplus import Namespace, Resource, fields
from sqlalchemy import desc
from ssapi.db import Semester

api = Namespace('semesters', description='Semester related operations')

semester_marshal_model = api.model('Semester', {
    'id': fields.String(required=True, description='The semester id'),
    'year': fields.Integer(required=True, description='The semester year'),
    'season': fields.String(required=True,
                            description='One of spring, summer, winter, or fall')
})


@api.route('/')
class SemesterListResource(Resource):
    @api.doc('list_semesters')
    @api.marshal_list_with(semester_marshal_model)
    @auth_required
    def get(self):
        return Semester.query.order_by(desc(Semester.id)).all()


@api.route('/current')
class PostResource(Resource):
    @api.doc('get_current_semester')
    @api.marshal_with(semester_marshal_model)
    @auth_required
    def get(self):
        semester = Semester.query.order_by(desc(Semester.id)).first()

        return semester
