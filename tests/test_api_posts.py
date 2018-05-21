import pytest
from datetime import datetime
from flask_restplus import marshal
from ssapi.db import db, Post, Course, Category, Semester

from ssapi.apis.post import post_marshal_model
from ssapi.apis.category import category_marshal_model
from ssapi.apis.course import course_marshal_model
from ssapi.apis.semester import semester_marshal_model


@pytest.fixture
def testdata_posts(app, test_user):
    with app.app_context():
        # create categories
        categories = []
        for n in range(0, 50):
            category = Category(name='name%d' % n)
            categories.append(category)
            db.session.add(category)

        # create courses
        courses = []
        for n in range(0, 50):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='subject%d' % n, course_number='cn%d' % n)
            courses.append(course)
            db.session.add(course)

        # create semesters
        semesters = []
        for n in range(0, 50):
            semester = Semester(year=n, season='Fall')
            semesters.append(semester)
            db.session.add(semester)

        # create posts
        posts = []
        for n in range(0, 50):
            post = Post(title='title%d' % n,
                        content='content%d' % n,
                        timestamp=datetime(2018 + n, 1, 1),
                        author_id=test_user.id,
                        course=courses[n],
                        category=categories[n],
                        semester=semesters[n])

            posts.append(post)
            db.session.add(post)

        db.session.commit()

        posts_json = marshal(posts, post_marshal_model)
        categories_json = marshal(categories, category_marshal_model)
        semesters_json = marshal(semesters, semester_marshal_model)
        courses_json = marshal(courses, course_marshal_model)

        return posts_json, courses_json, categories_json, semesters_json


def test_get_all_posts(app, client, test_user, testdata_posts):
    posts_json = testdata_posts[0]

    # hit the api
    rv = client.get('/posts/',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    json_data = rv.get_json()

    # sorts posts by time by default
    posts_json = sorted(posts_json, key=lambda p: p['timestamp'], reverse=True)

    # returns 100 posts max by default
    posts_json = posts_json[:100]

    assert posts_json == json_data


def test_get_all_posts_for_course(app, client, test_user, testdata_posts):
    posts_json = testdata_posts[0]
    target_course = testdata_posts[1][0]

    # hit the api
    rv = client.get('/posts/?courses[]={}'.format(target_course['id']),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    json_data = rv.get_json()

    # posts should be limited to the target course
    posts_json = [p for p in posts_json if p['course']
                  ['id'] == target_course['id']]

    assert json_data == posts_json


def test_get_all_posts_by_category(app, client, test_user, testdata_posts):
    posts_json = testdata_posts[0]
    target_category = testdata_posts[2][0]

    # hit the api
    rv = client.get('/posts/?categories[]={}'.format(target_category['id']),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    json_data = rv.get_json()

    # posts should be limited to the target category
    posts_json = [p for p in posts_json if p['category']
                  ['id'] == target_category['id']]

    assert posts_json == json_data


def test_get_all_posts_by_search(app, client, test_user, testdata_posts):
    posts_json = testdata_posts[0]

    content_query = posts_json[0]['content']

    # hit the api
    rv = client.get('/posts/?query={}'.format(content_query),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    json_data = rv.get_json()

    # posts should be limited by search
    posts_json = [p for p in posts_json if content_query in p['content']]

    assert posts_json == json_data


@pytest.mark.parametrize(
    ('limit', 'offset'),
    (
        (5, 0),
        (10, 0),
        (0, 0),
        (5, 5)
    )
)
def test_get_all_posts_with_limit(app, client, test_user, limit, offset, testdata_posts):
    posts_json = testdata_posts[0]

    # hit the api
    rv = client.get('/posts/?offset=%s&limit=%s' % (offset, limit),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    json_data = rv.get_json()

    # sorts posts by time by default
    posts_json = sorted(posts_json, key=lambda p: p['timestamp'], reverse=True)

    # posts should be limited by limit and offset
    posts_json = posts_json[offset:offset+limit]

    assert posts_json == json_data


def test_add_post(app, client, test_user, testdata_posts):
    target_course = testdata_posts[1][0]
    target_category = testdata_posts[2][0]
    target_semester = testdata_posts[3][-1]

    data = {
        'title': 'title',
        'content': '<p>content</p>',
        'category': {
            'id': target_category['id']
        },
        'course': {
            'id': target_course['id']
        }
    }

    # hit the api
    rv = client.post('/posts/',
                     json=data,
                     headers=test_user.auth_headers)

    assert rv.status_code == 201

    # returns the new post
    json_data = rv.get_json()

    expected = {
        'title': 'title',
        'content': '<p>content</p>',
        'category': target_category,
        'course': target_course,
        'comments': [],
        'cheers': [],
        'author': {
            'email': test_user.email
        },
        'semester': target_semester,
        'is_archived': False
    }

    assert all(json_data[k] == v for k, v in expected.items())


def test_add_comment(app, client, test_user, testdata_posts):
    target_post = testdata_posts[0][0]

    data = {
        'content': '<p>Example comment content</p>'
    }

    # hit the api
    rv = client.post('/posts/{}/comments/'.format(target_post['id']),
                     json=data,
                     headers=test_user.auth_headers)

    assert rv.status_code == 201

    # returns the updated post
    json_data = rv.get_json()

    # post remains unchanged except for comments
    expected = {
        'title': target_post['title'],
        'content': target_post['content'],
        'category': target_post['category'],
        'cheers': [],
        'author': {
            'email': test_user.email
        },
        'semester': target_post['semester'],
        'is_archived': False
    }

    assert all(json_data[k] == v for k, v in expected.items())

    expected_comment = {
        'content': '<p>Example comment content</p>',
        'author': {
            'email': test_user.email
        }
    }

    assert all(json_data['comments'][0][k] ==
               v for k, v in expected_comment.items())


def test_add_cheer(app, client, test_user, testdata_posts):
    target_post = testdata_posts[0][0]

    # hit the api
    rv = client.post('/posts/{}/cheers/'.format(target_post['id']),
                     headers=test_user.auth_headers)

    assert rv.status_code == 201

    # returns the updated post
    json_data = rv.get_json()

    # post remains unchanged except for comments
    expected = {
        'title': target_post['title'],
        'content': target_post['content'],
        'category': target_post['category'],
        'cheers': [{
            'email': test_user.email
        }],
        'comments': [],
        'author': {
            'email': test_user.email
        },
        'semester': target_post['semester'],
        'is_archived': False
    }

    assert all(json_data[k] == v for k, v in expected.items())
