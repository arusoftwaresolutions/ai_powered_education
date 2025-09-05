#!/usr/bin/env python3
"""
Seed data script for ARU Academy
Run with: python -m backend.seed.seed
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import db
from models.department import Department
from models.user import User, UserRole, UserStatus
from models.approved_user import ApprovedUser
from models.course import Course
from models.resource import Resource, ResourceType
from models.quiz import Quiz, QuizQuestion, QuestionType
from models.quiz import QuizSubmission
from models.progress import Progress, ProgressStatus
from models.ai_log import AiCallLog
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def create_departments():
    """Create departments"""
    departments = [
        {
            'name': 'Computer Science',
            'description': 'Computer Science and Software Engineering programs'
        },
        {
            'name': 'Electrical Engineering',
            'description': 'Electrical and Electronics Engineering programs'
        },
        {
            'name': 'Mechanical Engineering',
            'description': 'Mechanical and Manufacturing Engineering programs'
        },
        {
            'name': 'Business Administration',
            'description': 'Business and Management programs'
        }
    ]
    
    created_depts = []
    for dept_data in departments:
        dept = Department(**dept_data)
        db.session.add(dept)
        created_depts.append(dept)
    
    db.session.commit()
    print(f"Created {len(created_depts)} departments")
    return created_depts

def create_admin_user(departments):
    """Create admin user"""
    admin = User(
        name='Admin User',
        email='admin@aru.academy',
        role=UserRole.ADMIN,
        department_id=departments[0].id,  # CS department
        status=UserStatus.ACTIVE
    )
    admin.set_password('Admin@123')
    
    db.session.add(admin)
    db.session.commit()
    print("Created admin user: admin@aru.academy / Admin@123")
    return admin

def create_sample_users(departments):
    """Create sample students and instructors"""
    users = []
    
    # Computer Science
    cs_dept = next(d for d in departments if d.name == 'Computer Science')
    
    # CS Instructor
    cs_instructor = User(
        name='Dr. Sarah Johnson',
        email='sarah.johnson@aru.academy',
        role=UserRole.INSTRUCTOR,
        department_id=cs_dept.id,
        status=UserStatus.ACTIVE
    )
    cs_instructor.set_password('Instructor@123')
    users.append(cs_instructor)
    
    # CS Students
    cs_students = [
        ('Ahmed Hassan', 'ahmed.hassan@student.aru.academy'),
        ('Fatima Ali', 'fatima.ali@student.aru.academy'),
        ('Omar Khalil', 'omar.khalil@student.aru.academy')
    ]
    
    for name, email in cs_students:
        student = User(
            name=name,
            email=email,
            role=UserRole.STUDENT,
            department_id=cs_dept.id,
            status=UserStatus.ACTIVE
        )
        student.set_password('Student@123')
        users.append(student)
    
    # Electrical Engineering
    ee_dept = next(d for d in departments if d.name == 'Electrical Engineering')
    
    # EE Instructor
    ee_instructor = User(
        name='Dr. Michael Chen',
        email='michael.chen@aru.academy',
        role=UserRole.INSTRUCTOR,
        department_id=ee_dept.id,
        status=UserStatus.ACTIVE
    )
    ee_instructor.set_password('Instructor@123')
    users.append(ee_instructor)
    
    # EE Students
    ee_students = [
        ('Layla Ahmed', 'layla.ahmed@student.aru.academy'),
        ('Yusuf Ibrahim', 'yusuf.ibrahim@student.aru.academy'),
        ('Aisha Mohammed', 'aisha.mohammed@student.aru.academy')
    ]
    
    for name, email in ee_students:
        student = User(
            name=name,
            email=email,
            role=UserRole.STUDENT,
            department_id=ee_dept.id,
            status=UserStatus.ACTIVE
        )
        student.set_password('Student@123')
        users.append(student)
    
    # Mechanical Engineering
    me_dept = next(d for d in departments if d.name == 'Mechanical Engineering')
    
    # ME Instructor
    me_instructor = User(
        name='Dr. Robert Wilson',
        email='robert.wilson@aru.academy',
        role=UserRole.INSTRUCTOR,
        department_id=me_dept.id,
        status=UserStatus.ACTIVE
    )
    me_instructor.set_password('Instructor@123')
    users.append(me_instructor)
    
    # ME Students
    me_students = [
        ('Khalid Al-Rashid', 'khalid.alrashid@student.aru.academy'),
        ('Noor Al-Zahra', 'noor.alzahra@student.aru.academy'),
        ('Zaid Al-Mansouri', 'zaid.almansouri@student.aru.academy')
    ]
    
    for name, email in me_students:
        student = User(
            name=name,
            email=email,
            role=UserRole.STUDENT,
            department_id=me_dept.id,
            status=UserStatus.ACTIVE
        )
        student.set_password('Student@123')
        users.append(student)
    
    # Business Administration
    bu_dept = next(d for d in departments if d.name == 'Business Administration')
    
    # Business Instructor
    bu_instructor = User(
        name='Dr. Emily Rodriguez',
        email='emily.rodriguez@aru.academy',
        role=UserRole.INSTRUCTOR,
        department_id=bu_dept.id,
        status=UserStatus.ACTIVE
    )
    bu_instructor.set_password('Instructor@123')
    users.append(bu_instructor)
    
    # Business Students
    bu_students = [
        ('Mariam Al-Sayed', 'mariam.alsayed@student.aru.academy'),
        ('Hassan Al-Qahtani', 'hassan.alqahtani@student.aru.academy'),
        ('Amina Al-Sabah', 'amina.alsabah@student.aru.academy')
    ]
    
    for name, email in bu_students:
        student = User(
            name=name,
            email=email,
            role=UserRole.STUDENT,
            department_id=bu_dept.id,
            status=UserStatus.ACTIVE
        )
        student.set_password('Student@123')
        users.append(student)
    
    for user in users:
        db.session.add(user)
    
    db.session.commit()
    print(f"Created {len(users)} sample users")
    return users

def create_sample_courses(departments, users):
    """Create sample courses for each department"""
    courses = []
    
    # Computer Science Courses
    cs_dept = next(d for d in departments if d.name == 'Computer Science')
    cs_instructor = next(u for u in users if u.email == 'sarah.johnson@aru.academy')
    
    cs_courses = [
        {
            'title': 'Introduction to Programming',
            'description': 'Learn the fundamentals of programming with Python',
            'department_id': cs_dept.id,
            'created_by': cs_instructor.id
        },
        {
            'title': 'Data Structures and Algorithms',
            'description': 'Advanced programming concepts and problem-solving techniques',
            'department_id': cs_dept.id,
            'created_by': cs_instructor.id
        }
    ]
    
    for course_data in cs_courses:
        course = Course(**course_data)
        db.session.add(course)
        courses.append(course)
    
    # Electrical Engineering Courses
    ee_dept = next(d for d in departments if d.name == 'Electrical Engineering')
    ee_instructor = next(u for u in users if u.email == 'michael.chen@aru.academy')
    
    ee_courses = [
        {
            'title': 'Circuit Analysis',
            'description': 'Fundamentals of electrical circuits and analysis',
            'department_id': ee_dept.id,
            'created_by': ee_instructor.id
        },
        {
            'title': 'Digital Electronics',
            'description': 'Digital logic design and implementation',
            'department_id': ee_dept.id,
            'created_by': ee_instructor.id
        }
    ]
    
    for course_data in ee_courses:
        course = Course(**course_data)
        db.session.add(course)
        courses.append(course)
    
    # Mechanical Engineering Courses
    me_dept = next(d for d in departments if d.name == 'Mechanical Engineering')
    me_instructor = next(u for u in users if u.email == 'robert.wilson@aru.academy')
    
    me_courses = [
        {
            'title': 'Engineering Mechanics',
            'description': 'Statics and dynamics of mechanical systems',
            'department_id': me_dept.id,
            'created_by': me_instructor.id
        },
        {
            'title': 'Thermodynamics',
            'description': 'Heat transfer and energy conversion principles',
            'department_id': me_dept.id,
            'created_by': me_instructor.id
        }
    ]
    
    for course_data in me_courses:
        course = Course(**course_data)
        db.session.add(course)
        courses.append(course)
    
    # Business Administration Courses
    bu_dept = next(d for d in departments if d.name == 'Business Administration')
    bu_instructor = next(u for u in users if u.email == 'emily.rodriguez@aru.academy')
    
    bu_courses = [
        {
            'title': 'Business Management',
            'description': 'Principles of modern business management and leadership',
            'department_id': bu_dept.id,
            'created_by': bu_instructor.id
        },
        {
            'title': 'Marketing Strategy',
            'description': 'Strategic marketing planning and implementation',
            'department_id': bu_dept.id,
            'created_by': bu_instructor.id
        }
    ]
    
    for course_data in bu_courses:
        course = Course(**course_data)
        db.session.add(course)
        courses.append(course)
    
    db.session.commit()
    print(f"Created {len(courses)} sample courses")
    return courses

def create_sample_resources(courses):
    """Create sample resources for courses"""
    resources = []
    
    for course in courses:
        # Create 2-3 resources per course
        for i in range(random.randint(2, 3)):
            if i == 0:
                # PDF resource
                resource = Resource(
                    title=f'{course.title} - Lecture Notes {i+1}',
                    type=ResourceType.PDF,
                    course_id=course.id,
                    file_path_or_url=f'/storage/departments/{course.department.name.lower().replace(" ", "_")}/lecture_{i+1}.pdf',
                    description=f'Comprehensive lecture notes for {course.title}'
                )
            elif i == 1:
                # Text resource
                resource = Resource(
                    title=f'{course.title} - Study Guide',
                    type=ResourceType.TEXT,
                    course_id=course.id,
                    text_content=f'This is a comprehensive study guide for {course.title}. It covers all the essential topics and provides practice questions for students to test their understanding.',
                    description=f'Study guide with key concepts and practice questions'
                )
            else:
                # Video resource
                resource = Resource(
                    title=f'{course.title} - Video Tutorial',
                    type=ResourceType.VIDEO,
                    course_id=course.id,
                    file_path_or_url=f'/storage/departments/{course.department.name.lower().replace(" ", "_")}/tutorial_{i+1}.mp4',
                    description=f'Video tutorial covering key concepts in {course.title}'
                )
            
            db.session.add(resource)
            resources.append(resource)
    
    db.session.commit()
    print(f"Created {len(resources)} sample resources")
    return resources

def create_sample_quizzes(courses):
    """Create sample quizzes for courses"""
    quizzes = []
    
    for course in courses:
        # Create 1 quiz per course
        quiz = Quiz(
            title=f'{course.title} - Assessment Quiz',
            course_id=course.id,
            topic=course.title,
            description=f'Comprehensive assessment quiz for {course.title}'
        )
        
        db.session.add(quiz)
        db.session.flush()  # Get quiz ID
        
        # Create 5 questions per quiz
        for q_num in range(5):
            if q_num % 2 == 0:  # Multiple choice
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    question=f'Question {q_num + 1}: What is a key concept in {course.title}?',
                    options=['Option A', 'Option B', 'Option C', 'Option D'],
                    answer='Option A',
                    explanation=f'This is the correct answer because it represents a fundamental concept in {course.title}.',
                    points=1
                )
            else:  # Short answer
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_type=QuestionType.SHORT_ANSWER,
                    question=f'Question {q_num + 1}: Explain briefly about {course.title}.',
                    answer=f'{course.title} is an important subject that covers essential concepts and principles.',
                    explanation=f'This question tests understanding of {course.title} fundamentals.',
                    points=1
                )
            
            db.session.add(question)
        
        quizzes.append(quiz)
    
    db.session.commit()
    print(f"Created {len(quizzes)} sample quizzes")
    return quizzes

def create_sample_progress(users, resources):
    """Create sample progress records for students"""
    progress_records = []
    
    students = [u for u in users if u.role == UserRole.STUDENT]
    
    for student in students:
        # Get resources from student's department
        student_resources = [r for r in resources if r.course.department_id == student.department_id]
        
        for resource in student_resources[:3]:  # Progress on first 3 resources
            status = random.choice([ProgressStatus.NOT_STARTED, ProgressStatus.IN_PROGRESS, ProgressStatus.COMPLETED])
            completion = random.uniform(0, 100) if status != ProgressStatus.NOT_STARTED else 0
            
            progress = Progress(
                user_id=student.id,
                resource_id=resource.id,
                status=status,
                completion_percentage=completion,
                last_accessed_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            db.session.add(progress)
            progress_records.append(progress)
    
    db.session.commit()
    print(f"Created {len(progress_records)} sample progress records")
    return progress_records

def create_sample_quiz_submissions(users, quizzes):
    """Create sample quiz submissions"""
    submissions = []
    
    students = [u for u in users if u.role == UserRole.STUDENT]
    
    for student in students:
        # Get quizzes from student's department
        student_quizzes = [q for q in quizzes if q.course.department_id == student.department_id]
        
        for quiz in student_quizzes[:2]:  # Submit first 2 quizzes
            score = random.uniform(60, 100)  # Random score between 60-100
            max_score = len(quiz.questions)
            
            submission = QuizSubmission(
                quiz_id=quiz.id,
                user_id=student.id,
                score=score,
                max_score=max_score,
                answers={'q1': 'Option A', 'q2': 'Sample answer'},
                submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 14))
            )
            
            db.session.add(submission)
            submissions.append(submission)
    
    db.session.commit()
    print(f"Created {len(submissions)} sample quiz submissions")
    return submissions

def create_sample_ai_logs(users):
    """Create sample AI usage logs"""
    logs = []
    
    students = [u for u in users if u.role == UserRole.STUDENT]
    
    for student in students:
        # Create 2-3 AI call logs per student
        for i in range(random.randint(2, 3)):
            endpoint = random.choice(['ask', 'generate-questions'])
            success = random.choice([True, True, True, False])  # 75% success rate
            
            log = AiCallLog(
                user_id=student.id,
                endpoint=endpoint,
                request_data={'sample': 'data'},
                response_data={'result': 'sample response'},
                success=success,
                error_message='Sample error' if not success else None,
                processing_time=random.uniform(1, 5),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 7))
            )
            
            db.session.add(log)
            logs.append(log)
    
    db.session.commit()
    print(f"Created {len(logs)} sample AI usage logs")
    return logs

def main():
    """Main seeding function"""
    print("Starting ARU Academy database seeding...")
    
    try:
        # Create departments
        departments = create_departments()
        
        # Create admin user
        admin = create_admin_user(departments)
        
        # Create sample users
        users = create_sample_users(departments)
        
        # Create sample courses
        courses = create_sample_courses(departments, users)
        
        # Create sample resources
        resources = create_sample_resources(courses)
        
        # Create sample quizzes
        quizzes = create_sample_quizzes(courses)
        
        # Create sample progress records
        progress_records = create_sample_progress(users, resources)
        
        # Create sample quiz submissions
        submissions = create_sample_quiz_submissions(users, quizzes)
        
        # Create sample AI logs
        ai_logs = create_sample_ai_logs(users)
        
        print("\n✅ Database seeding completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Departments: {len(departments)}")
        print(f"   - Users: {len(users) + 1} (including admin)")
        print(f"   - Courses: {len(courses)}")
        print(f"   - Resources: {len(resources)}")
        print(f"   - Quizzes: {len(quizzes)}")
        print(f"   - Progress Records: {len(progress_records)}")
        print(f"   - Quiz Submissions: {len(submissions)}")
        print(f"   - AI Usage Logs: {len(ai_logs)}")
        
        print(f"\n🔑 Default Login Credentials:")
        print(f"   Admin: admin@aru.academy / Admin@123")
        print(f"   Instructor: sarah.johnson@aru.academy / Instructor@123")
        print(f"   Student: ahmed.hassan@student.aru.academy / Student@123")
        
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        db.session.rollback()
        raise

def seed_database():
    """Main seeding function that can be called from other scripts"""
    main()

if __name__ == '__main__':
    main()

