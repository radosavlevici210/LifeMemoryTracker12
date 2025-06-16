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
