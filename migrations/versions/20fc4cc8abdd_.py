"""deleted user account

Revision ID: 20fc4cc8abdd
Revises: 710877416229
Create Date: 2018-05-31 14:50:18.363892

"""
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String, Boolean
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20fc4cc8abdd'
down_revision = '710877416229'
branch_labels = None
depends_on = None

user_table = table('user',
                   column('email', String),
                   column('password', String),
                   column('is_verified', Boolean)
                   )


def upgrade():
    op.bulk_insert(user_table, [{
        'email': 'deletedaccount',
        'password': '42',
        'is_verified': False
    }])


def downgrade():
    op.execute(
        user_table
        .delete()
        .where(user_table.columns.email == 'deletedaccount')
    )
