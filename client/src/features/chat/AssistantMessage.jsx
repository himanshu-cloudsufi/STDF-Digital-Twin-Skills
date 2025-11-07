import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const AssistantMessage = ({ content }) => {
  return (
    <div className="flex justify-start mb-3">
      <div className="max-w-[70%] px-3.5 py-2.5 rounded bg-white text-gray-900 text-sm leading-relaxed border border-gray-300 prose prose-sm max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default AssistantMessage;
