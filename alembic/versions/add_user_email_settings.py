"""Add user email settings tables

Revision ID: add_user_email_settings
Revises: 
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_user_email_settings'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create user_email_settings table
    op.create_table('user_email_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('smtp_host', sa.String(255), nullable=True),
        sa.Column('smtp_port', sa.Integer(), nullable=True, default=587),
        sa.Column('smtp_user', sa.String(255), nullable=True),
        sa.Column('smtp_password', sa.Text(), nullable=True),
        sa.Column('smtp_use_tls', sa.Boolean(), nullable=True, default=True),
        sa.Column('smtp_use_ssl', sa.Boolean(), nullable=True, default=False),
        sa.Column('from_email', sa.String(255), nullable=True),
        sa.Column('from_name', sa.String(255), nullable=True, default='OpenScholar User'),
        sa.Column('is_configured', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('last_verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create user_notification_preferences table
    op.create_table('user_notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('share_invitations', sa.Boolean(), nullable=True, default=True),
        sa.Column('share_acceptances', sa.Boolean(), nullable=True, default=True),
        sa.Column('annotation_replies', sa.Boolean(), nullable=True, default=True),
        sa.Column('collection_updates', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    op.drop_table('user_notification_preferences')
    op.drop_table('user_email_settings')