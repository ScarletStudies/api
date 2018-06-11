import pytest
from flask_restplus import marshal
from ssapi.db import db, Course
from ssapi.apis.course import course_marshal_model


@pytest.fixture
def testdata_courses(app):
    with app.app_context():
        courses = []
        for n in range(0, 100):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='sb%d' % n, course_number='cn%d' % n)
            courses.append(course)
            db.session.add(course)

        db.session.commit()

        courses_json = marshal(courses, course_marshal_model)

        # courses are sorted by name by default
        courses_json = sorted(courses_json, key=lambda d: d['name'])

        return courses_json


@pytest.mark.parametrize(
    ('limit',),
    (
        (5,),
        (10,),
        (0,),
        (100,)
    )
)
def test_get_all_courses_with_limit(app, client, test_user, limit, testdata_courses):
    courses_json = testdata_courses

    # limit courses
    courses_json = courses_json[:limit]

    # hit the api
    rv = client.get('/courses/?limit=%s' % limit,
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert all(a == b for a, b in zip(courses_json, json_data))


@pytest.mark.parametrize(
    ('query', 'names',),
    (
        ('name0', ('name0',),),
        ('name99', ('name99',),),
        ('name1', ('name1', 'name10', 'name11', 'name12', 'name13', 'name14',
                   'name15', 'name16', 'name17', 'name18',),),
    )
)
def test_get_all_courses_by_search(app, client, test_user, testdata_courses, names, query):
    # hit the api
    rv = client.get('/courses/?query=%s' % query,
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    # reduce to names only
    json_data = [c['name'] for c in json_data]

    # confirm same data and order
    assert all(a == b for a, b in zip(names, json_data))
