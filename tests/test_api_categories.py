import pytest
from flask_restplus import marshal
from ssapi.db import db, Category
from ssapi.apis.category import category_marshal_model


@pytest.fixture
def testdata(app):
    with app.app_context():
        for n in range(0, 10):
            category = Category(name='name%d' % n)
            db.session.add(category)

        db.session.commit()


@pytest.mark.usefixtures('testdata')
def test_get_all_categories(app, client, test_user):
    rv = client.get('/categories/',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()

    assert json_data is not None

    with app.app_context():
        categories = Category.query.all()
        categories_json = marshal(categories, category_marshal_model)

    assert len(categories_json) == len(json_data)

    for category in categories_json:
        assert category in json_data
