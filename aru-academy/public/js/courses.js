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
            let department = document.getElementById('departmentFilter')?.value || '';
            const status = document.getElementById('statusFilter')?.value || '';

            // Auto-filter by user's department if coming from dashboard
            if (!department) {
                const user = JSON.parse(localStorage.getItem('user') || '{}');
                if (user.department_id) {
                    department = user.department_id;
                    // Set the department filter dropdown
                    const departmentFilter = document.getElementById('departmentFilter');
                    if (departmentFilter) {
                        departmentFilter.value = department;
                    }
                }
            }

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
                    <button class="btn btn-primary" onclick="coursesService.openCourseContent(${course.id})">📚 Open Course</button>
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

        // Add View Resources button for all users
        const viewResourcesBtn = `<button class="btn btn-secondary btn-sm" onclick="coursesService.viewCourseResources(${course.id})">📁 Browse Resources</button>`;

        if (userRole === 'Instructor' || userRole === 'Admin') {
            return `
                ${viewResourcesBtn}
                <a href="course_detail.html?id=${course.id}" class="btn btn-outline btn-sm">Course Detail</a>
                <button class="btn btn-outline btn-sm" onclick="coursesService.editCourse(${course.id})">Edit</button>
                <button class="btn btn-outline btn-sm" onclick="coursesService.manageResources(${course.id})">Manage</button>
            `;
        }

        if (userRole === 'Student') {
            const statusBadge = course.progress === 100 ? 
                '<span class="badge badge-success">Completed</span>' :
                course.progress > 0 ? 
                '<span class="badge badge-warning">In Progress</span>' :
                '<span class="badge badge-info">Not Started</span>';
            
            return `
                ${viewResourcesBtn}
                ${statusBadge}
            `;
        }

        return viewResourcesBtn;
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
     * Open course content directly
     */
    async openCourseContent(courseId) {
        try {
            showLoading();
            
            // Fetch course details and resources
            const [courseResponse, resourcesResponse] = await Promise.all([
                api.get(`/api/courses/${courseId}`),
                api.get(`/api/resources/?course_id=${courseId}`)
            ]);

            if (!courseResponse.success) {
                showAlert('Failed to load course details', 'error');
                return;
            }

            const course = courseResponse.course || courseResponse.data;
            const resources = resourcesResponse.success ? (resourcesResponse.resources || resourcesResponse.data || []) : [];

            // If there are resources, open the first one or show resource list
            if (resources.length > 0) {
                // Open the first resource in file viewer
                const firstResource = resources[0];
                this.openResource(firstResource.id, firstResource.type, firstResource.file_path_or_url || '', firstResource.title);
            } else {
                // Show course info modal if no resources
                this.showCourseInfoModal(course);
            }
            
        } catch (error) {
            console.error('Error loading course content:', error);
            showAlert('An error occurred while loading course content', 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Show course info modal when no resources are available
     */
    showCourseInfoModal(course) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>📚 ${course.title}</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="course-info" style="margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                        <p><strong>Description:</strong> ${course.description || 'No description available'}</p>
                        <p><strong>Department:</strong> ${course.department_name || 'N/A'}</p>
                        <p><strong>Instructor:</strong> ${course.instructor_name || 'N/A'}</p>
                    </div>
                    
                    <div class="empty-state" style="text-align: center; padding: 2rem; color: #666;">
                        <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;">📚</div>
                        <h4>No Resources Available</h4>
                        <p>This course doesn't have any resources yet.</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    /**
     * View course resources in a modal
     */
    async viewCourseResources(courseId) {
        try {
            showLoading();
            
            // Fetch course details and resources
            const [courseResponse, resourcesResponse] = await Promise.all([
                api.get(`/api/courses/${courseId}`),
                api.get(`/api/resources/?course_id=${courseId}`)
            ]);

            if (!courseResponse.success) {
                showAlert('Failed to load course details', 'error');
                return;
            }

            const course = courseResponse.course || courseResponse.data;
            const resources = resourcesResponse.success ? (resourcesResponse.resources || resourcesResponse.data || []) : [];

            // Create and show resources modal
            this.showResourcesModal(course, resources);
            
        } catch (error) {
            console.error('Error loading course resources:', error);
            showAlert('An error occurred while loading course resources', 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Show resources modal
     */
    showResourcesModal(course, resources) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 800px; max-height: 90vh;">
                <div class="modal-header">
                    <h3>📚 ${course.title} - Resources</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="course-info" style="margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                        <p><strong>Description:</strong> ${course.description || 'No description available'}</p>
                        <p><strong>Department:</strong> ${course.department_name || 'N/A'}</p>
                        <p><strong>Instructor:</strong> ${course.instructor_name || 'N/A'}</p>
                    </div>
                    
                    <div class="resources-section">
                        <h4>📁 Course Resources (${resources.length})</h4>
                        ${this.createResourcesList(resources)}
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    /**
     * Create resources list HTML
     */
    createResourcesList(resources) {
        if (!resources || resources.length === 0) {
            return `
                <div class="empty-state" style="text-align: center; padding: 2rem; color: #666;">
                    <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;">📄</div>
                    <h4>No Resources Available</h4>
                    <p>This course doesn't have any resources yet.</p>
                </div>
            `;
        }

        return `
            <div class="resources-grid" style="display: grid; gap: 1rem; margin-top: 1rem;">
                ${resources.map(resource => this.createResourceCard(resource)).join('')}
            </div>
        `;
    }

    /**
     * Create resource card HTML
     */
    createResourceCard(resource) {
        const typeIcon = this.getResourceTypeIcon(resource.type);
        const typeColor = this.getResourceTypeColor(resource.type);
        
        return `
            <div class="resource-card" style="border: 1px solid #e1e5e9; border-radius: 8px; padding: 1rem; background: white;">
                <div class="resource-header" style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span class="resource-icon" style="font-size: 1.5rem; margin-right: 0.5rem;">${typeIcon}</span>
                    <h5 style="margin: 0; flex: 1;">${resource.title}</h5>
                    <span class="resource-type-badge" style="background: ${typeColor}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
                        ${resource.type}
                    </span>
                </div>
                <div class="resource-content">
                    ${resource.description ? `<p style="margin: 0.5rem 0; color: #666; font-size: 0.9rem;">${resource.description}</p>` : ''}
                    <div class="resource-actions" style="margin-top: 1rem;">
                        <button class="btn btn-primary btn-sm" onclick="coursesService.openResource(${resource.id}, '${resource.type}', '${resource.file_path_or_url || ''}', '${resource.title}')">
                            👁️ View Resource
                        </button>
                        ${resource.file_path_or_url ? `
                            <button class="btn btn-outline btn-sm" onclick="coursesService.downloadResource('${resource.file_path_or_url}', '${resource.title}')">
                                ⬇️ Download
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Get resource type icon
     */
    getResourceTypeIcon(type) {
        const icons = {
            'PDF': '📄',
            'TEXT': '📝',
            'VIDEO': '🎥',
            'LINK': '🔗',
            'DOCUMENT': '📋',
            'IMAGE': '🖼️'
        };
        return icons[type] || '📄';
    }

    /**
     * Get resource type color
     */
    getResourceTypeColor(type) {
        const colors = {
            'PDF': '#dc3545',
            'TEXT': '#28a745',
            'VIDEO': '#007bff',
            'LINK': '#6f42c1',
            'DOCUMENT': '#fd7e14',
            'IMAGE': '#20c997'
        };
        return colors[type] || '#6c757d';
    }

    /**
     * Open resource for viewing
     */
    openResource(resourceId, resourceType, filePath, resourceTitle) {
        if (!filePath) {
            showAlert('No file path available for this resource', 'error');
            return;
        }

        // Open resource in file viewer
        const viewerUrl = `file-viewer.html?resource_id=${resourceId}&type=${resourceType}&file=${encodeURIComponent(filePath)}&title=${encodeURIComponent(resourceTitle)}`;
        window.open(viewerUrl, '_blank');
    }

    /**
     * Download resource
     */
    downloadResource(filePath, fileName) {
        if (!filePath) {
            showAlert('No file available for download', 'error');
            return;
        }

        // Create download link
        const link = document.createElement('a');
        link.href = filePath;
        link.download = fileName || 'resource';
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
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
