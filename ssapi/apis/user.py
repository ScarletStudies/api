from flask import abort, request
from flask_praetorian.exceptions import AuthenticationError, MissingUserError
from flask_restplus import Namespace, Resource, fields
from ssapi.praetorian import guard

api = Namespace('users', description='User related operations')

user_marshal_model = api.model('User', {
    'email': fields.String(required=True, description='The user name'),
    'jwt': fields.String(required=True, description='jwt auth')
})

login_marshal_model = api.model('', {
    'email': fields.String(required=True),
    'password': fields.String(required=True)
})


@api.route('/login')
class UserLoginResource(Resource):
    @api.doc('login_user')
    @api.expect(login_marshal_model)
    @api.marshal_with(user_marshal_model)
    def post(self):
        data = request.get_json()

        try:
            user = guard.authenticate(data['email'], data['password'])
        except (AuthenticationError, MissingUserError) as e:
            return abort(400, e.message)

        return {
            'jwt': guard.encode_jwt_token(user),
            'email': user.email
        }
