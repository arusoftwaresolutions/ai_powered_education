from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from auth.routes import auth_bp
from courses.routes import courses_bp
from resources.routes import resources_bp
from quizzes.routes import quizzes_bp
from admin.routes import admin_bp
from ai.routes import ai_bp
from health.routes import health_bp

# Import models and database
from models.base import db, migrate
from config.settings import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # JWT setup
    jwt = JWTManager(app)
    
    # CORS setup
    CORS(app, 
         origins=app.config['CORS_ORIGINS'], 
         supports_credentials=False,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get('REDIS_URL', 'memory://')
    )
    
    # Swagger documentation
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "ARU Academy API",
            "description": "E-Learning Platform API with AI-powered tutoring",
            "version": "1.0.0"
        }
    })
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(resources_bp, url_prefix='/api/resources')
    app.register_blueprint(quizzes_bp, url_prefix='/api/quizzes')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(health_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    

    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'message': 'Welcome to ARU Academy API',
            'version': '1.0.0',
            'docs': '/api/docs'
        })
    
    return app

# Create app instance
app = create_app()

def recreate_approved_users_table():
    """Recreate approved_users table with correct structure"""
    try:
        print("🗑️  Dropping existing approved_users table...")
        db.session.execute(db.text("DROP TABLE IF EXISTS approved_users"))
        db.session.commit()
        print("✅ Existing table dropped")
        
        print("🔧 Creating new approved_users table with name column...")
        create_table_sql = db.text("""
            CREATE TABLE approved_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL,
                department_id INT NOT NULL,
                approved_by INT,
                approved_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        """)
        db.session.execute(create_table_sql)
        db.session.commit()
        print("✅ New table created with correct structure")
        
    except Exception as e:
        print(f"❌ Error recreating table: {e}")
        db.session.rollback()
        raise e

def create_approved_users():
    """Create approved users for registration if they don't exist"""
    try:
        from models.department import Department
        from models.user import User, UserRole, UserStatus
        from models.approved_user import ApprovedUser
        from datetime import datetime
        from sqlalchemy.exc import IntegrityError
        
        # Check if approved users already exist (skip if any exist to avoid duplicates)
        required_emails = ['new.student@example.com', 'new.instructor@example.com']
        try:
            existing_approved = ApprovedUser.query.filter(ApprovedUser.email.in_(required_emails)).all()
            if existing_approved:
                print(f"✅ Found {len(existing_approved)} existing approved users. Skipping creation to avoid duplicates.")
                return
        except Exception as e:
            if "Unknown column 'approved_users.name'" in str(e):
                print("⚠️  approved_users table has wrong structure - recreating automatically...")
                recreate_approved_users_table()
                print("✅ approved_users table recreated successfully")
                # Check again after recreation
                existing_approved = ApprovedUser.query.filter(ApprovedUser.email.in_(required_emails)).all()
                if existing_approved:
                    print(f"✅ Found {len(existing_approved)} existing approved users after recreation. Skipping creation.")
                    return
            else:
                raise e
        
        print("🌱 Creating approved users for registration...")
        
        # Get or create CS department
        cs_dept = Department.query.filter_by(name='Computer Science').first()
        if not cs_dept:
            cs_dept = Department(
                name='Computer Science',
                description='Computer Science and Software Engineering programs'
            )
            db.session.add(cs_dept)
            db.session.commit()
            print("✅ Created Computer Science department")
        
        # Get or create admin user
        admin = User.query.filter_by(email='admin@aru.academy').first()
        if not admin:
            admin = User(
                name='System Administrator',
                email='admin@aru.academy',
                role=UserRole.ADMIN,
                department_id=cs_dept.id,
                status=UserStatus.ACTIVE
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Created admin user")
        
        # Create approved users for ALL departments (check for duplicates)
        approved_emails = ['new.student@example.com', 'new.instructor@example.com']
        
        # Get all departments to create approved users for each
        all_departments = Department.query.all()
        if not all_departments:
            # If no departments exist yet, create them first
            print("🌱 Creating departments for approved users...")
            departments_data = [
                {'name': 'Computer Science', 'description': 'Computer Science and Software Engineering programs'},
                {'name': 'Electrical Engineering', 'description': 'Electrical and Electronics Engineering programs'},
                {'name': 'Mechanical Engineering', 'description': 'Mechanical and Manufacturing Engineering programs'},
                {'name': 'Business Administration', 'description': 'Business and Management programs'}
            ]
            
            for dept_data in departments_data:
                dept = Department(**dept_data)
                db.session.add(dept)
                print(f"✅ Created department: {dept_data['name']}")
            
            db.session.commit()
            all_departments = Department.query.all()
        
        # Use no_autoflush to prevent premature flushing during duplicate checks
        with db.session.no_autoflush:
            for dept in all_departments:
                for email in approved_emails:
                    try:
                        existing = ApprovedUser.query.filter_by(email=email, department_id=dept.id).first()
                    except Exception as e:
                        if "Unknown column 'approved_users.name'" in str(e):
                            print("⚠️  approved_users table has wrong structure - recreating automatically...")
                            recreate_approved_users_table()
                            print("✅ approved_users table recreated successfully")
                            # Try again after recreation
                            existing = ApprovedUser.query.filter_by(email=email, department_id=dept.id).first()
                        else:
                            raise e
                    
                    if not existing:
                        role = 'Student' if 'student' in email else 'Instructor'
                        name = 'New Student' if 'student' in email else 'New Instructor'
                        
                        # Create approved user with correct structure
                        approved_user = ApprovedUser(
                            name=name,
                            email=email,
                            role=role,
                            department_id=dept.id,
                            approved_by=admin.id,
                            approved_at=datetime.utcnow()
                        )
                        db.session.add(approved_user)
                        print(f"✅ Created approved user: {email} for {dept.name}")
                    else:
                        print(f"✅ Approved user already exists: {email} for {dept.name}")
        
        # Commit all changes at once
        try:
            db.session.commit()
            print("✅ Successfully committed all approved users")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing approved users: {e}")
            raise e
        
        total_approved = ApprovedUser.query.count()
        print(f"✅ Created {total_approved} approved users for registration")
        print("   - new.student@example.com (student) for all departments")
        print("   - new.instructor@example.com (instructor) for all departments")
        print("✅ Approved users created/verified.")
        
    except IntegrityError as e:
        db.session.rollback()
        if "Duplicate entry" in str(e):
            print("⚠️  Duplicate entry detected - approved users may already exist. Skipping creation.")
            print("✅ Approved users verification completed.")
        else:
            print(f"❌ Database integrity error creating approved users: {e}")
            raise e
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating approved users: {e}")
        raise e

def seed_database_if_empty():
    """Seed database with initial data if it's empty"""
    try:
        from models.department import Department
        from models.user import User, UserRole, UserStatus
        from models.approved_user import ApprovedUser
        from models.course import Course
        from datetime import datetime
        
        # Always create approved users first (independent of other data)
        create_approved_users()
        
        # Check if database is already seeded
        if Department.query.count() > 0:
            print("✅ Database already contains data. Skipping full seeding.")
            return
        
        print("🌱 Database is empty. Starting full seeding process...")
        
        # Create departments (check for duplicates)
        departments_data = [
            {'name': 'Computer Science', 'description': 'Computer Science and Software Engineering programs'},
            {'name': 'Electrical Engineering', 'description': 'Electrical and Electronics Engineering programs'},
            {'name': 'Mechanical Engineering', 'description': 'Mechanical and Manufacturing Engineering programs'},
            {'name': 'Business Administration', 'description': 'Business and Management programs'}
        ]
        
        departments = []
        for dept_data in departments_data:
            existing_dept = Department.query.filter_by(name=dept_data['name']).first()
            if not existing_dept:
                dept = Department(**dept_data)
                db.session.add(dept)
                departments.append(dept)
                print(f"✅ Created department: {dept_data['name']}")
            else:
                departments.append(existing_dept)
                print(f"✅ Department already exists: {dept_data['name']}")
        
        db.session.commit()
        print(f"✅ Total departments: {len(departments)}")
        
        # Create admin user (check for duplicates)
        admin = User.query.filter_by(email='admin@aru.academy').first()
        if not admin:
            admin = User(
                name='Admin User',
                email='admin@aru.academy',
                role=UserRole.ADMIN,
                department_id=departments[0].id,
                status=UserStatus.ACTIVE
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Created admin user: admin@aru.academy / Admin@123")
        else:
            print("✅ Admin user already exists: admin@aru.academy")
        
        # Create sample users (check for duplicates)
        users = []
        
        def create_user_if_not_exists(name, email, role, department_id, password):
            existing_user = User.query.filter_by(email=email).first()
            if not existing_user:
                user = User(
                    name=name,
                    email=email,
                    role=role,
                    department_id=department_id,
                    status=UserStatus.ACTIVE
                )
                user.set_password(password)
                db.session.add(user)
                users.append(user)
                print(f"✅ Created user: {name} ({email})")
                return user
            else:
                print(f"✅ User already exists: {name} ({email})")
                return existing_user
        
        # Computer Science
        cs_dept = next(d for d in departments if d.name == 'Computer Science')
        cs_instructor = create_user_if_not_exists(
            'Dr. Sarah Johnson',
            'sarah.johnson@aru.academy',
            UserRole.INSTRUCTOR,
            cs_dept.id,
            'Instructor@123'
        )
        
        # CS Students
        cs_students = [
            ('Ahmed Hassan', 'ahmed.hassan@student.aru.academy'),
            ('Fatima Ali', 'fatima.ali@student.aru.academy'),
            ('Omar Khalil', 'omar.khalil@student.aru.academy')
        ]
        
        for name, email in cs_students:
            create_user_if_not_exists(
                name, email, UserRole.STUDENT, cs_dept.id, 'Student@123'
            )
        
        # Electrical Engineering
        ee_dept = next(d for d in departments if d.name == 'Electrical Engineering')
        ee_instructor = create_user_if_not_exists(
            'Dr. Michael Chen',
            'michael.chen@aru.academy',
            UserRole.INSTRUCTOR,
            ee_dept.id,
            'Instructor@123'
        )
        
        # EE Students
        ee_students = [
            ('Layla Ahmed', 'layla.ahmed@student.aru.academy'),
            ('Yusuf Ibrahim', 'yusuf.ibrahim@student.aru.academy'),
            ('Aisha Mohammed', 'aisha.mohammed@student.aru.academy')
        ]
        
        for name, email in ee_students:
            create_user_if_not_exists(
                name, email, UserRole.STUDENT, ee_dept.id, 'Student@123'
            )
        
        # Mechanical Engineering
        me_dept = next(d for d in departments if d.name == 'Mechanical Engineering')
        me_instructor = create_user_if_not_exists(
            'Dr. Robert Wilson',
            'robert.wilson@aru.academy',
            UserRole.INSTRUCTOR,
            me_dept.id,
            'Instructor@123'
        )
        
        # ME Students
        me_students = [
            ('Khalid Al-Rashid', 'khalid.al-rashid@student.aru.academy'),
            ('Noor Al-Zahra', 'noor.al-zahra@student.aru.academy'),
            ('Zaid Al-Mansouri', 'zaid.al-mansouri@student.aru.academy')
        ]
        
        for name, email in me_students:
            create_user_if_not_exists(
                name, email, UserRole.STUDENT, me_dept.id, 'Student@123'
            )
        
        # Business Administration
        bu_dept = next(d for d in departments if d.name == 'Business Administration')
        bu_instructor = create_user_if_not_exists(
            'Dr. Emily Rodriguez',
            'emily.rodriguez@aru.academy',
            UserRole.INSTRUCTOR,
            bu_dept.id,
            'Instructor@123'
        )
        
        # BU Students
        bu_students = [
            ('Mariam Al-Sayed', 'mariam.al-sayed@student.aru.academy'),
            ('Hassan Al-Qahtani', 'hassan.al-qahtani@student.aru.academy'),
            ('Amina Al-Sabah', 'amina.al-sabah@student.aru.academy')
        ]
        
        for name, email in bu_students:
            create_user_if_not_exists(
                name, email, UserRole.STUDENT, bu_dept.id, 'Student@123'
            )
        
        # Commit all users (already added by helper function)
        db.session.commit()
        print(f"✅ Total users processed: {len(users)}")
        
        # Create sample courses for each department (check for duplicates)
        courses = []
        
        def create_course_if_not_exists(title, description, department_id, created_by):
            existing_course = Course.query.filter_by(title=title, department_id=department_id).first()
            if not existing_course:
                course = Course(
                    title=title,
                    description=description,
                    department_id=department_id,
                    created_by=created_by
                )
                db.session.add(course)
                courses.append(course)
                print(f"✅ Created course: {title}")
                return course
            else:
                print(f"✅ Course already exists: {title}")
                return existing_course
        
        # Computer Science Courses
        cs_courses = [
            ('Introduction to Programming', 'Learn the fundamentals of programming with Python'),
            ('Data Structures and Algorithms', 'Advanced programming concepts and algorithm design')
        ]
        
        for title, description in cs_courses:
            create_course_if_not_exists(title, description, cs_dept.id, cs_instructor.id)
        
        # Electrical Engineering Courses
        ee_courses = [
            ('Circuit Analysis', 'Fundamentals of electrical circuits and analysis'),
            ('Digital Electronics', 'Introduction to digital systems and logic design')
        ]
        
        for title, description in ee_courses:
            create_course_if_not_exists(title, description, ee_dept.id, ee_instructor.id)
        
        # Mechanical Engineering Courses
        me_courses = [
            ('Engineering Mechanics', 'Statics and dynamics of mechanical systems'),
            ('Thermodynamics', 'Heat transfer and energy conversion principles')
        ]
        
        for title, description in me_courses:
            create_course_if_not_exists(title, description, me_dept.id, me_instructor.id)
        
        # Business Administration Courses
        bu_courses = [
            ('Business Management', 'Principles of modern business management and leadership'),
            ('Financial Accounting', 'Fundamentals of financial reporting and analysis')
        ]
        
        for title, description in bu_courses:
            create_course_if_not_exists(title, description, bu_dept.id, bu_instructor.id)
        
        db.session.commit()
        print(f"✅ Created {len(courses)} sample courses")
        
        # Approved users already created by create_approved_users() function
        
        print("🎉 Database seeding completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Departments: {len(departments)}")
        print(f"   - Users: {len(users) + 1} (1 admin + 4 instructors + 12 students)")
        print(f"   - Courses: {len(courses)}")
        print(f"   - Approved Users: 2")
        print("\n🔑 Default Login Credentials:")
        print("   Admin: admin@aru.academy / Admin@123")
        print("   CS Instructor: sarah.johnson@aru.academy / Instructor@123")
        print("   EE Instructor: michael.chen@aru.academy / Instructor@123")
        print("   ME Instructor: robert.wilson@aru.academy / Instructor@123")
        print("   BU Instructor: emily.rodriguez@aru.academy / Instructor@123")
        print("   CS Students: ahmed.hassan@student.aru.academy, fatima.ali@student.aru.academy, omar.khalil@student.aru.academy")
        print("   EE Students: layla.ahmed@student.aru.academy, yusuf.ibrahim@student.aru.academy, aisha.mohammed@student.aru.academy")
        print("   ME Students: khalid.al-rashid@student.aru.academy, noor.al-zahra@student.aru.academy, zaid.al-mansouri@student.aru.academy")
        print("   BU Students: mariam.al-sayed@student.aru.academy, hassan.al-qahtani@student.aru.academy, amina.al-sabah@student.aru.academy")
        print("   All student passwords: Student@123")
        
    except Exception as e:
        print(f"❌ Error during database seeding: {str(e)}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database_if_empty()
    app.run(debug=True, host='0.0.0.0', port=8000)

