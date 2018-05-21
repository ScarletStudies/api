import pytest


@pytest.mark.parametrize(
    ('url', 'status_code', 'method'),
    (
        ('/courses/', 401, 'get'),
        ('/categories/', 401, 'get'),
        ('/posts/', 401, 'get'),
        ('/posts/', 401, 'post'),
        ('/posts/1/cheers/', 401, 'post'),
        ('/posts/1/comments/', 401, 'post'),
        ('/semesters/', 401, 'get'),
        ('/users/courses/', 401, 'get'),
        ('/users/courses/1', 401, 'post'),
        ('/users/courses/1', 401, 'delete'),
        # returns invalid user @ 400, not unauthorized
        ('/users/login', 400, 'post'),
    )
)
def test_endpoint_authorization(app, client, url, status_code, method):
    if method == 'get':
        rv = client.get(url)
    elif method == 'post':
        rv = client.post(url)
    elif method == 'delete':
        rv = client.delete(url)

    assert rv.status_code == status_code
