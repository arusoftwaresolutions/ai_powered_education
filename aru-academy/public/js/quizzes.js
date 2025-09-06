/**
 * Quizzes Service for ARU Academy
 */

class QuizzesService {
    constructor() {
        this.currentQuiz = null;
        this.currentAnswers = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadQuizzes();
    }

    bindEvents() {
        const quizForm = document.getElementById('quiz-form');
        if (quizForm) {
            quizForm.addEventListener('submit', (e) => this.handleQuizSubmission(e));
        }
    }

    async loadQuizzes() {
        try {
            const response = await api.get('/api/quizzes/');
            if (response.success) {
                // Filter quizzes by user's department
                const user = JSON.parse(localStorage.getItem('user') || '{}');
                let quizzes = response.data || [];
                
                if (user.department_id) {
                    quizzes = quizzes.filter(quiz => 
                        quiz.course && quiz.course.department_id === user.department_id
                    );
                }
                
                this.displayQuizzes(quizzes);
            }
        } catch (error) {
            console.error('Error loading quizzes:', error);
            this.displayQuizzes([]);
        }
    }

    displayQuizzes(quizzes) {
        const container = document.getElementById('quizzes-container');
        if (!container) return;

        if (quizzes.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 3rem 2rem; color: #666;">
                    <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;">📋</div>
                    <h3 style="color: #333; margin-bottom: 0.5rem;">No Quizzes Available</h3>
                    <p style="margin-bottom: 1.5rem;">There are currently no quizzes available for your department. Check back later!</p>
                    <button class="btn btn-primary" onclick="window.location.href='dashboard.html'">
                        ← Back to Dashboard
                    </button>
                </div>
            `;
            return;
        }

        const html = quizzes.map(quiz => `
            <div class="quiz-card" data-quiz-id="${quiz.id}">
                <h3>${quiz.topic}</h3>
                <p>${quiz.description || ''}</p>
                <button class="btn btn-primary" onclick="quizzesService.selectQuiz(${quiz.id})">
                    Take Quiz
                </button>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    async selectQuiz(quizId) {
        try {
            const response = await API.get(`/quizzes/${quizId}`);
            if (response.success) {
                this.currentQuiz = response.data.quiz;
                this.showQuizInterface();
            }
        } catch (error) {
            console.error('Error selecting quiz:', error);
        }
    }

    showQuizInterface() {
        const container = document.getElementById('main-content');
        if (!container || !this.currentQuiz) return;

        const html = `
            <div class="quiz-interface">
                <h2>${this.currentQuiz.topic}</h2>
                <form id="quiz-form">
                    ${this.currentQuiz.questions.map((q, i) => this.renderQuestion(q, i)).join('')}
                    <button type="submit" class="btn btn-primary">Submit Quiz</button>
                </form>
            </div>
        `;

        container.innerHTML = html;
        this.bindEvents();
    }

    renderQuestion(question, index) {
        let optionsHTML = '';
        if (question.question_type === 'multiple_choice' && question.options) {
            optionsHTML = question.options.map((option, optIndex) => `
                <div class="option">
                    <input type="radio" name="q${index}" value="${optIndex}" id="q${index}opt${optIndex}">
                    <label for="q${index}opt${optIndex}">${option}</label>
                </div>
            `).join('');
        }

        return `
            <div class="question">
                <h4>Question ${index + 1}</h4>
                <p>${question.question}</p>
                ${optionsHTML}
            </div>
        `;
    }

    async handleQuizSubmission(e) {
        e.preventDefault();
        
        try {
            const formData = new FormData(e.target);
            const answers = {};
            
            for (let [key, value] of formData.entries()) {
                answers[key] = value;
            }

            const response = await API.post('/quizzes/submit', {
                quiz_id: this.currentQuiz.id,
                answers: answers
            });

            if (response.success) {
                this.showResults(response.data.submission);
            }
        } catch (error) {
            console.error('Error submitting quiz:', error);
        }
    }

    showResults(submission) {
        const container = document.getElementById('main-content');
        if (!container) return;

        const html = `
            <div class="quiz-results">
                <h2>Quiz Results</h2>
                <div class="score">
                    Score: ${submission.score}/${submission.max_score}
                    (${Math.round((submission.score / submission.max_score) * 100)}%)
                </div>
                <div class="status ${submission.passed ? 'passed' : 'failed'}">
                    ${submission.passed ? 'PASSED' : 'FAILED'}
                </div>
                <button class="btn btn-primary" onclick="quizzesService.backToQuizzes()">
                    Back to Quizzes
                </button>
            </div>
        `;

        container.innerHTML = html;
    }

    backToQuizzes() {
        this.currentQuiz = null;
        this.currentAnswers = {};
        this.loadQuizzes();
    }
}

// Initialize
let quizzesService;
document.addEventListener('DOMContentLoaded', () => {
    quizzesService = new QuizzesService();
});

window.QuizzesService = QuizzesService;
window.quizzesService = quizzesService;
