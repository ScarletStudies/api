import os

from flask import Flask
from flask_cors import CORS


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://test:test@db/postgres',
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
    from .cli import init_app as cli_init_app
    cli_init_app(app)

    return app
