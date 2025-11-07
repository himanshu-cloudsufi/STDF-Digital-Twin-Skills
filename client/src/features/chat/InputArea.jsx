import { useState, useRef, useEffect } from 'react';
import useStore from '../../store/useStore';

const InputArea = () => {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef(null);
  const { socket, sessionId, isWaitingForResponse, addMessage, setWaitingForResponse } = useStore();

  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  const handleSend = () => {
    const message = inputValue.trim();

    if (!message || isWaitingForResponse || !socket) {
      return;
    }

    // Add user message
    addMessage({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    });

    // Clear input
    setInputValue('');

    // Send to server
    socket.emit('message', {
      message: message,
      session_id: sessionId
    });

    // Set waiting state
    setWaitingForResponse(true);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-300 bg-white p-4">
      <div className="flex gap-2.5 mb-2.5">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about demand forecasts, tipping points, or disruption timelines..."
          rows={1}
          className="flex-1 px-2.5 py-2.5 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:border-primary font-sans"
          disabled={isWaitingForResponse}
        />
        <button
          onClick={handleSend}
          disabled={!inputValue.trim() || isWaitingForResponse}
          className="w-10 h-10 flex items-center justify-center border-none bg-primary text-white rounded cursor-pointer disabled:bg-gray-400 disabled:cursor-not-allowed hover:bg-primary-dark transition-colors"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default InputArea;
