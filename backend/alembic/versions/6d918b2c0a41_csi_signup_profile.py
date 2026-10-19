"""Separate synthetic signup profile for the opt-in CSI lab."""
from alembic import op
import sqlalchemy as sa

revision = '6d918b2c0a41'
down_revision = '7d44b682c91e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('csi_signup_profiles',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('phone_number', sa.String(20), nullable=False))


def downgrade():
    op.drop_table('csi_signup_profiles')
