import os

from flask import Flask
from flask_cors import CORS


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        ERROR_404_HELP=False,
        JWT_ACCESS_LIFESPAN={'hours': 24},
        JWT_REFRESH_LIFESPAN={'days': 30},
        MAIL_DEFAULT_SENDER='noreply@scarletstudies.org'
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_envvar('SSAPI_SETTINGS', silent=False)
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

    from .tasks import init_app as tasks_init_app
    tasks_init_app(app)

    # app scripts
    from .cli import init_app as cli_init_app
    cli_init_app(app)

    return app
