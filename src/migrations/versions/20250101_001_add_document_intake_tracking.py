"""Add document intake tracking and retry functionality

Revision ID: 20250101_001
Revises: 4f747892e9a0
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250101_001'
down_revision = '4f747892e9a0'
branch_labels = None
depends_on = None


def upgrade():
    # Create document_intake_history table first
    op.create_table('document_intake_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', name='documentintakestatus'), nullable=False),
        sa.Column('source', sa.Enum('USER_UPLOAD', 'SYSTEM_UPLOAD', name='documentintakesource'), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('doc_type_id', sa.String(), nullable=False),
        sa.Column('request_id', sa.String(length=26), nullable=False),
        sa.Column('processing_started_at', sa.String(length=50), nullable=True),
        sa.Column('processing_completed_at', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('failed_at_step', sa.String(length=100), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['doc_type_id'], ['doc_type.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for document_intake_history
    op.create_index('ix_document_intake_history_request_id', 'document_intake_history', ['request_id'])
    
    # Now add document_intake_id column to extraction_audit table
    op.add_column('extraction_audit', sa.Column('document_intake_id', sa.String(length=26), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_extraction_audit_document_intake_id',
        'extraction_audit', 'document_intake_history',
        ['document_intake_id'], ['id']
    )
    
    # Create index for better query performance
    op.create_index('ix_extraction_audit_document_intake_id', 'extraction_audit', ['document_intake_id'])


def downgrade():
    # Remove foreign key and column from extraction_audit first
    op.drop_index('ix_extraction_audit_document_intake_id', 'extraction_audit')
    op.drop_constraint('fk_extraction_audit_document_intake_id', 'extraction_audit', type_='foreignkey')
    op.drop_column('extraction_audit', 'document_intake_id')
    
    # Then remove document_intake_history table
    op.drop_index('ix_document_intake_history_request_id', 'document_intake_history')
    op.drop_table('document_intake_history') 