import sendgrid
import jwt
from flask import current_app
from flask_rq2 import RQ
from sendgrid.helpers.mail import Email, Content, Mail
from ssapi.db import User

rq = RQ()
sg = sendgrid.SendGridAPIClient()
sg_config = {}


def init_app(app):
    rq.init_app(app)
    sg.apikey = app.config['SENDGRID_API_KEY']
    sg_config['from_email'] = app.config['FROM_EMAIL_ADDRESS']


@rq.job
def add(x, y):
    return x + y


@rq.job
def verification_email(email):
    user = User.query.filter_by(email=email).one()
    from_email = Email(sg_config['from_email'])
    to_email = Email(user.email)
    subject = 'Verify Your Scarlet Studies Account'
    encoded = jwt.encode(
        {'user_id': user.id},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    ).decode('utf-8')
    verify_url = 'https://www.scarletstudies.org/user/verify/{}'.format(
        encoded
    )
    content = Content(
        'text/plain',
        'Please verify your account. You will not be able to log in until you do. {}'.format(
            verify_url
        )
    )
    mail = Mail(from_email, subject, to_email, content)
    return sg.client.mail.send.post(request_body=mail.get())
