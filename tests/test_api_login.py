
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
    assert json_data['jwt'] is not None
