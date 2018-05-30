import jwt
from flask import current_app
from flask_mail import Mail, Message
from flask_rq2 import RQ
from ssapi.db import User

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
