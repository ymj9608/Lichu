"""update brand display name

Revision ID: 7d44b682c91e
Revises: 2a8d5c11d1af
"""
from alembic import op
import sqlalchemy as sa

revision = '7d44b682c91e'
down_revision = '2a8d5c11d1af'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text("UPDATE users SET name = 'LiChU. Master' WHERE username = 'master' AND name = 'Lichu Master'"))


def downgrade():
    op.execute(sa.text("UPDATE users SET name = 'Lichu Master' WHERE username = 'master' AND name = 'LiChU. Master'"))
