from flask import abort, request
from flask_praetorian import auth_required, current_user
from flask_praetorian.exceptions import AuthenticationError, MissingUserError
from flask_restplus import Namespace, Resource, fields, marshal
from ssapi.db import db, Course
from ssapi.praetorian import guard
from .course import course_marshal_model

api = Namespace('users',
                description='User related operations')

basic_user_marshal_model = api.model('User', {
    'email': fields.String(required=True, description='The user email'),
})

user_marshal_model = api.model('User', {
    'email': fields.String(required=True, description='The user email'),
    'jwt': fields.String(required=True, description='jwt auth')
})

login_marshal_model = api.model('User', {
    'email': fields.String(required=True, description='The user email'),
    'password': fields.String(required=True, description='The user password')
})


@api.route('/login')
class UserLoginResource(Resource):
    @api.doc('login_user')
    @api.expect(login_marshal_model)
    @api.response(200, 'Success', user_marshal_model)
    def post(self):
        data = marshal(request.get_json(), login_marshal_model)

        try:
            user = guard.authenticate(data['email'], data['password'])
        except (AuthenticationError, MissingUserError) as e:
            return abort(400, e.message)

        return {
            'jwt': guard.encode_jwt_token(user),
            'email': user.email
        }


@api.route('/courses/')
class UserCoursesListResource(Resource):
    @api.doc('get_user_courses')
    @api.marshal_list_with(course_marshal_model)
    @auth_required
    def get(self):
        return current_user().courses


@api.route('/courses/<id>')
class UserCoursesResource(Resource):
    @api.doc('add_course_for_user')
    @api.marshal_list_with(course_marshal_model)
    @auth_required
    def post(self, id):
        user = current_user()
        course = Course.query.get(id)

        if course not in user.courses:
            user.courses.append(course)
            db.session.commit()

        return user.courses

    @api.doc('remove_course_from_user')
    @api.marshal_list_with(course_marshal_model)
    @auth_required
    def delete(self, id):
        user = current_user()
        course = Course.query.get(id)

        if course in user.courses:
            user.courses.remove(course)
            db.session.commit()

        return user.courses
