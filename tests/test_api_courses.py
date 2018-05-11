import pytest
from flask_restplus import marshal
from ssapi.db import db, Course
from ssapi.apis.course import course_marshal_model


@pytest.fixture
def testdata(app):
    with app.app_context():
        for n in range(0, 10):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='subject%d' % n, course_number='cn%d' % n)
            db.session.add(course)

        db.session.commit()


@pytest.mark.usefixtures('testdata')
def test_get_all_courses(app, client):
    rv = client.get('/courses/')

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    with app.app_context():
        courses = Course.query.all()
        courses_json = marshal(courses, course_marshal_model)

    assert len(courses_json) == len(json_data)

    for course in courses_json:
        assert course in json_data


@pytest.mark.usefixtures('testdata')
def test_get_one_course(app, client):
    with app.app_context():
        course = Course.query.first()
        course_json = marshal(course, course_marshal_model)

    rv = client.get('/courses/%d' % course.id)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data == course_json


@pytest.mark.usefixtures('testdata')
def test_get_one_course_error(app, client):
    rv = client.get('/courses/-1')

    assert rv.status_code == 404
