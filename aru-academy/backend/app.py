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
    
    # Ensure database is seeded when app is created (for production deployment)
    with app.app_context():
        try:
            db.create_all()
            seed_database_if_empty()
        except Exception as e:
            print(f"⚠️  Database seeding warning: {e}")
            # Don't fail the app startup if seeding fails
    
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
        
        # Check if any approved users already exist (skip creation entirely if any exist)
        try:
            existing_count = ApprovedUser.query.count()
            if existing_count > 0:
                print(f"✅ Found {existing_count} existing approved users. Skipping creation to avoid duplicates.")
                return
        except Exception as e:
            if "Unknown column 'approved_users.name'" in str(e):
                print("⚠️  approved_users table has wrong structure - recreating automatically...")
                recreate_approved_users_table()
                print("✅ approved_users table recreated successfully")
                # Check again after recreation
                existing_count = ApprovedUser.query.count()
                if existing_count > 0:
                    print(f"✅ Found {existing_count} existing approved users after recreation. Skipping creation.")
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
        
        # Create approved users for ALL departments with unique emails
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
                # Create unique emails for each department
                student_email = f'new.student.{dept.name.lower().replace(" ", ".")}@example.com'
                instructor_email = f'new.instructor.{dept.name.lower().replace(" ", ".")}@example.com'
                
                approved_emails = [
                    {'email': student_email, 'role': 'Student', 'name': f'New Student - {dept.name}'},
                    {'email': instructor_email, 'role': 'Instructor', 'name': f'New Instructor - {dept.name}'}
                ]
                
                for user_data in approved_emails:
                    try:
                        existing = ApprovedUser.query.filter_by(email=user_data['email']).first()
                    except Exception as e:
                        if "Unknown column 'approved_users.name'" in str(e):
                            print("⚠️  approved_users table has wrong structure - recreating automatically...")
                            recreate_approved_users_table()
                            print("✅ approved_users table recreated successfully")
                            # Try again after recreation
                            existing = ApprovedUser.query.filter_by(email=user_data['email']).first()
                        else:
                            raise e
                    
                    if not existing:
                        # Create approved user with correct structure
                        approved_user = ApprovedUser(
                            name=user_data['name'],
                            email=user_data['email'],
                            role=user_data['role'],
                            department_id=dept.id,
                            approved_by=admin.id,
                            approved_at=datetime.utcnow()
                        )
                        db.session.add(approved_user)
                        print(f"✅ Created approved user: {user_data['email']} for {dept.name}")
                    else:
                        print(f"✅ Approved user already exists: {user_data['email']} for {dept.name}")
        
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
        print("   - Unique student and instructor emails for each department")
        print("   - Format: new.student.{department}@example.com")
        print("   - Format: new.instructor.{department}@example.com")
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
        
        # Force recreation of courses and resources (for new content)
        print("🔄 Force recreating courses and resources with new content...")
        
        # Delete existing resources first (to avoid foreign key constraints)
        from models.resource import Resource
        existing_resources = Resource.query.all()
        for resource in existing_resources:
            db.session.delete(resource)
        print(f"🗑️  Deleted {len(existing_resources)} existing resources")
        
        # Delete existing courses
        existing_courses = Course.query.all()
        for course in existing_courses:
            db.session.delete(course)
        print(f"🗑️  Deleted {len(existing_courses)} existing courses")
        
        db.session.commit()
        print("✅ Cleared existing courses and resources")
        
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
        
        # Create sample resources/topics for each course
        from models.resource import Resource, ResourceType
        
        def create_resource_if_not_exists(title, description, content, course, resource_type=ResourceType.TEXT):
            existing_resource = Resource.query.filter_by(title=title, course_id=course.id).first()
            if not existing_resource:
                resource = Resource(
                    title=title,
                    description=description,
                    text_content=content,
                    type=resource_type,
                    course_id=course.id
                )
                db.session.add(resource)
                print(f"✅ Created resource: {title} for {course.title}")
                return resource
            else:
                print(f"✅ Resource already exists: {title}")
                return existing_resource
        
        # Get all created courses
        all_courses = Course.query.all()
        
        # Create resources for each course
        for course in all_courses:
            if "Introduction to Programming" in course.title:
                # Computer Science - Introduction to Programming
                create_resource_if_not_exists(
                    "Variables and Data Types",
                    "Understanding basic programming concepts",
                    "Variables are containers for storing data values. In Python, you don't need to declare variables with a specific type. Python automatically determines the type based on the value assigned. Common data types include integers, floats, strings, booleans, lists, and dictionaries.",
                    course
                )
                create_resource_if_not_exists(
                    "Control Structures",
                    "Conditional statements and loops",
                    "Control structures allow you to control the flow of your program. This includes if-else statements for decision making, for loops for iteration, while loops for repeated execution, and break/continue statements for loop control.",
                    course
                )
                create_resource_if_not_exists(
                    "Functions and Modules",
                    "Code organization and reusability",
                    "Functions are reusable blocks of code that perform specific tasks. They help organize code and avoid repetition. Modules are files containing Python code that can be imported and used in other programs. This promotes code reusability and maintainability.",
                    course
                )
                create_resource_if_not_exists(
                    "Object-Oriented Programming",
                    "Classes, objects, and inheritance",
                    "Object-Oriented Programming (OOP) is a programming paradigm based on objects and classes. Key concepts include encapsulation (data hiding), inheritance (code reuse), polymorphism (multiple forms), and abstraction (simplifying complex systems).",
                    course
                )
                
            elif "Data Structures and Algorithms" in course.title:
                # Computer Science - Data Structures and Algorithms
                create_resource_if_not_exists(
                    "Arrays and Linked Lists",
                    "Linear data structures",
                    "Arrays are contiguous memory locations storing elements of the same type. Linked lists are dynamic data structures where elements are stored in nodes with pointers to the next node. Arrays provide O(1) access time but fixed size, while linked lists provide dynamic size but O(n) access time.",
                    course
                )
                create_resource_if_not_exists(
                    "Stacks and Queues",
                    "LIFO and FIFO data structures",
                    "Stacks follow Last-In-First-Out (LIFO) principle, commonly used for function calls and expression evaluation. Queues follow First-In-First-Out (FIFO) principle, used in scheduling and breadth-first search. Both can be implemented using arrays or linked lists.",
                    course
                )
                create_resource_if_not_exists(
                    "Trees and Graphs",
                    "Hierarchical and network data structures",
                    "Trees are hierarchical data structures with a root node and child nodes. Binary trees, AVL trees, and B-trees are common variants. Graphs represent relationships between entities using vertices and edges. They're used in social networks, maps, and dependency resolution.",
                    course
                )
                create_resource_if_not_exists(
                    "Sorting and Searching Algorithms",
                    "Efficient data processing techniques",
                    "Sorting algorithms arrange data in order: bubble sort, selection sort, insertion sort, merge sort, quick sort, and heap sort. Searching algorithms find elements: linear search, binary search, and hash-based search. Time complexity analysis helps choose the right algorithm.",
                    course
                )
                
            elif "Circuit Analysis" in course.title:
                # Electrical Engineering - Circuit Analysis
                create_resource_if_not_exists(
                    "Ohm's Law and Basic Circuits",
                    "Fundamental electrical principles",
                    "Ohm's Law states that voltage equals current times resistance (V = IR). This fundamental relationship governs basic electrical circuits. Understanding voltage, current, and resistance is essential for analyzing simple circuits and understanding electrical behavior.",
                    course
                )
                create_resource_if_not_exists(
                    "Kirchhoff's Laws",
                    "Circuit analysis techniques",
                    "Kirchhoff's Current Law (KCL) states that the sum of currents entering a node equals the sum leaving. Kirchhoff's Voltage Law (KVL) states that the sum of voltages around any closed loop is zero. These laws are fundamental for analyzing complex circuits.",
                    course
                )
                create_resource_if_not_exists(
                    "AC Circuit Analysis",
                    "Alternating current circuits",
                    "AC circuits involve sinusoidal voltages and currents. Key concepts include impedance, phasors, and frequency response. AC analysis requires understanding of complex numbers, reactance, and resonance. Applications include power systems and signal processing.",
                    course
                )
                create_resource_if_not_exists(
                    "Network Theorems",
                    "Advanced circuit analysis methods",
                    "Network theorems simplify complex circuit analysis. Thevenin's theorem replaces complex networks with equivalent voltage sources. Norton's theorem uses equivalent current sources. Superposition principle allows analyzing circuits with multiple sources by considering one source at a time.",
                    course
                )
                
            elif "Digital Electronics" in course.title:
                # Electrical Engineering - Digital Electronics
                create_resource_if_not_exists(
                    "Boolean Algebra and Logic Gates",
                    "Digital logic fundamentals",
                    "Boolean algebra uses binary values (0 and 1) and logical operations (AND, OR, NOT). Logic gates implement these operations in hardware. Understanding truth tables, logic expressions, and gate combinations is essential for digital circuit design.",
                    course
                )
                create_resource_if_not_exists(
                    "Combinational Logic Circuits",
                    "Logic circuits without memory",
                    "Combinational circuits produce outputs based only on current inputs. Common examples include adders, multiplexers, decoders, and encoders. These circuits are fundamental building blocks for digital systems and processors.",
                    course
                )
                create_resource_if_not_exists(
                    "Sequential Logic Circuits",
                    "Logic circuits with memory",
                    "Sequential circuits have memory elements (flip-flops) that store previous states. They include latches, flip-flops, counters, and registers. Clock signals synchronize operations. These circuits enable state machines and complex digital systems.",
                    course
                )
                create_resource_if_not_exists(
                    "Memory and Storage Systems",
                    "Data storage in digital systems",
                    "Memory systems store and retrieve digital data. Types include RAM (Random Access Memory), ROM (Read-Only Memory), and secondary storage. Understanding memory hierarchy, addressing, and access patterns is crucial for computer architecture.",
                    course
                )
                
            elif "Engineering Mechanics" in course.title:
                # Mechanical Engineering - Engineering Mechanics
                create_resource_if_not_exists(
                    "Statics and Force Analysis",
                    "Equilibrium of rigid bodies",
                    "Statics deals with bodies at rest or in uniform motion. Key concepts include force vectors, moments, equilibrium conditions, and free body diagrams. Understanding how forces act on structures is fundamental for mechanical design and analysis.",
                    course
                )
                create_resource_if_not_exists(
                    "Dynamics and Motion",
                    "Kinematics and kinetics",
                    "Dynamics studies motion and forces causing motion. Kinematics describes motion without considering forces (position, velocity, acceleration). Kinetics relates forces to motion using Newton's laws. Applications include machine design and vehicle dynamics.",
                    course
                )
                create_resource_if_not_exists(
                    "Stress and Strain Analysis",
                    "Material behavior under loads",
                    "Stress is force per unit area, strain is deformation per unit length. Understanding stress-strain relationships, elastic and plastic behavior, and failure criteria is essential for material selection and structural design.",
                    course
                )
                create_resource_if_not_exists(
                    "Mechanical Systems Design",
                    "Integration of mechanical components",
                    "Mechanical systems design involves selecting and integrating components like gears, bearings, springs, and linkages. Design considerations include load capacity, efficiency, reliability, and manufacturability. CAD tools aid in design and analysis.",
                    course
                )
                
            elif "Thermodynamics" in course.title:
                # Mechanical Engineering - Thermodynamics
                create_resource_if_not_exists(
                    "Laws of Thermodynamics",
                    "Fundamental energy principles",
                    "The four laws of thermodynamics govern energy transfer and conversion. The first law (conservation of energy) states energy cannot be created or destroyed. The second law (entropy) describes energy quality and direction of processes. These laws apply to all energy systems.",
                    course
                )
                create_resource_if_not_exists(
                    "Heat Transfer Mechanisms",
                    "Conduction, convection, and radiation",
                    "Heat transfer occurs through conduction (molecular motion), convection (fluid motion), and radiation (electromagnetic waves). Understanding these mechanisms is crucial for thermal system design, including heat exchangers, cooling systems, and insulation.",
                    course
                )
                create_resource_if_not_exists(
                    "Power Cycles and Engines",
                    "Energy conversion systems",
                    "Power cycles convert heat to work. Common cycles include Rankine (steam), Brayton (gas turbine), and Otto/Diesel (internal combustion). Understanding cycle efficiency, work output, and heat rejection is essential for power plant and engine design.",
                    course
                )
                create_resource_if_not_exists(
                    "Refrigeration and Heat Pumps",
                    "Cooling and heating systems",
                    "Refrigeration systems remove heat from low-temperature spaces. Heat pumps can provide both heating and cooling. Understanding coefficient of performance, refrigerants, and system components is important for HVAC and refrigeration applications.",
                    course
                )
                
            elif "Business Management" in course.title:
                # Business Administration - Business Management
                create_resource_if_not_exists(
                    "Management Principles and Functions",
                    "Core management concepts",
                    "Management involves planning, organizing, leading, and controlling organizational resources. Key principles include division of work, authority and responsibility, unity of command, and scalar chain. Understanding these functions is essential for effective leadership.",
                    course
                )
                create_resource_if_not_exists(
                    "Organizational Behavior",
                    "Human behavior in organizations",
                    "Organizational behavior studies how individuals and groups behave in organizational settings. Topics include motivation theories, leadership styles, team dynamics, and organizational culture. This knowledge helps improve workplace productivity and employee satisfaction.",
                    course
                )
                create_resource_if_not_exists(
                    "Strategic Planning and Decision Making",
                    "Long-term business planning",
                    "Strategic planning involves setting long-term goals and developing plans to achieve them. Decision-making processes include problem identification, alternative generation, evaluation, and implementation. Tools like SWOT analysis and decision trees aid in strategic planning.",
                    course
                )
                create_resource_if_not_exists(
                    "Operations and Supply Chain Management",
                    "Efficient business operations",
                    "Operations management focuses on producing goods and services efficiently. Supply chain management coordinates activities from raw materials to final products. Key concepts include quality management, inventory control, and process optimization.",
                    course
                )
                
            elif "Financial Accounting" in course.title:
                # Business Administration - Financial Accounting
                create_resource_if_not_exists(
                    "Accounting Principles and Standards",
                    "Fundamental accounting concepts",
                    "Accounting principles include the accrual basis, matching principle, and conservatism. Generally Accepted Accounting Principles (GAAP) provide standardized guidelines for financial reporting. Understanding these principles ensures accurate and consistent financial statements.",
                    course
                )
                create_resource_if_not_exists(
                    "Financial Statements Analysis",
                    "Balance sheet, income statement, and cash flow",
                    "Financial statements provide information about a company's financial position and performance. The balance sheet shows assets, liabilities, and equity. The income statement shows revenues and expenses. The cash flow statement shows cash inflows and outflows.",
                    course
                )
                create_resource_if_not_exists(
                    "Cost Accounting and Budgeting",
                    "Internal financial management",
                    "Cost accounting tracks and analyzes costs for decision-making. Budgeting involves planning future financial activities. Key concepts include cost classification, variance analysis, and performance measurement. These tools help control costs and improve profitability.",
                    course
                )
                create_resource_if_not_exists(
                    "Auditing and Internal Controls",
                    "Financial integrity and compliance",
                    "Auditing examines financial records for accuracy and compliance. Internal controls are procedures to safeguard assets and ensure reliable financial reporting. Understanding audit procedures, risk assessment, and control testing is essential for financial integrity.",
                    course
                )
        
        db.session.commit()
        print(f"✅ Created sample resources/topics for all courses")
        
        # Approved users already created by create_approved_users() function
        
        print("🎉 Database seeding completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Departments: {len(departments)}")
        print(f"   - Users: {len(users) + 1} (1 admin + 4 instructors + 12 students)")
        print(f"   - Courses: {len(courses)}")
        print(f"   - Resources/Topics: {Resource.query.count()}")
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

def force_seed_database():
    """Force seed database with new content (deletes existing courses/resources)"""
    try:
        print("🔄 FORCE SEEDING: Recreating all courses and resources...")
        
        from models.department import Department
        from models.user import User, UserRole, UserStatus
        from models.approved_user import ApprovedUser
        from models.course import Course
        from models.resource import Resource
        from datetime import datetime
        
        # Always create approved users first (independent of other data)
        create_approved_users()
        
        # Delete existing resources first (to avoid foreign key constraints)
        existing_resources = Resource.query.all()
        for resource in existing_resources:
            db.session.delete(resource)
        print(f"🗑️  Deleted {len(existing_resources)} existing resources")
        
        # Delete existing courses
        existing_courses = Course.query.all()
        for course in existing_courses:
            db.session.delete(course)
        print(f"🗑️  Deleted {len(existing_courses)} existing courses")
        
        db.session.commit()
        print("✅ Cleared existing courses and resources")
        
        # Now run the full seeding process
        print("🌱 Starting full seeding process with new content...")
        seed_database_if_empty()
        
        print("🎉 FORCE SEEDING completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during force seeding: {str(e)}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database_if_empty()
    app.run(debug=True, host='0.0.0.0', port=8000)

