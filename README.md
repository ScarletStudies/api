# Scarlet Studies Backend/API

## Setup

With Python 3 installed and working in this project directory:

```
$ python3 -m venv . # create virtual env
$ source bin/activate
$ pip install -r requirements.txt
$ export FLASK_APP=ssapi
$ export FLASK_ENV=development # or production
$ flask run
```

Then point your browser at http://localhost:5000 to see the autogenerated Swagger documentation.

## Tests

With the virtual env activated:

```
$ pip install -e .
$ make test
```

## Stack

#### Backend

- [Flask](http://flask.pocoo.org/) _three clause BSD_
- [Flask-RestPlus](https://flask-restplus.readthedocs.io/en/stable/) _MIT_
- [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/2.3/) _three clause BSD_
- [SQLAlchemy](https://www.sqlalchemy.org/) _MIT_
- [SQLite](https://www.sqlite.org/index.html) _public domain_

## License

GPL
