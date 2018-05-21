import pytest
from flask_restplus import marshal
from random import choice
from ssapi.db import db, Semester
from ssapi.apis.semester import semester_marshal_model


@pytest.fixture
def testdata_semesters(app):
    with app.app_context():
        semesters = []

        for n in range(0, 100):
            semester = Semester(year=2010 + n,
                                season=choice(('fall', 'summer', 'spring', 'winter')))
            semesters.append(semester)
            db.session.add(semester)

        db.session.commit()

        semesters_json = marshal(semesters, semester_marshal_model)

        # semesters are sorted by id desc
        semesters_json = sorted(
            semesters_json, key=lambda d: int(d['id']), reverse=True
        )

        return semesters_json


def test_get_all_semesters(app, client, test_user, testdata_semesters):
    semesters_json = testdata_semesters

    # hit the api
    rv = client.get('/semesters/',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    # confirm same data and order
    assert json_data == semesters_json
