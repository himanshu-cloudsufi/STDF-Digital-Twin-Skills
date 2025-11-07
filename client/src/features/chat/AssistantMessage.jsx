import { marked } from 'marked';
import { useEffect, useRef } from 'react';

// Configure marked options
marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: false,
  mangle: false,
});

const AssistantMessage = ({ content }) => {
  const contentRef = useRef(null);

  useEffect(() => {
    if (contentRef.current && content) {
      try {
        contentRef.current.innerHTML = marked.parse(content);
      } catch (error) {
        console.error('Markdown rendering error:', error);
        contentRef.current.textContent = content;
      }
    }
  }, [content]);

  return (
    <div className="flex justify-start mb-3">
      <div
        ref={contentRef}
        className="max-w-[70%] px-3.5 py-2.5 rounded bg-white text-gray-900 text-sm leading-relaxed border border-gray-300 prose prose-sm max-w-none"
      />
    </div>
  );
};

export default AssistantMessage;
