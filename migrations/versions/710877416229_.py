"""first semester

Revision ID: 710877416229
Revises: 884507477d68
Create Date: 2018-05-24 13:48:54.549214

"""
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '710877416229'
down_revision = '884507477d68'
branch_labels = None
depends_on = None

semesters_table = table('semester',
                        column('year', Integer),
                        column('season', String)
                        )


def upgrade():
    op.bulk_insert(semesters_table, [{
        'year': 2018,
        'season': 'Summer'
    }])


def downgrade():
    op.execute(
        semesters_table
        .delete()
        .where(semesters_table.columns.year == 2018)
        .where(semesters_table.columns.season == 'Summer')
    )
