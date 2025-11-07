import { useEffect } from 'react';
import { io } from 'socket.io-client';
import useStore from '../store/useStore';

const useSocket = () => {
  const {
    setSocket,
    setConnectionStatus,
    setSessionId,
    setSessions,
    addMessage,
    setCurrentAssistantMessage,
    appendToCurrentAssistant,
    setWaitingForResponse,
    addContentBlock,
    updateContentBlock,
    clearContentBlocks,
    setComparisonData,
    resumeSession,
  } = useStore();

  useEffect(() => {
    const socket = io();
    setSocket(socket);

    // Connection events
    socket.on('connect', () => {
      console.log('Connected to server');
      setConnectionStatus('Connected', true);
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
      setConnectionStatus('Disconnected', false);
      setWaitingForResponse(false);
    });

    socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
      setConnectionStatus('Connection error', false);
    });

    // Chat events
    socket.on('status', (data) => {
      console.log('Status:', data.message);
    });

    socket.on('user_message', (data) => {
      if (data.session_id) {
        setSessionId(data.session_id);
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
        setSessionId(data.session_id);
      }
    });

    socket.on('error', (data) => {
      console.error('Server error:', data.message);
      addMessage({
        role: 'system',
        content: `Error: ${data.message}`,
        timestamp: new Date().toISOString()
      });
      setWaitingForResponse(false);
    });

    socket.on('retry_notification', (data) => {
      console.log('Retry notification:', data);
      addMessage({
        role: 'system',
        content: `⚠️ ${data.message}`,
        timestamp: new Date().toISOString()
      });
    });

    // Session management events
    socket.on('sessions_list', (data) => {
      setSessions(data.sessions);
    });

    socket.on('session_resumed', (data) => {
      handleSessionResumed(data);
    });

    socket.on('session_deleted', (data) => {
      // Refresh session list
      socket.emit('list_sessions');
    });

    socket.on('session_title_updated', (data) => {
      // Session list will be refreshed
      socket.emit('list_sessions');
    });

    // Content block events
    socket.on('content_block_start', (data) => {
      handleContentBlockStart(data);
    });

    socket.on('tool_input_delta', (data) => {
      handleToolInputDelta(data);
    });

    socket.on('thinking_chunk', (data) => {
      handleThinkingChunk(data);
    });

    socket.on('content_block_stop', (data) => {
      handleContentBlockStop(data);
    });

    socket.on('message_start', (data) => {
      console.log('Message started:', data);
    });

    socket.on('usage_update', (data) => {
      console.log('Usage update:', data);
    });

    // Comparison events
    socket.on('comparison_complete', (data) => {
      console.log('Comparison complete:', data);
      setComparisonData(data);
    });

    // Backfill events
    socket.on('backfill_complete', (data) => {
      console.log('Backfill complete:', data);
      addMessage({
        role: 'system',
        content: `✓ Backfill complete: ${data.updated_count} sessions updated${data.failed_count > 0 ? `, ${data.failed_count} failed` : ''}`,
        timestamp: new Date().toISOString()
      });
      socket.emit('list_sessions');
    });

    // Handler functions
    const handleAssistantChunk = (data) => {
      const store = useStore.getState();
      if (!store.currentAssistantMessage) {
        const newMessage = {
          role: 'assistant',
          content: data.text,
          timestamp: new Date().toISOString(),
          isStreaming: true
        };
        addMessage(newMessage);
        setCurrentAssistantMessage(newMessage);
      } else {
        appendToCurrentAssistant(data.text);
      }

      if (data.session_id) {
        setSessionId(data.session_id);
      }
    };

    const handleAssistantComplete = (data) => {
      setCurrentAssistantMessage(null);
      clearContentBlocks();
      setWaitingForResponse(false);

      if (data.session_id) {
        setSessionId(data.session_id);
      }
    };

    const handleToolUse = (data) => {
      addMessage({
        role: 'tool',
        toolName: data.tool,
        input: data.input,
        timestamp: new Date().toISOString()
      });
    };

    const handleSessionResumed = (data) => {
      console.log('Session resumed:', data.session_id);
      const history = (data.history || []).map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: new Date().toISOString()
      }));
      resumeSession(data.session_id, history);
    };

    const handleContentBlockStart = (data) => {
      addContentBlock(data.index, {
        type: data.type,
        tool_name: data.tool_name,
        tool_id: data.tool_id,
        accumulated_json: '',
        status: 'running'
      });
    };

    const handleToolInputDelta = (data) => {
      updateContentBlock(data.index, {
        accumulated_json: data.accumulated_json
      });
    };

    const handleThinkingChunk = (data) => {
      const store = useStore.getState();
      const block = store.contentBlocks[data.index];
      updateContentBlock(data.index, {
        thinking_text: (block?.thinking_text || '') + data.text
      });
    };

    const handleContentBlockStop = (data) => {
      updateContentBlock(data.index, {
        status: 'completed',
        accumulated_json: data.accumulated_json
      });
    };

    // Load sessions on startup
    setTimeout(() => {
      socket.emit('list_sessions');
    }, 500);

    // Check for session in URL
    const urlParams = new URLSearchParams(window.location.search);
    const sessionIdFromUrl = urlParams.get('session');
    if (sessionIdFromUrl) {
      console.log('Auto-resuming session from URL:', sessionIdFromUrl);
      socket.emit('resume_session', { session_id: sessionIdFromUrl });
    }

    return () => {
      socket.disconnect();
    };
  }, []);
};

export default useSocket;
