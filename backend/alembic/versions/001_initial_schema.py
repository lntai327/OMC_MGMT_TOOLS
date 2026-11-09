"""Initial schema for users, jobs, and megawan_metronet

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='operator', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # 2. Create jobs table
    # Safe enum handling for Postgres
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("CREATE TYPE job_type AS ENUM ('import', 'export');")
        op.execute("CREATE TYPE job_status AS ENUM ('pending', 'processing', 'completed', 'failed');")
        job_type_col = postgresql.ENUM('import', 'export', name='job_type', create_type=False)
        job_status_col = postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='job_status', create_type=False)
        uuid_col = postgresql.UUID(as_uuid=True)
        json_col = postgresql.JSONB()
    else:
        job_type_col = sa.String(20)
        job_status_col = sa.String(20)
        uuid_col = sa.CHAR(36)
        json_col = sa.JSON()

    op.create_table(
        'jobs',
        sa.Column('id', uuid_col, primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('type', job_type_col, nullable=False),
        sa.Column('status', job_status_col, server_default='pending', nullable=False),
        sa.Column('progress', sa.Integer(), server_default='0', nullable=False),
        sa.Column('input_file_path', sa.Text(), nullable=True),
        sa.Column('output_file_path', sa.Text(), nullable=True),
        sa.Column('result_meta', json_col, nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_jobs_status_type', 'jobs', ['status', 'type'])
    op.create_index('idx_jobs_user_id', 'jobs', ['user_id'])

    # 3. Create megawan_metronet table
    op.create_table(
        'megawan_metronet',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('last_update', sa.String(length=100), nullable=True),
        sa.Column('ma_tb', sa.String(length=500), nullable=True),
        sa.Column('ma_lt_ma_tb_sub', sa.String(length=500), nullable=True),
        sa.Column('ten_th_bao', sa.String(length=500), nullable=True),
        sa.Column('dia_chi', sa.String(length=500), nullable=True),
        sa.Column('diem_cuoi', sa.String(length=500), nullable=True),
        sa.Column('ip_src', sa.String(length=500), nullable=True),
        sa.Column('ip_des', sa.String(length=500), nullable=True),
        sa.Column('svlan_cvlan', sa.String(length=500), nullable=True),
        sa.Column('cap_adsl', sa.String(length=500), nullable=True),
        sa.Column('cap_odf', sa.String(length=500), nullable=True),
        sa.Column('ghi_chu', sa.Text(), nullable=True),
        sa.Column('ip', sa.Text(), nullable=True),
        sa.Column('ten_he_thong', sa.Text(), nullable=True),
        sa.Column('port_switch', sa.String(length=500), nullable=True),
        sa.Column('upe', sa.String(length=500), nullable=True),
        sa.Column('loai_hinh_tb', sa.String(length=500), nullable=True),
        sa.Column('trang_thai', sa.String(length=500), nullable=True),
        sa.Column('toc_do', sa.String(length=500), nullable=True),
        sa.Column('don_vi', sa.String(length=500), nullable=True),
        sa.Column('loai_kenh', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_megawan_ma_tb', 'megawan_metronet', ['ma_tb'])
    op.create_index('ix_megawan_ten_th_bao', 'megawan_metronet', ['ten_th_bao'])
    op.create_index('ix_megawan_loai_hinh_tb', 'megawan_metronet', ['loai_hinh_tb'])
    op.create_index('ix_megawan_loai_kenh', 'megawan_metronet', ['loai_kenh'])
    op.create_index('idx_megawan_multi_search', 'megawan_metronet', ['loai_hinh_tb', 'ten_th_bao', 'loai_kenh'])


def downgrade() -> None:
    op.drop_table('megawan_metronet')
    op.drop_table('jobs')
    op.drop_table('users')
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TYPE IF EXISTS job_status;")
        op.execute("DROP TYPE IF EXISTS job_type;")

