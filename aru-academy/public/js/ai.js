/**
 * AI Tutor Service for ARU Academy
 * Handles AI interactions, question asking, and quiz generation
 */

class AITutorService {
    constructor() {
        this.currentContext = '';
        this.conversationHistory = [];
        this.isLoading = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadConversationHistory();
    }

    bindEvents() {
        // Question input form
        const questionForm = document.getElementById('question-form');
        if (questionForm) {
            questionForm.addEventListener('submit', (e) => this.handleQuestionSubmit(e));
        }

        // Quiz generation form
        const quizForm = document.getElementById('quiz-generation-form');
        if (quizForm) {
            quizForm.addEventListener('submit', (e) => this.handleQuizGeneration(e));
        }

        // Context selection
        const contextSelect = document.getElementById('context-select');
        if (contextSelect) {
            contextSelect.addEventListener('change', (e) => this.handleContextChange(e));
        }

        // Clear conversation button
        const clearBtn = document.getElementById('clear-conversation');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearConversation());
        }

        // Export conversation button
        const exportBtn = document.getElementById('export-conversation');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportConversation());
        }
    }

    async handleQuestionSubmit(e) {
        e.preventDefault();
        
        const questionInput = document.getElementById('question-input');
        const question = questionInput.value.trim();
        
        if (!question) {
            UI.showAlert('Please enter a question', 'error');
            return;
        }

        await this.askQuestion(question);
        questionInput.value = '';
    }

    async handleQuizGeneration(e) {
        e.preventDefault();
        
        const topicInput = document.getElementById('topic-input');
        const questionCountInput = document.getElementById('question-count');
        const topic = topicInput.value.trim();
        const questionCount = parseInt(questionCountInput.value) || 5;
        
        if (!topic) {
            UI.showAlert('Please enter a topic', 'error');
            return;
        }

        await this.generateQuiz(topic, questionCount);
    }

    handleContextChange(e) {
        this.currentContext = e.target.value;
        this.updateContextDisplay();
    }

    async askQuestion(question) {
        try {
            this.setLoading(true);
            
            const response = await API.post('/ai/ask', {
                question: question,
                context: this.currentContext
            });

            if (response.success) {
                const answer = response.data.answer;
                this.addToConversation('user', question);
                this.addToConversation('ai', answer);
                this.saveConversationHistory();
                this.updateConversationDisplay();
            } else {
                UI.showAlert(response.message || 'Failed to get answer', 'error');
            }
        } catch (error) {
            console.error('Error asking question:', error);
            UI.showAlert('Failed to get answer. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async generateQuiz(topic, questionCount) {
        try {
            this.setLoading(true);
            
            const response = await API.post('/ai/generate-questions', {
                topic: topic,
                question_count: questionCount,
                context: this.currentContext
            });

            if (response.success) {
                const quiz = response.data.quiz;
                this.displayGeneratedQuiz(quiz);
                this.addToConversation('system', `Generated quiz for topic: ${topic}`);
                this.saveConversationHistory();
            } else {
                UI.showAlert(response.message || 'Failed to generate quiz', 'error');
            }
        } catch (error) {
            console.error('Error generating quiz:', error);
            UI.showAlert('Failed to generate quiz. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    addToConversation(role, content) {
        const message = {
            role: role,
            content: content,
            timestamp: new Date().toISOString()
        };
        
        this.conversationHistory.push(message);
        
        // Keep only last 50 messages
        if (this.conversationHistory.length > 50) {
            this.conversationHistory = this.conversationHistory.slice(-50);
        }
    }

    updateConversationDisplay() {
        const conversationContainer = document.getElementById('conversation-container');
        if (!conversationContainer) return;

        conversationContainer.innerHTML = '';
        
        this.conversationHistory.forEach(message => {
            const messageElement = this.createMessageElement(message);
            conversationContainer.appendChild(messageElement);
        });

        // Scroll to bottom
        conversationContainer.scrollTop = conversationContainer.scrollHeight;
    }

    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        
        const roleLabel = message.role === 'user' ? 'You' : 
                         message.role === 'ai' ? 'AI Tutor' : 'System';
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="role">${roleLabel}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
            <div class="message-content">${this.formatMessageContent(message.content)}</div>
        `;
        
        return messageDiv;
    }

    formatMessageContent(content) {
        // Convert markdown-like syntax to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    displayGeneratedQuiz(quiz) {
        const quizContainer = document.getElementById('generated-quiz-container');
        if (!quizContainer) return;

        quizContainer.innerHTML = `
            <div class="quiz-header">
                <h3>Generated Quiz: ${quiz.topic}</h3>
                <p>${quiz.description || ''}</p>
            </div>
            <div class="quiz-questions">
                ${quiz.questions.map((q, index) => this.createQuestionHTML(q, index)).join('')}
            </div>
            <div class="quiz-actions">
                <button class="btn btn-primary" onclick="aiTutor.saveQuiz('${quiz.topic}')">
                    Save Quiz
                </button>
                <button class="btn btn-secondary" onclick="aiTutor.clearGeneratedQuiz()">
                    Clear
                </button>
            </div>
        `;
    }

    createQuestionHTML(question, index) {
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
            <div class="question" data-question-id="${index}">
                <h4>Question ${index + 1}</h4>
                <p class="question-text">${question.question}</p>
                ${optionsHTML}
                <div class="question-actions">
                    <button class="btn btn-sm btn-outline" onclick="aiTutor.showAnswer(${index})">
                        Show Answer
                    </button>
                </div>
                <div class="answer-explanation" id="answer-${index}" style="display: none;">
                    <strong>Answer:</strong> ${question.correct_answer}
                    ${question.explanation ? `<br><em>Explanation:</strong> ${question.explanation}</em>` : ''}
                </div>
            </div>
        `;
    }

    showAnswer(questionIndex) {
        const answerElement = document.getElementById(`answer-${questionIndex}`);
        if (answerElement) {
            answerElement.style.display = answerElement.style.display === 'none' ? 'block' : 'none';
        }
    }

    async saveQuiz(topic) {
        try {
            const quizContainer = document.getElementById('generated-quiz-container');
            const questions = [];
            
            // Extract questions from the displayed quiz
            const questionElements = quizContainer.querySelectorAll('.question');
            questionElements.forEach((qElement, index) => {
                const questionText = qElement.querySelector('.question-text').textContent;
                const options = Array.from(qElement.querySelectorAll('.option label')).map(label => label.textContent);
                const answer = qElement.querySelector('.answer-explanation strong').textContent.replace('Answer:', '').trim();
                
                questions.push({
                    question_type: 'multiple_choice',
                    question: questionText,
                    options: options,
                    correct_answer: answer,
                    points: 1.0
                });
            });

            const quizData = {
                topic: topic,
                questions: questions
            };

            const response = await API.post('/quizzes', quizData);
            
            if (response.success) {
                UI.showAlert('Quiz saved successfully!', 'success');
                this.clearGeneratedQuiz();
            } else {
                UI.showAlert(response.message || 'Failed to save quiz', 'error');
            }
        } catch (error) {
            console.error('Error saving quiz:', error);
            UI.showAlert('Failed to save quiz. Please try again.', 'error');
        }
    }

    clearGeneratedQuiz() {
        const quizContainer = document.getElementById('generated-quiz-container');
        if (quizContainer) {
            quizContainer.innerHTML = '';
        }
    }

    clearConversation() {
        this.conversationHistory = [];
        this.updateConversationDisplay();
        this.saveConversationHistory();
        UI.showAlert('Conversation cleared', 'info');
    }

    exportConversation() {
        const dataStr = JSON.stringify(this.conversationHistory, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `ai-conversation-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }

    loadConversationHistory() {
        const saved = localStorage.getItem('ai_conversation_history');
        if (saved) {
            try {
                this.conversationHistory = JSON.parse(saved);
                this.updateConversationDisplay();
            } catch (error) {
                console.error('Error loading conversation history:', error);
                this.conversationHistory = [];
            }
        }
    }

    saveConversationHistory() {
        try {
            localStorage.setItem('ai_conversation_history', JSON.stringify(this.conversationHistory));
        } catch (error) {
            console.error('Error saving conversation history:', error);
        }
    }

    updateContextDisplay() {
        const contextDisplay = document.getElementById('current-context');
        if (contextDisplay) {
            contextDisplay.textContent = this.currentContext || 'No specific context selected';
        }
    }

    setLoading(loading) {
        this.isLoading = loading;
        
        const submitBtn = document.querySelector('#question-form button[type="submit"]');
        const quizBtn = document.querySelector('#quiz-generation-form button[type="submit"]');
        
        if (submitBtn) {
            submitBtn.disabled = loading;
            submitBtn.innerHTML = loading ? '<span class="spinner"></span> Asking...' : 'Ask Question';
        }
        
        if (quizBtn) {
            quizBtn.disabled = loading;
            quizBtn.innerHTML = loading ? '<span class="spinner"></span> Generating...' : 'Generate Quiz';
        }

        // Show/hide loading indicator
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = loading ? 'block' : 'none';
        }
    }

    // Public methods for external use
    setContext(context) {
        this.currentContext = context;
        this.updateContextDisplay();
    }

    getConversationHistory() {
        return this.conversationHistory;
    }

    reset() {
        this.conversationHistory = [];
        this.currentContext = '';
        this.updateConversationDisplay();
        this.updateContextDisplay();
        this.saveConversationHistory();
    }
}

// Initialize AI Tutor Service
let aiTutor;

document.addEventListener('DOMContentLoaded', () => {
    aiTutor = new AITutorService();
});

// Export for global access
window.AITutorService = AITutorService;
window.aiTutor = aiTutor;
