/**
 * Demand Forecasting Chatbot - WebSocket Client
 */

// Global state
let socket = null;
let sessionId = null;
let isWaitingForResponse = false;
let currentAssistantMessage = null;
let contentBlocks = {};  // Track content blocks by index for tool use and code execution

// Comparison mode state
let isCompareMode = false;
let selectedSessions = [];

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

    socket.on('retry_notification', (data) => {
        console.log('Retry notification:', data);
        addSystemMessage(`⚠️ ${data.message}`);
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

    // New event handlers for code execution and tool use visibility
    socket.on('content_block_start', (data) => {
        console.log('Content block started:', data);
        handleContentBlockStart(data);
    });

    socket.on('tool_input_delta', (data) => {
        console.log('Tool input delta:', data);
        handleToolInputDelta(data);
    });

    socket.on('thinking_chunk', (data) => {
        console.log('Thinking chunk:', data);
        handleThinkingChunk(data);
    });

    socket.on('content_block_stop', (data) => {
        console.log('Content block stopped:', data);
        handleContentBlockStop(data);
    });

    socket.on('message_start', (data) => {
        console.log('Message started:', data);
    });

    socket.on('usage_update', (data) => {
        console.log('Usage update:', data);
        handleUsageUpdate(data);
    });

    // Comparison events
    socket.on('comparison_complete', (data) => {
        console.log('Comparison complete:', data);
        displayComparisonResults(data);
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

    // Render the accumulated markdown
    renderMarkdownContent(currentAssistantMessage);

    // Update session ID
    if (data.session_id) {
        sessionId = data.session_id;
        updateUrlWithSession(sessionId);
    }
}

/**
 * Render markdown content from raw text
 */
function renderMarkdownContent(contentElement) {
    if (!contentElement || !contentElement.dataset.rawText) {
        return;
    }

    try {
        // Parse and render markdown
        const rawText = contentElement.dataset.rawText;
        contentElement.innerHTML = marked.parse(rawText);
        scrollToBottom();
    } catch (error) {
        console.error('Markdown rendering error:', error);
        // Fallback to plain text if markdown parsing fails
        contentElement.textContent = contentElement.dataset.rawText;
    }
}

/**
 * Handle assistant message completion
 */
function handleAssistantComplete(data) {
    currentAssistantMessage = null;
    contentBlocks = {};  // Clear content blocks for next message
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
 * Export chat to Markdown
 */
function exportChatToMarkdown() {
    const chatMessages = document.querySelectorAll('.message');

    if (chatMessages.length === 0) {
        alert('No messages to export!');
        return;
    }

    // Disable button during export
    const exportBtn = document.querySelector('.export-md');
    const originalText = exportBtn.innerHTML;
    exportBtn.disabled = true;
    exportBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> ...';

    try {
        let markdown = '# Demand Forecasting Chat Export\n\n';
        markdown += `**Exported:** ${new Date().toLocaleString()}\n\n`;
        markdown += '---\n\n';

        // Process each message
        chatMessages.forEach(message => {
            const isUser = message.classList.contains('message-user');
            const isAssistant = message.classList.contains('message-assistant');
            const isSystem = message.classList.contains('message-system');

            // Skip typing indicators
            if (message.id === 'typing-indicator') return;

            const content = message.querySelector('.message-content');
            if (!content) return;

            // For assistant messages with markdown, get the raw text from dataset
            let text;
            if (isAssistant && content.dataset.rawText) {
                text = content.dataset.rawText.trim();
            } else {
                text = (content.textContent || content.innerText).trim();
            }

            if (!text) return;

            // Add role header
            if (isUser) {
                markdown += '## 👤 User\n\n';
            } else if (isAssistant) {
                markdown += '## 🤖 Assistant\n\n';
            } else if (isSystem) {
                markdown += '## ⚙️ System\n\n';
            }

            // Add message content
            markdown += text + '\n\n';
            markdown += '---\n\n';
        });

        // Create blob and download
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // Generate filename with timestamp
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        a.download = `chat-export-${timestamp}.md`;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Show success message
        addSystemMessage(`Chat exported successfully as ${a.download}`);
    } catch (error) {
        console.error('Markdown export error:', error);
        alert('Failed to export Markdown. Please try again.');
    } finally {
        // Re-enable button
        exportBtn.disabled = false;
        exportBtn.innerHTML = originalText;
    }
}

/**
 * Export chat to PDF
 */
async function exportChatToPDF() {
    const chatMessages = document.querySelectorAll('.message');

    if (chatMessages.length === 0) {
        alert('No messages to export!');
        return;
    }

    // Disable button during export
    const exportBtn = document.querySelector('.export-pdf');
    const originalText = exportBtn.innerHTML;
    exportBtn.disabled = true;
    exportBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> ...';

    try {
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');

        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();
        const margin = 15;
        const contentWidth = pageWidth - (2 * margin);
        let yPosition = margin;

        // Add title
        pdf.setFontSize(16);
        pdf.setFont(undefined, 'bold');
        pdf.text('Demand Forecasting Chat Export', margin, yPosition);
        yPosition += 10;

        // Add export date
        pdf.setFontSize(10);
        pdf.setFont(undefined, 'normal');
        pdf.setTextColor(100, 100, 100);
        const exportDate = new Date().toLocaleString();
        pdf.text(`Exported: ${exportDate}`, margin, yPosition);
        yPosition += 10;

        // Add separator line
        pdf.setDrawColor(200, 200, 200);
        pdf.line(margin, yPosition, pageWidth - margin, yPosition);
        yPosition += 8;

        // Reset text color
        pdf.setTextColor(0, 0, 0);

        // Process each message
        for (let i = 0; i < chatMessages.length; i++) {
            const message = chatMessages[i];
            const isUser = message.classList.contains('message-user');
            const isAssistant = message.classList.contains('message-assistant');
            const isSystem = message.classList.contains('message-system');

            // Skip typing indicators
            if (message.id === 'typing-indicator') continue;

            const content = message.querySelector('.message-content');
            if (!content) continue;

            // Get text content, handling markdown content
            let text = content.textContent || content.innerText;
            text = text.trim();

            if (!text) continue;

            // Check if we need a new page
            if (yPosition > pageHeight - 40) {
                pdf.addPage();
                yPosition = margin;
            }

            // Set role styling
            if (isUser) {
                pdf.setFillColor(52, 152, 219);
                pdf.setTextColor(255, 255, 255);
                pdf.setFont(undefined, 'bold');
                pdf.text('User:', margin, yPosition);
                yPosition += 6;
            } else if (isAssistant) {
                pdf.setFillColor(240, 240, 240);
                pdf.setTextColor(0, 0, 0);
                pdf.setFont(undefined, 'bold');
                pdf.text('Assistant:', margin, yPosition);
                yPosition += 6;
            } else if (isSystem) {
                pdf.setFillColor(255, 243, 205);
                pdf.setTextColor(133, 100, 4);
                pdf.setFont(undefined, 'bold');
                pdf.text('System:', margin, yPosition);
                yPosition += 6;
            }

            // Reset font for content
            pdf.setFont(undefined, 'normal');
            pdf.setTextColor(0, 0, 0);

            // Split text into lines that fit the page width
            const lines = pdf.splitTextToSize(text, contentWidth);

            for (let line of lines) {
                // Check if we need a new page
                if (yPosition > pageHeight - 20) {
                    pdf.addPage();
                    yPosition = margin;
                }

                pdf.text(line, margin + 5, yPosition);
                yPosition += 5;
            }

            // Add spacing between messages
            yPosition += 5;

            // Add separator line between messages
            pdf.setDrawColor(230, 230, 230);
            pdf.line(margin, yPosition, pageWidth - margin, yPosition);
            yPosition += 5;
        }

        // Generate filename with timestamp
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `chat-export-${timestamp}.pdf`;

        // Save the PDF
        pdf.save(filename);

        // Show success message
        addSystemMessage(`Chat exported successfully as ${filename}`);
    } catch (error) {
        console.error('PDF export error:', error);
        alert('Failed to export PDF. Please try again.');
    } finally {
        // Re-enable button
        exportBtn.disabled = false;
        exportBtn.innerHTML = originalText;
    }
}

/**
 * Handle content block start event
 */
function handleContentBlockStart(data) {
    // Remove typing indicator if this is the first block
    if (Object.keys(contentBlocks).length === 0 && !currentAssistantMessage) {
        removeTypingIndicator();
    }

    const blockIndex = data.index;
    const blockType = data.type;

    console.log(`Content block started: index=${blockIndex}, type=${blockType}`);

    // Initialize block tracking
    contentBlocks[blockIndex] = {
        type: blockType,
        tool_name: data.tool_name,
        tool_id: data.tool_id,
        accumulated_json: '',
        element: null
    };

    // Create UI element based on block type
    if (blockType === 'tool_use' || blockType === 'server_tool_use') {
        createToolUseBlock(blockIndex, data.tool_name);
    } else if (blockType === 'thinking') {
        createThinkingBlock(blockIndex);
    } else if (blockType === 'text') {
        // Text blocks are handled by existing assistant_chunk handler
        if (!currentAssistantMessage) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message message-assistant';

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content markdown-content';
            contentDiv.id = 'current-assistant-message';
            contentDiv.dataset.rawText = '';

            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);

            currentAssistantMessage = contentDiv;
        }
    }
}

/**
 * Create a tool use block in the chat
 */
function createToolUseBlock(blockIndex, toolName) {
    const toolBlock = document.createElement('div');
    toolBlock.className = 'tool-execution-block';
    toolBlock.id = `tool-block-${blockIndex}`;
    toolBlock.dataset.blockIndex = blockIndex;

    // Determine if this is code execution or another tool
    const isCodeExecution = toolName === 'code_execution' || toolName === 'text_editor_code_execution';
    const isWebSearch = toolName === 'web_search';

    let icon = '🔧';
    let displayName = toolName || 'Tool';

    if (isCodeExecution) {
        icon = '⚙️';
        displayName = 'Code Execution';
    } else if (isWebSearch) {
        icon = '🔍';
        displayName = 'Web Search';
    } else if (toolName) {
        // Format tool name for display (e.g., "my_tool" -> "My Tool")
        displayName = toolName.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    toolBlock.innerHTML = `
        <div class="tool-header">
            <div class="tool-title">
                <span class="tool-icon">${icon}</span>
                <span class="tool-name">${displayName}</span>
                <span class="tool-status running">Running...</span>
            </div>
            <button class="tool-toggle" onclick="toggleToolDetails(${blockIndex})">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </button>
        </div>
        <div class="tool-details" id="tool-details-${blockIndex}">
            <div class="tool-input">
                <div class="tool-section-label">Input Parameters:</div>
                <pre class="tool-input-json" id="tool-input-${blockIndex}"><code>Loading...</code></pre>
            </div>
        </div>
    `;

    chatContainer.appendChild(toolBlock);
    scrollToBottom();

    // Store reference
    contentBlocks[blockIndex].element = toolBlock;
}

/**
 * Create a thinking block in the chat
 */
function createThinkingBlock(blockIndex) {
    const thinkingBlock = document.createElement('div');
    thinkingBlock.className = 'thinking-block';
    thinkingBlock.id = `thinking-block-${blockIndex}`;
    thinkingBlock.dataset.blockIndex = blockIndex;

    thinkingBlock.innerHTML = `
        <div class="thinking-header" onclick="toggleThinkingDetails(${blockIndex})">
            <div class="thinking-title">
                <span class="thinking-icon">💭</span>
                <span class="thinking-label">Claude's Thinking Process</span>
            </div>
            <button class="thinking-toggle">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </button>
        </div>
        <div class="thinking-content" id="thinking-content-${blockIndex}" style="display: none;">
            <div class="thinking-text"></div>
        </div>
    `;

    chatContainer.appendChild(thinkingBlock);
    scrollToBottom();

    // Store reference
    contentBlocks[blockIndex].element = thinkingBlock;
}

/**
 * Handle tool input delta event
 */
function handleToolInputDelta(data) {
    const blockIndex = data.index;
    const blockInfo = contentBlocks[blockIndex];

    if (!blockInfo) {
        console.warn(`Received tool input delta for unknown block ${blockIndex}`);
        return;
    }

    // Update accumulated JSON
    blockInfo.accumulated_json = data.accumulated_json;

    // Update the UI with the latest JSON
    const inputElement = document.getElementById(`tool-input-${blockIndex}`);
    if (inputElement) {
        try {
            // Try to parse and pretty-print the JSON
            const parsed = JSON.parse(data.accumulated_json);
            inputElement.innerHTML = `<code>${escapeHtml(JSON.stringify(parsed, null, 2))}</code>`;
        } catch (e) {
            // If not valid JSON yet, show raw accumulated text
            inputElement.innerHTML = `<code>${escapeHtml(data.accumulated_json)}</code>`;
        }
    }
}

/**
 * Handle thinking chunk event
 */
function handleThinkingChunk(data) {
    const blockIndex = data.index;
    const blockInfo = contentBlocks[blockIndex];

    if (!blockInfo) {
        console.warn(`Received thinking chunk for unknown block ${blockIndex}`);
        return;
    }

    // Append thinking text
    const thinkingBlock = document.getElementById(`thinking-block-${blockIndex}`);
    if (thinkingBlock) {
        const textContainer = thinkingBlock.querySelector('.thinking-text');
        if (textContainer) {
            textContainer.textContent += data.text;
            scrollToBottom();
        }
    }
}

/**
 * Handle content block stop event
 */
function handleContentBlockStop(data) {
    const blockIndex = data.index;
    const blockInfo = contentBlocks[blockIndex];

    if (!blockInfo) {
        console.warn(`Received block stop for unknown block ${blockIndex}`);
        return;
    }

    console.log(`Content block stopped: index=${blockIndex}, type=${blockInfo.type}`);

    // Update tool block status if it's a tool
    if (blockInfo.type === 'tool_use' || blockInfo.type === 'server_tool_use') {
        const toolBlock = document.getElementById(`tool-block-${blockIndex}`);
        if (toolBlock) {
            const statusElement = toolBlock.querySelector('.tool-status');
            if (statusElement) {
                statusElement.textContent = 'Completed';
                statusElement.className = 'tool-status completed';
            }

            // Parse and display final JSON
            if (data.accumulated_json) {
                try {
                    const parsed = JSON.parse(data.accumulated_json);
                    const inputElement = document.getElementById(`tool-input-${blockIndex}`);
                    if (inputElement) {
                        inputElement.innerHTML = `<code>${escapeHtml(JSON.stringify(parsed, null, 2))}</code>`;
                    }
                } catch (e) {
                    console.error('Failed to parse final JSON:', e);
                }
            }
        }
    }
}

/**
 * Handle usage update event
 */
function handleUsageUpdate(data) {
    console.log('Token usage:', data.usage);
    // Could display this in the UI if desired
    // For now, just logging
}

/**
 * Toggle tool details visibility
 */
function toggleToolDetails(blockIndex) {
    const details = document.getElementById(`tool-details-${blockIndex}`);
    const toggle = document.querySelector(`#tool-block-${blockIndex} .tool-toggle svg`);

    if (details && toggle) {
        if (details.style.display === 'none') {
            details.style.display = 'block';
            toggle.style.transform = 'rotate(180deg)';
        } else {
            details.style.display = 'none';
            toggle.style.transform = 'rotate(0deg)';
        }
    }
}

/**
 * Toggle thinking details visibility
 */
function toggleThinkingDetails(blockIndex) {
    const content = document.getElementById(`thinking-content-${blockIndex}`);
    const toggle = document.querySelector(`#thinking-block-${blockIndex} .thinking-toggle svg`);

    if (content && toggle) {
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggle.style.transform = 'rotate(180deg)';
        } else {
            content.style.display = 'none';
            toggle.style.transform = 'rotate(0deg)';
        }
    }
}

// ============================================================================
// COMPARISON FUNCTIONS
// ============================================================================

/**
 * Toggle comparison mode
 */
function toggleCompareMode() {
    isCompareMode = !isCompareMode;
    selectedSessions = [];

    const compareModeButton = document.getElementById('compareModeButton');
    const compareControls = document.getElementById('compareControls');
    const sessionList = document.getElementById('sessionList');

    if (isCompareMode) {
        // Enter compare mode
        compareModeButton.classList.add('active');
        compareControls.style.display = 'block';

        // Add checkboxes to all session items
        const sessions = sessionList.querySelectorAll('.session-item');
        sessions.forEach(sessionItem => {
            if (!sessionItem.querySelector('.session-checkbox')) {
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'session-checkbox';
                checkbox.dataset.sessionId = sessionItem.dataset.sessionId;
                checkbox.addEventListener('change', handleSessionCheckboxChange);
                sessionItem.insertBefore(checkbox, sessionItem.firstChild);
            }
        });
    } else {
        // Exit compare mode
        compareModeButton.classList.remove('active');
        compareControls.style.display = 'none';

        // Remove all checkboxes
        const checkboxes = sessionList.querySelectorAll('.session-checkbox');
        checkboxes.forEach(checkbox => checkbox.remove());
    }

    updateCompareButton();
}

/**
 * Handle session checkbox change
 */
function handleSessionCheckboxChange(event) {
    const sessionId = event.target.dataset.sessionId;
    const isChecked = event.target.checked;

    if (isChecked) {
        // Add to selected sessions (max 2)
        if (selectedSessions.length < 2) {
            selectedSessions.push(sessionId);
        } else {
            // Already have 2 selected, uncheck this one
            event.target.checked = false;
            return;
        }
    } else {
        // Remove from selected sessions
        selectedSessions = selectedSessions.filter(id => id !== sessionId);
    }

    // If trying to select more than 2, uncheck all others
    if (selectedSessions.length === 2) {
        const allCheckboxes = document.querySelectorAll('.session-checkbox');
        allCheckboxes.forEach(cb => {
            if (!selectedSessions.includes(cb.dataset.sessionId)) {
                cb.disabled = true;
            }
        });
    } else {
        // Re-enable all checkboxes
        const allCheckboxes = document.querySelectorAll('.session-checkbox');
        allCheckboxes.forEach(cb => {
            cb.disabled = false;
        });
    }

    updateCompareButton();
}

/**
 * Update compare button state
 */
function updateCompareButton() {
    const compareActionButton = document.getElementById('compareActionButton');
    compareActionButton.disabled = selectedSessions.length !== 2;

    const instructions = document.querySelector('.compare-instructions');
    if (selectedSessions.length === 0) {
        instructions.textContent = 'Select 2 chats to compare';
    } else if (selectedSessions.length === 1) {
        instructions.textContent = 'Select 1 more chat';
    } else {
        instructions.textContent = 'Ready to compare!';
    }
}

/**
 * Compare selected chats
 */
function compareSelectedChats() {
    if (selectedSessions.length !== 2) {
        return;
    }

    console.log('Comparing sessions:', selectedSessions);

    // Show modal with loading state
    const modal = document.getElementById('comparisonModal');
    const resultDiv = document.getElementById('comparisonResult');
    resultDiv.innerHTML = '<div class="loading-spinner">Analyzing chats with Haiku model...</div>';
    modal.style.display = 'flex';

    // Emit comparison request
    socket.emit('compare_sessions', {
        session_id_1: selectedSessions[0],
        session_id_2: selectedSessions[1]
    });
}

/**
 * Display comparison results in modal
 */
function displayComparisonResults(data) {
    console.log('Displaying comparison results:', data);

    // Update chat info
    document.getElementById('chat1Title').textContent = data.session_1.title;
    document.getElementById('chat1Count').textContent = `(${data.session_1.message_count} messages)`;
    document.getElementById('chat2Title').textContent = data.session_2.title;
    document.getElementById('chat2Count').textContent = `(${data.session_2.message_count} messages)`;

    // Display comparison result (use markdown rendering)
    const resultDiv = document.getElementById('comparisonResult');
    const comparisonHtml = marked.parse(data.comparison);
    resultDiv.innerHTML = comparisonHtml;
}

/**
 * Close comparison modal
 */
function closeComparisonModal(event) {
    // Only close if clicking overlay or close button
    if (!event || event.target === event.currentTarget || event === undefined) {
        const modal = document.getElementById('comparisonModal');
        modal.style.display = 'none';
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

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
