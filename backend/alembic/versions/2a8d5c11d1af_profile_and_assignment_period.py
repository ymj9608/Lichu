"""add profile image and assignment approval period

Revision ID: 2a8d5c11d1af
Revises: b60651b58df5
"""
from alembic import op
import sqlalchemy as sa

revision = '2a8d5c11d1af'
down_revision = 'b60651b58df5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('profile_image', sa.Text(), nullable=True))
    op.add_column('license_assignments', sa.Column('valid_from', sa.Date(), nullable=True))
    op.add_column('license_assignments', sa.Column('valid_until', sa.Date(), nullable=True))
    op.execute('''
        UPDATE license_assignments AS assignment
        SET valid_from = COALESCE(request.start_date, assignment.assigned_at::date),
            valid_until = COALESCE(request.end_date, assignment.assigned_at::date + 90)
        FROM license_requests AS request
        WHERE assignment.request_id = request.id
    ''')
    op.execute('''
        UPDATE license_assignments
        SET valid_from = assigned_at::date,
            valid_until = assigned_at::date + 90
        WHERE valid_from IS NULL OR valid_until IS NULL
    ''')
    op.alter_column('license_assignments', 'valid_from', nullable=False)
    op.alter_column('license_assignments', 'valid_until', nullable=False)
    op.create_check_constraint('ck_assignment_period', 'license_assignments', 'valid_from <= valid_until')

    surnames = ['김', '이', '박', '최']
    given_names = ['민준', '서준', '도윤', '예준', '시우', '하준', '주원', '지호', '지후', '준서',
                   '서연', '서윤', '지우', '하윤', '민서', '지민', '채원', '수아', '지아', '다은']
    bind = op.get_bind()
    for number in range(1, 77):
        bind.execute(
            sa.text('UPDATE users SET name = :name WHERE username = :username AND name LIKE :pattern'),
            {'name': f'{surnames[(number - 1) // 20]}{given_names[(number - 1) % 20]}',
             'username': f'employee{number:03}', 'pattern': '데모 직원 %'},
        )


def downgrade():
    op.drop_constraint('ck_assignment_period', 'license_assignments', type_='check')
    op.drop_column('license_assignments', 'valid_until')
    op.drop_column('license_assignments', 'valid_from')
    op.drop_column('users', 'profile_image')
