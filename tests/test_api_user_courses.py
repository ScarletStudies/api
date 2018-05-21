import pytest
from flask_restplus import marshal
from ssapi.db import db, User, Course
from ssapi.apis.course import course_marshal_model


@pytest.fixture
def testdata_user_courses(app, test_user):
    with app.app_context():
        user = User.query.get(test_user.id)

        # courses assigned to test user by default
        user_courses = []
        # other courses in database
        other_courses = []

        for n in range(0, 50):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='subject%d' % n, course_number='cn%d' % n)

            user_courses.append(course)

            db.session.add(course)

            user.courses.append(course)

        for n in range(50, 100):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='subject%d' % n, course_number='cn%d' % n)

            other_courses.append(course)

            db.session.add(course)

        db.session.commit()

        user_courses_json = marshal(user_courses, course_marshal_model)

        # courses are sorted by name by default
        user_courses_json = sorted(user_courses_json, key=lambda d: d['name'])

        other_courses_json = marshal(other_courses, course_marshal_model)

        return user_courses_json, other_courses_json


def test_get_all_user_courses(app, client, test_user, testdata_user_courses):
    courses_json, _ = testdata_user_courses

    # hit the api
    rv = client.get('/users/courses/',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data == courses_json


def test_add_course_for_user(app, client, test_user, testdata_user_courses):
    user_courses_json, other_courses_json = testdata_user_courses

    target_course = other_courses_json[0]

    # hit the api to create the relationship for user and course
    rv = client.post('/users/courses/{}'.format(target_course['id']),
                     headers=test_user.auth_headers)

    assert rv.status_code == 200

    # compare against expected user courses
    user_courses_json.append(target_course)

    # courses are sorted by name by default
    user_courses_json = sorted(user_courses_json, key=lambda d: d['name'])

    # returns user courses
    json_data = rv.get_json()

    assert json_data == user_courses_json

    # hit the api to retrieve user semester
    rv = client.get('/users/courses/',
                    headers=test_user.auth_headers)

    # confirm user semester is changed
    assert rv.get_json() == user_courses_json


def test_add_existing_course_for_user(app, client, test_user, testdata_user_courses):
    user_courses_json, _ = testdata_user_courses

    target_course = user_courses_json[0]

    # hit the api to create the relationship for user and course
    rv = client.post('/users/courses/{}'.format(target_course['id']),
                     headers=test_user.auth_headers)

    assert rv.status_code == 200

    # expected user courses are same as before

    # returns user courses
    json_data = rv.get_json()

    assert json_data == user_courses_json

    # hit the api to retrieve user semester
    rv = client.get('/users/courses/',
                    headers=test_user.auth_headers)

    # confirm user semester is changed
    assert rv.get_json() == user_courses_json


def test_remove_course_from_user(app, client, test_user, testdata_user_courses):
    user_courses_json, _ = testdata_user_courses

    target_course = user_courses_json[0]

    # hit the api to remove the relationship for user and course
    rv = client.delete('/users/courses/{}'.format(target_course['id']),
                       headers=test_user.auth_headers)

    assert rv.status_code == 200

    # compare against expected user courses
    user_courses_json.remove(target_course)

    # returns user courses
    json_data = rv.get_json()

    assert json_data == user_courses_json


def test_remove_nonexisting_course_from_user(app, client, test_user, testdata_user_courses):
    user_courses_json, other_courses_json = testdata_user_courses

    target_course = other_courses_json[0]

    # hit the api to remove the relationship for user and course
    rv = client.delete('/users/courses/{}'.format(target_course['id']),
                       headers=test_user.auth_headers)

    assert rv.status_code == 200

    # expected user courses are same as before

    # returns user courses
    json_data = rv.get_json()

    assert json_data == user_courses_json
