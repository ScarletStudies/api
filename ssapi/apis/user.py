import jwt
from jwt.exceptions import DecodeError
from flask import abort, request, current_app
from flask_praetorian import auth_required, current_user
from flask_praetorian.exceptions import AuthenticationError, MissingUserError
from flask_restplus import Namespace, Resource, fields, marshal
from ssapi.db import db, Course, User
from ssapi.praetorian import guard
from ssapi.tasks import verification_email, forgot_password_email, user_deletion

from .course import course_marshal_model


api = Namespace('users',
                description='User related operations')

basic_user_marshal_model = api.model('Basic User', {
    'email': fields.String(required=True,
                           description='The user email',
                           default=''),
})

verify_user_marshal_model = api.model('Verify User', {
    'jwt': fields.String(required=True,
                         description='The provided jwt',
                         default=''),
})

refresh_user_marshal_model = api.model('Refresh User', {
    'jwt': fields.String(required=True,
                         description='The old jwt to refresh',
                         default=''),
})

user_marshal_model = api.model('User with Auth Token', {
    'email': fields.String(required=True,
                           description='The user email',
                           default=''),
    'jwt': fields.String(required=True,
                         description='jwt auth',
                         default='')
})

login_or_register_marshal_model = api.model('Login or Register', {
    'email': fields.String(required=True,
                           description='The user email',
                           default=''),
    'password': fields.String(required=True,
                              description='The user password',
                              default='')
})

change_password_marshal_model = api.model('Change Password', {
    'old': fields.String(required=True,
                         description='The old password',
                         default=''),
    'new': fields.String(required=True,
                         description='The new password',
                         default='')
})

delete_account_marshal_model = api.model('Delete Account', {
    'password': fields.String(required=True,
                              description='The account password',
                              default=''),
    'remove_content': fields.Boolean(required=True,
                                     description='Whether or not to delete all user content',
                                     default=False)
})


@api.route('/login')
class UserLoginResource(Resource):
    @api.doc('login_user')
    @api.expect(login_or_register_marshal_model)
    @api.response(200, 'Success', user_marshal_model)
    def post(self):
        data = marshal(request.get_json(), login_or_register_marshal_model)

        try:
            user = guard.authenticate(data['email'], data['password'])
        except (AuthenticationError, MissingUserError) as e:
            return abort(400, e.message)

        if not user.is_verified:
            return abort(400, 'User must verify their email address')

        return {
            'jwt': guard.encode_jwt_token(user),
            'email': user.email
        }


@api.route('/refresh')
class UserRefreshResource(Resource):
    @api.doc('refresh_jwt')
    @api.response(200, 'Success', refresh_user_marshal_model)
    def get(self):
        """
        Refreshes an existing JWT by creating a new one that is a copy of
        the old except that it has a refrehsed access expiration.

        copied from
        https://github.com/dusktreader/flask-praetorian/blob/master/example/refresh.py
        """
        old_token = guard.read_token_from_header()
        new_token = guard.refresh_jwt_token(old_token)

        return {
            'jwt': new_token
        }


@api.route('/password/change')
class UserChangePasswordResource(Resource):
    @api.doc('change_password')
    @api.expect(change_password_marshal_model)
    @api.response(200, 'Success')
    @auth_required
    def post(self):
        data = marshal(request.get_json(), change_password_marshal_model)
        old = data['old']
        new = data['new']

        # check old password
        current = current_user()
        user = guard.authenticate(current.email, old)

        # check for valid new password
        if len(new) not in range(10, 33):
            return abort(400,
                         'Invalid password. Must be between 10 and 32 characters (inclusive)')

        # change user password
        user.password = guard.encrypt_password(new)

        # commit database
        db.session.commit()

        return 'OK', 200


@api.route('/password/forgot')
class UserForgotPasswordResource(Resource):
    @api.doc('forgot_password')
    @api.expect(basic_user_marshal_model)
    @api.response(200, 'Success')
    def post(self):
        data = marshal(request.get_json(), basic_user_marshal_model)
        email = data['email']

        # look up user
        user = User.query.filter_by(email=email).one_or_none()

        if user is None:
            return abort(400, 'Account for email {} does not exist'.format(email))

        # queue email
        forgot_password_email.queue(email)

        return 'OK', 200


@api.route('/login/magic')
class UserMagicLoginResource(Resource):
    @api.doc('magic_login')
    @api.expect(verify_user_marshal_model)
    @api.response(200, 'Success', user_marshal_model)
    def post(self):
        """
        like verify, but does not verify the user
        """
        data = marshal(request.get_json(), verify_user_marshal_model)
        encoded = data['jwt']

        try:
            decoded = jwt.decode(
                encoded, current_app.config['SECRET_KEY'], algorithm='HS256'
            )
        except DecodeError:
            return abort(400, 'Invalid magic login token')

        user = User.query.get(decoded['user_id'])

        if user is None:
            return abort(400, 'User does not exist')

        if not user.is_verified:
            return abort(400, 'User must verify their email address')

        return {
            'jwt': guard.encode_jwt_token(user),
            'email': user.email
        }


@api.route('/register')
class UserRegisterResource(Resource):
    @api.doc('register_user')
    @api.expect(login_or_register_marshal_model)
    @api.response(201, 'Success')
    def post(self):
        data = marshal(request.get_json(), login_or_register_marshal_model)
        email = data['email']
        password = data['password']

        # check for existing user
        user = User.query.filter_by(email=email).first()

        if user is not None:
            return abort(400, 'Account for email {} already exists'.format(email))

        # check for valid signup email
        if not email.endswith('rutgers.edu'):
            return abort(400, 'Must provide a valid rutgers.edu email address')

        # check for valid password
        if len(password) not in range(10, 33):
            return abort(400,
                         'Invalid password. Must be between 10 and 32 characters (inclusive)')

        # finally, create the user and send the verification email
        user = User(email=email, password=guard.encrypt_password(password))

        db.session.add(user)
        db.session.commit()

        verification_email.queue(email)

        return 'OK', 201


@api.route('/register/resend')
class UserResendResource(Resource):
    @api.doc('resend_verification')
    @api.expect(basic_user_marshal_model)
    @api.response(200, 'Success')
    def post(self):
        data = marshal(request.get_json(), basic_user_marshal_model)
        email = data['email']

        # check for existing user
        user = User.query.filter_by(email=email).one_or_none()

        if user is None:
            return abort(400, 'No account for email {}'.format(email))

        if user.is_verified:
            return abort(400, 'Account with email {} already verified'.format(email))

        verification_email.queue(email)

        return 'OK', 200


@api.route('/register/verify')
class UserVerifyResource(Resource):
    @api.doc('verify_account')
    @api.expect(verify_user_marshal_model)
    @api.response(200, 'Success', user_marshal_model)
    def post(self):
        data = marshal(request.get_json(), verify_user_marshal_model)
        encoded = data['jwt']

        try:
            decoded = jwt.decode(
                encoded, current_app.config['SECRET_KEY'], algorithm='HS256'
            )
        except DecodeError:
            return abort(400, 'Invalid verification token')

        user = User.query.get(decoded['user_id'])

        if user is None:
            return abort(400, 'User does not exist')

        user.is_verified = True
        db.session.commit()

        return {
            'jwt': guard.encode_jwt_token(user),
            'email': user.email
        }


@api.route('/remove')
class UserDeleteAccountResource(Resource):
    @api.doc('delete_account')
    @api.expect(delete_account_marshal_model)
    @api.response(200, 'Success')
    @auth_required
    def post(self):
        data = marshal(request.get_json(), delete_account_marshal_model)
        password = data['password']
        remove_content = data['remove_content']

        # check old password
        current = current_user()
        user = guard.authenticate(current.email, password)

        user_deletion.queue(user.email, remove_content)

        return 'OK', 200


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
