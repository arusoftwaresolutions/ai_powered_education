/**
 * Configuration file for ARU Academy Frontend
 * Update the BACKEND_URL to match your actual Render deployment URL
 */

const CONFIG = {
    // Update this URL to match your actual Render deployment
    BACKEND_URL: 'https://aru-academy-backend.onrender.com',
    
    // Local development URL (automatically used when running on localhost)
    LOCAL_BACKEND_URL: 'http://localhost:8000',
    
    // API endpoints
    API_ENDPOINTS: {
        AUTH: {
            LOGIN: '/api/auth/login',
            REGISTER: '/api/auth/register',
            LOGOUT: '/api/auth/logout',
            PROFILE: '/api/auth/profile',
            CHECK_AUTH: '/api/auth/check-auth'
        },
        COURSES: {
            LIST: '/api/courses',
            CREATE: '/api/courses',
            DETAIL: '/api/courses'
        },
        RESOURCES: {
            LIST: '/api/resources',
            UPLOAD: '/api/resources'
        },
        QUIZZES: {
            LIST: '/api/quizzes',
            SUBMIT: '/api/quizzes/submit'
        },
        AI: {
            ASK: '/api/ai/ask',
            GENERATE_QUESTIONS: '/api/ai/generate-questions'
        },
        ADMIN: {
            USERS: '/api/admin/users',
            APPROVE: '/api/admin/users/approve',
            ANALYTICS: '/api/admin/analytics'
        },
        HEALTH: {
            CHECK: '/api/health',
            SEED_DATABASE: '/api/seed-database'
        }
    },
    
    // Application settings
    APP: {
        NAME: 'ARU Academy',
        VERSION: '1.0.0',
        DESCRIPTION: 'AI-Powered E-Learning Platform'
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
}
