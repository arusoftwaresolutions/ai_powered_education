# ARU Academy - AI-Powered E-Learning Platform

A complete, production-ready e-learning web application built with modern web technologies and AI integration.

## 🚀 Project Overview

ARU Academy is a comprehensive e-learning platform that combines traditional educational features with cutting-edge AI capabilities. The system supports multiple user roles, department-based access control, and intelligent AI tutoring powered by Hugging Face's inference API.

## ✨ Key Features

### 🔐 **Authentication & Security**
- **Role-Based Access Control**: Student, Instructor, and Admin roles
- **JWT Authentication**: Secure token-based authentication with httpOnly cookies
- **User Approval Workflow**: Admin approval required for new registrations
- **Password Security**: Bcrypt password hashing
- **CSRF Protection**: Cross-site request forgery protection

### 🏫 **Department-Based Learning**
- **4 Departments**: Computer Science, Electrical Engineering, Mechanical Engineering, Business Administration
- **Access Control**: Users only see resources from their assigned department
- **Instructor Management**: Instructors manage courses within their department

### 📚 **Course & Resource Management**
- **Course Creation**: Instructors can create and manage courses
- **Resource Upload**: Support for PDFs, text content, video links, and external resources
- **Progress Tracking**: Students can track their learning progress
- **File Storage**: Organized storage structure by department

### 🤖 **AI-Powered Learning**
- **AI Tutor**: Students can ask questions and get AI-generated explanations
- **Quiz Generation**: AI creates quizzes from course content and topics
- **Context Retrieval**: Smart context provision for better AI responses
- **Hugging Face Integration**: Powered by state-of-the-art language models

### 📝 **Assessment System**
- **AI-Generated Quizzes**: 5-10 questions per quiz (MCQ + Short Answer)
- **Auto-Grading**: Multiple choice questions automatically graded
- **Performance Tracking**: Student quiz history and scores
- **Progress Analytics**: Learning progress visualization

### 👨‍💼 **Admin Dashboard**
- **User Management**: Approve/deny pending users
- **Department Management**: Manage departments and assignments
- **Analytics Dashboard**: Active users, resources, quizzes, AI usage statistics
- **CSV Import**: Bulk user import functionality

## 🛠️ Technology Stack

### **Frontend**
- **HTML5**: Semantic markup and modern structure
- **CSS3**: Responsive design with CSS Grid and Flexbox
- **Vanilla JavaScript**: No frameworks, pure ES6+ JavaScript
- **Fetch API**: Modern HTTP client for backend communication

### **Backend**
- **Python 3**: Core application logic
- **Flask**: Lightweight web framework
- **SQLAlchemy**: Object-relational mapping
- **Flask-Migrate**: Database migration management (Alembic)

### **Database**
- **MySQL**: Primary database system
- **Optimized Schema**: Efficient table design with proper relationships
- **Migration System**: Version-controlled database changes

### **AI Integration**
- **Hugging Face Inference API**: Access to state-of-the-art models
- **HTTP Integration**: Python requests library for API calls
- **Error Handling**: Graceful fallbacks when AI services are unavailable

### **Security & Performance**
- **JWT Tokens**: Secure authentication
- **Rate Limiting**: API request throttling
- **Input Validation**: Comprehensive data validation
- **Error Handling**: Robust error management

## 📁 Project Structure

```
aru-academy/
├── backend/                    # 🎯 Complete backend application
│   ├── app.py                 # Main Flask application
│   ├── wsgi.py               # WSGI entry point
│   ├── Dockerfile            # Docker build configuration
│   ├── render.yaml           # Render deployment configuration
│   ├── requirements.txt      # Python dependencies
│   ├── gunicorn.conf.py      # Production server configuration
│   ├── env.example           # Environment variables template
│   ├── .dockerignore         # Docker ignore patterns
│   ├── config/               # Configuration settings
│   ├── auth/                 # Authentication system
│   ├── ai/                   # AI integration services
│   ├── courses/              # Course management
│   ├── resources/            # Resource management
│   ├── quizzes/              # Quiz system
│   ├── admin/                # Admin dashboard
│   ├── health/               # Health monitoring
│   ├── models/               # Database models
│   ├── migrations/           # Database migrations
│   ├── seed/                 # Database seeding
│   └── storage/              # File storage
│       └── departments/      # Department-based file organization
├── public/                    # 🌐 Frontend static files
│   ├── index.html            # Landing page
│   ├── about.html            # About page
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── dashboard.html        # User dashboard
│   ├── courses.html          # Course listing
│   ├── course_detail.html    # Course details
│   ├── quizzes.html          # Quiz interface
│   ├── ai-tutor.html         # AI tutor interface
│   ├── admin.html            # Admin dashboard
│   ├── profile.html          # User profile
│   ├── css/                  # Stylesheets
│   │   ├── base.css          # Base styles
│   │   ├── layout.css        # Layout styles
│   │   └── components.css    # Component styles
│   └── js/                   # JavaScript services
│       ├── api.js            # API client
│       ├── auth.js           # Authentication
│       ├── courses.js        # Course management
│       ├── quizzes.js        # Quiz functionality
│       ├── ai.js             # AI integration
│       ├── admin.js          # Admin functions
│       └── ui.js             # UI utilities
└── docker-compose.yml        # Docker orchestration
```

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+
- MySQL 8.0+
- Git

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/arusoftwaresolutions/ai_powered_education.git
   cd ai_powered_education/aru-academy
   ```

2. **Set up environment**
   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up database**
   ```bash
   # Create MySQL database
   mysql -u root -p -e "CREATE DATABASE aru_academy;"
   
   # Run migrations
   flask db upgrade
   
   # Seed with sample data
   python -m seed.seed
   ```

5. **Start the application**
   ```bash
   # Option 1: Direct Python
   python app.py
   
   # Option 2: Docker Compose (recommended)
   cd ..
   docker-compose up -d
   ```

6. **Access the application**
   - Frontend: `http://localhost:80` (Docker) or `http://localhost:5000` (Direct)
   - Backend API: `http://localhost:8000/api` (Docker) or `http://localhost:5000/api` (Direct)
   - Health Check: `http://localhost:8000/api/health`

## 🔑 Default Credentials

After seeding the database:

### **Admin Users**
- **Admin**: `admin@aru.academy` / `Admin@123`

### **Instructors (1 per department)**
- **Computer Science**: `sarah.johnson@aru.academy` / `Instructor@123`
- **Electrical Engineering**: `michael.chen@aru.academy` / `Instructor@123`
- **Mechanical Engineering**: `robert.wilson@aru.academy` / `Instructor@123`
- **Business Administration**: `emily.rodriguez@aru.academy` / `Instructor@123`

### **Students (3 per department)**
- **Computer Science**:
  - `ahmed.hassan@student.aru.academy` / `Student@123`
  - `fatima.ali@student.aru.academy` / `Student@123`
  - `omar.khalil@student.aru.academy` / `Student@123`
- **Electrical Engineering**:
  - `layla.ahmed@student.aru.academy` / `Student@123`
  - `yusuf.ibrahim@student.aru.academy` / `Student@123`
  - `aisha.mohammed@student.aru.academy` / `Student@123`
- **Mechanical Engineering**:
  - `khalid.al-rashid@student.aru.academy` / `Student@123`
  - `noor.al-zahra@student.aru.academy` / `Student@123`
  - `zaid.al-mansouri@student.aru.academy` / `Student@123`
- **Business Administration**:
  - `mariam.al-sayed@student.aru.academy` / `Student@123`
  - `hassan.al-qahtani@student.aru.academy` / `Student@123`
  - `amina.al-sabah@student.aru.academy` / `Student@123`

## 🌐 API Endpoints

### **Authentication**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile

### **AI Services**
- `POST /api/ai/ask` - Ask AI tutor questions
- `POST /api/ai/generate-questions` - Generate AI quizzes

### **Courses & Resources**
- `GET /api/courses` - List courses
- `POST /api/courses` - Create course (instructors)
- `GET /api/resources` - List resources
- `POST /api/resources` - Upload resource (instructors)

### **Quizzes**
- `GET /api/quizzes` - List available quizzes
- `POST /api/quizzes/submit` - Submit quiz answers

### **Admin**
- `GET /api/admin/users` - List all users
- `POST /api/admin/users/approve` - Approve pending users
- `GET /api/admin/analytics` - System analytics

## 🐳 Docker Deployment

### **Local Development with Docker Compose**

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f db

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### **Services Included:**
- **Backend**: Flask API server (Port 8000)
- **Database**: MySQL 8.0 (Port 3306)
- **Frontend**: Nginx static file server (Port 80)

### **Docker Backend Only (for Render deployment)**

```bash
# Build backend Docker image
cd backend
docker build -t aru-academy-backend .

# Run backend container
docker run -p 8000:8000 aru-academy-backend
```

## 🚀 Production Deployment

### **Backend (Render) - Docker Deployment**
1. **Connect Repository**: Link your GitHub repository to Render
2. **Create Web Service**: 
   - Environment: `Docker`
   - Dockerfile Path: `./backend/Dockerfile`
   - Docker Context: `./backend`
3. **Environment Variables**: Set up in Render dashboard
4. **Auto-Deploy**: Enable automatic deployments from main branch

### **Frontend (Vercel/Netlify)**
1. **Deploy `public/` directory** to your preferred static hosting
2. **Configure API Base URL** to point to your Render backend
3. **Set up custom domain** (optional)

### **Database (Railway/PlanetScale)**
1. **Provision MySQL database** on your preferred provider
2. **Update connection strings** in Render environment variables
3. **Run migrations** on first deployment

### **Environment Variables for Production**
```bash
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
MYSQL_HOST=your-database-host
MYSQL_PORT=3306
MYSQL_USER=your-db-user
MYSQL_PASSWORD=your-db-password
MYSQL_DB=aru_academy
HF_API_TOKEN=your-huggingface-token
CORS_ORIGINS=https://your-frontend-domain.com
```

## 📊 Sample Data

The system comes pre-loaded with:
- **4 Departments** with realistic course offerings
- **8 Sample Courses** (2 per department)
- **24+ Resources** (PDFs, text, videos)
- **8 Quizzes** with sample questions
- **17 Sample Users** (admin, instructors, students)
- **Progress Tracking** and **Quiz Submissions**

## 🔧 Configuration

Key environment variables in `.env`:
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
MYSQL_HOST=your-mysql-host
MYSQL_DB=aru_academy
HF_API_TOKEN=your-huggingface-token
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request



**ARU Academy** - Empowering Education with AI Technology 🚀
