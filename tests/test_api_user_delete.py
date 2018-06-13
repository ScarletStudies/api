import pytest
from datetime import datetime
from flask_restplus import marshal

from ssapi.db import db, User, Category, Course, Semester, Post, Comment
from ssapi.tasks import mail

from ssapi.apis.post import post_marshal_model
from ssapi.apis.comment import comment_marshal_model


@pytest.fixture
def testdata_posts(app, test_user):
    with app.app_context():
        # create categories
        categories = []
        for n in range(0, 10):
            category = Category(name='name%d' % n)
            categories.append(category)
            db.session.add(category)

        # create courses
        courses = []
        for n in range(0, 10):
            course = Course(name='name%d' % n, offering_unit='ou%d' % n,
                            subject='subject%d' % n, course_number='cn%d' % n)
            courses.append(course)
            db.session.add(course)

        # create semesters
        semesters = []
        for n in range(0, 10):
            semester = Semester(year=n, season='Fall')
            semesters.append(semester)
            db.session.add(semester)

        # create posts
        posts = []
        for n in range(0, 10):
            post = Post(title='title%d' % n,
                        content='content%d' % n,
                        timestamp=datetime(2018 + n, 1, 1),
                        author_id=test_user.id,
                        course=courses[n],
                        category=categories[n],
                        semester=semesters[n])

            posts.append(post)
            db.session.add(post)

        db.session.commit()

        # create comments
        comments = []
        for n in range(0, 10):
            comment = Comment(author_id=test_user.id,
                              content='content%d' % n,
                              post=posts[n])
            comments.append(comment)
            db.session.add(comment)

        db.session.commit()

        posts_json = marshal(posts, post_marshal_model)
        comments_json = marshal(comments, comment_marshal_model)

        return posts_json, comments_json


@pytest.mark.usefixtures('special_deleted_account')
def test_user_account_delete_without_content(app, client, test_user, testdata_posts):
    posts_json, comments_json = testdata_posts

    # payload
    data = {
        'password': test_user.password,
        'remove_content': False
    }

    with mail.record_messages() as outbox:
        # hit the api
        rv = client.post('/users/remove',
                         json=data,
                         headers=test_user.auth_headers)

        assert rv.status_code == 200

        # email should have been sent
        assert len(outbox) == 1

        with app.app_context():
            # confirm user account deleted
            assert not User.query.get(test_user.id)

            # confirm that posts and comments remain with different author
            for post in posts_json:
                found = Post.query.get(post['id'])
                assert found.content == post['content']
                assert found.author.id != test_user.id

            for comment in comments_json:
                found = Post.query.get(post['id'])
                assert found.content == post['content']
                assert found.author.id != test_user.id


@pytest.mark.usefixtures('special_deleted_account')
def test_user_account_delete_with_content(app, client, test_user, testdata_posts):
    posts_json, comments_json = testdata_posts

    # payload
    data = {
        'password': test_user.password,
        'remove_content': True  # changed from previous test
    }

    with mail.record_messages() as outbox:
        # hit the api
        rv = client.post('/users/remove',
                         json=data,
                         headers=test_user.auth_headers)

        assert rv.status_code == 200

        # email should have been sent
        assert len(outbox) == 1

        with app.app_context():
            # confirm user account deleted
            assert not User.query.get(test_user.id)

            # confirm that post and comment content is updated
            for post in posts_json:
                found = Post.query.get(post['id'])
                assert '[deleted]' in found.content

            for comment in comments_json:
                found = Post.query.get(post['id'])
                assert '[deleted]' in found.content


def test_user_account_bad_password(app, client, test_user):
    # payload
    data = {
        'password': test_user.password + 'oops',
        'delete_content': False
    }

    with mail.record_messages() as outbox:
        # hit the api
        rv = client.post('/users/remove',
                         json=data,
                         headers=test_user.auth_headers)

        assert rv.status_code == 401

        # assert no email sent
        assert len(outbox) == 0
