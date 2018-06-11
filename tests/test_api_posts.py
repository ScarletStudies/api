import pytest
from datetime import datetime, date
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
                            subject='sb%d' % n, course_number='cn%d' % n)
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
                        due_date=date(2018 + n, 2, 3),
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
    test_posts_json = testdata_posts[0]

    # hit the api
    rv = client.get('/posts/',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()
    api_posts_json = api_data_json['items']

    # sorts posts by time by default
    test_posts_json = sorted(
        test_posts_json, key=lambda p: p['timestamp'], reverse=True)

    # returns 20 posts max by default
    test_posts_json = test_posts_json[:20]

    assert api_posts_json == test_posts_json


def test_get_all_posts_sorted_by_time(app, client, test_user, testdata_posts):
    test_posts_json = testdata_posts[0]

    # hit the api
    rv = client.get('/posts/?sort=time',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()
    api_posts_json = api_data_json['items']

    # sorts posts by time by default
    test_posts_json = sorted(
        test_posts_json, key=lambda p: p['timestamp'], reverse=True)

    # returns 20 posts max by default
    test_posts_json = test_posts_json[:20]

    assert api_posts_json == test_posts_json


def test_get_all_posts_sorted_by_latest_activity(app, client, test_user, testdata_posts):
    test_posts_json = testdata_posts[0]

    # hit the api
    rv = client.get('/posts/?sort=activity',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()
    api_posts_json = api_data_json['items']

    # sorts posts by latest activity
    def sort_key(p):
        if len(p['comments']):
            return max(c['timestamp'] for c in p['comments'])
        return p['timestamp']

    test_posts_json = sorted(test_posts_json, key=sort_key, reverse=True)

    # returns 20 posts max by default
    test_posts_json = test_posts_json[:20]

    assert api_posts_json == test_posts_json


def test_get_all_posts_for_course(app, client, test_user, testdata_posts):
    test_posts_json = testdata_posts[0]
    target_course = testdata_posts[1][0]

    # hit the api
    rv = client.get('/posts/?courses[]={}'.format(target_course['id']),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()
    api_posts_json = api_data_json['items']

    # posts should be limited to the target course
    test_posts_json = [p for p in test_posts_json if p['course']
                       ['id'] == target_course['id']]

    # don't have to worry about limiting or sorting because there
    # are few posts per course for this test

    assert api_posts_json == test_posts_json


def test_get_all_posts_by_category(app, client, test_user, testdata_posts):
    test_posts_json = testdata_posts[0]
    target_category = testdata_posts[2][0]

    # hit the api
    rv = client.get('/posts/?categories[]={}'.format(target_category['id']),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()
    api_posts_json = api_data_json['items']

    # posts should be limited to the target category
    test_posts_json = [p for p in test_posts_json if p['category']
                       ['id'] == target_category['id']]

    # don't have to worry about limiting or sorting because there
    # are few posts per category for this test

    assert test_posts_json == api_posts_json


def test_get_all_posts_by_search_content(app, client, test_user, testdata_posts):
    test_posts_json = testdata_posts[0]
    content_query = test_posts_json[0]['content']

    # hit the api
    rv = client.get('/posts/?query={}'.format(content_query),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()
    api_posts_json = api_data_json['items']

    # posts should be limited by simple search
    test_posts_json = [
        p for p in test_posts_json if content_query in p['content']]

    assert test_posts_json == api_posts_json


def test_get_all_posts_by_search_title(app, client, test_user, testdata_posts):
    test_posts_json = testdata_posts[0]
    title_query = test_posts_json[0]['title']

    # hit the api
    rv = client.get('/posts/?query={}'.format(title_query),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()
    api_posts_json = api_data_json['items']

    # posts should be limited by simple search
    test_posts_json = [
        p for p in test_posts_json if title_query in p['title']]

    assert test_posts_json == api_posts_json


def test_get_all_posts_within_time_period(app, client, test_user, testdata_posts):
    test_posts_json = testdata_posts[0]

    start_date = datetime(2018, 1, 1)
    start = '2018-1-1'
    end_date = datetime(2020, 1, 1)
    end = '2020-1-1'

    # hit the api
    rv = client.get('/posts/?start_date={}&end_date={}'.format(start, end),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()
    api_posts_json = api_data_json['items']

    # posts should be limited by search
    for pj in test_posts_json:
        pj['due_date'] = datetime.strptime(pj['due_date'], '%Y-%m-%d')

    # need to convert json data due dates to datetime objects now too
    for jd in api_posts_json:
        jd['due_date'] = datetime.strptime(jd['due_date'], '%Y-%m-%d')

    test_posts_json = [p for p in test_posts_json if p['due_date'] <
                       end_date and p['due_date'] >= start_date]

    # sorts posts by time by default
    test_posts_json = sorted(
        test_posts_json, key=lambda p: p['timestamp'], reverse=True)

    assert test_posts_json == api_posts_json


@pytest.mark.parametrize(
    ('page',),
    (
        (1,),
        (2,),
        (3,),
    )
)
def test_get_all_posts_with_limit(app, client, test_user, page, testdata_posts):
    test_posts_json = testdata_posts[0]

    # hit the api
    rv = client.get('/posts/?page=%d' % page,
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the posts
    api_data_json = rv.get_json()

    # grab the posts and total count
    api_posts_json = api_data_json['items']

    # sorts posts by time by default
    test_posts_json = sorted(
        test_posts_json, key=lambda p: p['timestamp'], reverse=True)

    # posts should be limited by limit and offset
    test_posts_json = test_posts_json[(page - 1) * 20: page * 20]

    assert test_posts_json == api_posts_json


def test_add_post(app, client, test_user, testdata_posts):
    target_course = testdata_posts[1][0]
    target_category = testdata_posts[2][0]
    target_semester = testdata_posts[3][-1]

    data = {
        'title': 'title',
        'content': '<p>content</p>',
        'due_date': '2015-01-01',
        'category': {
            'id': target_category['id']
        },
        'course': {
            'id': target_course['id']
        },
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
        'due_date': '2015-01-01',
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


def test_get_one_post(app, client, test_user, testdata_posts):
    target_post = testdata_posts[0][0]

    # hit the api
    rv = client.get('/posts/{}'.format(target_post['id']),
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns the post
    json_data = rv.get_json()

    assert json_data == target_post


def test_fail_get_one_post(app, client, test_user, testdata_posts):
    unavailable_id = 1000000

    # hit the api
    rv = client.get('/posts/{}'.format(unavailable_id),
                    headers=test_user.auth_headers)

    assert rv.status_code == 404
