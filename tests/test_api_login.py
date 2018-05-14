from ssapi.db import User


def test_login(app, client, test_user):
    data = {
        'email': test_user.email,
        'password': test_user.password
    }

    rv = client.post('/users/login',
                     json=data)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    with app.app_context():
        user = User.query.get(test_user.id)

    assert user.email == json_data['email']
    assert json_data['jwt'] is not None
