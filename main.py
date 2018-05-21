from ssapi import create_app
from ssapi.db import db

app = create_app()

# todo this should be migrations
with app.app_context():
    db.create_all()
