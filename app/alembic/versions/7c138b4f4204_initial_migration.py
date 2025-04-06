"""Initial migration

Revision ID: 7c138b4f4204
Revises: 06a8dc03a245
Create Date: 2025-04-06 04:47:53.800454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c138b4f4204'
down_revision: Union[str, None] = '06a8dc03a245'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('secrets', sa.Column('secret_key', sa.String(length=36), nullable=False, comment='Уникальный ключ доступа к секрету'))
    op.create_index(op.f('ix_secrets_secret_key'), 'secrets', ['secret_key'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_secrets_secret_key'), table_name='secrets')
    op.drop_column('secrets', 'secret_key')
    # ### end Alembic commands ###
