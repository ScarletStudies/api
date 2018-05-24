"""courses, term 7, campuses nk nb cm, year 2018

Revision ID: 9c7b9b1597d0
Revises: 04c0a19ef0c1
Create Date: 2018-05-24 11:09:56.847834

"""
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String
import os
import json
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c7b9b1597d0'
down_revision = '04c0a19ef0c1'
branch_labels = None
depends_on = None

courses_table = table('course',
                      column('name', String),
                      column('offering_unit', String),
                      column('subject', String),
                      column('course_number', String)
                      )

paths = (
    os.path.join(os.path.dirname(__file__), 'courses/7-2018-NK.json'),
    os.path.join(os.path.dirname(__file__), 'courses/7-2018-NB.json'),
    os.path.join(os.path.dirname(__file__), 'courses/7-2018-CM.json')
)


def upgrade():
    for path in paths:
        with open(path, 'r') as fp:
            courses = json.load(fp)

            op.bulk_insert(courses_table, courses)


def downgrade():
    for path in paths:
        with open(path, 'r') as fp:
            courses = json.load(fp)

            for course in courses:
                op.execute(
                    courses_table
                    .delete()
                    .where(courses_table.columns.name == op.inline_literal(course['name']))
                    .where(courses_table.columns.offering_unit == op.inline_literal(course['offering_unit']))
                    .where(courses_table.columns.subject == op.inline_literal(course['subject']))
                    .where(courses_table.columns.course_number == op.inline_literal(course['course_number']))
                )
