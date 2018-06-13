import pytest
from functools import namedtuple
from ssapi import create_app
from ssapi.db import db, User
from ssapi.praetorian import guard


@pytest.fixture
def app():
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    TestUser = namedtuple(
        'TestUser', ['email', 'password', 'id', 'auth_headers']
    )

    with app.app_context():
        email = 'test@unittest.com'
        password = 'password123'

        user = User(email=email,
                    password=guard.encrypt_password(password),
                    is_verified=True)

        db.session.add(user)
        db.session.commit()

        headers = {'Authorization': 'Bearer %s' % guard.encode_jwt_token(user)}

        return TestUser(email=email,
                        password=password,
                        id=user.id,
                        auth_headers=headers)


@pytest.fixture
def another_test_user(app):
    TestUser = namedtuple(
        'TestUser', ['email', 'password', 'id', 'auth_headers']
    )

    with app.app_context():
        email = 'test_user_two@unittest.com'
        password = 'password1234'

        user = User(email=email,
                    password=guard.encrypt_password(password),
                    is_verified=True)

        db.session.add(user)
        db.session.commit()

        headers = {'Authorization': 'Bearer %s' % guard.encode_jwt_token(user)}

        return TestUser(email=email,
                        password=password,
                        id=user.id,
                        auth_headers=headers)


@pytest.fixture
def special_deleted_account(app):
    with app.app_context():
        db.session.add(User(email=app.config['DELETED_ACCOUNT_EMAIL'],
                            password='42',
                            is_verified=False))

        db.session.commit()
