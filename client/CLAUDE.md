# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **React frontend client** for a Demand Forecasting Chatbot that communicates with a Python backend via WebSocket (Socket.IO). The application provides real-time chat streaming, session management, chat comparison, and export functionality.

## Tech Stack

- **React 19.1** - UI library
- **Vite 7.1** - Build tool and dev server
- **Tailwind CSS 3.4** - Utility-first styling
- **Zustand 5.0** - Lightweight state management
- **Socket.IO Client 4.8** - WebSocket communication
- **Marked 14.1** - Markdown parsing and rendering
- **jsPDF 2.5** + **html2canvas 1.4** - PDF export

## Development Commands

```bash
# Install dependencies
npm install

# Start development server (runs on http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## Backend Connection

The frontend expects a backend server running on **http://localhost:8000** with Socket.IO support. The WebSocket proxy is configured in `vite.config.js`:

```javascript
server: {
  proxy: {
    '/socket.io': {
      target: 'http://localhost:8000',
      ws: true,
      changeOrigin: true
    }
  }
}
```

**To change backend port**: Edit `vite.config.js` and update the target URL.

## Architecture

### Feature-Based Structure

The codebase uses a **feature-based architecture** where related components are grouped by feature:

```
src/
├── features/
│   ├── chat/          # Chat UI components (messages, input, tool execution)
│   ├── sidebar/       # Session list and management
│   ├── comparison/    # Side-by-side chat comparison
│   ├── export/        # Export utilities (Markdown, PDF)
│   └── header/        # Header and connection status
├── hooks/             # Custom React hooks
├── store/             # Zustand global state
├── utils/             # Utility functions
├── App.jsx            # Main app component
└── main.jsx           # React entry point
```

### State Management (Zustand)

The application uses a **single Zustand store** (`src/store/useStore.js`) that manages:

- **Connection state**: socket, isConnected, connectionStatus
- **Session state**: sessionId, sessions, messages
- **Streaming state**: currentAssistantMessage, contentBlocks, isWaitingForResponse
- **UI state**: isSidebarCollapsed, isCompareMode, selectedSessions, comparisonData

**Key patterns**:
- State is accessed via `useStore()` hook selectors
- Actions are defined in the store and called directly
- URL state is synchronized with sessionId (query param: `?session=<id>`)

### WebSocket Communication (useSocket hook)

The `src/hooks/useSocket.js` hook:
- Establishes Socket.IO connection on mount
- Registers event handlers for all server events
- Updates Zustand store based on incoming events
- Auto-resumes sessions from URL parameter (`?session=<id>`)
- Loads session list on startup

**Key Socket.IO events**:

**Outgoing (client → server)**:
- `send_message` - Send user message
- `list_sessions` - Request session list
- `resume_session` - Resume existing session
- `rename_session` - Rename session title
- `delete_session` - Delete session
- `compare_sessions` - Request comparison of two sessions

**Incoming (server → client)**:
- `connect` / `disconnect` / `connect_error` - Connection events
- `assistant_chunk` - Streaming response text
- `assistant_complete` - Response finished
- `tool_use` - Tool execution display
- `content_block_start` / `content_block_stop` - Tool/thinking blocks
- `tool_input_delta` - Tool input streaming
- `thinking_chunk` - Thinking block streaming
- `sessions_list` - List of available sessions
- `session_resumed` - Session history loaded
- `comparison_complete` - Comparison data ready
- `error` - Error message
- `retry_notification` - API retry notification

### Message Flow

1. **User sends message** → `InputArea.jsx` emits `send_message` event
2. **Server processes** → Backend calls Anthropic API with streaming
3. **Streaming chunks** → Server emits `assistant_chunk` events
4. **Frontend updates** → `useSocket` appends chunks to `currentAssistantMessage`
5. **Completion** → Server emits `assistant_complete`, clears streaming state
6. **Session saved** → Messages persisted to database on backend

### Content Blocks

**Tool execution and thinking blocks** are tracked separately in `contentBlocks` state:

```javascript
contentBlocks = {
  [index]: {
    type: 'tool_use' | 'thinking',
    tool_name: string,
    tool_id: string,
    accumulated_json: string,  // For tool_use
    thinking_text: string,     // For thinking
    status: 'running' | 'completed'
  }
}
```

These are displayed as collapsible blocks in `ToolExecutionBlock.jsx`.

## Key Features

### 1. Real-Time Chat Streaming
- Messages stream character-by-character via `assistant_chunk` events
- `currentAssistantMessage` tracks in-progress message
- Messages append to `messages` array when complete

### 2. Session Management
- Sessions stored in backend SQLite database
- Auto-resume from URL query parameter (`?session=<id>`)
- Rename, delete, and create new sessions
- Session list auto-refreshes after operations

### 3. Chat Comparison
- Select 2 sessions from sidebar (compare mode)
- Server generates side-by-side comparison
- Displays in modal (`ComparisonModal.jsx`)
- Shows aligned messages with differences

### 4. Export
- **Markdown export** (`exportToMarkdown.js`): Plain text with markdown formatting
- **PDF export** (`exportToPDF.js`): Uses jsPDF + html2canvas to render chat

### 5. Markdown Rendering
- Uses `marked` library to parse markdown in messages
- Code blocks, lists, tables, and inline formatting supported
- Rendered in `AssistantMessage.jsx`

## Important Implementation Notes

### URL State Synchronization
The `sessionId` is always kept in sync with the URL query parameter:
- On session change → Update URL
- On page load → Check URL for session ID and auto-resume
- On new chat → Clear URL parameter

This enables **shareable session links** and **browser back/forward navigation**.

### Message Types
Messages have different `role` values:
- `user` - User input (displayed with `UserMessage.jsx`)
- `assistant` - AI response (displayed with `AssistantMessage.jsx`)
- `tool` - Tool execution (displayed with `ToolExecutionBlock.jsx`)
- `system` - System notifications (displayed with `SystemMessage.jsx`)

### Streaming State Management
Two states track streaming:
- `currentAssistantMessage` - The in-progress message being streamed
- `isWaitingForResponse` - Whether we're waiting for any response

**Pattern**:
```javascript
// Start streaming
if (!currentAssistantMessage) {
  const newMessage = { role: 'assistant', content: text, isStreaming: true };
  addMessage(newMessage);
  setCurrentAssistantMessage(newMessage);
} else {
  appendToCurrentAssistant(text);
}

// Complete streaming
setCurrentAssistantMessage(null);
setWaitingForResponse(false);
```

### Error Handling
- Connection errors → Display in `ConnectionStatus` component
- Server errors → Add system message to chat
- Retry notifications → Display inline as system messages

## Common Development Tasks

### Adding a New Socket Event

1. **Register handler in `useSocket.js`**:
```javascript
socket.on('new_event', (data) => {
  handleNewEvent(data);
});
```

2. **Create handler function**:
```javascript
const handleNewEvent = (data) => {
  // Update store or trigger action
  addMessage({ role: 'system', content: data.message });
};
```

3. **Update store if needed** (in `useStore.js`):
```javascript
newState: null,
setNewState: (value) => set({ newState: value }),
```

### Adding a New Feature Component

1. **Create feature directory**: `src/features/new-feature/`
2. **Add components**: `NewFeature.jsx`, `FeatureItem.jsx`, etc.
3. **Import in `App.jsx`** or parent component
4. **Connect to store**: Use `useStore()` for state and actions

### Modifying the UI Theme

All styling uses **Tailwind CSS utility classes**. Common patterns:

- Layout: `flex`, `grid`, `w-full`, `h-screen`
- Spacing: `p-4`, `m-2`, `gap-4`
- Colors: `bg-gray-100`, `text-gray-700`, `border-gray-300`
- Responsive: `sm:`, `md:`, `lg:` prefixes

**Global styles** are in `src/index.css` and `tailwind.config.js`.

### Testing WebSocket Events

Use browser DevTools console:
```javascript
// Access store
const store = useStore.getState();

// Emit event
store.socket.emit('event_name', { data: 'value' });

// Check state
console.log(store.messages);
```

## Debugging Tips

### Socket Connection Issues
1. Check backend is running on port 8000
2. Verify `vite.config.js` proxy target matches backend port
3. Check browser console for connection errors
4. Inspect Network tab for WebSocket frames

### State Not Updating
1. Verify Zustand action is called: `console.log()` in action
2. Check if selector is correct: `useStore(state => state.messages)`
3. Ensure component re-renders on state change

### Streaming Issues
1. Check `currentAssistantMessage` state
2. Verify `assistant_chunk` events are received
3. Ensure `appendToCurrentAssistant()` is called
4. Check if `assistant_complete` clears streaming state

## Build and Deployment

### Production Build
```bash
npm run build
```
Outputs to `dist/` directory. Serve with any static file server.

### Environment Variables
No environment variables required for frontend. Backend connection is configured in `vite.config.js`.

### Deployment Checklist
- [ ] Update backend URL in `vite.config.js` for production
- [ ] Run `npm run build`
- [ ] Test production build with `npm run preview`
- [ ] Ensure CORS is configured on backend for production domain
- [ ] Verify WebSocket connection works in production environment
