import re
from freezegun import freeze_time
from datetime import date, timedelta

from ssapi.tasks import mail


def test_login(app, client, test_user):
    # login payload
    data = {
        'email': test_user.email,
        'password': test_user.password
    }

    # hit the api
    rv = client.post('/users/login',
                     json=data)

    assert rv.status_code == 200

    json_data = rv.get_json()

    # confirm login succeeded for correct user
    assert test_user.email == json_data['email']
    assert 'jwt' in json_data


def test_refresh(app, client, test_user):
    today = date.today()
    future = today + timedelta(days=5)

    # move five days into the future in order to avoid EarlyRefresh error
    with freeze_time(future):
        # hit the api
        rv = client.get('/users/refresh',
                        headers=test_user.auth_headers)

        assert rv.status_code == 200

        json_data = rv.get_json()

        assert 'jwt' in json_data


def test_change_password(app, client, test_user):
    data = {
        'old': test_user.password,
        'new': 'some random password'
    }

    # hit the api
    rv = client.post('/users/password/change',
                     json=data,
                     headers=test_user.auth_headers)

    assert rv.status_code == 200

    # confirm the password was changed by logging in
    data = {
        'email': test_user.email,
        'password': data['new']
    }

    # hit the api
    rv = client.post('/users/login',
                     json=data)

    assert rv.status_code == 200

    json_data = rv.get_json()

    # confirm login succeeded for correct user
    assert test_user.email == json_data['email']
    assert 'jwt' in json_data


def test_forgot_password(app, client, test_user):
    with app.app_context():
        with mail.record_messages() as outbox:
            data = {
                'email': test_user.email
            }

            # hit the api
            rv = client.post('/users/password/forgot',
                             json=data)

            assert rv.status_code == 200

            assert len(outbox) == 1

            # grab the jwt from the email
            result = re.search(
                r'https:\/\/www\.scarletstudies\.org\/forgot\/([a-zA-Z0-9\-_]+?\.[a-zA-Z0-9\-_]+?\.[a-zA-Z0-9\-_]+)',
                outbox[-1].body
            )

            assert result

            token = result.group(1)

            # token is used as "magic" login
            data = {
                'jwt': token
            }

            # hit magic login api
            rv = client.post('/users/login/magic',
                             json=data)

            assert rv.status_code == 200

            json_data = rv.get_json()

            assert 'jwt' in json_data
            assert test_user.email == json_data['email']
