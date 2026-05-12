"""add_indexes_for_performance

Revision ID: 002_add_indexes
Revises: 001_initial_migration
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_indexes'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    # 为 learning_topics 表添加 task_id 索引
    op.create_index(
        'ix_learning_topics_task_id',
        'learning_topics',
        ['task_id'],
        unique=False
    )

    # 为 resources 表添加 task_id 索引
    op.create_index(
        'ix_resources_task_id',
        'resources',
        ['task_id'],
        unique=False
    )

    # 为 resources 表添加 task_id + final_score 复合索引（用于排序查询）
    op.create_index(
        'ix_resources_task_id_final_score',
        'resources',
        ['task_id', sa.text('final_score DESC')],
        unique=False
    )

    # 为 learning_paths 表添加 task_id 索引
    op.create_index(
        'ix_learning_paths_task_id',
        'learning_paths',
        ['task_id'],
        unique=False
    )

    # 为 practice_tasks 表添加 task_id 索引
    op.create_index(
        'ix_practice_tasks_task_id',
        'practice_tasks',
        ['task_id'],
        unique=False
    )


def downgrade():
    op.drop_index('ix_practice_tasks_task_id', table_name='practice_tasks')
    op.drop_index('ix_learning_paths_task_id', table_name='learning_paths')
    op.drop_index('ix_resources_task_id_final_score', table_name='resources')
    op.drop_index('ix_resources_task_id', table_name='resources')
    op.drop_index('ix_learning_topics_task_id', table_name='learning_topics')
