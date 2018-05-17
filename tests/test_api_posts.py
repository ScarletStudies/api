import pytest
from datetime import datetime
from flask_restplus import marshal
from sqlalchemy import desc
from ssapi.db import db, Post, Course, Category, Semester, Comment
from ssapi.apis.post import post_marshal_model, post_with_comments_marshal_model


@pytest.fixture
def testdata_for_sorting(app):
    with app.app_context():
        for n in range(0, 10):
            category = Category(name='name%d' % n)

            db.session.add(category)

        for n in range(0, 10):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='subject%d' % n, course_number='cn%d' % n)

            db.session.add(course)

        for n in range(0, 10):
            semester = Semester(year=n, season='Fall')

            db.session.add(semester)

        db.session.commit()

        for n in range(0, 10):
            post = Post(title='title%d' % n,
                        content='content%d' % n,
                        timestamp=datetime(2018 + n, 1, 1),
                        author_id=n, course_id=n,
                        category_id=n, semester_id=n)

            db.session.add(post)

        db.session.commit()


@pytest.fixture
def testdata(app, test_user):
    with app.app_context():
        for n in range(0, 10):
            category = Category(name='name%d' % n)

            db.session.add(category)

        for n in range(0, 10):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='subject%d' % n, course_number='cn%d' % n)

            db.session.add(course)

        for n in range(0, 10):
            semester = Semester(year=n, season='Fall')

            db.session.add(semester)

        db.session.commit()

        for n in range(0, 10):
            post = Post(title='title%d' % n,
                        content='content%d' % n,
                        author_id=n, course_id=n,
                        category_id=n, semester_id=n)

            db.session.add(post)

        db.session.commit()


@pytest.fixture
def testdata_for_comments(app, test_user):
    with app.app_context():
        post = Post(title='title',
                    content='content',
                    author_id=0, course_id=0,
                    category_id=0, semester_id=0)

        db.session.add(post)

        for n in range(0, 100):
            comment = Comment(content='content%d' % n,
                              post=post,
                              author_id=test_user.id)

            db.session.add(comment)

        db.session.commit()

        return post.id


@pytest.fixture
def testdata_for_add_comment(app, test_user):
    with app.app_context():
        post = Post(title='title',
                    content='content',
                    author_id=0, course_id=0,
                    category_id=0, semester_id=0)

        post.comments = []

        db.session.add(post)

        db.session.commit()

        return post.id


@pytest.mark.usefixtures('testdata')
def test_get_all_posts(app, client, test_user):
    rv = client.get('/posts/',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    with app.app_context():
        posts = Post.query.all()
        posts_json = marshal(posts, post_marshal_model)

    assert len(posts_json) == len(json_data)

    for post in posts_json:
        assert post in json_data


@pytest.mark.usefixtures('testdata')
def test_get_all_posts_for_course(app, client, test_user):
    with app.app_context():
        course = Course.query.first()
        posts = Post.query.filter_by(course_id=course.id).all()
        posts_json = marshal(posts, post_marshal_model)

    rv = client.get('/posts/?courses[]=%d' % course.id,
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    assert len(posts_json) == len(json_data)

    for post in posts_json:
        assert post in json_data


@pytest.mark.usefixtures('testdata')
def test_get_all_posts_by_category(app, client, test_user):
    with app.app_context():
        category = Category.query.first()
        posts = Post.query.filter_by(category_id=category.id).all()
        posts_json = marshal(posts, post_marshal_model)

    rv = client.get('/posts/?categories[]=%d' % category.id,
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    assert len(posts_json) == len(json_data)

    for post in posts_json:
        assert post in json_data


@pytest.mark.usefixtures('testdata')
def test_get_all_posts_by_search(app, client, test_user):
    query = 'content0'

    with app.app_context():
        posts = Post.query.filter(Post.content.like(query)).all()
        posts_json = marshal(posts, post_marshal_model)

    rv = client.get('/posts/?query=%s' % query,
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    assert len(posts_json) == len(json_data)

    for post in posts_json:
        assert post in json_data


@pytest.mark.parametrize(
    ('limit', 'offset'),
    (
        (5, 0),
        (10, 0),
        (0, 0),
        (5, 5)
    )
)
@pytest.mark.usefixtures('testdata')
def test_get_all_posts_with_limit(app, client, test_user, limit, offset):
    with app.app_context():
        posts = Post.query.offset(offset).limit(limit).all()
        posts_json = marshal(posts, post_marshal_model)

    rv = client.get('/posts/?offset=%s&limit=%s' % (offset, limit),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    assert len(posts_json) == len(json_data)

    for post in posts_json:
        assert post in json_data


@pytest.mark.usefixtures('testdata_for_sorting')
def test_get_all_posts_sort_by_time(app, client, test_user):
    with app.app_context():
        posts = Post.query.order_by(desc(Post.timestamp)).all()
        posts_json = marshal(posts, post_marshal_model)

    rv = client.get('/posts/?sort=time',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    assert len(posts_json) == len(json_data)

    # test same order
    for i in range(0, len(posts_json)):
        assert json_data[i] == posts_json[i]


def test_get_one_post(app, client, test_user, testdata_for_comments):
    post_id = testdata_for_comments

    with app.app_context():
        # this post id has many comments associated with it
        post = Post.query.get(post_id)
        post_json = marshal(post, post_with_comments_marshal_model)

    rv = client.get('/posts/%d' % post.id,
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data == post_json

    assert len(json_data['comments']) == len(post.comments)


@pytest.mark.usefixtures('testdata')
def test_get_one_post_error(app, client, test_user):
    rv = client.get('/posts/-1',
                    headers=test_user.auth_headers)

    assert rv.status_code == 404


@pytest.mark.usefixtures('testdata')
def test_add_post(app, client, test_user):
    data = {
        'title': 'title',
        'content': 'content',
        'category_id': 1,
        'course_id': 1
    }

    rv = client.post('/posts/',
                     json=data,
                     headers=test_user.auth_headers)

    assert rv.status_code == 201

    json_data = rv.get_json()

    assert json_data is not None

    with app.app_context():
        post = Post.query \
            .filter_by(title=data['title'], content=data['content']) \
            .first()

        # load relationships within session/app context

        # confirm expected default values
        assert post.comments_count == 0
        assert post.cheers_count == 0
        assert len(post.comments) == 0
        assert post.semester is not None

        # confirm relationships
        assert post.category.id == data['category_id']
        assert post.course.id == data['course_id']
        assert post.author.id == test_user.id


def test_add_comment(app, client, test_user, testdata_for_add_comment):
    # this post id has no comments
    post_id = testdata_for_add_comment

    data = {
        'content': 'Example comment content'
    }

    rv = client.post('/posts/%d/comments/' % post_id,
                     json=data,
                     headers=test_user.auth_headers)

    assert rv.status_code == 201

    with app.app_context():
        post = Post.query.get(post_id)

        assert len(post.comments) == 1
        assert post.comments[0].content == data['content']
