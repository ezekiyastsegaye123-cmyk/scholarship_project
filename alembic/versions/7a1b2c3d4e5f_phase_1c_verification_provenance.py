"""phase_1c_verification_provenance

Revision ID: 7a1b2c3d4e5f
Revises: 65d003844d47
Create Date: 2026-09-11 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '65d003844d47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enhance conflict_records with provenance and resolution tracking
    with op.batch_alter_table('conflict_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_a_tier', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('source_b_tier', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('source_a_evidence', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('source_b_evidence', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('resolved_at', sa.DateTime(), nullable=True))

    # 2. Create verification_histories for canonical fact change audit trail
    op.create_table(
        'verification_histories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('scholarship_id', sa.String(length=36), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('old_evidence_url', sa.String(length=1000), nullable=True),
        sa.Column('old_evidence_quote', sa.Text(), nullable=True),
        sa.Column('new_evidence_url', sa.String(length=1000), nullable=True),
        sa.Column('new_evidence_quote', sa.Text(), nullable=True),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scholarship_id'], ['scholarship_opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('verification_histories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_verification_histories_scholarship_id'), ['scholarship_id'], unique=False)

    # 3. Create source_liveness_logs for source reachability and soft-404 audit
    op.create_table(
        'source_liveness_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('scholarship_id', sa.String(length=36), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('liveness_status', sa.String(length=50), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('final_url', sa.String(length=1000), nullable=True),
        sa.Column('redirect_chain_json', sa.Text(), nullable=True),
        sa.Column('content_sha256', sa.String(length=64), nullable=True),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scholarship_id'], ['scholarship_opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('source_liveness_logs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_source_liveness_logs_scholarship_id'), ['scholarship_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_source_liveness_logs_source_url'), ['source_url'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('source_liveness_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_source_liveness_logs_source_url'))
        batch_op.drop_index(batch_op.f('ix_source_liveness_logs_scholarship_id'))
    op.drop_table('source_liveness_logs')

    with op.batch_alter_table('verification_histories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_verification_histories_scholarship_id'))
    op.drop_table('verification_histories')

    with op.batch_alter_table('conflict_records', schema=None) as batch_op:
        batch_op.drop_column('resolved_at')
        batch_op.drop_column('source_b_evidence')
        batch_op.drop_column('source_a_evidence')
        batch_op.drop_column('source_b_tier')
        batch_op.drop_column('source_a_tier')
