from flask_migrate import Migrate
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
migrate = Migrate(db=db)


def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app)


usercourses = db.Table('usercourses',
                       db.Column('user_id', db.Integer, db.ForeignKey(
                           'user.id'), primary_key=True),
                       db.Column('course_id', db.Integer, db.ForeignKey(
                           'course.id'), primary_key=True)
                       )

userpostcheers = db.Table('userpostcheers',
                          db.Column('user_id', db.Integer, db.ForeignKey(
                              'user.id'), primary_key=True),
                          db.Column('post_id', db.Integer, db.ForeignKey(
                              'post.id'), primary_key=True)
                          )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    courses = db.relationship(
        'Course', secondary=usercourses, order_by='Course.name'
    )

    @property
    def rolenames(self):
        return ['user']

    @classmethod
    def lookup(cls, email):
        return cls.query.filter_by(email=email).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_verified


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


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.Text, nullable=False)
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
    cheers = db.relationship('User', secondary=userpostcheers)

    @property
    def comments_count(self):
        return Comment.query.filter_by(post_id=self.id).count()

    @property
    def cheers_count(self):
        return len(self.cheers)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False,
                          server_default=func.now())

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', uselist=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', uselist=False)
