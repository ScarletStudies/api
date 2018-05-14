from flask_praetorian import Praetorian


guard = Praetorian()


def init_app(app):
    from .db import User
    guard.init_app(app, User)
