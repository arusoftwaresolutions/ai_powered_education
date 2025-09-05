"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create departments table
    op.create_table('departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create approved_users table
    op.create_table('approved_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create courses table
    op.create_table('courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create resources table
    op.create_table('resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('file_path_or_url', sa.String(length=500), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create progress table
    op.create_table('progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=False),
        sa.Column('completion_percentage', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'resource_id')
    )
    
    # Create quizzes table
    op.create_table('quizzes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('passing_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create quiz_questions table
    op.create_table('quiz_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.String(length=20), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.String(length=500), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('points', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create quiz_submissions table
    op.create_table('quiz_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ai_call_logs table
    op.create_table('ai_call_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('endpoint', sa.String(length=100), nullable=False),
        sa.Column('request_data', sa.JSON(), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create foreign key constraints
    op.create_foreign_key('fk_users_department', 'users', 'departments', ['department_id'], ['id'])
    op.create_foreign_key('fk_approved_users_department', 'approved_users', 'departments', ['department_id'], ['id'])
    op.create_foreign_key('fk_courses_department', 'courses', 'departments', ['department_id'], ['id'])
    op.create_foreign_key('fk_courses_created_by', 'courses', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_resources_course', 'resources', 'courses', ['course_id'], ['id'])
    op.create_foreign_key('fk_progress_user', 'progress', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_progress_resource', 'progress', 'resources', ['resource_id'], ['id'])
    op.create_foreign_key('fk_quizzes_course', 'quizzes', 'courses', ['course_id'], ['id'])
    op.create_foreign_key('fk_quiz_questions_quiz', 'quiz_questions', 'quizzes', ['quiz_id'], ['id'])
    op.create_foreign_key('fk_quiz_submissions_quiz', 'quiz_submissions', 'quizzes', ['quiz_id'], ['id'])
    op.create_foreign_key('fk_quiz_submissions_user', 'quiz_submissions', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_ai_call_logs_user', 'ai_call_logs', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints first
    op.drop_constraint('fk_ai_call_logs_user', 'ai_call_logs', type_='foreignkey')
    op.drop_constraint('fk_quiz_submissions_user', 'quiz_submissions', type_='foreignkey')
    op.drop_constraint('fk_quiz_submissions_quiz', 'quiz_submissions', type_='foreignkey')
    op.drop_constraint('fk_quiz_questions_quiz', 'quiz_questions', type_='foreignkey')
    op.drop_constraint('fk_quizzes_course', 'quizzes', type_='foreignkey')
    op.drop_constraint('fk_progress_resource', 'progress', type_='foreignkey')
    op.drop_constraint('fk_progress_user', 'progress', type_='foreignkey')
    op.drop_constraint('fk_resources_course', 'resources', type_='foreignkey')
    op.drop_constraint('fk_courses_created_by', 'courses', type_='users', type_='foreignkey')
    op.drop_constraint('fk_courses_department', 'courses', type_='departments', type_='foreignkey')
    op.drop_constraint('fk_approved_users_department', 'approved_users', type_='departments', type_='foreignkey')
    op.drop_constraint('fk_users_department', 'users', type_='departments', type_='foreignkey')
    
    # Drop tables
    op.drop_table('ai_call_logs')
    op.drop_table('quiz_submissions')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')
    op.drop_table('progress')
    op.drop_table('resources')
    op.drop_table('courses')
    op.drop_table('users')
    op.drop_table('approved_users')
    op.drop_table('departments')
