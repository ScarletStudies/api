import os
import tempfile
import pytest
from functools import namedtuple
from ssapi import create_app
from ssapi.db import db, User
from ssapi.praetorian import guard


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path
    })

    with app.app_context():
        db.create_all()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


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
                    password=guard.encrypt_password('password123'))

        db.session.add(user)
        db.session.commit()

        user.id

        headers = {'Authorization': 'Bearer %s' % guard.encode_jwt_token(user)}

    return TestUser(email=email,
                    password=password,
                    id=user.id,
                    auth_headers=headers)
