/**
 * Courses Service for ARU Academy
 * Handles course management, resource uploads, and course-related operations
 */

class CoursesService {
    constructor() {
        this.currentPage = 1;
        this.itemsPerPage = 12;
        this.currentFilters = {};
        this.initializeEventListeners();
    }

    /**
     * Initialize event listeners for course-related functionality
     */
    initializeEventListeners() {
        // Create course modal
        const createCourseBtn = document.getElementById('createCourseBtn');
        if (createCourseBtn) {
            createCourseBtn.addEventListener('click', () => this.showCreateCourseModal());
        }

        // Upload resource modal
        const uploadResourceBtn = document.getElementById('uploadResourceBtn');
        if (uploadResourceBtn) {
            uploadResourceBtn.addEventListener('click', () => this.showUploadResourceModal());
        }

        // Modal close buttons
        const closeCreateModal = document.getElementById('closeCreateModal');
        if (closeCreateModal) {
            closeCreateModal.addEventListener('click', () => this.hideCreateCourseModal());
        }

        const closeUploadModal = document.getElementById('closeUploadModal');
        if (closeUploadModal) {
            closeUploadModal.addEventListener('click', () => this.hideUploadResourceModal());
        }

        // Cancel buttons
        const cancelCreate = document.getElementById('cancelCreate');
        if (cancelCreate) {
            cancelCreate.addEventListener('click', () => this.hideCreateCourseModal());
        }

        const cancelUpload = document.getElementById('cancelUpload');
        if (cancelUpload) {
            cancelUpload.addEventListener('click', () => this.hideUploadResourceModal());
        }

        // Form submissions
        const createCourseForm = document.getElementById('createCourseForm');
        if (createCourseForm) {
            createCourseForm.addEventListener('submit', (e) => this.handleCreateCourse(e));
        }

        const uploadResourceForm = document.getElementById('uploadResourceForm');
        if (uploadResourceForm) {
            uploadResourceForm.addEventListener('submit', (e) => this.handleUploadResource(e));
        }

        // Resource type change handler
        const resourceType = document.getElementById('resourceType');
        if (resourceType) {
            resourceType.addEventListener('change', (e) => this.handleResourceTypeChange(e));
        }

        // Search and filter handlers
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.loadCourses(), 300));
        }

        const departmentFilter = document.getElementById('departmentFilter');
        if (departmentFilter) {
            departmentFilter.addEventListener('change', () => this.loadCourses());
        }

        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.loadCourses());
        }

        // Pagination handlers
        const prevPage = document.getElementById('prevPage');
        if (prevPage) {
            prevPage.addEventListener('click', () => this.previousPage());
        }

        const nextPage = document.getElementById('nextPage');
        if (nextPage) {
            nextPage.addEventListener('click', () => this.nextPage());
        }
    }

    /**
     * Load courses with current filters and pagination
     */
    async loadCourses() {
        try {
            const coursesGrid = document.getElementById('coursesGrid');
            if (!coursesGrid) return;

            coursesGrid.innerHTML = '<div class="loading-spinner">Loading courses...</div>';

            // Get current filter values
            const search = document.getElementById('searchInput')?.value || '';
            const department = document.getElementById('departmentFilter')?.value || '';
            const status = document.getElementById('statusFilter')?.value || '';

            // Build query parameters
            const params = new URLSearchParams();
            if (search) params.append('search', search);
            if (department) params.append('department_id', department);
            if (status) params.append('status', status);
            params.append('page', this.currentPage);
            params.append('per_page', this.itemsPerPage);

            const response = await api.get(`/api/courses/?${params.toString()}`);

            if (response.success) {
                this.displayCourses(response.data);
                this.updatePagination(response.total || response.data.length);
            } else {
                coursesGrid.innerHTML = '<p class="text-muted">Error loading courses</p>';
            }
        } catch (error) {
            console.error('Error loading courses:', error);
            const coursesGrid = document.getElementById('coursesGrid');
            if (coursesGrid) {
                coursesGrid.innerHTML = '<p class="text-muted">Error loading courses</p>';
            }
        }
    }

    /**
     * Display courses in the grid
     */
    displayCourses(courses) {
        const coursesGrid = document.getElementById('coursesGrid');
        if (!coursesGrid) return;

        if (!courses || courses.length === 0) {
            coursesGrid.innerHTML = '<p class="text-muted">No courses found matching your criteria</p>';
            return;
        }

        const coursesHTML = courses.map(course => this.createCourseCard(course)).join('');
        coursesGrid.innerHTML = coursesHTML;
    }

    /**
     * Create HTML for a course card
     */
    createCourseCard(course) {
        const progressPercentage = course.progress || 0;
        const progressClass = progressPercentage === 100 ? 'completed' : 
                             progressPercentage > 0 ? 'in-progress' : 'not-started';

        return `
            <div class="course-card">
                <div class="course-header">
                    <h3>${course.title}</h3>
                    <span class="course-department">${course.department_name || 'N/A'}</span>
                </div>
                <div class="course-content">
                    <p>${course.description || 'No description available'}</p>
                    <div class="course-meta">
                        <span class="meta-item">
                            <strong>Instructor:</strong> ${course.instructor_name || 'N/A'}
                        </span>
                        <span class="meta-item">
                            <strong>Resources:</strong> ${course.resource_count || 0}
                        </span>
                        <span class="meta-item">
                            <strong>Quizzes:</strong> ${course.quiz_count || 0}
                        </span>
                    </div>
                </div>
                <div class="course-progress">
                    <div class="progress-bar">
                        <div class="progress-fill ${progressClass}" style="width: ${progressPercentage}%"></div>
                    </div>
                    <span class="progress-text">${progressPercentage}% Complete</span>
                </div>
                <div class="course-actions">
                    <a href="course_detail.html?id=${course.id}" class="btn btn-primary">View Course</a>
                    ${this.getCourseActionButtons(course)}
                </div>
            </div>
        `;
    }

    /**
     * Get additional action buttons based on user role and course status
     */
    getCourseActionButtons(course) {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const userRole = user.role;

        if (userRole === 'Instructor' || userRole === 'Admin') {
            return `
                <button class="btn btn-outline btn-sm" onclick="coursesService.editCourse(${course.id})">Edit</button>
                <button class="btn btn-outline btn-sm" onclick="coursesService.manageResources(${course.id})">Resources</button>
            `;
        }

        if (userRole === 'Student') {
            if (course.progress === 100) {
                return '<span class="badge badge-success">Completed</span>';
            } else if (course.progress > 0) {
                return '<span class="badge badge-warning">In Progress</span>';
            } else {
                return '<span class="badge badge-info">Not Started</span>';
            }
        }

        return '';
    }

    /**
     * Update pagination controls
     */
    updatePagination(totalItems) {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        const totalPages = Math.ceil(totalItems / this.itemsPerPage);
        
        if (totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';
        
        const pageInfo = document.getElementById('pageInfo');
        if (pageInfo) {
            pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
        }

        const prevPage = document.getElementById('prevPage');
        const nextPage = document.getElementById('nextPage');
        
        if (prevPage) {
            prevPage.disabled = this.currentPage === 1;
        }
        
        if (nextPage) {
            nextPage.disabled = this.currentPage === totalPages;
        }
    }

    /**
     * Go to previous page
     */
    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadCourses();
        }
    }

    /**
     * Go to next page
     */
    nextPage() {
        this.currentPage++;
        this.loadCourses();
    }

    /**
     * Show create course modal
     */
    showCreateCourseModal() {
        const modal = document.getElementById('createCourseModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.classList.add('modal-open');
        }
    }

    /**
     * Hide create course modal
     */
    hideCreateCourseModal() {
        const modal = document.getElementById('createCourseModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
    }

    /**
     * Show upload resource modal
     */
    showUploadResourceModal() {
        const modal = document.getElementById('uploadResourceModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.classList.add('modal-open');
            this.loadUserCourses();
        }
    }

    /**
     * Hide upload resource modal
     */
    hideUploadResourceModal() {
        const modal = document.getElementById('uploadResourceModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
    }

    /**
     * Handle create course form submission
     */
    async handleCreateCourse(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const courseData = {
            title: formData.get('title'),
            description: formData.get('description'),
            department_id: parseInt(formData.get('department_id')),
            topic: formData.get('topic') || null,
            difficulty: formData.get('difficulty') || 'intermediate'
        };

        console.log('Creating course with data:', courseData);

        try {
            showLoading();
            
            const response = await api.post('/api/courses/', courseData);
            console.log('Course creation response:', response);

            if (response.success) {
                showAlert('Course created successfully!', 'success');
                this.hideCreateCourseModal();
                e.target.reset();
                this.loadCourses();
            } else {
                showAlert(response.message || 'Failed to create course', 'error');
            }
        } catch (error) {
            console.error('Error creating course:', error);
            showAlert(`Error creating course: ${error.message || 'Please try again.'}`, 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Handle upload resource form submission
     */
    async handleUploadResource(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const resourceData = new FormData();
        
        // Add basic resource data
        resourceData.append('title', formData.get('title'));
        resourceData.append('description', formData.get('description'));
        resourceData.append('course_id', formData.get('course_id'));
        resourceData.append('type', formData.get('type'));

        console.log('Uploading resource with data:', {
            title: formData.get('title'),
            description: formData.get('description'),
            course_id: formData.get('course_id'),
            type: formData.get('type')
        });

        // Handle different resource types
        const resourceType = formData.get('type');
        
        if (resourceType === 'PDF' || resourceType === 'VIDEO') {
            const file = formData.get('file');
            if (file) {
                resourceData.append('file', file);
            }
        } else if (resourceType === 'TEXT') {
            resourceData.append('text_content', formData.get('text_content'));
        } else if (resourceType === 'LINK') {
            resourceData.append('file_path_or_url', formData.get('file_path_or_url'));
        }

        try {
            showLoading();
            
            const response = await api.post('/api/resources/', resourceData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            console.log('Resource upload response:', response);

            if (response.success) {
                showAlert('Resource uploaded successfully!', 'success');
                this.hideUploadResourceModal();
                e.target.reset();
                this.loadCourses();
            } else {
                showAlert(response.message || 'Failed to upload resource', 'error');
            }
        } catch (error) {
            console.error('Error uploading resource:', error);
            showAlert('An error occurred while uploading the resource', 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Handle resource type change
     */
    handleResourceTypeChange(e) {
        const resourceType = e.target.value;
        
        // Hide all input groups
        document.getElementById('fileUploadGroup').style.display = 'none';
        document.getElementById('textContentGroup').style.display = 'none';
        document.getElementById('linkGroup').style.display = 'none';
        
        // Show appropriate input group
        if (resourceType === 'PDF' || resourceType === 'VIDEO') {
            document.getElementById('fileUploadGroup').style.display = 'block';
        } else if (resourceType === 'TEXT') {
            document.getElementById('textContentGroup').style.display = 'block';
        } else if (resourceType === 'LINK') {
            document.getElementById('linkGroup').style.display = 'block';
        }
    }

    /**
     * Load user's courses for resource upload
     */
    async loadUserCourses() {
        try {
            const response = await api.get('/api/courses/');
            if (response.success) {
                this.populateCourseSelects(response.data);
            }
        } catch (error) {
            console.error('Error loading user courses:', error);
        }
    }

    /**
     * Populate course select dropdowns
     */
    populateCourseSelects(courses) {
        const courseSelects = [
            'course_id', // in create course form
            'resourceCourse' // in upload resource form
        ];
        
        courseSelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = '<option value="">Select Course</option>';
                courses.forEach(course => {
                    const option = document.createElement('option');
                    option.value = course.id;
                    option.textContent = course.title;
                    select.appendChild(option);
                });
            }
        });
    }

    /**
     * Edit course
     */
    async editCourse(courseId) {
        try {
            const response = await api.get(`/api/courses/${courseId}`);
            if (response.success) {
                this.showEditCourseModal(response.data);
            } else {
                showAlert('Failed to load course details', 'error');
            }
        } catch (error) {
            console.error('Error loading course details:', error);
            showAlert('An error occurred while loading course details', 'error');
        }
    }

    /**
     * Show edit course modal
     */
    showEditCourseModal(course) {
        // This would show a modal with course editing form
        // For now, redirect to course detail page
        window.location.href = `course_detail.html?id=${course.id}&edit=true`;
    }

    /**
     * Manage course resources
     */
    manageResources(courseId) {
        window.location.href = `course_detail.html?id=${courseId}&tab=resources`;
    }

    /**
     * Search courses
     */
    searchCourses(query) {
        this.currentFilters.search = query;
        this.currentPage = 1;
        this.loadCourses();
    }

    /**
     * Filter courses by department
     */
    filterByDepartment(departmentId) {
        this.currentFilters.department_id = departmentId;
        this.currentPage = 1;
        this.loadCourses();
    }

    /**
     * Filter courses by status
     */
    filterByStatus(status) {
        this.currentFilters.status = status;
        this.currentPage = 1;
        this.loadCourses();
    }

    /**
     * Clear all filters
     */
    clearFilters() {
        this.currentFilters = {};
        this.currentPage = 1;
        
        // Reset form inputs
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.value = '';
        
        const departmentFilter = document.getElementById('departmentFilter');
        if (departmentFilter) departmentFilter.value = '';
        
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) statusFilter.value = '';
        
        this.loadCourses();
    }

    /**
     * Utility function for debouncing
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Initialize the courses page
     */
    initialize() {
        this.loadCourses();
        this.loadUserCourses();
    }
}

// Initialize courses service
const coursesService = new CoursesService();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CoursesService;
}
