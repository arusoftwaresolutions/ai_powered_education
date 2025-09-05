/**
 * API Service for ARU Academy
 * Handles all HTTP requests to the backend with authentication and error handling
 */

class ApiService {
    constructor() {
        this.baseURL = window.location.hostname === 'localhost' 
            ? 'http://localhost:8000' 
            : 'https://aru-academy-backend.onrender.com';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    /**
     * Get authentication token from localStorage
     */
    getAuthToken() {
        return localStorage.getItem('token');
    }

    /**
     * Get user data from localStorage
     */
    getUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }

    /**
     * Set default headers including authentication
     */
    getHeaders(additionalHeaders = {}) {
        const token = this.getAuthToken();
        const headers = { ...this.defaultHeaders, ...additionalHeaders };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
            console.log('API: Sending request with token:', token.substring(0, 20) + '...');
        } else {
            console.log('API: No token found in localStorage');
        }
        
        return headers;
    }

    /**
     * Handle API response and common errors
     */
    async handleResponse(response) {
        console.log('API: Response status:', response.status);
        if (response.status === 401) {
            console.log('API: 401 Unauthorized response');
            // Unauthorized - let calling code handle the redirect
            throw new Error('Authentication required');
        }

        if (response.status === 403) {
            throw new Error('Access denied');
        }

        if (response.status === 404) {
            throw new Error('Resource not found');
        }

        if (response.status >= 500) {
            throw new Error('Server error');
        }

        try {
            const data = await response.json();
            return {
                success: response.ok,
                data: data.data || data,
                message: data.message || '',
                total: data.total,
                ...data
            };
        } catch (error) {
            throw new Error('Invalid response format');
        }
    }

    /**
     * Make GET request
     */
    async get(endpoint, params = {}) {
        try {
            const url = new URL(this.baseURL + endpoint);
            
            // Add query parameters
            Object.keys(params).forEach(key => {
                if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
                    url.searchParams.append(key, params[key]);
                }
            });

            const response = await fetch(url, {
                method: 'GET',
                headers: this.getHeaders()
            });

            return await this.handleResponse(response);
        } catch (error) {
            console.error('GET request error:', error);
            return {
                success: false,
                message: error.message || 'Request failed'
            };
        }
    }

    /**
     * Make POST request
     */
    async post(endpoint, data = {}, options = {}) {
        try {
            let body = data;
            let headers = this.getHeaders();

            // Handle FormData (file uploads)
            if (data instanceof FormData) {
                // Don't set Content-Type for FormData, let browser set it with boundary
                delete headers['Content-Type'];
            } else if (typeof data === 'object') {
                body = JSON.stringify(data);
            }

            // Merge custom headers
            if (options.headers) {
                headers = { ...headers, ...options.headers };
            }

            const response = await fetch(this.baseURL + endpoint, {
                method: 'POST',
                headers,
                body
            });

            return await this.handleResponse(response);
        } catch (error) {
            console.error('POST request error:', error);
            return {
                success: false,
                message: error.message || 'Request failed'
            };
        }
    }

    /**
     * Make PUT request
     */
    async put(endpoint, data = {}) {
        try {
            const response = await fetch(this.baseURL + endpoint, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify(data)
            });

            return await this.handleResponse(response);
        } catch (error) {
            console.error('PUT request error:', error);
            return {
                success: false,
                message: error.message || 'Request failed'
            };
        }
    }

    /**
     * Make DELETE request
     */
    async delete(endpoint) {
        try {
            const response = await fetch(this.baseURL + endpoint, {
                method: 'DELETE',
                headers: this.getHeaders()
            });

            return await this.handleResponse(response);
        } catch (error) {
            console.error('DELETE request error:', error);
            return {
                success: false,
                message: error.message || 'Request failed'
            };
        }
    }

    /**
     * Upload file with progress tracking
     */
    async uploadFile(endpoint, formData, onProgress = null) {
        try {
            const xhr = new XMLHttpRequest();
            
            return new Promise((resolve, reject) => {
                xhr.upload.addEventListener('progress', (event) => {
                    if (event.lengthComputable && onProgress) {
                        const percentComplete = (event.loaded / event.total) * 100;
                        onProgress(percentComplete);
                    }
                });

                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            resolve({
                                success: true,
                                data: response.data || response,
                                message: response.message || '',
                                ...response
                            });
                        } catch (error) {
                            resolve({
                                success: true,
                                data: xhr.responseText,
                                message: 'File uploaded successfully'
                            });
                        }
                    } else {
                        reject(new Error(`Upload failed with status ${xhr.status}`));
                    }
                });

                xhr.addEventListener('error', () => {
                    reject(new Error('Upload failed'));
                });

                xhr.addEventListener('abort', () => {
                    reject(new Error('Upload aborted'));
                });

                xhr.open('POST', this.baseURL + endpoint);
                
                // Add authentication header
                const token = this.getAuthToken();
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }

                xhr.send(formData);
            });
        } catch (error) {
            console.error('File upload error:', error);
            return {
                success: false,
                message: error.message || 'Upload failed'
            };
        }
    }

    /**
     * Download file
     */
    async downloadFile(endpoint, filename = null) {
        try {
            const response = await fetch(this.baseURL + endpoint, {
                method: 'GET',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`Download failed with status ${response.status}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename || 'download';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            return {
                success: true,
                message: 'File downloaded successfully'
            };
        } catch (error) {
            console.error('File download error:', error);
            return {
                success: false,
                message: error.message || 'Download failed'
            };
        }
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getAuthToken();
    }

    /**
     * Check if user has specific role
     */
    hasRole(role) {
        const user = this.getUser();
        return user && user.role === role;
    }

    /**
     * Check if user has any of the specified roles
     */
    hasAnyRole(roles) {
        const user = this.getUser();
        return user && roles.includes(user.role);
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
     * Refresh authentication token
     */
    async refreshToken() {
        try {
            const response = await fetch(this.baseURL + '/api/auth/refresh', {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.data.access_token) {
                    localStorage.setItem('token', data.data.access_token);
                    return true;
                }
            }
            return false;
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }

    /**
     * Handle authentication errors
     */
    handleAuthError(error) {
        if (error.status === 401) {
            console.log('API: 401 error, clearing localStorage and redirecting');
            // Clear invalid token
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            
            // Redirect to login if not already there
            if (window.location.pathname !== '/login.html' && window.location.pathname !== '/') {
                console.log('API: Redirecting to login due to 401 error');
                window.location.href = 'login.html';
            }
        }
    }

    /**
     * Make authenticated request with automatic token refresh
     */
    async authenticatedRequest(method, endpoint, data = null, options = {}) {
        try {
            // First attempt with current token
            let response;
            switch (method.toLowerCase()) {
                case 'get':
                    response = await this.get(endpoint, data);
                    break;
                case 'post':
                    response = await this.post(endpoint, data, options);
                    break;
                case 'put':
                    response = await this.put(endpoint, data);
                    break;
                case 'delete':
                    response = await this.delete(endpoint);
                    break;
                default:
                    throw new Error(`Unsupported HTTP method: ${method}`);
            }

            // If unauthorized, try to refresh token and retry once
            if (!response.success && response.message === 'Authentication required') {
                const tokenRefreshed = await this.refreshToken();
                if (tokenRefreshed) {
                    // Retry the request with new token
                    switch (method.toLowerCase()) {
                        case 'get':
                            response = await this.get(endpoint, data);
                            break;
                        case 'post':
                            response = await this.post(endpoint, data, options);
                            break;
                        case 'put':
                            response = await this.put(endpoint, data);
                            break;
                        case 'delete':
                            response = await this.delete(endpoint);
                            break;
                    }
                }
            }

            return response;
        } catch (error) {
            console.error('Authenticated request error:', error);
            return {
                success: false,
                message: error.message || 'Request failed'
            };
        }
    }

    /**
     * Batch multiple requests
     */
    async batch(requests) {
        try {
            const responses = await Promise.all(requests);
            return {
                success: true,
                data: responses,
                message: 'Batch request completed'
            };
        } catch (error) {
            console.error('Batch request error:', error);
            return {
                success: false,
                message: error.message || 'Batch request failed'
            };
        }
    }

    /**
     * Retry request with exponential backoff
     */
    async retryRequest(requestFn, maxRetries = 3, baseDelay = 1000) {
        let lastError;
        
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                return await requestFn();
            } catch (error) {
                lastError = error;
                
                if (attempt === maxRetries) {
                    break;
                }
                
                // Wait before retrying with exponential backoff
                const delay = baseDelay * Math.pow(2, attempt);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        
        throw lastError;
    }
}

// Initialize API service
const api = new ApiService();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiService;
}
