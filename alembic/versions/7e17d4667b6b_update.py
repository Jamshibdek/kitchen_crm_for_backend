"""update 

Revision ID: 7e17d4667b6b
Revises: 7bb2b6cf9092
Create Date: 2025-05-30 15:00:09.567426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e17d4667b6b'
down_revision: Union[str, None] = '7bb2b6cf9092'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('action_logs_user_id_fkey', 'action_logs', type_='foreignkey')
    op.create_foreign_key(None, 'action_logs', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'action_logs', type_='foreignkey')
    op.create_foreign_key('action_logs_user_id_fkey', 'action_logs', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###
