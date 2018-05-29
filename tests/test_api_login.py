from freezegun import freeze_time
from datetime import date, timedelta


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
