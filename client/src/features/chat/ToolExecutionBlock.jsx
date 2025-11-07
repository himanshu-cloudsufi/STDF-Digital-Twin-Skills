import { useState } from 'react';
import { escapeHtml } from '../../utils/formatters';

const ToolExecutionBlock = ({ toolName, input, blockIndex, status = 'running', accumulatedJson }) => {
  const [isExpanded, setIsExpanded] = useState(false);

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
    displayName = toolName.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  }

  const formatJson = (json) => {
    try {
      const parsed = JSON.parse(json);
      return JSON.stringify(parsed, null, 2);
    } catch (e) {
      return json;
    }
  };

  return (
    <div className="bg-gray-50 border border-gray-300 rounded-lg my-3 overflow-hidden">
      <div
        className="flex justify-between items-center px-4 py-3 bg-white border-b border-gray-200 cursor-pointer hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2.5 flex-1">
          <span className="text-lg">{icon}</span>
          <span className="font-semibold text-sm text-gray-800">{displayName}</span>
          <span className={`px-3 py-1 rounded-full text-xs font-medium uppercase tracking-wide ${
            status === 'running' ? 'bg-blue-100 text-blue-800 animate-status-pulse' :
            status === 'completed' ? 'bg-green-100 text-green-800' :
            'bg-red-100 text-red-800'
          }`}>
            {status}
          </span>
        </div>
        <button className="p-1 hover:bg-gray-100 rounded">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
      </div>
      {isExpanded && (
        <div className="px-4 py-4 bg-white">
          <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
            Input Parameters:
          </div>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto font-mono text-xs leading-relaxed">
            <code>{accumulatedJson ? formatJson(accumulatedJson) : JSON.stringify(input, null, 2)}</code>
          </pre>
        </div>
      )}
    </div>
  );
};

export default ToolExecutionBlock;
