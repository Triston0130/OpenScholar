# app/database/migrations/add_sharing_models.py
"""
Migration to add sharing and PDF annotation tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create ShareRole enum
    op.execute("CREATE TYPE sharerole AS ENUM ('viewer', 'commenter', 'editor', 'admin')")
    
    # Create folders table
    op.create_table('folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_folder_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('color', sa.String(7)),
        sa.Column('icon', sa.String(50)),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_folder_id'], ['folders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create collection_shares table
    op.create_table('collection_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_with_user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('shared_with_email', sa.String(255)),
        sa.Column('role', sa.Enum('viewer', 'commenter', 'editor', 'admin', name='sharerole'), nullable=False),
        sa.Column('can_reshare', sa.Boolean(), default=False),
        sa.Column('share_link', sa.String(100)),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('message', sa.Text()),
        sa.Column('accepted', sa.Boolean(), default=False),
        sa.Column('accepted_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
        sa.ForeignKeyConstraint(['shared_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shared_with_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('collection_id', 'shared_with_user_id', name='uq_collection_user_share'),
        sa.UniqueConstraint('collection_id', 'shared_with_email', name='uq_collection_email_share'),
        sa.UniqueConstraint('share_link')
    )
    
    op.create_index('idx_share_collection', 'collection_shares', ['collection_id'])
    op.create_index('idx_share_user', 'collection_shares', ['shared_with_user_id'])
    op.create_index('idx_share_link', 'collection_shares', ['share_link'])
    
    # Create folder_shares table
    op.create_table('folder_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_with_user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('shared_with_email', sa.String(255)),
        sa.Column('role', sa.Enum('viewer', 'commenter', 'editor', 'admin', name='sharerole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ),
        sa.ForeignKeyConstraint(['shared_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shared_with_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create pdf_annotations table
    op.create_table('pdf_annotations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True)),
        sa.Column('annotation_type', sa.String(20), nullable=False),
        sa.Column('color', sa.String(7), default='#FFFF00'),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('position_x', sa.Float()),
        sa.Column('position_y', sa.Float()),
        sa.Column('width', sa.Float()),
        sa.Column('height', sa.Float()),
        sa.Column('selected_text', sa.Text()),
        sa.Column('start_offset', sa.Integer()),
        sa.Column('end_offset', sa.Integer()),
        sa.Column('comment', sa.Text()),
        sa.Column('tags', sa.JSON()),
        sa.Column('is_private', sa.Boolean(), default=True),
        sa.Column('shared_in_collection', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_annotation_paper_user', 'pdf_annotations', ['paper_id', 'user_id'])
    op.create_index('idx_annotation_collection', 'pdf_annotations', ['collection_id'])
    op.create_index('idx_annotation_type', 'pdf_annotations', ['annotation_type'])
    
    # Create annotation_replies table
    op.create_table('annotation_replies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('annotation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('parent_reply_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['annotation_id'], ['pdf_annotations.id'], ),
        sa.ForeignKeyConstraint(['parent_reply_id'], ['annotation_replies.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create pdf_cache table
    op.create_table('pdf_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_size', sa.Integer()),
        sa.Column('file_hash', sa.String(64)),
        sa.Column('page_count', sa.Integer()),
        sa.Column('pdf_version', sa.String(10)),
        sa.Column('is_text_extractable', sa.Boolean(), default=True),
        sa.Column('extracted_text', sa.Text()),
        sa.Column('download_status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('downloaded_at', sa.DateTime()),
        sa.Column('last_accessed', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id', name='uq_pdf_cache_paper')
    )
    
    op.create_index('idx_pdf_cache_status', 'pdf_cache', ['download_status'])

def downgrade():
    op.drop_index('idx_pdf_cache_status', 'pdf_cache')
    op.drop_table('pdf_cache')
    op.drop_table('annotation_replies')
    op.drop_index('idx_annotation_type', 'pdf_annotations')
    op.drop_index('idx_annotation_collection', 'pdf_annotations')
    op.drop_index('idx_annotation_paper_user', 'pdf_annotations')
    op.drop_table('pdf_annotations')
    op.drop_table('folder_shares')
    op.drop_index('idx_share_link', 'collection_shares')
    op.drop_index('idx_share_user', 'collection_shares')
    op.drop_index('idx_share_collection', 'collection_shares')
    op.drop_table('collection_shares')
    op.drop_table('folders')
    op.execute("DROP TYPE sharerole")