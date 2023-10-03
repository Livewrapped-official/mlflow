"""add tags field to metrics

Revision ID: b42bb53aa9e5
Revises: 2d6e25af4d3e
Create Date: 2023-10-03 13:16:13.031578

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b42bb53aa9e5"
down_revision = "2d6e25af4d3e"
branch_labels = None
depends_on = None


def upgrade():
    pass  # Add column tags of type JSON


def downgrade():
    pass  # Can probably leave the column as-is?
