import jwt
from flask import current_app
from flask_mail import Mail, Message
from flask_rq2 import RQ
from ssapi.db import User
from ssapi.praetorian import guard

mail = Mail()
rq = RQ()


def init_app(app):
    rq.init_app(app)
    mail.init_app(app)


@rq.job
def add(x, y):
    return x + y


@rq.job
def verification_email(email):
    user = User.query.filter_by(email=email).one()
    to_email = user.email
    subject = 'Verify Your Scarlet Studies Account'

    # TODO should be normal login token
    encoded = jwt.encode(
        {'user_id': user.id},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    ).decode('utf-8')
    verify_url = 'https://www.scarletstudies.org/user/verify/{}'.format(
        encoded
    )
    content = 'Please verify your account. You will not be able to log in until you do. {}'.format(
        verify_url
    )
    message = Message(subject,
                      recipients=[to_email],
                      body=content)
    mail.send(message)


@rq.job
def forgot_password_email(email):
    user = User.query.filter_by(email=email).one()
    to_email = user.email
    subject = 'Access Your Scarlet Studies Account'

    # generate normal login token
    token = guard.encode_jwt_token(user)
    verify_url = 'https://www.scarletstudies.org/user/forgot/' + token
    content = 'You forgot your password. Please follow the link to access your account and change your password. ' + verify_url
    message = Message(subject,
                      recipients=[to_email],
                      body=content)
    mail.send(message)
