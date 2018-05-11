from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.sql import func

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


db = SQLAlchemy(metadata=metadata)


def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)


usercourses = db.Table('usercourses',
                       db.Column('user_id', db.Integer, db.ForeignKey(
                           'user.id'), primary_key=True),
                       db.Column('course_id', db.Integer, db.ForeignKey(
                           'course.id'), primary_key=True)
                       )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(128), nullable=False)
    pwhash = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    courses = db.relationship('Course', secondary=usercourses)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(128), nullable=False)
    offering_unit = db.Column(db.String(8), nullable=False)
    subject = db.Column(db.String(8), nullable=False)
    course_number = db.Column(db.String(8), nullable=False)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(32), nullable=False)


class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    year = db.Column(db.Integer, nullable=False)
    season = db.Column(db.String(16), nullable=False)


class PostCheerUserAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey(
        'post.id'), nullable=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False,
                          server_default=func.now())
    is_archived = db.Column(db.Boolean, nullable=False, default=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', uselist=False)

    course_id = db.Column(db.Integer, db.ForeignKey(
        'course.id'), nullable=False)
    course = db.relationship('Course', uselist=False)

    semester_id = db.Column(db.Integer, db.ForeignKey(
        'semester.id'), nullable=False)
    semester = db.relationship('Semester', uselist=False)

    category_id = db.Column(db.Integer, db.ForeignKey(
        'category.id'), nullable=False)
    category = db.relationship('Category', uselist=False)

    comments = db.relationship('Comment')

    cheers = db.relationship('PostCheerUserAssociation')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False,
                          server_default=func.now())

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', uselist=False)
