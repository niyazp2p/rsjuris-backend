"""create_enquiries_table

Revision ID: 9593e317255a
Revises: c93042b693db
Create Date: 2026-09-26 19:55:03.392197

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9593e317255a'
down_revision: Union[str, None] = 'c93042b693db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define PostgreSQL ENUMs
enquirystatus_enum = postgresql.ENUM(
    'NEW', 'CONTACTED', 'CONVERTED_TO_LEAD', 'ARCHIVED', 'SPAM',
    name='enquirystatus',
    create_type=False
)

mattertype_enum = postgresql.ENUM(
    'Corporate & Commercial Law',
    'Civil Litigation & Dispute Resolution',
    'Criminal Law',
    'Property & Real Estate Law',
    'Family & Matrimonial Law',
    'Employment & Labour Law',
    'Banking & Financial Disputes',
    'Intellectual Property Rights',
    'Arbitration & Alternative Dispute Resolution',
    'General Chamber Advisory / Other',
    name='mattertype',
    create_type=False
)

def upgrade() -> None:
    # 1. Create Enums first in PostgreSQL
    enquirystatus_enum.create(op.get_bind(), checkfirst=True)
    mattertype_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create the enquiries table
    op.create_table(
        'enquiries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('reference_number', sa.String(length=50), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('matter_type', mattertype_enum, nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('status', enquirystatus_enum, nullable=False, server_default='NEW'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create indexes
    op.create_index(op.f('ix_enquiries_reference_number'), 'enquiries', ['reference_number'], unique=True)
    op.create_index(op.f('ix_enquiries_email'), 'enquiries', ['email'], unique=False)
    op.create_index(op.f('ix_enquiries_matter_type'), 'enquiries', ['matter_type'], unique=False)
    op.create_index(op.f('ix_enquiries_status'), 'enquiries', ['status'], unique=False)
    op.create_index(op.f('ix_enquiries_created_at'), 'enquiries', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_enquiries_created_at'), table_name='enquiries')
    op.drop_index(op.f('ix_enquiries_status'), table_name='enquiries')
    op.drop_index(op.f('ix_enquiries_matter_type'), table_name='enquiries')
    op.drop_index(op.f('ix_enquiries_email'), table_name='enquiries')
    op.drop_index(op.f('ix_enquiries_reference_number'), table_name='enquiries')
    op.drop_table('enquiries')

    mattertype_enum.drop(op.get_bind(), checkfirst=True)
    enquirystatus_enum.drop(op.get_bind(), checkfirst=True)