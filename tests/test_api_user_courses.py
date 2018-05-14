import pytest
from flask_restplus import marshal
from ssapi.db import db, User, Course
from ssapi.apis.course import course_marshal_model
from ssapi.praetorian import guard


@pytest.fixture
def testdata(app, test_user):
    with app.app_context():
        user = User.query.get(test_user.id)

        for n in range(0, 5):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='subject%d' % n, course_number='cn%d' % n)
            db.session.add(course)

            user.courses.append(course)

        db.session.commit()


@pytest.mark.usefixtures('testdata')
def test_get_all_user_courses(app, client, test_user):
    with app.app_context():
        user = User.query.get(test_user.id)
        courses = user.courses
        courses_json = marshal(courses, course_marshal_model)

    rv = client.get('/users/courses/',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    assert len(json_data) == len(courses_json)

    for course in json_data:
        assert course in courses_json


@pytest.mark.usefixtures('testdata')
def test_add_course_for_user(app, client, test_user):
    with app.app_context():
        user = User.query.get(test_user.id)

        target_course = Course(name='target',
                               offering_unit='target_ou',
                               subject='target_subject',
                               course_number='target_cn')

        db.session.add(target_course)
        db.session.commit()

        target_course_json = marshal(target_course, course_marshal_model)

        target_course.id
        user.id

    # create the relationship for user and course
    rv = client.post('/users/courses/%d' % target_course.id,
                     headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns user courses, compare against user courses in db
    with app.app_context():
        user = User.query.get(user.id)
        courses = user.courses
        courses_json = marshal(courses, course_marshal_model)

    json_data = rv.get_json()

    assert json_data is not None

    assert target_course_json in json_data
    assert json_data == courses_json


@pytest.mark.usefixtures('testdata')
def test_remove_course_from_user(app, client, test_user):
    with app.app_context():
        user = User.query.get(test_user.id)
        target_course = user.courses[0]
        target_course_json = marshal(target_course, course_marshal_model)
        user.id

    # remove the relationship for user and course
    rv = client.delete('/users/courses/%d' % target_course.id,
                       headers=test_user.auth_headers)

    assert rv.status_code == 200

    # returns user courses, compare against user courses in db
    with app.app_context():
        user = User.query.get(user.id)
        courses = user.courses
        courses_json = marshal(courses, course_marshal_model)

    json_data = rv.get_json()

    assert json_data is not None

    assert target_course_json not in json_data
    assert json_data == courses_json
