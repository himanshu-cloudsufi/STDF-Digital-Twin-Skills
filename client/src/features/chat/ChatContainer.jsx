import { useEffect, useRef } from 'react';
import useStore from '../../store/useStore';
import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';
import SystemMessage from './SystemMessage';
import TypingIndicator from './TypingIndicator';
import ToolExecutionBlock from './ToolExecutionBlock';

const WelcomeMessage = () => (
  <div className="bg-white p-4 border border-gray-200 mb-4">
    <h2 className="text-base font-semibold mb-2.5">Available Forecasts</h2>
    <p className="text-sm leading-relaxed mb-2">
      <strong>Products:</strong> Electric vehicles, solar panels, batteries, commercial vehicles
    </p>
    <p className="text-sm leading-relaxed mb-2">
      <strong>Commodities:</strong> Copper, lithium, lead, coal, oil, natural gas
    </p>
    <p className="text-sm leading-relaxed mb-2">
      <strong>Disruptions:</strong> Cross-market impacts and displacement timelines
    </p>
    <p className="mt-2.5 px-2.5 py-2.5 bg-gray-100 border-l-2 border-gray-600 text-xs">
      Example: "What is the forecast for electric vehicles in China through 2040?"
    </p>
  </div>
);

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
      {messages.length === 0 && !currentAssistantMessage && <WelcomeMessage />}

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
