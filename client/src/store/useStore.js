import { create } from 'zustand';

const useStore = create((set, get) => ({
  // Connection state
  socket: null,
  isConnected: false,
  connectionStatus: 'connecting',

  // Session state
  sessionId: null,
  sessions: [],

  // Messages state
  messages: [],
  currentAssistantMessage: null,
  contentBlocks: {},
  isWaitingForResponse: false,

  // UI state
  isSidebarCollapsed: false,
  isCompareMode: false,
  selectedSessions: [],
  comparisonData: null,
  showComparisonModal: false,

  // Actions
  setSocket: (socket) => set({ socket }),

  setConnectionStatus: (status, isConnected) => set({
    connectionStatus: status,
    isConnected
  }),

  setSessionId: (sessionId) => {
    set({ sessionId });
    // Update URL with session ID
    if (sessionId) {
      const url = new URL(window.location);
      url.searchParams.set('session', sessionId);
      window.history.replaceState({}, '', url);
    }
  },

  setSessions: (sessions) => set({ sessions }),

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  updateLastMessage: (updates) => set((state) => ({
    messages: state.messages.map((msg, idx) =>
      idx === state.messages.length - 1 ? { ...msg, ...updates } : msg
    )
  })),

  setCurrentAssistantMessage: (message) => set({ currentAssistantMessage: message }),

  appendToCurrentAssistant: (text) => set((state) => ({
    currentAssistantMessage: {
      ...state.currentAssistantMessage,
      content: (state.currentAssistantMessage?.content || '') + text
    }
  })),

  setMessages: (messages) => set({ messages }),

  clearMessages: () => set({ messages: [], currentAssistantMessage: null, contentBlocks: {} }),

  setWaitingForResponse: (isWaiting) => set({ isWaitingForResponse: isWaiting }),

  // Content blocks (for tool execution and thinking)
  addContentBlock: (index, block) => set((state) => ({
    contentBlocks: { ...state.contentBlocks, [index]: block }
  })),

  updateContentBlock: (index, updates) => set((state) => ({
    contentBlocks: {
      ...state.contentBlocks,
      [index]: { ...state.contentBlocks[index], ...updates }
    }
  })),

  clearContentBlocks: () => set({ contentBlocks: {} }),

  // UI actions
  toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

  toggleCompareMode: () => set((state) => ({
    isCompareMode: !state.isCompareMode,
    selectedSessions: !state.isCompareMode ? [] : state.selectedSessions
  })),

  toggleSessionSelection: (sessionId) => set((state) => {
    const { selectedSessions } = state;
    if (selectedSessions.includes(sessionId)) {
      return { selectedSessions: selectedSessions.filter(id => id !== sessionId) };
    } else if (selectedSessions.length < 2) {
      return { selectedSessions: [...selectedSessions, sessionId] };
    }
    return {};
  }),

  setComparisonData: (data) => set({ comparisonData: data, showComparisonModal: true }),

  closeComparisonModal: () => set({ showComparisonModal: false }),

  // Session management
  startNewChat: () => {
    set({
      sessionId: null,
      messages: [],
      currentAssistantMessage: null,
      contentBlocks: {},
      isWaitingForResponse: false
    });
    // Clear URL parameter
    const url = new URL(window.location);
    url.searchParams.delete('session');
    window.history.replaceState({}, '', url);
  },

  resumeSession: (sessionId, history) => {
    set({
      sessionId,
      messages: history || [],
      currentAssistantMessage: null,
      contentBlocks: {},
      isWaitingForResponse: false
    });
    // Update URL with session ID
    const url = new URL(window.location);
    url.searchParams.set('session', sessionId);
    window.history.replaceState({}, '', url);
  },
}));

export default useStore;
