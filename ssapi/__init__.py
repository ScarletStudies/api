import click
import os

from flask import Flask
from flask.cli import with_appcontext
from flask_cors import CORS


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' +
        os.path.join(app.instance_path, 'app.sqlite'),
        ERROR_404_HELP=False,
        JWT_ACCESS_LIFESPAN={'hours': 24},
        JWT_REFRESH_LIFESPAN={'days': 30}
    )

    # load the config from env var
    if os.environ.get('e2e', False):
        e2e_db_path = '/tmp/ssapi/e2e.db'
        try:
            os.makedirs(e2e_db_path)
        except OSError:
            pass
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + e2e_db_path

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config is passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # CORS
    CORS(app)

    from . import db
    db.init_app(app)

    import ssapi.apis as api
    api.init_app(app)

    from .praetorian import init_app as praetorian_init_app
    praetorian_init_app(app)

    # app scripts
    app.cli.add_command(seed_test_data)

    return app


@click.command()
@with_appcontext
def seed_test_data():
    """
    create (and/or reset) the e2e testing database and seed it
    """
    from itertools import chain
    from .db import db, User, Course
    from .praetorian import guard

    db.drop_all()

    db.create_all()

    courses = [
        Course(name='Programming I',
               offering_unit='21',
               subject='98',
               course_number='101'),
        Course(name='Programming II',
               offering_unit='21',
               subject='98',
               course_number='102'),
        Course(name='Linear Algebra',
               offering_unit='21',
               subject='640',
               course_number='350'),
        Course(name='Calc I',
               offering_unit='21',
               subject='640',
               course_number='135'),
        Course(name='Calc II',
               offering_unit='21',
               subject='640',
               course_number='136'),
        Course(name='Calc III',
               offering_unit='21',
               subject='640',
               course_number='235'),
        Course(name='Foundations of Modern Math',
               offering_unit='21',
               subject='640',
               course_number='238'),
        Course(name='Elementary Differential Equations',
               offering_unit='21',
               subject='640',
               course_number='314'),
        Course(name='Probability and Statistics',
               offering_unit='21',
               subject='640',
               course_number='327'),
        Course(name='Topology I',
               offering_unit='21',
               subject='640',
               course_number='441'),
        Course(name='Theory of Numbers',
               offering_unit='21',
               subject='640',
               course_number='456'),
        Course(name='Numerical Analysis',
               offering_unit='21',
               subject='640',
               course_number='473'),
    ]

    users = [
        User(email='test@example.com',
             password=guard.encrypt_password('password123')),
    ]

    for data in chain(courses, users):
        db.session.add(data)

    db.session.commit()
