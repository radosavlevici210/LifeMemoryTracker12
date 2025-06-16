// Life Coach Chat Application JavaScript

let chatMessages = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Enable Enter key to send message
    document.getElementById('messageInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Focus on input field
    document.getElementById('messageInput').focus();
});

// Send message to the AI life coach
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const chatContainer = document.getElementById('chatMessages');
    
    const message = messageInput.value.trim();
    if (!message) {
        showAlert('Please enter a message to continue our conversation.', 'warning');
        return;
    }
    
    // Disable input and show loading
    messageInput.disabled = true;
    sendButton.disabled = true;
    loadingIndicator.classList.remove('d-none');
    
    // Add user message to chat
    addMessage(message, 'user');
    messageInput.value = '';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Add AI response to chat
            addMessage(data.response, 'ai');
        } else {
            throw new Error(data.error || 'Failed to get response from life coach');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage(
            "I apologize, but I'm having trouble connecting right now. Please check your internet connection and try again. If the problem persists, there might be an issue with the AI service.",
            'ai',
            true
        );
    } finally {
        // Re-enable input and hide loading
        messageInput.disabled = false;
        sendButton.disabled = false;
        loadingIndicator.classList.add('d-none');
        messageInput.focus();
    }
}

// Add message to chat interface
function addMessage(content, sender, isError = false) {
    const chatContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const timestamp = new Date().toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-user me-2"></i>
                ${escapeHtml(content)}
            </div>
            <div class="message-time">You • ${timestamp}</div>
        `;
    } else {
        const iconClass = isError ? 'fas fa-exclamation-triangle text-warning' : 'fas fa-brain text-primary';
        const alertClass = isError ? 'alert-warning' : '';
        
        messageDiv.innerHTML = `
            <div class="message-content ${alertClass}">
                <i class="${iconClass} me-2"></i>
                ${formatAIResponse(content)}
            </div>
            <div class="message-time">AI Life Coach • ${timestamp}</div>
        `;
    }
    
    // Remove welcome message if it exists
    const welcomeAlert = chatContainer.querySelector('.alert-info');
    if (welcomeAlert && chatMessages.length === 0) {
        welcomeAlert.remove();
    }
    
    chatContainer.appendChild(messageDiv);
    chatMessages.push({ content, sender, timestamp: new Date().toISOString() });
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Format AI response with proper line breaks and structure
function formatAIResponse(content) {
    return escapeHtml(content)
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^/, '<p>')
        .replace(/$/, '</p>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container .row .col-lg-8');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Show memory modal
async function showMemoryModal() {
    const modal = new bootstrap.Modal(document.getElementById('memoryModal'));
    const memoryContent = document.getElementById('memoryContent');
    
    modal.show();
    
    try {
        const response = await fetch('/memory');
        const data = await response.json();
        
        if (response.ok) {
            displayMemoryData(data);
        } else {
            throw new Error(data.error || 'Failed to load memory');
        }
    } catch (error) {
        console.error('Error loading memory:', error);
        memoryContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to load memory data. Please try again.
            </div>
        `;
    }
}

// Display memory data in modal
function displayMemoryData(memory) {
    const memoryContent = document.getElementById('memoryContent');
    
    if (!memory.life_events || memory.life_events.length === 0) {
        memoryContent.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No life events recorded yet. Start chatting to build your memory!
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="mb-3">
            <h6 class="text-primary">
                <i class="fas fa-calendar-alt me-2"></i>
                Life Events (${memory.life_events.length} entries)
            </h6>
        </div>
        <div class="life-events-container" style="max-height: 400px; overflow-y: auto;">
    `;
    
    // Sort events by date (newest first)
    const sortedEvents = memory.life_events.sort((a, b) => 
        new Date(b.timestamp || b.date) - new Date(a.timestamp || a.date)
    );
    
    sortedEvents.forEach(event => {
        const date = new Date(event.timestamp || event.date).toLocaleDateString();
        html += `
            <div class="life-event">
                <div class="life-event-date">
                    <i class="fas fa-clock me-1"></i>
                    ${date}
                </div>
                <div class="life-event-content">
                    ${escapeHtml(event.entry)}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    memoryContent.innerHTML = html;
}

// Clear memory with confirmation
async function clearMemory() {
    if (!confirm('Are you sure you want to clear all your life memory? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/clear_memory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Memory cleared successfully. Starting fresh!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('memoryModal'));
            modal.hide();
            
            // Clear chat messages
            const chatContainer = document.getElementById('chatMessages');
            chatContainer.innerHTML = `
                <div class="alert alert-info" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Fresh Start!</strong> Your memory has been cleared. 
                    Tell me about yourself to begin building new insights together.
                </div>
            `;
            chatMessages = [];
            
        } else {
            throw new Error(data.error || 'Failed to clear memory');
        }
    } catch (error) {
        console.error('Error clearing memory:', error);
        showAlert('Failed to clear memory. Please try again.', 'danger');
    }
}

// Show mood tracker modal
function showMoodTracker() {
    const modal = new bootstrap.Modal(document.getElementById('moodModal'));
    modal.show();
}

// Analyze mood
async function analyzeMood() {
    const moodInput = document.getElementById('moodInput');
    const moodResult = document.getElementById('moodResult');
    const moodAnalysis = document.getElementById('moodAnalysis');
    
    const text = moodInput.value.trim();
    if (!text) {
        showAlert('Please describe how you\'re feeling first.', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/mood_check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: text })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            moodAnalysis.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <strong>Emotion:</strong> ${data.emotion}<br>
                        <strong>Intensity:</strong> ${data.intensity}/10
                    </div>
                    <div class="col-md-6">
                        <strong>Key Factors:</strong><br>
                        <ul class="mb-0">
                            ${data.factors.map(factor => `<li>${factor}</li>`).join('')}
                        </ul>
                    </div>
                </div>
                <div class="mt-3">
                    <strong>Recommendation:</strong><br>
                    ${data.recommendation}
                </div>
            `;
            moodResult.classList.remove('d-none');
        } else {
            throw new Error(data.error || 'Failed to analyze mood');
        }
    } catch (error) {
        console.error('Error analyzing mood:', error);
        showAlert('Failed to analyze mood. Please try again.', 'danger');
    }
}

// Quick mood check
async function quickMoodCheck() {
    const messageInput = document.getElementById('messageInput');
    const currentText = messageInput.value.trim();
    
    if (!currentText) {
        showAlert('Please type something about how you\'re feeling first.', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/mood_check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: currentText })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addMessage(`Mood Analysis: ${data.emotion} (${data.intensity}/10) - ${data.recommendation}`, 'ai');
        } else {
            throw new Error(data.error || 'Failed to analyze mood');
        }
    } catch (error) {
        console.error('Error in quick mood check:', error);
        addMessage('Unable to analyze mood right now. Please try again.', 'ai', true);
    }
}

// Show goals modal
async function showGoalsModal() {
    const modal = new bootstrap.Modal(document.getElementById('goalsModal'));
    const goalsContent = document.getElementById('goalsContent');
    
    modal.show();
    
    try {
        const response = await fetch('/memory');
        const data = await response.json();
        
        if (response.ok) {
            displayGoals(data.goals || []);
        } else {
            throw new Error(data.error || 'Failed to load goals');
        }
    } catch (error) {
        console.error('Error loading goals:', error);
        goalsContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to load goals. Please try again.
            </div>
        `;
    }
}

// Display goals
function displayGoals(goals) {
    const goalsContent = document.getElementById('goalsContent');
    
    if (!goals || goals.length === 0) {
        goalsContent.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No goals set yet. Add your first goal above!
            </div>
        `;
        return;
    }
    
    let html = '';
    goals.forEach(goal => {
        const statusClass = goal.status === 'completed' ? 'success' : 'primary';
        const statusIcon = goal.status === 'completed' ? 'check-circle' : 'clock';
        
        html += `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="card-title">${escapeHtml(goal.text)}</h6>
                            <div class="text-muted small">
                                <i class="fas fa-tag me-1"></i>${goal.category}
                                <span class="ms-3"><i class="fas fa-calendar me-1"></i>${goal.created_date}</span>
                            </div>
                            ${goal.progress ? `
                                <div class="progress mt-2" style="height: 6px;">
                                    <div class="progress-bar" style="width: ${goal.progress}%"></div>
                                </div>
                                <small class="text-muted">${goal.progress}% complete</small>
                            ` : ''}
                        </div>
                        <span class="badge bg-${statusClass}">
                            <i class="fas fa-${statusIcon} me-1"></i>${goal.status}
                        </span>
                    </div>
                    ${goal.status === 'active' ? `
                        <div class="mt-3">
                            <button class="btn btn-sm btn-success" onclick="completeGoal(${goal.id})">
                                <i class="fas fa-check me-1"></i>Mark Complete
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    goalsContent.innerHTML = html;
}

// Add goal
async function addGoal() {
    const goalText = document.getElementById('newGoalText').value.trim();
    const category = document.getElementById('goalCategory').value;
    
    if (!goalText) {
        showAlert('Please enter a goal description.', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/goal_tracker', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'add',
                goal: goalText,
                category: category
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Goal added successfully!', 'success');
            document.getElementById('newGoalText').value = '';
            displayGoals(data.goals);
        } else {
            throw new Error(data.error || 'Failed to add goal');
        }
    } catch (error) {
        console.error('Error adding goal:', error);
        showAlert('Failed to add goal. Please try again.', 'danger');
    }
}

// Complete goal
async function completeGoal(goalId) {
    try {
        const response = await fetch('/goal_tracker', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'complete',
                goal_id: goalId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Congratulations on completing your goal!', 'success');
            displayGoals(data.goals);
        } else {
            throw new Error(data.error || 'Failed to complete goal');
        }
    } catch (error) {
        console.error('Error completing goal:', error);
        showAlert('Failed to complete goal. Please try again.', 'danger');
    }
}

// Add quick goal
function addQuickGoal() {
    const goalText = prompt('What goal would you like to add?');
    if (goalText && goalText.trim()) {
        addGoalDirectly(goalText.trim());
    }
}

// Add goal directly
async function addGoalDirectly(goalText) {
    try {
        const response = await fetch('/goal_tracker', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'add',
                goal: goalText,
                category: 'general'
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Goal added successfully!', 'success');
            addMessage(`Goal added: "${goalText}"`, 'ai');
        } else {
            throw new Error(data.error || 'Failed to add goal');
        }
    } catch (error) {
        console.error('Error adding goal:', error);
        showAlert('Failed to add goal. Please try again.', 'danger');
    }
}

// Generate action items
async function generateActionItems() {
    try {
        const response = await fetch('/action_items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.action_items) {
            let itemsText = 'Based on your recent conversations, here are some action items:\n\n';
            data.action_items.forEach((item, index) => {
                itemsText += `${index + 1}. **${item.title}** (${item.priority} priority)\n`;
                itemsText += `   Category: ${item.category}\n`;
                itemsText += `   Why: ${item.description}\n\n`;
            });
            
            addMessage(itemsText, 'ai');
        } else {
            addMessage('Not enough conversation history to generate action items. Chat more first!', 'ai');
        }
    } catch (error) {
        console.error('Error generating action items:', error);
        addMessage('Unable to generate action items right now. Please try again.', 'ai', true);
    }
}

// Show insights modal
async function showInsightsModal() {
    const modal = new bootstrap.Modal(document.getElementById('insightsModal'));
    const insightsContent = document.getElementById('insightsContent');
    
    modal.show();
    
    try {
        const response = await fetch('/insights');
        const data = await response.json();
        
        if (response.ok) {
            displayInsights(data.insights || []);
        } else {
            throw new Error(data.error || 'Failed to load insights');
        }
    } catch (error) {
        console.error('Error loading insights:', error);
        insightsContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to load insights. Please try again.
            </div>
        `;
    }
}

// Display insights
function displayInsights(insights) {
    const insightsContent = document.getElementById('insightsContent');
    
    if (!insights || insights.length === 0) {
        insightsContent.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Not enough data to generate insights yet. Keep chatting to build your profile!
            </div>
        `;
        return;
    }
    
    let html = '';
    insights.forEach(insight => {
        const typeClass = {
            'positive': 'success',
            'growth': 'info',
            'warning': 'warning',
            'opportunity': 'primary'
        }[insight.type] || 'secondary';
        
        const typeIcon = {
            'positive': 'thumbs-up',
            'growth': 'arrow-up',
            'warning': 'exclamation-triangle',
            'opportunity': 'lightbulb'
        }[insight.type] || 'info-circle';
        
        html += `
            <div class="card mb-3">
                <div class="card-header bg-${typeClass} text-white">
                    <h6 class="mb-0">
                        <i class="fas fa-${typeIcon} me-2"></i>
                        ${escapeHtml(insight.title)}
                    </h6>
                </div>
                <div class="card-body">
                    <p class="card-text">${escapeHtml(insight.description)}</p>
                    <div class="alert alert-light">
                        <strong>Action Tip:</strong> ${escapeHtml(insight.actionable_tip)}
                    </div>
                </div>
            </div>
        `;
    });
    
    insightsContent.innerHTML = html;
}

// Refresh insights
function refreshInsights() {
    const insightsContent = document.getElementById('insightsContent');
    insightsContent.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Analyzing your patterns and generating fresh insights...</p>
        </div>
    `;
    
    setTimeout(() => {
        showInsightsModal();
    }, 1000);
}

// Export data
async function exportData() {
    try {
        const response = await fetch('/export_data');
        const data = await response.json();
        
        if (response.ok) {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `life-coach-data-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showAlert('Data exported successfully!', 'success');
        } else {
            throw new Error(data.error || 'Failed to export data');
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        showAlert('Failed to export data. Please try again.', 'danger');
    }
}
