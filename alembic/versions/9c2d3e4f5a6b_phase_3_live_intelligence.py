"""phase_3_live_intelligence

Revision ID: 9c2d3e4f5a6b
Revises: 7a1b2c3d4e5f
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c2d3e4f5a6b'
down_revision: Union[str, Sequence[str], None] = '7a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ingestion_sources table
    op.create_table(
        'ingestion_sources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('source_domain', sa.String(length=255), nullable=False),
        sa.Column('authority_tier', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('fetch_interval_hours', sa.Integer(), nullable=False, default=24),
        sa.Column('last_crawled_at', sa.DateTime(), nullable=True),
        sa.Column('last_content_sha256', sa.String(length=64), nullable=True),
        sa.Column('last_http_status', sa.Integer(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False, default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('ingestion_sources', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ingestion_sources_url'), ['url'], unique=True)
        batch_op.create_index(batch_op.f('ix_ingestion_sources_source_domain'), ['source_domain'], unique=False)

    # 2. Create ingestion_runs table
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('sources_attempted', sa.Integer(), nullable=False, default=0),
        sa.Column('sources_succeeded', sa.Integer(), nullable=False, default=0),
        sa.Column('sources_failed', sa.Integer(), nullable=False, default=0),
        sa.Column('opportunities_scanned', sa.Integer(), nullable=False, default=0),
        sa.Column('opportunities_updated', sa.Integer(), nullable=False, default=0),
        sa.Column('opportunities_created', sa.Integer(), nullable=False, default=0),
        sa.Column('conflicts_detected', sa.Integer(), nullable=False, default=0),
        sa.Column('error_log_json', sa.Text(), nullable=True),
        sa.Column('reference_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('ingestion_runs')
    with op.batch_alter_table('ingestion_sources', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ingestion_sources_source_domain'))
        batch_op.drop_index(batch_op.f('ix_ingestion_sources_url'))
    op.drop_table('ingestion_sources')
