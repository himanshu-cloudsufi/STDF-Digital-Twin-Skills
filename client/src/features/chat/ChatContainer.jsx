import { useEffect, useRef } from 'react';
import useStore from '../../store/useStore';
import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';
import SystemMessage from './SystemMessage';
import TypingIndicator from './TypingIndicator';
import ToolExecutionBlock from './ToolExecutionBlock';



const ChatContainer = () => {
  const containerRef = useRef(null);
  const { messages, currentAssistantMessage, contentBlocks, isWaitingForResponse } = useStore();

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, currentAssistantMessage, contentBlocks, isWaitingForResponse]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto p-4 bg-gray-50 custom-scrollbar"
    >

      {messages.map((message, index) => {
        if (message.role === 'user') {
          return <UserMessage key={index} content={message.content} />;
        } else if (message.role === 'assistant') {
          return <AssistantMessage key={index} content={message.content} />;
        } else if (message.role === 'system') {
          return <SystemMessage key={index} content={message.content} />;
        } else if (message.role === 'tool') {
          return (
            <ToolExecutionBlock
              key={index}
              toolName={message.toolName}
              input={message.input}
              blockIndex={index}
            />
          );
        }
        return null;
      })}

      {currentAssistantMessage && (
        <AssistantMessage content={currentAssistantMessage.content} />
      )}

      {Object.entries(contentBlocks).map(([index, block]) => {
        if (block.type === 'tool_use' || block.type === 'server_tool_use') {
          return (
            <ToolExecutionBlock
              key={`block-${index}`}
              toolName={block.tool_name}
              input={block.input}
              blockIndex={index}
              status={block.status}
              accumulatedJson={block.accumulated_json}
            />
          );
        } else if (block.type === 'thinking') {
          return (
            <div key={`block-${index}`} className="bg-yellow-50 border border-yellow-300 rounded-lg my-3 overflow-hidden">
              <div className="px-4 py-3 bg-yellow-100 border-b border-yellow-200 font-semibold text-sm text-yellow-900">
                <span className="mr-2">💭</span>
                Claude's Thinking Process
              </div>
              <div className="px-4 py-4 bg-yellow-50 text-yellow-900 text-sm font-mono whitespace-pre-wrap">
                {block.thinking_text || 'Thinking...'}
              </div>
            </div>
          );
        }
        return null;
      })}

      {isWaitingForResponse && !currentAssistantMessage && <TypingIndicator />}
    </div>
  );
};

export default ChatContainer;
