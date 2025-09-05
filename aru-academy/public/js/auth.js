/**
 * Authentication Service for ARU Academy
 * Handles user authentication, session management, and user-related operations
 */

class AuthService {
    constructor() {
        this.baseURL = window.location.hostname === 'localhost' 
            ? 'http://localhost:8000' 
            : 'https://aru-academy-backend.onrender.com';
        this.currentUser = null;
        this.isAuthenticated = false;
        
        // Check for existing session on initialization
        this.checkExistingSession();
    }

    /**
     * Check if user is already authenticated
     */
    checkExistingSession() {
        const user = localStorage.getItem('user');
        const token = localStorage.getItem('token');
        
        if (user && token) {
            try {
                this.currentUser = JSON.parse(user);
                this.isAuthenticated = true;
                // Skip automatic token validation to prevent redirect loops
                // this.validateToken();
            } catch (error) {
                console.error('Error parsing stored user data:', error);
                this.clearSession();
            }
        }
    }

    /**
     * Validate stored token with backend
     */
    async validateToken() {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/check-auth`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('Token validation failed');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.message || 'Token validation failed');
            }

            // Update user data if needed
            if (data.data && data.data.user) {
                this.currentUser = data.data.user;
                localStorage.setItem('user', JSON.stringify(data.data.user));
            }

        } catch (error) {
            console.error('Token validation error:', error);
            this.clearSession();
            this.redirectToLogin();
        }
    }

    /**
     * User login
     */
    async login(email, password, rememberMe = false) {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email,
                    password,
                    remember_me: rememberMe
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Store user data and token
                this.currentUser = data.data.user;
                this.isAuthenticated = true;
                
                localStorage.setItem('user', JSON.stringify(data.data.user));
                localStorage.setItem('token', data.data.access_token);
                
                // Store remember me preference
                if (rememberMe) {
                    localStorage.setItem('rememberMe', 'true');
                } else {
                    localStorage.removeItem('rememberMe');
                }

                return {
                    success: true,
                    user: data.data.user,
                    message: 'Login successful'
                };
            } else {
                return {
                    success: false,
                    message: data.message || 'Login failed'
                };
            }
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                message: 'An error occurred during login'
            };
        }
    }

    /**
     * User registration
     */
    async register(userData) {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                return {
                    success: true,
                    message: data.message || 'Registration successful'
                };
            } else {
                return {
                    success: false,
                    message: data.message || 'Registration failed'
                };
            }
        } catch (error) {
            console.error('Registration error:', error);
            return {
                success: false,
                message: 'An error occurred during registration'
            };
        }
    }

    /**
     * User logout
     */
    async logout() {
        try {
            // Call logout endpoint
            await fetch(`${this.baseURL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
        } catch (error) {
            console.error('Logout API error:', error);
        } finally {
            // Clear local session regardless of API response
            this.clearSession();
        }
    }

    /**
     * Get current user profile
     */
    async getProfile() {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/profile`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                return {
                    success: true,
                    data: data.data
                };
            } else {
                return {
                    success: false,
                    message: data.message || 'Failed to load profile'
                };
            }
        } catch (error) {
            console.error('Profile fetch error:', error);
            return {
                success: false,
                message: 'An error occurred while loading profile'
            };
        }
    }

    /**
     * Update user profile
     */
    async updateProfile(profileData) {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(profileData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Update local user data
                if (data.data && data.data.user) {
                    this.currentUser = data.data.user;
                    localStorage.setItem('user', JSON.stringify(data.data.user));
                }

                return {
                    success: true,
                    data: data.data,
                    message: 'Profile updated successfully'
                };
            } else {
                return {
                    success: false,
                    message: data.message || 'Failed to update profile'
                };
            }
        } catch (error) {
            console.error('Profile update error:', error);
            return {
                success: false,
                message: 'An error occurred while updating profile'
            };
        }
    }

    /**
     * Change user password
     */
    async changePassword(currentPassword, newPassword) {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/change-password`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                return {
                    success: true,
                    message: 'Password changed successfully'
                };
            } else {
                return {
                    success: false,
                    message: data.message || 'Failed to change password'
                };
            }
        } catch (error) {
            console.error('Password change error:', error);
            return {
                success: false,
                message: 'An error occurred while changing password'
            };
        }
    }

    /**
     * Check if user has specific role
     */
    hasRole(role) {
        return this.currentUser && this.currentUser.role === role;
    }

    /**
     * Check if user has any of the specified roles
     */
    hasAnyRole(roles) {
        return this.currentUser && roles.includes(this.currentUser.role);
    }

    /**
     * Check if user is admin
     */
    isAdmin() {
        return this.hasRole('Admin');
    }

    /**
     * Check if user is instructor
     */
    isInstructor() {
        return this.hasRole('Instructor');
    }

    /**
     * Check if user is student
     */
    isStudent() {
        return this.hasRole('Student');
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Get authentication status
     */
    getAuthStatus() {
        return this.isAuthenticated;
    }

    /**
     * Clear user session
     */
    clearSession() {
        this.currentUser = null;
        this.isAuthenticated = false;
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        localStorage.removeItem('rememberMe');
    }

    /**
     * Redirect to login page
     */
    redirectToLogin() {
        if (window.location.pathname !== '/login.html' && window.location.pathname !== '/') {
            window.location.href = '/login.html';
        }
    }

    /**
     * Redirect to dashboard
     */
    redirectToDashboard() {
        window.location.href = '/dashboard.html';
    }

    /**
     * Handle authentication errors
     */
    handleAuthError(error) {
        if (error.status === 401) {
            this.clearSession();
            this.redirectToLogin();
        }
    }
}

// Initialize authentication service
const authService = new AuthService();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthService;
}
