import pytest
from flask_restplus import marshal
from ssapi.db import db, Category
from ssapi.apis.category import category_marshal_model


@pytest.fixture
def categories_testdata(app):
    """
    prepare the testdata and return the expected json result
    """
    with app.app_context():
        categories = []

        for n in range(0, 10):
            category = Category(name='name%d' % n)
            categories.append(category)
            db.session.add(category)

        db.session.commit()

        # categories are sorted by name by default
        categories_json = marshal(categories, category_marshal_model)

        categories_json = sorted(categories_json, key=lambda d: d['name'])

        return categories_json


def test_get_all_categories(app, client, test_user, categories_testdata):
    # hit the api
    rv = client.get('/categories/',
                    headers=test_user.auth_headers)

    assert rv.status_code == 200

    json_data = rv.get_json()
    categories_json = categories_testdata

    # confirm same data and order
    assert all(a == b for a, b in zip(categories_json, json_data))
