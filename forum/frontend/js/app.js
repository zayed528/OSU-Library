// API Configuration
const API_BASE_URL = 'http://localhost:8001/api';

// State
let currentQuestions = [];

// Utility Functions
function formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined 
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// API Functions
async function fetchQuestions() {
    try {
        const response = await fetch(`${API_BASE_URL}/questions`);
        if (!response.ok) throw new Error('Failed to fetch questions');
        return await response.json();
    } catch (error) {
        console.error('Error fetching questions:', error);
        throw error;
    }
}

async function createQuestion(questionData) {
    try {
        const response = await fetch(`${API_BASE_URL}/questions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(questionData)
        });
        if (!response.ok) throw new Error('Failed to create question');
        return await response.json();
    } catch (error) {
        console.error('Error creating question:', error);
        throw error;
    }
}

async function addReply(postId, replyData) {
    try {
        const response = await fetch(`${API_BASE_URL}/questions/${postId}/replies`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(replyData)
        });
        if (!response.ok) throw new Error('Failed to add reply');
        return await response.json();
    } catch (error) {
        console.error('Error adding reply:', error);
        throw error;
    }
}

async function searchQuestions(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/questions/search/?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Failed to search questions');
        return await response.json();
    } catch (error) {
        console.error('Error searching questions:', error);
        throw error;
    }
}

// Render Functions
function renderQuestion(question, expanded = false) {
    const repliesHtml = question.replies && question.replies.length > 0 ? `
        <div class="replies-section">
            <h4 class="replies-title">Replies (${question.replyCount})</h4>
            ${question.replies.map(reply => `
                <div class="reply-card">
                    <div class="reply-meta">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        <strong>${escapeHtml(reply.author)}</strong>
                        <span>•</span>
                        <span>${formatDate(reply.createdAt)}</span>
                    </div>
                    <div class="reply-content">${escapeHtml(reply.content)}</div>
                </div>
            `).join('')}
        </div>
    ` : '';

    return `
        <div class="question-card ${expanded ? 'question-expanded' : ''}" data-post-id="${question.postId}">
            <div class="question-header">
                <div style="flex: 1;">
                    <h3 class="question-title">${escapeHtml(question.title)}</h3>
                    <div class="question-meta">
                        <span class="question-meta-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                            ${escapeHtml(question.author)}
                        </span>
                        <span class="question-meta-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                            ${formatDate(question.createdAt)}
                        </span>
                    </div>
                </div>
                <div class="reply-count">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    ${question.replyCount}
                </div>
            </div>
            <div class="question-content">${escapeHtml(question.content)}</div>
            ${expanded ? repliesHtml : ''}
            ${expanded ? `
                <button class="reply-button" onclick="showReplyModal('${question.postId}')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="9 14 4 9 9 4"></polyline>
                        <path d="M20 20v-7a4 4 0 0 0-4-4H4"></path>
                    </svg>
                    Reply to this question
                </button>
            ` : ''}
        </div>
    `;
}

function renderQuestions(questions) {
    const container = document.getElementById('questionsList');
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const questionsContainer = document.getElementById('questionsContainer');
    
    loadingState.style.display = 'none';
    
    if (questions.length === 0) {
        questionsContainer.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    questionsContainer.style.display = 'block';
    
    container.innerHTML = questions.map(q => renderQuestion(q, false)).join('');
    
    // Add click handlers to expand questions
    document.querySelectorAll('.question-card').forEach(card => {
        card.addEventListener('click', async (e) => {
            if (e.target.closest('.reply-button')) return;
            
            const postId = card.dataset.postId;
            const question = questions.find(q => q.postId === postId);
            
            if (card.classList.contains('question-expanded')) {
                card.outerHTML = renderQuestion(question, false);
                // Re-attach click handler
                const newCard = document.querySelector(`[data-post-id="${postId}"]`);
                newCard.addEventListener('click', arguments.callee);
            } else {
                card.outerHTML = renderQuestion(question, true);
                // Re-attach click handler
                const newCard = document.querySelector(`[data-post-id="${postId}"]`);
                newCard.addEventListener('click', arguments.callee);
            }
        });
    });
}

// Modal Functions
function showQuestionModal() {
    document.getElementById('questionModal').classList.add('active');
}

function closeQuestionModal() {
    document.getElementById('questionModal').classList.remove('active');
    document.getElementById('questionForm').reset();
}

function showReplyModal(postId) {
    document.getElementById('replyPostId').value = postId;
    document.getElementById('replyModal').classList.add('active');
}

function closeReplyModal() {
    document.getElementById('replyModal').classList.remove('active');
    document.getElementById('replyForm').reset();
}

// Event Handlers
async function handleQuestionSubmit(e) {
    e.preventDefault();
    
    const questionData = {
        title: document.getElementById('questionTitle').value,
        content: document.getElementById('questionContent').value,
        author: document.getElementById('authorName').value
    };
    
    try {
        await createQuestion(questionData);
        closeQuestionModal();
        await loadQuestions();
    } catch (error) {
        alert('Failed to create question. Please try again.');
    }
}

async function handleReplySubmit(e) {
    e.preventDefault();
    
    const postId = document.getElementById('replyPostId').value;
    const replyData = {
        content: document.getElementById('replyContent').value,
        author: document.getElementById('replyAuthor').value
    };
    
    try {
        await addReply(postId, replyData);
        closeReplyModal();
        await loadQuestions();
    } catch (error) {
        alert('Failed to add reply. Please try again.');
    }
}

async function handleSearch(e) {
    const query = e.target.value.trim();
    
    if (query.length === 0) {
        renderQuestions(currentQuestions);
        return;
    }
    
    if (query.length < 2) return;
    
    try {
        const results = await searchQuestions(query);
        renderQuestions(results);
    } catch (error) {
        console.error('Search failed:', error);
    }
}

// Initialize
async function loadQuestions() {
    try {
        currentQuestions = await fetchQuestions();
        renderQuestions(currentQuestions);
    } catch (error) {
        document.getElementById('loadingState').innerHTML = `
            <div style="color: var(--scarlet-primary);">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <p>Failed to load questions. Make sure the backend is running.</p>
                <button class="btn-primary" onclick="loadQuestions()" style="margin-top: 1rem;">Retry</button>
            </div>
        `;
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadQuestions();
    
    document.getElementById('askQuestionBtn').addEventListener('click', showQuestionModal);
    document.getElementById('questionForm').addEventListener('submit', handleQuestionSubmit);
    document.getElementById('replyForm').addEventListener('submit', handleReplySubmit);
    
    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => handleSearch(e), 300);
    });
    
    // Close modals on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});
