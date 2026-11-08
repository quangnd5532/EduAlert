"""Student access and individual course results. Keep data and existing account IDs."""
from alembic import op
from app.schema_v2 import UPGRADE_SQL
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    for statement in UPGRADE_SQL:
        op.execute(statement)

def downgrade():
    raise RuntimeError('Revision 0002 contains student accounts: restore a backup to downgrade without losing data.')
