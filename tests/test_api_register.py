import jwt
import pytest
from functools import namedtuple
from ssapi.db import db, User
from ssapi.praetorian import guard
from ssapi.tasks import mail


def test_register(app, client):
    # register payload
    data = {
        'email': 'example@rutgers.edu',
        'password': 'password456'
    }

    # record outbound messages
    with app.app_context():
        with mail.record_messages() as outbox:
            # hit the api
            rv = client.post('/users/register',
                             json=data)

            assert rv.status_code == 201

            # confirm user is created in database _without_ verification flag set

            user = User.query.filter_by(email=data['email']).first()
            assert not user.is_verified

            # confirm cannot login yet
            rv = client.post('/users/login',
                             json=data)

            assert rv.status_code == 400
            assert 'verify their email address' in rv.get_json()['message']

            assert len(outbox) == 1

            # resend verification email
            rv = client.post('/users/register/resend',
                             json=data)

            assert rv.status_code == 200

            assert len(outbox) == 2


def test_register_existing_user(app, client, test_user):
    # register payload
    data = {
        'email': test_user.email,
        'password': 'password456'  # note: different password
    }

    with app.app_context():
        with mail.record_messages() as outbox:
            # hit the api
            rv = client.post('/users/register',
                             json=data)

            assert rv.status_code == 400
            assert 'already exists' in rv.get_json()['message']

            # resend verification email
            rv = client.post('/users/register/resend',
                             json=data)

            assert rv.status_code == 400

            assert 'already verified' in rv.get_json()['message']

            assert len(outbox) == 0


def test_register_non_rutgers_user(app, client):
    # register payload
    data = {
        'email': 'example@pennstate.edu',
        'password': 'password456'
    }

    # hit the api
    rv = client.post('/users/register',
                     json=data)

    assert rv.status_code == 400
    assert 'valid rutgers.edu email address' in rv.get_json()['message']


@pytest.mark.parametrize(
    ('password', 'is_valid'),
    (
        ('short', False),
        ('', False),
        ('helloworld', True),
        ('tttttttttttttttttttttttttttttttt', True),
        ('tttttttttttttttttttttttttttttttt+', False),
    )
)
def test_register_user_with_bad_password(app, client, password, is_valid):
    # register payload
    data = {
        'email': 'example@rutgers.edu',
        'password': password
    }

    # hit the api
    rv = client.post('/users/register',
                     json=data)

    if is_valid:
        assert rv.status_code == 201
    else:
        assert rv.status_code == 400
        assert 'Invalid password' in rv.get_json()['message']


@pytest.fixture
def test_unregistered_user(app):
    TestUser = namedtuple(
        'TestUser', ['email', 'password', 'id', 'auth_headers', 'register_jwt']
    )

    with app.app_context():
        email = 'test2@unittest.com'
        password = 'password123'

        user = User(email=email,
                    password=guard.encrypt_password('password123'),
                    is_verified=True)

        db.session.add(user)
        db.session.commit()

        headers = {'Authorization': 'Bearer %s' % guard.encode_jwt_token(user)}

        register_jwt = jwt.encode(
            {'user_id': user.id},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        ).decode('utf-8')

    return TestUser(email=email,
                    password=password,
                    id=user.id,
                    auth_headers=headers,
                    register_jwt=register_jwt)


def test_verify_user(app, client, test_unregistered_user):
    data = {
        'jwt': test_unregistered_user.register_jwt
    }

    # hit the api
    rv = client.post('/users/register/verify',
                     json=data)

    assert rv.status_code == 200

    # should return jwt
    assert rv.get_json()['jwt'] is not None

    # should be able to log in now
    data = {
        'email': test_unregistered_user.email,
        'password': test_unregistered_user.password
    }

    rv = client.post('/users/login',
                     json=data)

    assert rv.status_code == 200
