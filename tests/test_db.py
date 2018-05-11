import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError
from ssapi.db import db, User, Course, Category, Semester, Post, Comment, \
    PostCheerUserAssociation

################
# User Model
##############


@pytest.mark.parametrize(('email', 'pwhash', 'is_verified'), (
    ('me@me.com', 'asdf', True),
    ('aslightlylongeremailaddress@aslightlylongerdomain.com',
     'a slightly longer pwhash', False),
))
def test_valid_user_model(app, email, pwhash, is_verified):
    with app.app_context():
        user = User(email=email, pwhash=pwhash, is_verified=is_verified)

        db.session.add(user)
        db.session.commit()

        found = User.query.filter_by(email=email).first()
        assert found is not None

        # test user properties
        assert found.email == email
        assert found.pwhash == pwhash
        assert found.is_verified == is_verified

        # test courses relationship

        # create example courses
        courses = [
            Course(name='n%d' % n, offering_unit='ou%d' % n,
                   subject='s%d' % n, course_number='cn%d' % n)
            for n in range(0, 5)
        ]

        for course in courses:
            db.session.add(course)

        db.session.commit()

        # add courses to user
        # thanks to https://stackoverflow.com/a/45047925
        user.courses.extend(courses)

        db.session.commit()

        assert user.courses is not None
        assert len(user.courses) == len(courses)
        for course in courses:
            assert course in user.courses


@pytest.mark.parametrize(('email', 'pwhash', 'is_verified'), (
    (None, 'valid', True),
    ('valid', None, True)
))
def test_invalid_user_model(app, email, pwhash, is_verified):
    with app.app_context():
        user = User(email=email, pwhash=pwhash, is_verified=is_verified)

        with pytest.raises(IntegrityError) as excinfo:
            db.session.add(user)
            db.session.commit()

        db.session.rollback()
        found = User.query.filter_by(email=email).first()
        assert found is None

        assert 'NOT NULL constraint failed' in str(excinfo)

################
# Course Model
##############


@pytest.mark.parametrize(('name', 'offering_unit', 'subject', 'course_number'), (
    ('cs111', '1', '1', '123'),
    ('cs112', '2', '2', '1234')
))
def test_valid_course_model(app, name, offering_unit, subject, course_number):
    with app.app_context():
        course = Course(name=name, offering_unit=offering_unit,
                        subject=subject, course_number=course_number)

        db.session.add(course)
        db.session.commit()

        found = Course.query.filter_by(name=name).first()
        assert found is not None

        assert found.name == name
        assert found.offering_unit == offering_unit
        assert found.subject == subject
        assert found.course_number == course_number


@pytest.mark.parametrize(('name', 'offering_unit', 'subject', 'course_number'), (
    (None, '1', '1', '123'),
    ('', None, '1', '123'),
    ('', '1', None, '123'),
    ('', '1', '1', None),
))
def test_invalid_course_model(app, name, offering_unit, subject, course_number):
    with app.app_context():
        course = Course(name=name, offering_unit=offering_unit,
                        subject=subject, course_number=course_number)

        with pytest.raises(IntegrityError) as excinfo:
            db.session.add(course)
            db.session.commit()

        db.session.rollback()
        found = Course.query.filter_by(name=name).first()
        assert found is None

        assert 'NOT NULL constraint failed' in str(excinfo)

################
# Category Model
##############


@pytest.mark.parametrize(('name',), (
    ('Exam',),
    ('Lecture',)
))
def test_valid_category_model(app, name):
    with app.app_context():
        category = Category(name=name)

        db.session.add(category)
        db.session.commit()

        found = Category.query.filter_by(name=name).first()
        assert found is not None

        assert found.name == name


@pytest.mark.parametrize(('name',), (
    (None,),
))
def test_invalid_category_model(app, name):
    with app.app_context():
        category = Category(name=name)

        with pytest.raises(IntegrityError) as excinfo:
            db.session.add(category)
            db.session.commit()

        db.session.rollback()

        found = Category.query.filter_by(name=name).first()
        assert found is None

        assert 'NOT NULL constraint failed' in str(excinfo)

################
# Semester Model
##############


@pytest.mark.parametrize(
    ('year', 'season'),
    (
        (2018, 'fall'),
    )
)
def test_valid_semester_model(app, year, season):
    with app.app_context():
        semester = Semester(year=year, season=season)

        db.session.add(semester)
        db.session.commit()

        found = Semester.query.filter_by(year=year, season=season).first()
        assert found is not None

        assert found.year == year
        assert found.season == season


@pytest.mark.parametrize(
    ('year', 'season'),
    (
        (None, 'fall'),
        (2018, None)
    )
)
def test_invalid_semester_model(app, year, season):
    with app.app_context():
        semester = Semester(year=year, season=season)

        with pytest.raises(IntegrityError) as excinfo:
            db.session.add(semester)
            db.session.commit()

        db.session.rollback()
        found = Semester.query.filter_by(year=year, season=season).first()
        assert found is None

        assert 'NOT NULL constraint failed' in str(excinfo)

################
# Post Model
##############


def test_valid_post_model(app):
    with app.app_context():
        content = 'example post content'
        is_archived = False

        author = User(email='email', pwhash='pwhash', is_verified=True)
        course = Course(name='name', offering_unit='1',
                        subject='2', course_number='3')
        semester = Semester(year=2018, season='fall')
        category = Category(name='name')

        db.session.add(author)
        db.session.add(course)
        db.session.add(semester)
        db.session.add(category)

        db.session.commit()

        post = Post(content=content,
                    is_archived=is_archived, author_id=author.id,
                    semester_id=semester.id, category_id=category.id,
                    course_id=course.id)

        db.session.add(post)
        db.session.commit()

        found = Post.query.filter_by(id=post.id).first()
        assert found is not None

        # test Post object properties
        assert found.content == content
        assert found.timestamp is not None
        assert found.is_archived == is_archived

        # test relationships
        assert found.author.email == author.email

        assert found.course.name == course.name

        assert found.semester.year == semester.year

        assert found.category.name == category.name

        # test comments
        comments = [
            Comment(content='c%d' % n, post_id=post.id, author_id=author.id)
            for n in range(0, 5)
        ]

        for comment in comments:
            db.session.add(comment)

        db.session.commit()

        assert post.comments is not None
        assert len(post.comments) == len(comments)
        for comment in comments:
            assert comment in post.comments

        # test cheers
        cheers = [
            PostCheerUserAssociation(post_id=post.id, user_id=author.id)
            for _ in range(0, 100)
        ]

        for cheer in cheers:
            db.session.add(cheer)

        db.session.commit()

        assert post.cheers is not None
        assert len(post.cheers) == len(cheers)
        for cheer in cheers:
            assert cheer in post.cheers

# TODO test invalid


################
# Comment Model
##############


def test_valid_comment_model(app):
    with app.app_context():
        content = 'example comment content'

        author = User(email='email', pwhash='pwhash', is_verified=True)
        course = Course(name='name', offering_unit='1',
                        subject='2', course_number='3')
        semester = Semester(year=2018, season='fall')
        category = Category(name='name')

        db.session.add(author)
        db.session.add(course)
        db.session.add(semester)
        db.session.add(category)

        db.session.commit()

        post = Post(content='example post content',
                    author_id=author.id, semester_id=semester.id,
                    category_id=category.id, course_id=course.id)

        db.session.add(post)
        db.session.commit()

        comment = Comment(content=content,
                          post_id=post.id,
                          author_id=author.id)

        db.session.add(comment)
        db.session.commit()

        found = Comment.query.filter_by(id=comment.id).first()
        assert found is not None

        assert found.content == content
        assert found.timestamp is not None

        assert found.author.email == author.email

# TODO test invalid
