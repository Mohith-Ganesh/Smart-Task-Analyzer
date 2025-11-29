// Configuration
const API_BASE_URL = 'https://accomplished-grace-production.up.railway.app/api';

// Constants
const STRATEGY_NAMES = {
    smart_balance: 'Smart Balance',
    fastest_wins: 'Fastest Wins',
    high_impact: 'High Impact',
    deadline_driven: 'Deadline Driven'
};

const TOAST_ICONS = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
};

const PRIORITY_THRESHOLDS = { high: 8, medium: 6 };

// State
let currentStrategy = 'smart_balance';
let tasks = [];

// DOM Elements Cache
const elements = {
    taskForm: document.getElementById('taskForm'),
    bulkImportBtn: document.getElementById('bulkImportBtn'),
    bulkJson: document.getElementById('bulkJson'),
    tasksList: document.getElementById('tasksList'),
    taskCount: document.getElementById('taskCount'),
    refreshTasksBtn: document.getElementById('refreshTasksBtn'),
    deleteAllBtn: document.getElementById('deleteAllBtn'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    analysisResults: document.getElementById('analysisResults'),
    suggestBtn: document.getElementById('suggestBtn'),
    suggestionResults: document.getElementById('suggestionResults'),
    suggestionCount: document.getElementById('suggestionCount'),
    suggestionStrategy: document.getElementById('suggestionStrategy'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer'),
    apiStatus: document.getElementById('apiStatus'),
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeStrategyButtons();
    initializeEventListeners();
    checkAPIHealth();
    loadTasks();
    setDefaultDate();
});

// Tab Management
function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            if (targetTab === 'manage') loadTasks();
        });
    });
}

// Strategy Button Management
function initializeStrategyButtons() {
    const strategyBtns = document.querySelectorAll('.strategy-btn');
    
    strategyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            strategyBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentStrategy = btn.dataset.strategy;
        });
    });
}

// Event Listeners
function initializeEventListeners() {
    elements.taskForm.addEventListener('submit', handleTaskSubmit);
    elements.bulkImportBtn.addEventListener('click', handleBulkImport);
    elements.refreshTasksBtn.addEventListener('click', loadTasks);
    elements.deleteAllBtn.addEventListener('click', handleDeleteAll);
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.suggestBtn.addEventListener('click', handleSuggest);
}

// Set Default Date (tomorrow)
function setDefaultDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('dueDate').value = tomorrow.toISOString().split('T')[0];
}

// API Functions
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

async function checkAPIHealth() {
    try {
        const data = await apiRequest('/health/');
        updateAPIStatus(
            data.status === 'healthy',
            data.status === 'healthy' ? `Connected (${data.database_tasks} tasks)` : 'API Error'
        );
    } catch (error) {
        updateAPIStatus(false, 'API Offline');
        showToast('Cannot connect to API. Make sure the Django server is running.', 'error');
    }
}

function updateAPIStatus(isOnline, message) {
    const indicator = elements.apiStatus.querySelector('.status-indicator');
    const text = elements.apiStatus.querySelector('.status-text');
    indicator.className = `status-indicator ${isOnline ? 'online' : 'offline'}`;
    text.textContent = message;
}

// Task Management
async function loadTasks() {
    showLoading(true);
    
    try {
        const data = await apiRequest('/tasks/');
        
        if (data.status === 'success') {
            tasks = data.tasks;
            renderTasks(data.tasks);
            elements.taskCount.textContent = data.count;
            updateAPIStatus(true, `Connected (${data.count} tasks)`);
        } else {
            showToast('Failed to load tasks', 'error');
        }
    } catch (error) {
        showToast('Error loading tasks: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function renderTasks(tasksList) {
    if (!tasksList?.length) {
        elements.tasksList.innerHTML = '<div class="empty-state">No tasks yet. Create one above!</div>';
        return;
    }
    
    elements.tasksList.innerHTML = tasksList.map(task => createTaskHTML(task)).join('');
}

function createTaskHTML(task) {
    return `
        <div class="task-item" data-task-id="${task.id}">
            <div class="task-header">
                <div class="task-title">${escapeHtml(task.title)}</div>
                <div class="task-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editTask(${task.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">Delete</button>
                </div>
            </div>
            <div class="task-details">
                <div class="task-detail-item">Due: ${formatDate(task.due_date)}</div>
                <div class="task-detail-item">Estimated Hours: ${task.estimated_hours}h</div>
                <div class="task-detail-item">Importance: ${task.importance}/10</div>
                <div class="task-detail-item">Dependencies: ${task.dependencies.length > 0 ? task.dependencies.join(', ') : 'None'}</div>
            </div>
        </div>
    `;
}

async function handleTaskSubmit(e) {
    e.preventDefault();
    
    const taskData = {
        title: document.getElementById('taskTitle').value.trim(),
        due_date: document.getElementById('dueDate').value,
        estimated_hours: parseFloat(document.getElementById('estimatedHours').value),
        importance: parseInt(document.getElementById('importance').value),
        dependencies: parseDependencies(document.getElementById('dependencies').value)
    };
    
    // Validation
    if (!taskData.title || !taskData.due_date || !taskData.estimated_hours || !taskData.importance) {
        return showToast('Please fill in all required fields', 'error');
    }
    
    if (taskData.importance < 1 || taskData.importance > 10) {
        return showToast('Importance must be between 1 and 10', 'error');
    }
    
    if (taskData.estimated_hours <= 0) {
        return showToast('Estimated hours must be greater than 0', 'error');
    }
    
    showLoading(true);
    
    try {
        const data = await apiRequest('/tasks/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        
        if (data.status === 'success') {
            showToast('Task created successfully!', 'success');
            elements.taskForm.reset();
            setDefaultDate();
            loadTasks();
        } else {
            showToast('Failed to create task: ' + JSON.stringify(data.errors), 'error');
        }
    } catch (error) {
        showToast('Error creating task: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function handleBulkImport() {
    const jsonText = elements.bulkJson.value.trim();
    
    if (!jsonText) return showToast('Please paste JSON data', 'error');
    
    let tasksData;
    try {
        tasksData = JSON.parse(jsonText);
    } catch (error) {
        return showToast('Invalid JSON format', 'error');
    }
    
    if (!Array.isArray(tasksData)) {
        return showToast('JSON must be an array of tasks', 'error');
    }
    
    showLoading(true);
    
    try {
        const data = await apiRequest('/tasks/bulk/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tasks: tasksData })
        });
        
        if (data.status === 'success' || data.status === 'partial') {
            showToast(`Successfully created ${data.created_count} task(s)`, 'success');
            if (data.errors?.length > 0) {
                showToast(`Failed to create ${data.failed_count} task(s)`, 'warning');
            }
            elements.bulkJson.value = '';
            loadTasks();
        } else {
            showToast('Failed to import tasks', 'error');
        }
    } catch (error) {
        showToast('Error importing tasks: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    showLoading(true);
    
    try {
        const data = await apiRequest(`/tasks/${taskId}/`, { method: 'DELETE' });
        
        if (data.status === 'success') {
            showToast('Task deleted successfully', 'success');
            loadTasks();
        } else {
            showToast('Failed to delete task', 'error');
        }
    } catch (error) {
        showToast('Error deleting task: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function handleDeleteAll() {
    if (!confirm('Are you sure you want to delete ALL tasks? This cannot be undone.')) return;
    
    showLoading(true);
    
    try {
        const data = await apiRequest('/tasks/all/', { method: 'DELETE' });
        
        if (data.status === 'success') {
            showToast(data.message, 'success');
            loadTasks();
        } else {
            showToast('Failed to delete tasks', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Analysis
async function handleAnalyze() {
    showLoading(true);
    elements.analysisResults.innerHTML = '';
    
    try {
        const data = await apiRequest('/tasks/analyze/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ strategy: currentStrategy })
        });
        
        if (data.status === 'success') {
            renderAnalysisResults(data);
            showToast(`Analyzed ${data.total_tasks} tasks`, 'success');
        } else {
            showToast(data.message || 'Failed to analyze tasks', 'error');
            elements.analysisResults.innerHTML = `<div class="empty-state">${data.message || 'No tasks to analyze. Please create tasks first.'}</div>`;
        }
    } catch (error) {
        showToast('Error analyzing tasks: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function renderAnalysisResults(data) {
    if (!data.tasks?.length) {
        elements.analysisResults.innerHTML = '<div class="empty-state">No tasks to analyze</div>';
        return;
    }
    
    elements.analysisResults.innerHTML = `
        ${createResultsHeader(data)}
        ${data.tasks.map((task, index) => renderResultItem(task, index + 1)).join('')}
    `;
}

// Suggestions
async function handleSuggest() {
    showLoading(true);
    elements.suggestionResults.innerHTML = '';
    
    const count = parseInt(elements.suggestionCount.value) || 3;
    const strategy = elements.suggestionStrategy.value;
    
    try {
        const data = await apiRequest('/tasks/suggest/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ strategy, count })
        });
        
        if (data.status === 'success') {
            renderSuggestions(data);
            showToast(`Generated ${data.suggestion_count} suggestion(s)`, 'success');
        } else {
            showToast(data.message || 'Failed to generate suggestions', 'error');
            elements.suggestionResults.innerHTML = `<div class="empty-state">${data.message || 'No tasks available for suggestions. Please create tasks first.'}</div>`;
        }
    } catch (error) {
        showToast('Error getting suggestions: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function renderSuggestions(data) {
    if (!data.suggestions?.length) {
        elements.suggestionResults.innerHTML = '<div class="empty-state">No suggestions available</div>';
        return;
    }
    
    elements.suggestionResults.innerHTML = `
        ${createResultsHeader(data)}
        ${data.suggestions.map(task => renderSuggestionItem(task)).join('')}
    `;
}

// Shared Rendering Functions
function createResultsHeader(data) {
    return `
        <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--bg-secondary); border-radius: var(--radius-lg);">
            <strong>Strategy:</strong> ${STRATEGY_NAMES[data.strategy]} | 
            <strong>${data.total_tasks ? 'Total Tasks' : 'Suggestions'}:</strong> ${data.total_tasks || data.suggestion_count} | 
            <strong>Source:</strong> ${data.source === 'database' ? 'Database' : 'Request'}
        </div>
    `;
}

function getPriorityClass(score) {
    return score >= PRIORITY_THRESHOLDS.high ? 'priority-high' : 
           score >= PRIORITY_THRESHOLDS.medium ? 'priority-medium' : 'priority-low';
}

function createTaskDetailsHTML(task) {
    return `
        <div class="result-details">
            <div class="result-detail">
                <span class="result-detail-label">Due Date</span>
                <span class="result-detail-value">${formatDate(task.due_date)}</span>
            </div>
            <div class="result-detail">
                <span class="result-detail-label">Effort</span>
                <span class="result-detail-value">${task.estimated_hours}h</span>
            </div>
            <div class="result-detail">
                <span class="result-detail-label">Importance</span>
                <span class="result-detail-value">${task.importance}/10</span>
            </div>
            <div class="result-detail">
                <span class="result-detail-label">Dependencies</span>
                <span class="result-detail-value">${task.dependencies.length}</span>
            </div>
        </div>
    `;
}

function createScoreBreakdownHTML(breakdown) {
    return `
        <div class="result-breakdown">
            ${['urgency', 'importance', 'effort', 'dependency'].map(key => `
                <div class="breakdown-item">
                    <span class="breakdown-label">${key.charAt(0).toUpperCase() + key.slice(1)}</span>
                    <span class="breakdown-score">${breakdown[key + '_score']}</span>
                </div>
            `).join('')}
        </div>
    `;
}

function renderResultItem(task, rank) {
    return `
        <div class="result-item ${getPriorityClass(task.priority_score)}">
            <div class="result-header">
                <div class="result-rank">#${rank}</div>
                <div class="result-title"><h3>${escapeHtml(task.title)}</h3></div>
                <div class="result-score">
                    <div class="score-value">${task.priority_score}</div>
                    <div class="score-label">Priority Score</div>
                </div>
            </div>
            <div class="result-explanation">${task.explanation}</div>
            ${createTaskDetailsHTML(task)}
            ${createScoreBreakdownHTML(task.score_breakdown)}
            ${task.has_circular_dependency ? `
                <div class="result-recommendation" style="background: rgba(239, 68, 68, 0.1); border-color: var(--danger);">
                    Warning: This task is part of a circular dependency chain
                </div>
            ` : ''}
        </div>
    `;
}

function renderSuggestionItem(task) {
    return `
        <div class="result-item ${getPriorityClass(task.priority_score)}">
            <div class="result-header">
                <div class="result-rank">${task.rank}</div>
                <div class="result-title"><h3>${escapeHtml(task.title)}</h3></div>
                <div class="result-score">
                    <div class="score-value">${task.priority_score}</div>
                    <div class="score-label">Priority Score</div>
                </div>
            </div>
            <div class="result-explanation">${task.explanation}</div>
            ${createTaskDetailsHTML(task)}
            ${createScoreBreakdownHTML(task.score_breakdown)}
            <div class="result-recommendation">${task.recommendation}</div>
        </div>
    `;
}

// Utility Functions
function showLoading(show) {
    elements.loadingOverlay.classList.toggle('active', show);
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${TOAST_ICONS[type]}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    [today, tomorrow, date].forEach(d => d.setHours(0, 0, 0, 0));
    
    if (date.getTime() === today.getTime()) return 'Today';
    if (date.getTime() === tomorrow.getTime()) return 'Tomorrow';
    
    if (date < today) {
        const days = Math.floor((today - date) / (1000 * 60 * 60 * 24));
        return `${days} day${days > 1 ? 's' : ''} overdue`;
    }
    
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });
}

function parseDependencies(input) {
    if (!input?.trim()) return [];
    
    return input.split(',')
        .map(id => parseInt(id.trim()))
        .filter(id => !isNaN(id));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function editTask(taskId) {
    showToast('Edit functionality coming soon!', 'info');
}

// Global exports
window.deleteTask = deleteTask;
window.editTask = editTask;