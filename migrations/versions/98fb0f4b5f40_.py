"""empty message

Revision ID: 98fb0f4b5f40
Revises: 6f992faf3b14
Create Date: 2018-11-28 17:24:09.575637

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime as dt

# revision identifiers, used by Alembic.
revision = '98fb0f4b5f40'
down_revision = '6f992faf3b14'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('convo_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('router_id', sa.String(length=32), nullable=False),
    sa.Column('inbound', sa.String(length=128), nullable=True),
    sa.Column('outbound', sa.String(length=128), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=False, server_default=dt.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('convo_history')
    # ### end Alembic commands ###