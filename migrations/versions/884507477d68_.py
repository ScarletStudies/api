"""categories

Revision ID: 884507477d68
Revises: 9c7b9b1597d0
Create Date: 2018-05-24 13:37:14.817439

"""
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '884507477d68'
down_revision = '9c7b9b1597d0'
branch_labels = None
depends_on = None

categories_table = table('category',
                         column('name', String)
                         )

names = [
    'Exam',
    'Lecture',
    'Homework',
    'Recitation',
    'Complaint',
    'Off Topic'
]


def upgrade():
    op.bulk_insert(categories_table, [{'name': n} for n in names])


def downgrade():
    for name in names:
        op.execute(
            categories_table
            .delete()
            .where(categories_table.columns.name == op.inline_literal(name))
        )
