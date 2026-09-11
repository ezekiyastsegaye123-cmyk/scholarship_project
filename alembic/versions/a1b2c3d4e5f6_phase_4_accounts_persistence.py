"""phase_4_accounts_persistence

Revision ID: a1b2c3d4e5f6
Revises: 9c2d3e4f5a6b
Create Date: 2026-09-12 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9c2d3e4f5a6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create student_accounts table
    op.create_table(
        'student_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('student_accounts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_accounts_email'), ['email'], unique=True)

    # 2. Add account_id to student_profiles
    with op.batch_alter_table('student_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('account_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            'fk_student_profiles_account_id',
            'student_accounts',
            ['account_id'],
            ['id'],
            ondelete='CASCADE',
        )
        batch_op.create_index(batch_op.f('ix_student_profiles_account_id'), ['account_id'], unique=True)

    # 3. Create saved_opportunities table
    op.create_table(
        'saved_opportunities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_account_id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['scholarship_opportunities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_account_id'], ['student_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_account_id', 'opportunity_id', name='uq_student_saved_opportunity'),
    )
    with op.batch_alter_table('saved_opportunities', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_saved_opportunities_student_account_id'), ['student_account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_saved_opportunities_opportunity_id'), ['opportunity_id'], unique=False)

    # 4. Create application_records table
    op.create_table(
        'application_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_account_id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('student_notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['scholarship_opportunities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_account_id'], ['student_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_account_id', 'opportunity_id', name='uq_student_application_record'),
    )
    with op.batch_alter_table('application_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_application_records_student_account_id'), ['student_account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_records_opportunity_id'), ['opportunity_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_records_status'), ['status'], unique=False)

    # 5. Create comparison_selections table
    op.create_table(
        'comparison_selections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_account_id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['scholarship_opportunities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_account_id'], ['student_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_account_id', 'opportunity_id', name='uq_student_comparison_selection'),
    )
    with op.batch_alter_table('comparison_selections', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_comparison_selections_student_account_id'), ['student_account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_comparison_selections_opportunity_id'), ['opportunity_id'], unique=False)


def downgrade() -> None:
    # 1. Drop comparison_selections
    with op.batch_alter_table('comparison_selections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_comparison_selections_opportunity_id'))
        batch_op.drop_index(batch_op.f('ix_comparison_selections_student_account_id'))
    op.drop_table('comparison_selections')

    # 2. Drop application_records
    with op.batch_alter_table('application_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_application_records_status'))
        batch_op.drop_index(batch_op.f('ix_application_records_opportunity_id'))
        batch_op.drop_index(batch_op.f('ix_application_records_student_account_id'))
    op.drop_table('application_records')

    # 3. Drop saved_opportunities
    with op.batch_alter_table('saved_opportunities', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_saved_opportunities_opportunity_id'))
        batch_op.drop_index(batch_op.f('ix_saved_opportunities_student_account_id'))
    op.drop_table('saved_opportunities')

    # 4. Remove account_id from student_profiles
    with op.batch_alter_table('student_profiles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_student_profiles_account_id'))
        batch_op.drop_constraint('fk_student_profiles_account_id', type_='foreignkey')
        batch_op.drop_column('account_id')

    # 5. Drop student_accounts
    with op.batch_alter_table('student_accounts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_student_accounts_email'))
    op.drop_table('student_accounts')
