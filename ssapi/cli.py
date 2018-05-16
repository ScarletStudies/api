import click
from flask.cli import with_appcontext


def init_app(app):
    app.cli.add_command(seed_test_data)


@click.command()
@with_appcontext
def seed_test_data():
    """
    create (and/or reset) the e2e testing database and seed it
    """
    from itertools import chain
    from .db import db, User, Course, Category, Post, Semester
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
        Post(content='Hello world',
             author=users[0],
             course=courses[0],
             category=categories[0],
             semester=semesters[0]),
        Post(content='Hello world again',
             author=users[0],
             course=courses[1],
             category=categories[0],
             semester=semesters[0]),
        Post(content='Hello world thrice',
             author=users[0],
             course=courses[2],
             category=categories[0],
             semester=semesters[0]),
    ]

    for data in chain(courses, users, categories, semesters, posts):
        db.session.add(data)

    db.session.commit()
