"""Initial migration

Revision ID: 83ff5e07bbab
Revises: 9d8bbc63db42
Create Date: 2025-04-06 00:14:39.299319

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '83ff5e07bbab'
down_revision: Union[str, None] = '9d8bbc63db42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('secrets', 'passphrase',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('secrets', 'expires_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('secrets', 'expires_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)
    op.alter_column('secrets', 'passphrase',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    # ### end Alembic commands ###
