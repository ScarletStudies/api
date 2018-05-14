import pytest
from ssapi.db import db, User
from ssapi.praetorian import guard


@pytest.fixture
def testdata(app):
    with app.app_context():
        user = User(email='test@unittest.com',
                    password=guard.encrypt_password('password123'))

        db.session.add(user)

        db.session.commit()


@pytest.mark.usefixtures('testdata')
def test_login(app, client):
    data = {
        'email': 'test@unittest.com',
        'password': 'password123'
    }

    rv = client.post('/users/login',
                     json=data)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    with app.app_context():
        user = User.query.filter_by(email=data['email']).first()

    assert user.email == json_data['email']
    assert json_data['jwt'] is not None
