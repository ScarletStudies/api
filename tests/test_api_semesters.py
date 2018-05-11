import pytest
from flask_restplus import marshal
from random import choice
from sqlalchemy import desc
from ssapi.db import db, Semester
from ssapi.apis.semester import semester_marshal_model


@pytest.fixture
def testdata(app):
    with app.app_context():
        for n in range(0, 10):
            semester = Semester(year=2010 + n,
                                season=choice(('fall', 'summer', 'spring', 'winter')))
            db.session.add(semester)

        db.session.commit()


@pytest.mark.usefixtures('testdata')
def test_get_all_semesters(app, client):
    rv = client.get('/semesters/')

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    with app.app_context():
        semesters = Semester.query.order_by(desc(Semester.id)).all()
        semesters_json = marshal(semesters, semester_marshal_model)

    assert len(semesters_json) == len(json_data)

    # semesters should be returned in descending order
    for i in range(0, len(semesters_json)):
        assert semesters_json[i] == json_data[i]


@pytest.mark.usefixtures('testdata')
def test_get_current_semester(app, client):
    rv = client.get('/semesters/current')

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    with app.app_context():
        semesters = Semester.query.order_by(desc(Semester.year)).first()
        semesters_json = marshal(semesters, semester_marshal_model)

    assert semesters_json == json_data
