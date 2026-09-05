"""indice producto_imagen

Revision ID: b3f6a1d90c5e
Revises: 9f974d918aae
Create Date: 2026-09-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f6a1d90c5e'
down_revision: Union[str, None] = '9f974d918aae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_producto_imagen_producto', 'producto_imagen', ['producto_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_producto_imagen_producto', table_name='producto_imagen')
