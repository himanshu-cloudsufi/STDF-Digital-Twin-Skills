# Demand Forecasting Chatbot - React Frontend

A modern React + Vite + Tailwind CSS implementation of the Demand Forecasting Chatbot with real-time WebSocket communication.

## Features

✨ **Real-time Chat** - Streaming responses with Socket.IO
📝 **Markdown Support** - Rendered messages with code highlighting
🛠️ **Tool Execution** - Collapsible tool/code execution blocks
💭 **Thinking Blocks** - View Claude's thinking process
📂 **Session Management** - Save, resume, rename, and delete conversations
🔍 **Chat Comparison** - Compare two chat sessions side-by-side
📤 **Export** - Export to Markdown or PDF
📱 **Responsive Design** - Mobile-friendly layout
🎨 **Tailwind CSS** - Modern utility-first styling
⚡ **Zustand** - Lightweight state management

## Tech Stack

- **React 19** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Socket.IO Client** - WebSocket communication
- **Marked** - Markdown parsing
- **jsPDF** - PDF export

## Setup Instructions

### Prerequisites

- Node.js 20.19+ or 22.12+
- npm
- Backend server running on `http://localhost:5000`

### Installation

1. **Navigate to the client directory:**
   ```bash
   cd client
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The app will open at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

### Configuration

The WebSocket proxy is configured in `vite.config.js`. Change the target if your backend runs on a different port:

```javascript
server: {
  proxy: {
    '/socket.io': {
      target: 'http://localhost:5000',  // Change this if needed
      ws: true,
      changeOrigin: true
    }
  }
}
```

## Project Structure

```
client/src/
├── features/
│   ├── chat/          # Chat components (messages, input, tool blocks)
│   ├── sidebar/       # Session list and management
│   ├── comparison/    # Chat comparison modal
│   ├── export/        # Export utilities (Markdown, PDF)
│   └── header/        # Header and connection status
├── hooks/             # Custom hooks (useSocket)
├── store/             # Zustand store
├── utils/             # Utility functions
└── App.jsx            # Main app component
```

## Usage

- **New Chat**: Click "New Chat" button in sidebar
- **Resume Session**: Click any session in the sidebar
- **Compare Chats**: Click "Compare Chats", select 2 sessions, then "Compare Selected"
- **Export**: Click "MD" or "PDF" buttons in header
- **Manage Sessions**: Hover over sessions to rename or delete

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
