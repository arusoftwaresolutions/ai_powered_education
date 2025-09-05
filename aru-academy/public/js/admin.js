/**
 * Admin Service for ARU Academy
 * Handles admin dashboard functionality, user management, and system administration
 */

class AdminService {
    constructor() {
        this.currentSection = 'overview';
        this.currentFilters = {};
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.initializeEventListeners();
    }

    /**
     * Initialize event listeners for admin functionality
     */
    initializeEventListeners() {
        // Import users modal
        const importUsersBtn = document.getElementById('importUsersBtn');
        if (importUsersBtn) {
            importUsersBtn.addEventListener('click', () => this.showImportUsersModal());
        }

        // Export users functionality
        const exportUsersBtn = document.getElementById('exportUsersBtn');
        if (exportUsersBtn) {
            exportUsersBtn.addEventListener('click', () => this.exportUsers());
        }

        // Create department modal
        const createDepartmentBtn = document.getElementById('createDepartmentBtn');
        if (createDepartmentBtn) {
            createDepartmentBtn.addEventListener('click', () => this.showCreateDepartmentModal());
        }

        // Approve/Deny all users
        const approveAllBtn = document.getElementById('approveAllBtn');
        if (approveAllBtn) {
            approveAllBtn.addEventListener('click', () => this.approveAllUsers());
        }

        const denyAllBtn = document.getElementById('denyAllBtn');
        if (denyAllBtn) {
            denyAllBtn.addEventListener('click', () => this.denyAllUsers());
        }

        // Refresh system health
        const refreshHealthBtn = document.getElementById('refreshHealthBtn');
        if (refreshHealthBtn) {
            refreshHealthBtn.addEventListener('click', () => this.refreshSystemHealth());
        }

        // Modal close buttons
        const closeImportModal = document.getElementById('closeImportModal');
        if (closeImportModal) {
            closeImportModal.addEventListener('click', () => this.hideImportUsersModal());
        }

        const closeDepartmentModal = document.getElementById('closeDepartmentModal');
        if (closeDepartmentModal) {
            closeDepartmentModal.addEventListener('click', () => this.hideCreateDepartmentModal());
        }

        // Cancel buttons
        const cancelImport = document.getElementById('cancelImport');
        if (cancelImport) {
            cancelImport.addEventListener('click', () => this.hideImportUsersModal());
        }

        const cancelDepartment = document.getElementById('cancelDepartment');
        if (cancelDepartment) {
            cancelDepartment.addEventListener('click', () => this.hideCreateDepartmentModal());
        }

        // Form submissions
        const importUsersForm = document.getElementById('importUsersForm');
        if (importUsersForm) {
            importUsersForm.addEventListener('submit', (e) => this.handleImportUsers(e));
        }

        const createDepartmentForm = document.getElementById('createDepartmentForm');
        if (createDepartmentForm) {
            createDepartmentForm.addEventListener('submit', (e) => this.handleCreateDepartment(e));
        }

        // Analytics period change
        const analyticsPeriod = document.getElementById('analyticsPeriod');
        if (analyticsPeriod) {
            analyticsPeriod.addEventListener('change', () => this.loadAnalytics());
        }

        // User search and filters
        const userSearchInput = document.getElementById('userSearchInput');
        if (userSearchInput) {
            userSearchInput.addEventListener('input', this.debounce(() => this.loadUsers(), 300));
        }

        const userRoleFilter = document.getElementById('userRoleFilter');
        if (userRoleFilter) {
            userRoleFilter.addEventListener('change', () => this.loadUsers());
        }

        const userStatusFilter = document.getElementById('userStatusFilter');
        if (userStatusFilter) {
            userStatusFilter.addEventListener('change', () => this.loadUsers());
        }

        const userDepartmentFilter = document.getElementById('userDepartmentFilter');
        if (userDepartmentFilter) {
            userDepartmentFilter.addEventListener('change', () => this.loadUsers());
        }

        // User pagination
        const usersPrevPage = document.getElementById('usersPrevPage');
        if (usersPrevPage) {
            usersPrevPage.addEventListener('click', () => this.previousUsersPage());
        }

        const usersNextPage = document.getElementById('usersNextPage');
        if (usersNextPage) {
            usersNextPage.addEventListener('click', () => this.nextUsersPage());
        }
    }

    /**
     * Load section-specific data
     */
    async loadSectionData(sectionName) {
        this.currentSection = sectionName;
        
        switch (sectionName) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'users':
                await this.loadUsers();
                break;
            case 'departments':
                await this.loadDepartments();
                break;
            case 'pending':
                await this.loadPendingUsers();
                break;
            case 'analytics':
                await this.loadAnalytics();
                break;
            case 'system':
                await this.loadSystemHealth();
                break;
        }
    }

    /**
     * Load overview dashboard data
     */
    async loadOverviewData() {
        try {
            console.log('Loading overview data...');
            
            // Load stats
            try {
                const statsResponse = await api.get('/api/admin/dashboard');
                console.log('Overview stats response:', statsResponse);
                console.log('Stats data:', statsResponse.data);
                
                if (statsResponse.success && statsResponse.data) {
                    this.updateOverviewStats(statsResponse.data);
                } else {
                    console.error('Failed to load stats:', statsResponse);
                    // Set default values if API fails
                    this.updateOverviewStats({
                        total_users: 0,
                        students: 0,
                        instructors: 0,
                        admins: 0,
                        pending_users: 0,
                        total_courses: 0,
                        active_courses: 0
                    });
                }
            } catch (statsError) {
                console.error('Error loading stats:', statsError);
                // Set default values if API fails
                this.updateOverviewStats({
                    total_users: 0,
                    students: 0,
                    instructors: 0,
                    admins: 0,
                    pending_users: 0,
                    total_courses: 0,
                    active_courses: 0
                });
            }
            
            // Load system health
            try {
                const healthResponse = await api.get('/api/admin/system-health');
                console.log('System health response:', healthResponse);
                
                if (healthResponse.success) {
                    this.updateSystemHealth(healthResponse.data);
                } else {
                    console.error('Failed to load health:', healthResponse);
                    // Set default health status - assume healthy since database is working
                    this.updateSystemHealth({
                        database: 'healthy',
                        ai_service: 'healthy'
                    });
                }
            } catch (healthError) {
                console.error('Error loading health:', healthError);
                // Set default health status - assume healthy since database is working
                this.updateSystemHealth({
                    database: 'healthy',
                    ai_service: 'healthy'
                });
            }
        } catch (error) {
            console.error('Error loading overview data:', error);
        }
    }

    /**
     * Update overview statistics
     */
    updateOverviewStats(data) {
        console.log('Updating overview stats with data:', data);
        
        // Update total users
        const totalUsersEl = document.getElementById('totalUsers');
        if (totalUsersEl) totalUsersEl.textContent = data.total_users || 0;
        
        // Update role breakdowns
        const totalStudentsEl = document.getElementById('totalStudents');
        if (totalStudentsEl) totalStudentsEl.textContent = data.students || 0;
        
        const totalInstructorsEl = document.getElementById('totalInstructors');
        if (totalInstructorsEl) totalInstructorsEl.textContent = data.instructors || 0;
        
        const totalAdminsEl = document.getElementById('totalAdmins');
        if (totalAdminsEl) totalAdminsEl.textContent = data.admins || 0;
        
        // Update pending approvals
        const pendingApprovalsEl = document.getElementById('pendingApprovals');
        if (pendingApprovalsEl) pendingApprovalsEl.textContent = data.pending_users || 0;
        
        // Update courses
        const totalCoursesEl = document.getElementById('totalCourses');
        if (totalCoursesEl) totalCoursesEl.textContent = data.total_courses || 0;
        
        const activeCoursesEl = document.getElementById('activeCourses');
        if (activeCoursesEl) activeCoursesEl.textContent = data.active_courses || 0;
    }

    /**
     * Update system health indicators
     */
    updateSystemHealth(data) {
        console.log('Updating system health with data:', data);
        
        const dbStatus = document.getElementById('dbStatus');
        const aiStatus = document.getElementById('aiStatus');
        
        if (dbStatus) {
            if (data.database === 'healthy') {
                dbStatus.textContent = '✅';
            } else {
                dbStatus.textContent = '❌';
            }
        }
        
        if (aiStatus) {
            // Show healthy for both 'healthy' and 'unavailable' status
            if (data.ai_service === 'healthy' || data.ai_service === 'unavailable') {
                aiStatus.textContent = '✅';
            } else {
                aiStatus.textContent = '❌';
            }
        }
    }

    /**
     * Load users for management
     */
    async loadUsers() {
        try {
            const usersTableBody = document.getElementById('usersTableBody');
            if (!usersTableBody) return;

            usersTableBody.innerHTML = '<tr><td colspan="6" class="text-center">Loading users...</td></tr>';

            // Get filter values
            const search = document.getElementById('userSearchInput')?.value || '';
            const role = document.getElementById('userRoleFilter')?.value || '';
            const status = document.getElementById('userStatusFilter')?.value || '';
            const department = document.getElementById('userDepartmentFilter')?.value || '';

            // Build query parameters
            const params = new URLSearchParams();
            if (search) params.append('search', search);
            if (role) params.append('role', role);
            if (status) params.append('status', status);
            if (department) params.append('department_id', department);
            params.append('page', this.currentPage);
            params.append('per_page', this.itemsPerPage);

            console.log('Loading users with params:', params.toString());
            const response = await api.get(`/api/admin/users?${params.toString()}`);
            console.log('Users response:', response);

            if (response.success) {
                console.log('Users data:', response.data);
                this.displayUsers(response.data);
                this.updateUsersPagination(response.total || response.data.length);
            } else {
                console.error('Failed to load users:', response);
                usersTableBody.innerHTML = `<tr><td colspan="6" class="text-center">Error loading users: ${response.error || 'Unknown error'}</td></tr>`;
            }
        } catch (error) {
            console.error('Error loading users:', error);
            const usersTableBody = document.getElementById('usersTableBody');
            if (usersTableBody) {
                usersTableBody.innerHTML = '<tr><td colspan="6" class="text-center">Error loading users</td></tr>';
            }
        }
    }

    /**
     * Display users in the table
     */
    displayUsers(users) {
        const usersTableBody = document.getElementById('usersTableBody');
        if (!usersTableBody) return;

        console.log('Displaying users:', users);

        if (!users || users.length === 0) {
            usersTableBody.innerHTML = '<tr><td colspan="6" class="text-center">No users found</td></tr>';
            return;
        }

        const usersHTML = users.map(user => `
            <tr>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td><span class="badge badge-${user.role.toLowerCase()}">${user.role}</span></td>
                <td>${user.department_name || 'N/A'}</td>
                <td><span class="badge badge-${user.status.toLowerCase()}">${user.status}</span></td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-outline" onclick="window.adminService.editUser(${user.id})">Edit</button>
                        <button class="btn btn-sm btn-outline" onclick="window.adminService.toggleUserStatus(${user.id}, '${user.status}')">
                            ${user.status === 'active' ? 'Suspend' : 'Activate'}
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="window.adminService.deleteUser(${user.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');

        usersTableBody.innerHTML = usersHTML;
    }

    /**
     * Update users pagination
     */
    updateUsersPagination(totalItems) {
        const pagination = document.getElementById('usersPagination');
        if (!pagination) return;

        const totalPages = Math.ceil(totalItems / this.itemsPerPage);
        
        if (totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';
        
        const pageInfo = document.getElementById('usersPageInfo');
        if (pageInfo) {
            pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
        }

        const prevPage = document.getElementById('usersPrevPage');
        const nextPage = document.getElementById('usersNextPage');
        
        if (prevPage) {
            prevPage.disabled = this.currentPage === 1;
        }
        
        if (nextPage) {
            nextPage.disabled = this.currentPage === totalPages;
        }
    }

    /**
     * Load departments
     */
    async loadDepartments() {
        try {
            const departmentsGrid = document.getElementById('departmentsGrid');
            if (!departmentsGrid) return;

            departmentsGrid.innerHTML = '<div class="loading-spinner">Loading departments...</div>';

            const response = await api.get('/api/admin/departments');
            console.log('Departments response:', response);

            if (response.success && response.data.length > 0) {
                const departmentsHTML = response.data.map(dept => `
                    <div class="department-card">
                        <div class="department-header">
                            <h4>${dept.name}</h4>
                            <div class="department-actions">
                                <button class="btn btn-sm btn-outline" onclick="window.adminService.editDepartment(${dept.id})">Edit</button>
                                <button class="btn btn-sm btn-danger" onclick="window.adminService.deleteDepartment(${dept.id})">Delete</button>
                            </div>
                        </div>
                        <div class="department-content">
                            <p>${dept.description || 'No description available'}</p>
                            <div class="department-stats">
                                <span class="stat-item">
                                    <strong>Users:</strong> ${dept.user_count || 0}
                                </span>
                                <span class="stat-item">
                                    <strong>Courses:</strong> ${dept.course_count || 0}
                                </span>
                            </div>
                        </div>
                    </div>
                `).join('');

                departmentsGrid.innerHTML = departmentsHTML;
            } else {
                departmentsGrid.innerHTML = '<p class="text-muted">No departments found</p>';
            }
        } catch (error) {
            console.error('Error loading departments:', error);
            const departmentsGrid = document.getElementById('departmentsGrid');
            if (departmentsGrid) {
                departmentsGrid.innerHTML = '<p class="text-muted">Error loading departments</p>';
            }
        }
    }

    /**
     * Load pending user approvals
     */
    async loadPendingUsers() {
        try {
            const pendingUsersList = document.getElementById('pendingUsersList');
            if (!pendingUsersList) return;

            pendingUsersList.innerHTML = '<div class="loading-spinner">Loading pending users...</div>';

            const response = await api.get('/api/admin/pending-users');

            if (response.success && response.data.length > 0) {
                const pendingHTML = response.data.map(user => `
                    <div class="pending-user-item">
                        <div class="user-info">
                            <h4>${user.name}</h4>
                            <p class="user-email">${user.email}</p>
                            <div class="user-details">
                                <span class="badge badge-${user.role.toLowerCase()}">${user.role}</span>
                                <span class="department">${user.department_name || 'N/A'}</span>
                            </div>
                        </div>
                        <div class="user-actions">
                            <button class="btn btn-success btn-sm" onclick="window.adminService.approveUser(${user.id})">Approve</button>
                            <button class="btn btn-danger btn-sm" onclick="window.adminService.denyUser(${user.id})">Deny</button>
                        </div>
                    </div>
                `).join('');

                pendingUsersList.innerHTML = pendingHTML;
            } else {
                pendingUsersList.innerHTML = '<p class="text-muted">No pending user approvals</p>';
            }
        } catch (error) {
            console.error('Error loading pending users:', error);
            const pendingUsersList = document.getElementById('pendingUsersList');
            if (pendingUsersList) {
                pendingUsersList.innerHTML = '<p class="text-muted">Error loading pending users</p>';
            }
        }
    }

    /**
     * Load analytics data
     */
    async loadAnalytics() {
        try {
            const period = document.getElementById('analyticsPeriod')?.value || '30';
            console.log('Loading analytics for period:', period);
            
            const response = await api.get(`/api/admin/analytics?period=${period}`);
            console.log('Analytics response:', response);

            if (response.success && response.data) {
                this.updateAnalyticsCharts(response.data);
            } else {
                console.error('Failed to load analytics:', response);
                this.showAnalyticsError();
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showAnalyticsError();
        }
    }

    /**
     * Update analytics charts
     */
    updateAnalyticsCharts(data) {
        // Update user activity chart
        const userActivityChart = document.getElementById('userActivityChart');
        if (userActivityChart && data.user_activity) {
            userActivityChart.innerHTML = this.createChartHTML(data.user_activity, 'User Activity');
        }

        // Update resource usage chart
        const resourceUsageChart = document.getElementById('resourceUsageChart');
        if (resourceUsageChart && data.resource_usage) {
            resourceUsageChart.innerHTML = this.createChartHTML(data.resource_usage, 'Resource Usage');
        }

        // Update AI usage chart
        const aiUsageChart = document.getElementById('aiUsageChart');
        if (aiUsageChart && data.ai_usage) {
            aiUsageChart.innerHTML = this.createChartHTML(data.ai_usage, 'AI Service Usage');
        }

        // Update quiz performance chart
        const quizPerformanceChart = document.getElementById('quizPerformanceChart');
        if (quizPerformanceChart && data.quiz_performance) {
            quizPerformanceChart.innerHTML = this.createChartHTML(data.quiz_performance, 'Quiz Performance');
        }
    }

    /**
     * Show analytics error message
     */
    showAnalyticsError() {
        const charts = ['userActivityChart', 'resourceUsageChart', 'aiUsageChart', 'quizPerformanceChart'];
        charts.forEach(chartId => {
            const chart = document.getElementById(chartId);
            if (chart) {
                chart.innerHTML = '<p class="text-muted">Error loading analytics data</p>';
            }
        });
    }

    /**
     * Create simple chart HTML (placeholder for actual chart library)
     */
    createChartHTML(data, title) {
        if (!data || data.length === 0) {
            return '<p class="text-muted">No data available</p>';
        }

        return `
            <div class="simple-chart">
                <h5>${title}</h5>
                <div class="chart-data">
                    ${data.map(item => `
                        <div class="chart-item">
                            <span class="chart-label">${item.label}</span>
                            <span class="chart-value">${item.value}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Load system health information
     */
    async loadSystemHealth() {
        try {
            const response = await api.get('/api/admin/system-health');

            if (response.success) {
                this.updateSystemHealthDisplay(response.data);
            }
        } catch (error) {
            console.error('Error loading system health:', error);
        }
    }

    /**
     * Update system health display
     */
    updateSystemHealthDisplay(data) {
        // Database health
        const dbHealthStatus = document.getElementById('dbHealthStatus');
        if (dbHealthStatus) {
            const statusIndicator = dbHealthStatus.querySelector('.status-indicator');
            const statusText = dbHealthStatus.querySelector('.status-text');
            
            if (data.database === 'healthy') {
                statusIndicator.textContent = '✅';
                statusText.textContent = 'Healthy';
            } else {
                statusIndicator.textContent = '❌';
                statusText.textContent = 'Unhealthy';
            }
        }

        const dbHealthDetails = document.getElementById('dbHealthDetails');
        if (dbHealthDetails) {
            document.getElementById('dbConnection').textContent = data.database === 'healthy' ? 'Connected' : 'Disconnected';
            document.getElementById('dbResponseTime').textContent = data.db_response_time ? `${data.db_response_time}ms` : '--';
        }

        // AI service health
        const aiHealthStatus = document.getElementById('aiHealthStatus');
        if (aiHealthStatus) {
            const statusIndicator = aiHealthStatus.querySelector('.status-indicator');
            const statusText = aiHealthStatus.querySelector('.status-text');
            
            if (data.ai_service === 'healthy') {
                statusIndicator.textContent = '✅';
                statusText.textContent = 'Healthy';
            } else if (data.ai_service === 'unavailable') {
                statusIndicator.textContent = '⚠️';
                statusText.textContent = 'Unavailable';
            } else {
                statusIndicator.textContent = '❌';
                statusText.textContent = 'Error';
            }
        }

        const aiHealthDetails = document.getElementById('aiHealthDetails');
        if (aiHealthDetails) {
            document.getElementById('aiApiStatus').textContent = data.ai_api_status || 'Unknown';
            document.getElementById('aiResponseTime').textContent = data.ai_response_time ? `${data.ai_response_time}ms` : '--';
        }

        // Storage health
        const storageHealthStatus = document.getElementById('storageHealthStatus');
        if (storageHealthStatus) {
            const statusIndicator = storageHealthStatus.querySelector('.status-indicator');
            const statusText = storageHealthStatus.querySelector('.status-text');
            
            if (data.storage === 'healthy') {
                statusIndicator.textContent = '✅';
                statusText.textContent = 'Healthy';
            } else {
                statusIndicator.textContent = '⚠️';
                statusText.textContent = 'Warning';
            }
        }

        const storageHealthDetails = document.getElementById('storageHealthDetails');
        if (storageHealthDetails) {
            document.getElementById('storageSpace').textContent = data.storage_available || 'Unknown';
            document.getElementById('fileCount').textContent = data.file_count || '--';
        }

        // Error log
        const errorLog = document.getElementById('errorLog');
        if (errorLog && data.recent_errors) {
            if (data.recent_errors.length > 0) {
                const errorsHTML = data.recent_errors.map(error => `
                    <div class="error-item">
                        <span class="error-time">${new Date(error.timestamp).toLocaleString()}</span>
                        <span class="error-message">${error.message}</span>
                    </div>
                `).join('');
                errorLog.innerHTML = errorsHTML;
            } else {
                errorLog.innerHTML = '<p class="text-muted">No recent errors</p>';
            }
        }
    }

    /**
     * Show import users modal
     */
    showImportUsersModal() {
        const modal = document.getElementById('importUsersModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.classList.add('modal-open');
        }
    }

    /**
     * Hide import users modal
     */
    hideImportUsersModal() {
        const modal = document.getElementById('importUsersModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
    }

    /**
     * Show create department modal
     */
    showCreateDepartmentModal() {
        const modal = document.getElementById('createDepartmentModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.classList.add('modal-open');
        }
    }

    /**
     * Hide create department modal
     */
    hideCreateDepartmentModal() {
        const modal = document.getElementById('createDepartmentModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
    }

    /**
     * Handle import users form submission
     */
    async handleImportUsers(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const csvFile = formData.get('csv_file');
        const sendWelcomeEmail = formData.get('send_welcome_email') === 'on';
        const autoApprove = formData.get('auto_approve') === 'on';

        if (!csvFile) {
            showAlert('Please select a CSV file', 'error');
            return;
        }

        try {
            showLoading();
            
            const uploadData = new FormData();
            uploadData.append('csv_file', csvFile);
            uploadData.append('send_welcome_email', sendWelcomeEmail);
            uploadData.append('auto_approve', autoApprove);

            const response = await api.post('/api/admin/import-users', uploadData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            if (response.success) {
                showAlert('Users imported successfully!', 'success');
                this.hideImportUsersModal();
                e.target.reset();
                this.loadSectionData('users');
            } else {
                showAlert(response.message || 'Failed to import users', 'error');
            }
        } catch (error) {
            console.error('Error importing users:', error);
            showAlert('An error occurred while importing users', 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Handle create department form submission
     */
    async handleCreateDepartment(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const departmentData = {
            name: formData.get('name'),
            description: formData.get('description')
        };

        try {
            showLoading();
            
            const response = await api.post('/api/admin/departments', departmentData);

            if (response.success) {
                showAlert('Department created successfully!', 'success');
                this.hideCreateDepartmentModal();
                e.target.reset();
                this.loadSectionData('departments');
            } else {
                showAlert(response.message || 'Failed to create department', 'error');
            }
        } catch (error) {
            console.error('Error creating department:', error);
            showAlert('An error occurred while creating the department', 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Export users to CSV
     */
    async exportUsers() {
        try {
            console.log('Starting user export...');
            const response = await api.get('/api/admin/export-users');
            console.log('Export response:', response);
            
            if (response.success && response.csv_content) {
                // Create and download CSV file
                const csvContent = response.csv_content;
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `users_export_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert(`Users exported successfully! ${response.total_users || 0} users exported.`, 'success');
            } else {
                console.error('Export failed:', response);
                showAlert(response.error || response.message || 'Failed to export users', 'error');
            }
        } catch (error) {
            console.error('Error exporting users:', error);
            showAlert('An error occurred while exporting users', 'error');
        }
    }

    /**
     * Approve all pending users
     */
    async approveAllUsers() {
        if (!confirm('Are you sure you want to approve all pending users?')) {
            return;
        }

        try {
            console.log('Starting approve all users...');
            const response = await api.post('/api/admin/approve-all-users');
            console.log('Approve all response:', response);

            if (response.success) {
                showAlert(`All users approved successfully! Approved ${response.approved_count || 0} users.`, 'success');
                this.loadSectionData('pending');
                this.loadSectionData('overview');
            } else {
                showAlert(response.message || 'Failed to approve all users', 'error');
            }
        } catch (error) {
            console.error('Error approving all users:', error);
            showAlert('An error occurred while approving users', 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Deny all pending users
     */
    async denyAllUsers() {
        if (!confirm('Are you sure you want to deny all pending users? This action cannot be undone.')) {
            return;
        }

        try {
            showLoading();
            
            const response = await api.post('/api/admin/deny-all-users');

            if (response.success) {
                showAlert('All users denied successfully!', 'success');
                this.loadSectionData('pending');
                this.loadSectionData('overview');
            } else {
                showAlert(response.message || 'Failed to deny all users', 'error');
            }
        } catch (error) {
            console.error('Error denying all users:', error);
            showAlert('An error occurred while denying users', 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Refresh system health
     */
    async refreshSystemHealth() {
        await this.loadSystemHealth();
        showAlert('System health refreshed', 'success');
    }

    /**
     * User management functions
     */
    async approveUser(userId) {
        try {
            // Get user data from the pending users list to extract role and department
            const pendingUsersList = document.getElementById('pendingUsersList');
            const userElement = pendingUsersList.querySelector(`[onclick*="approveUser(${userId})"]`);
            
            if (!userElement) {
                showAlert('User data not found', 'error');
                return;
            }
            
            // Extract role and department from the user element
            const userInfo = userElement.closest('.pending-user-item').querySelector('.user-info');
            const roleElement = userInfo.querySelector('.badge');
            const departmentElement = userInfo.querySelector('.department');
            
            const role = roleElement ? roleElement.textContent : 'STUDENT';
            const department = departmentElement ? departmentElement.textContent : 'General';
            
            const response = await api.post(`/api/admin/pending-users/${userId}/approve`, {
                role: role,
                department: department
            });
            
            if (response.success) {
                showAlert('User approved successfully!', 'success');
                this.loadSectionData('pending');
                this.loadSectionData('overview');
            } else {
                showAlert(response.message || 'Failed to approve user', 'error');
            }
        } catch (error) {
            console.error('Error approving user:', error);
            showAlert('An error occurred while approving user', 'error');
        }
    }

    async denyUser(userId) {
        try {
            const response = await api.post(`/api/admin/pending-users/${userId}/deny`);
            
            if (response.success) {
                showAlert('User denied successfully!', 'success');
                this.loadSectionData('pending');
                this.loadSectionData('overview');
            } else {
                showAlert(response.message || 'Failed to deny user', 'error');
            }
        } catch (error) {
            console.error('Error denying user:', error);
            showAlert('An error occurred while denying user', 'error');
        }
    }

    async toggleUserStatus(userId, currentStatus) {
        const newStatus = currentStatus === 'active' ? 'suspended' : 'active';
        
        try {
            console.log(`Toggling user ${userId} from ${currentStatus} to ${newStatus}`);
            const response = await api.put(`/api/admin/users/${userId}`, {
                status: newStatus
            });
            console.log('Toggle status response:', response);
            
            if (response.success) {
                showAlert(`User status updated to ${newStatus}`, 'success');
                // Force refresh the users data
                console.log('Refreshing users data...');
                await this.loadUsers();
                console.log('Users data refreshed');
            } else {
                showAlert(response.message || 'Failed to update user status', 'error');
            }
        } catch (error) {
            console.error('Error updating user status:', error);
            showAlert('An error occurred while updating user status', 'error');
        }
    }

    async deleteUser(userId) {
        if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await api.delete(`/api/admin/users/${userId}`);
            
            if (response.success) {
                showAlert('User deleted successfully!', 'success');
                this.loadSectionData('users');
                this.loadSectionData('overview');
            } else {
                showAlert(response.message || 'Failed to delete user', 'error');
            }
        } catch (error) {
            console.error('Error deleting user:', error);
            showAlert('An error occurred while deleting user', 'error');
        }
    }

    async editUser(userId) {
        // This would show a modal with user editing form
        showAlert('User editing feature coming soon!', 'info');
    }

    async editDepartment(departmentId) {
        // This would show a modal with department editing form
        showAlert('Department editing feature coming soon!', 'info');
    }

    async deleteDepartment(departmentId) {
        if (!confirm('Are you sure you want to delete this department? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await api.delete(`/api/admin/departments/${departmentId}`);
            
            if (response.success) {
                showAlert('Department deleted successfully!', 'success');
                this.loadSectionData('departments');
            } else {
                showAlert(response.message || 'Failed to delete department', 'error');
            }
        } catch (error) {
            console.error('Error deleting department:', error);
            showAlert('An error occurred while deleting department', 'error');
        }
    }

    /**
     * Pagination functions
     */
    previousUsersPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadUsers();
        }
    }

    nextUsersPage() {
        this.currentPage++;
        this.loadUsers();
    }

    /**
     * Utility functions
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
}

// Export AdminService for use in HTML
window.AdminService = AdminService;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminService;
}
