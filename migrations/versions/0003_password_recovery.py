"""Registered recovery contacts, one-time codes and session revocation."""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('session_version', sa.Integer(), nullable=False, server_default='0'))
    with op.batch_alter_table('student_accounts') as batch:
        batch.add_column(sa.Column('email', sa.String(254)))
        batch.add_column(sa.Column('phone', sa.String(20)))
        batch.create_unique_constraint('uq_student_accounts_email', ['email'])
        batch.create_unique_constraint('uq_student_accounts_phone', ['phone'])
    op.create_table('password_recoveries',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('session_version', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(10), nullable=False),
        sa.Column('destination_hash', sa.String(64), nullable=False),
        sa.Column('ip_hash', sa.String(64), nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.Integer(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('consumed', sa.Boolean(), nullable=False))
    op.create_index('ix_password_recoveries_destination_hash', 'password_recoveries', ['destination_hash'])
    op.create_index('ix_password_recoveries_ip_hash', 'password_recoveries', ['ip_hash'])


def downgrade():
    raise RuntimeError('Restore a backup to downgrade without losing registered recovery contacts.')
