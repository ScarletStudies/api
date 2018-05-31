import jwt
from flask import current_app
from flask_mail import Mail, Message
from flask_rq2 import RQ
from ssapi.db import db, User, Post, Comment

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

    # TODO should be a better token, with timeout?
    encoded = jwt.encode(
        {'user_id': user.id},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    ).decode('utf-8')
    verify_url = 'https://www.scarletstudies.org/verify/{}'.format(
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

    # TODO should be a better token, with timeout?
    encoded = jwt.encode(
        {'user_id': user.id},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    ).decode('utf-8')
    verify_url = 'https://www.scarletstudies.org/forgot/' + encoded
    content = 'You forgot your password. Please follow the link to access your account and change your password. ' + verify_url
    message = Message(subject,
                      recipients=[to_email],
                      body=content)
    mail.send(message)


@rq.job
def user_deletion(email, remove_content):
    user = User.query.filter_by(email=email).one()
    to_email = user.email

    # update content of posts and comments by user
    # to change author to special 'deleted' account
    message = '<p>Removed as requested by user</p>'
    special_account = User.query.filter_by(
        email=current_app.config['DELETED_ACCOUNT_EMAIL']).one()

    posts = Post.query.filter_by(author=user).all()

    for post in posts:
        post.author = special_account

        if remove_content:
            post.content = message

    comments = Comment.query.filter_by(author=user).all()

    for comment in comments:
        comment.author = special_account

        if remove_content:
            comment.content = message

    # delete the user account
    db.session.delete(user)
    db.session.commit()

    # finally, send an email to the user confirming account deletion
    subject = 'Scarlet Studies Account Deleted'
    content = 'Your account has been deleted. You may re-register, but your new account will not be associated with the previous content. If you requested your posts and comments to be deleted, they have been. Thank you and have a great day.'
    message = Message(subject,
                      recipients=[to_email],
                      body=content)
    mail.send(message)
