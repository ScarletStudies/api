import click
from flask.cli import with_appcontext


def init_app(app):
    app.cli.add_command(seed_test_data)
    app.cli.add_command(seed_test_user)


@click.command()
@with_appcontext
def seed_test_user():
    """
    seed test user for casual interaction
    """
    from .db import db, User
    from .praetorian import guard

    user = User(email='tristan.kernan@rutgers.edu',
                password=guard.encrypt_password('stringstring'),
                is_verified=True)

    db.session.add(user)
    db.session.commit()

    print('Added test user {}'.format(user.email))


@click.command()
@with_appcontext
def seed_test_data():
    """
    create (and/or reset) the e2e testing database and seed it
    """
    from itertools import chain
    from .db import db, User, Course, Category, Post, Semester, Comment
    from .praetorian import guard

    db.drop_all()

    db.create_all()

    courses = [
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
             password=guard.encrypt_password('password123'),
             is_verified=True),
    ]

    categories = [
        Category(name='Exam'),
        Category(name='Lecture'),
        Category(name='Recitation'),
        Category(name='Homework')
    ]

    semesters = [
        Semester(year=2018,
                 season='Spring')
    ]

    posts = [
        Post(title='I have a title',
             content='Hello world, {}'.format(course.name),
             author=users[0],
             course=course,
             category=categories[0],
             semester=semesters[0])
        for course in courses
    ]

    comments = [
        Comment(content='Comment 1',
                post=posts[0],
                author=users[0]),
        Comment(content='Comment 2',
                post=posts[0],
                author=users[0]),
        Comment(content='Comment 3',
                post=posts[0],
                author=users[0]),
        Comment(content='Comment 4',
                post=posts[0],
                author=users[0]),
        Comment(content='Comment 5',
                post=posts[0],
                author=users[0]),
    ]

    for data in chain(courses, users, categories, semesters, posts, comments):
        db.session.add(data)

    db.session.commit()

    print('Seeded database with {} items'
          .format(len(courses) + len(users) + len(categories) + len(semesters) + len(posts) + len(comments)))
