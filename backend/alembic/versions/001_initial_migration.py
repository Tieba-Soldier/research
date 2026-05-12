"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'recommendation_tasks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('user_input', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_step', sa.String(length=255), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'learning_topics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('normalized_topic', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'resources',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('topic_id', sa.BigInteger(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('relevance_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('practical_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('final_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('content_markdown', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'learning_paths',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('stages', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'practice_tasks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('topic_id', sa.BigInteger(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('task_text', sa.Text(), nullable=False),
        sa.Column('reference_answer', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('task_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'user_resource_progress',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('resource_id', sa.BigInteger(), nullable=False),
        sa.Column('studied', sa.Boolean(), nullable=True),
        sa.Column('favorite', sa.Boolean(), nullable=True),
        sa.Column('studied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('user_resource_progress')
    op.drop_table('practice_tasks')
    op.drop_table('learning_paths')
    op.drop_table('resources')
    op.drop_table('learning_topics')
    op.drop_table('recommendation_tasks')
