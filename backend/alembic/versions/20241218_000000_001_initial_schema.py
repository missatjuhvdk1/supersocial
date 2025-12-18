"""Initial schema creation

Revision ID: 001
Revises:
Create Date: 2024-12-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create proxies table
    op.create_table(
        'proxies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('password', sa.String(255), nullable=True),
        sa.Column('type', sa.Enum('residential', 'datacenter', 'mobile', name='proxytype'), nullable=False),
        sa.Column('status', sa.Enum('active', 'inactive', 'banned', 'error', name='proxystatus'), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('last_checked', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_proxies_id'), 'proxies', ['id'], unique=False)
    op.create_index(op.f('ix_proxies_host'), 'proxies', ['host'], unique=False)

    # Create browser_profiles table
    op.create_table(
        'browser_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=False),
        sa.Column('viewport_width', sa.Integer(), nullable=False),
        sa.Column('viewport_height', sa.Integer(), nullable=False),
        sa.Column('timezone', sa.String(100), nullable=False),
        sa.Column('locale', sa.String(50), nullable=False),
        sa.Column('fingerprint', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_browser_profiles_id'), 'browser_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_browser_profiles_name'), 'browser_profiles', ['name'], unique=True)

    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('cookies', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('active', 'banned', 'cooldown', 'needs_captcha', 'inactive', name='accountstatus'), nullable=False),
        sa.Column('proxy_id', sa.Integer(), nullable=True),
        sa.Column('profile_id', sa.Integer(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['proxy_id'], ['proxies.id'], ),
        sa.ForeignKeyConstraint(['profile_id'], ['browser_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)
    op.create_index(op.f('ix_accounts_email'), 'accounts', ['email'], unique=True)

    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('draft', 'scheduled', 'running', 'paused', 'completed', 'cancelled', name='campaignstatus'), nullable=False),
        sa.Column('video_path', sa.String(500), nullable=False),
        sa.Column('caption_template', sa.String(2200), nullable=False),
        sa.Column('account_selection', sa.JSON(), nullable=False),
        sa.Column('schedule', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaigns_id'), 'campaigns', ['id'], unique=False)
    op.create_index(op.f('ix_campaigns_name'), 'campaigns', ['name'], unique=False)

    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', 'retrying', name='jobstatus'), nullable=False),
        sa.Column('video_path', sa.String(500), nullable=False),
        sa.Column('caption', sa.String(2200), nullable=False),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_table('jobs')

    op.drop_index(op.f('ix_campaigns_name'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_id'), table_name='campaigns')
    op.drop_table('campaigns')

    op.drop_index(op.f('ix_accounts_email'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_id'), table_name='accounts')
    op.drop_table('accounts')

    op.drop_index(op.f('ix_browser_profiles_name'), table_name='browser_profiles')
    op.drop_index(op.f('ix_browser_profiles_id'), table_name='browser_profiles')
    op.drop_table('browser_profiles')

    op.drop_index(op.f('ix_proxies_host'), table_name='proxies')
    op.drop_index(op.f('ix_proxies_id'), table_name='proxies')
    op.drop_table('proxies')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS campaignstatus")
    op.execute("DROP TYPE IF EXISTS accountstatus")
    op.execute("DROP TYPE IF EXISTS proxystatus")
    op.execute("DROP TYPE IF EXISTS proxytype")
