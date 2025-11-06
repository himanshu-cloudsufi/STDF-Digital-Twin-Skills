/**
 * Demand Forecasting Chatbot - WebSocket Client
 */

// Global state
let socket = null;
let sessionId = null;
let isWaitingForResponse = false;
let currentAssistantMessage = null;

// DOM elements
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

/**
 * Initialize WebSocket connection
 */
function initializeSocket() {
    socket = io();

    // Connection events
    socket.on('connect', () => {
        console.log('Connected to server');
        updateConnectionStatus('connected', 'Connected');
        sendButton.disabled = false;
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus('disconnected', 'Disconnected');
        sendButton.disabled = true;
        isWaitingForResponse = false;
    });

    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        updateConnectionStatus('disconnected', 'Connection error');
    });

    // Chat events
    socket.on('status', (data) => {
        console.log('Status:', data.message);
    });

    socket.on('user_message', (data) => {
        // User message echoed back (already displayed locally)
        // Capture session_id if server created one
        if (data.session_id && !sessionId) {
            sessionId = data.session_id;
            updateUrlWithSession(sessionId);
            console.log('Captured new session ID from server:', sessionId);
        }
    });

    socket.on('assistant_chunk', (data) => {
        handleAssistantChunk(data);
    });

    socket.on('assistant_complete', (data) => {
        handleAssistantComplete(data);
    });

    socket.on('tool_use', (data) => {
        handleToolUse(data);
    });

    socket.on('result', (data) => {
        if (data.session_id) {
            sessionId = data.session_id;
        }
    });

    socket.on('error', (data) => {
        console.error('Server error:', data.message);
        addSystemMessage(`Error: ${data.message}`);
        removeTypingIndicator();
        isWaitingForResponse = false;
        sendButton.disabled = false;
    });

    // Session management events
    socket.on('sessions_list', (data) => {
        renderSessionList(data.sessions);
    });

    socket.on('session_resumed', (data) => {
        handleSessionResumed(data);
    });

    socket.on('session_deleted', (data) => {
        // Refresh session list
        socket.emit('list_sessions');
        if (sessionId === data.session_id) {
            startNewChat();
        }
    });

    socket.on('session_title_updated', (data) => {
        // Update session title in sidebar
        const sessionEl = document.querySelector(`[data-session-id="${data.session_id}"] .session-title`);
        if (sessionEl) {
            sessionEl.textContent = data.title;
        }
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(status, text) {
    statusDot.className = `status-dot ${status}`;
    statusText.textContent = text;
}

/**
 * Send a message to the server
 */
function sendMessage() {
    const message = messageInput.value.trim();

    if (!message || isWaitingForResponse) {
        return;
    }

    // Add user message to chat
    addUserMessage(message);

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Send to server
    socket.emit('message', {
        message: message,
        session_id: sessionId
    });

    // Show typing indicator
    addTypingIndicator();
    isWaitingForResponse = true;
    sendButton.disabled = true;
}

/**
 * Send a quick message
 */
function sendQuickMessage(message) {
    if (isWaitingForResponse) {
        return;
    }
    messageInput.value = message;
    sendMessage();
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyDown(event) {
    // Send on Enter (without Shift)
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }

    // Auto-resize textarea
    setTimeout(() => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    }, 0);
}

/**
 * Add user message to chat
 */
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-user';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Add system message to chat
 */
function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-system';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Add typing indicator
 */
function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-assistant';
    messageDiv.id = 'typing-indicator';

    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'typing-indicator';

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        indicatorDiv.appendChild(dot);
    }

    messageDiv.appendChild(indicatorDiv);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Handle assistant text chunk
 */
function handleAssistantChunk(data) {
    // Remove typing indicator on first chunk
    if (!currentAssistantMessage) {
        removeTypingIndicator();

        // Create new assistant message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-assistant';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content markdown-content';
        contentDiv.id = 'current-assistant-message';
        contentDiv.dataset.rawText = ''; // Store raw markdown text

        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);

        currentAssistantMessage = contentDiv;
    }

    // Accumulate raw markdown text
    currentAssistantMessage.dataset.rawText += data.text;

    // Render markdown
    currentAssistantMessage.innerHTML = marked.parse(currentAssistantMessage.dataset.rawText);
    scrollToBottom();

    // Update session ID
    if (data.session_id) {
        sessionId = data.session_id;
        updateUrlWithSession(sessionId);
    }
}

/**
 * Handle assistant message completion
 */
function handleAssistantComplete(data) {
    currentAssistantMessage = null;
    isWaitingForResponse = false;
    sendButton.disabled = false;
    messageInput.focus();

    // Update session ID
    if (data.session_id) {
        sessionId = data.session_id;
        updateUrlWithSession(sessionId);
    }
}

/**
 * Handle tool use notification
 */
function handleToolUse(data) {
    const toolDiv = document.createElement('div');
    toolDiv.className = 'tool-invocation';

    let toolText = `<strong>Invoking: ${data.tool}</strong>`;

    // Format tool input for display
    if (data.input) {
        if (data.input.product) {
            toolText += `<br>Product: ${data.input.product}`;
        }
        if (data.input.commodity) {
            toolText += `<br>Commodity: ${data.input.commodity}`;
        }
        if (data.input.event) {
            toolText += `<br>Event: ${data.input.event}`;
        }
        if (data.input.region) {
            toolText += `<br>Region: ${data.input.region}`;
        }
        if (data.input.end_year) {
            toolText += `<br>Forecast to: ${data.input.end_year}`;
        }
    }

    toolDiv.innerHTML = toolText;
    chatContainer.appendChild(toolDiv);
    scrollToBottom();
}

/**
 * Clear chat history
 */
function clearChat() {
    if (confirm('Clear chat history and start a new session?')) {
        // Clear UI
        while (chatContainer.firstChild) {
            chatContainer.removeChild(chatContainer.firstChild);
        }

        // Clear session on server
        if (sessionId) {
            socket.emit('clear_session', { session_id: sessionId });
        }

        // Reset state
        sessionId = null;
        currentAssistantMessage = null;
        isWaitingForResponse = false;

        // Clear URL parameter
        const url = new URL(window.location);
        url.searchParams.delete('session');
        window.history.replaceState({}, '', url);

        // Show welcome message again
        location.reload();
    }
}

/**
 * Scroll to bottom of chat
 */
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Update URL with current session ID
 */
function updateUrlWithSession(newSessionId) {
    if (!newSessionId) return;

    const url = new URL(window.location);
    url.searchParams.set('session', newSessionId);
    window.history.replaceState({}, '', url);
    console.log('Updated URL with session:', newSessionId);
}

/**
 * Get session ID from URL
 */
function getSessionIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('session');
}

/**
 * Toggle sidebar visibility
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

/**
 * Load and render session list
 */
function loadSessionList() {
    socket.emit('list_sessions');
}

/**
 * Render session list in sidebar
 */
function renderSessionList(sessions) {
    const sessionList = document.getElementById('sessionList');
    sessionList.innerHTML = '';

    if (sessions.length === 0) {
        sessionList.innerHTML = '<div class="session-list-empty">No saved conversations</div>';
        return;
    }

    sessions.forEach(session => {
        const sessionEl = document.createElement('div');
        sessionEl.className = 'session-item';
        if (session.session_id === sessionId) {
            sessionEl.classList.add('active');
        }
        sessionEl.dataset.sessionId = session.session_id;

        // Format timestamp
        const date = new Date(session.last_activity);
        const timeAgo = formatTimeAgo(date);

        sessionEl.innerHTML = `
            <div class="session-main">
                <div class="session-header">
                    <div class="session-title">${escapeHtml(session.title)}</div>
                    <div class="session-actions">
                        <button class="session-action-btn" title="Rename">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                        </button>
                        <button class="session-action-btn delete" title="Delete">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="session-meta">
                    <span class="session-time">${timeAgo}</span>
                    <span class="session-count">${session.message_count} messages</span>
                </div>
            </div>
        `;

        // Add click event listener to session-main
        const sessionMain = sessionEl.querySelector('.session-main');
        sessionMain.addEventListener('click', () => {
            resumeSession(session.session_id);
        });

        // Add click event listeners to action buttons
        const editBtn = sessionEl.querySelector('.session-action-btn:not(.delete)');
        const deleteBtn = sessionEl.querySelector('.session-action-btn.delete');

        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            editSessionTitle(session.session_id, session.title);
        });

        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSession(session.session_id);
        });

        sessionList.appendChild(sessionEl);
    });
}

/**
 * Format time ago string
 */
function formatTimeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

    return date.toLocaleDateString();
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Start a new chat session
 */
function startNewChat() {
    // Clear UI
    while (chatContainer.firstChild) {
        chatContainer.removeChild(chatContainer.firstChild);
    }

    // Reset state
    sessionId = null;
    currentAssistantMessage = null;
    isWaitingForResponse = false;
    sendButton.disabled = false;

    // Clear URL parameter
    const url = new URL(window.location);
    url.searchParams.delete('session');
    window.history.replaceState({}, '', url);
    console.log('Cleared session from URL');

    // Show welcome message
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'welcome-message';
    welcomeDiv.innerHTML = `
        <h2>Available Forecasts</h2>
        <p><strong>Products:</strong> Electric vehicles, solar panels, batteries, commercial vehicles</p>
        <p><strong>Commodities:</strong> Copper, lithium, lead, coal, oil, natural gas</p>
        <p><strong>Disruptions:</strong> Cross-market impacts and displacement timelines</p>
        <p class="example-prompt">Example: "What is the forecast for electric vehicles in China through 2040?"</p>
    `;
    chatContainer.appendChild(welcomeDiv);

    // Refresh session list
    loadSessionList();
    messageInput.focus();
}

/**
 * Resume a previous session
 */
function resumeSession(newSessionId) {
    if (newSessionId === sessionId) {
        return; // Already active
    }

    console.log('Resuming session:', newSessionId);
    socket.emit('resume_session', { session_id: newSessionId });
}

/**
 * Handle session resumed event
 */
function handleSessionResumed(data) {
    console.log('Session resumed:', data.session_id);

    // Clear current chat
    while (chatContainer.firstChild) {
        chatContainer.removeChild(chatContainer.firstChild);
    }

    // Update session ID
    sessionId = data.session_id;
    updateUrlWithSession(sessionId);

    // Render conversation history
    if (data.history && data.history.length > 0) {
        data.history.forEach(msg => {
            if (msg.role === 'user') {
                addUserMessage(msg.content);
            } else if (msg.role === 'assistant') {
                addAssistantMessage(msg.content);
            }
        });
    }

    // Update active session in sidebar
    document.querySelectorAll('.session-item').forEach(el => {
        el.classList.remove('active');
    });
    const activeSession = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (activeSession) {
        activeSession.classList.add('active');
    }

    // Refresh session list to update counts
    loadSessionList();
    messageInput.focus();
}

/**
 * Add assistant message to chat (for history rendering)
 */
function addAssistantMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-assistant';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content markdown-content';
    contentDiv.innerHTML = marked.parse(text);

    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Delete a session
 */
function deleteSession(delSessionId) {
    if (confirm('Delete this conversation? This action cannot be undone.')) {
        console.log('Deleting session:', delSessionId);
        socket.emit('delete_session', { session_id: delSessionId });
    }
}

/**
 * Edit session title
 */
function editSessionTitle(editSessionId, currentTitle) {
    const newTitle = prompt('Enter new title:', currentTitle);
    if (newTitle && newTitle.trim() !== '' && newTitle !== currentTitle) {
        console.log('Updating title for session:', editSessionId);
        socket.emit('update_session_title', {
            session_id: editSessionId,
            title: newTitle.trim()
        });
    }
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Configure marked.js options
    marked.setOptions({
        breaks: true,          // Convert \n to <br>
        gfm: true,            // GitHub Flavored Markdown
        headerIds: false,      // Don't add IDs to headers
        mangle: false,        // Don't mangle email addresses
    });

    initializeSocket();

    // Check if session ID is in URL and auto-resume
    const urlSessionId = getSessionIdFromUrl();
    if (urlSessionId) {
        console.log('Found session in URL, will auto-resume:', urlSessionId);
        sessionId = urlSessionId;

        // Wait for socket connection before resuming
        socket.on('connect', () => {
            if (urlSessionId && !isWaitingForResponse) {
                console.log('Auto-resuming session from URL:', urlSessionId);
                resumeSession(urlSessionId);
            }
        });
    } else {
        messageInput.focus();
    }

    // Load session list on startup
    setTimeout(() => {
        loadSessionList();
    }, 500);

    // Enable send button when input has text
    messageInput.addEventListener('input', () => {
        sendButton.disabled = !messageInput.value.trim() || isWaitingForResponse;
    });
});
