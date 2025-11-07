import { useEffect, useRef } from 'react';
import { marked } from 'marked';
import useStore from '../../store/useStore';

const ComparisonModal = () => {
  const contentRef = useRef(null);
  const { showComparisonModal, comparisonData, closeComparisonModal } = useStore();

  useEffect(() => {
    if (contentRef.current && comparisonData?.comparison) {
      try {
        contentRef.current.innerHTML = marked.parse(comparisonData.comparison);
      } catch (error) {
        console.error('Markdown rendering error:', error);
        contentRef.current.textContent = comparisonData.comparison;
      }
    }
  }, [comparisonData]);

  if (!showComparisonModal) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      closeComparisonModal();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-[9999] backdrop-blur-sm animate-fade-in"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-[90%] max-h-[85vh] flex flex-col animate-slide-up">
        <div className="px-6 py-5 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Chat Comparison Results</h2>
          <button
            onClick={closeComparisonModal}
            className="bg-transparent border-none cursor-pointer p-2 flex items-center justify-center rounded-md hover:bg-gray-100 transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 py-6 overflow-y-auto flex-1">
          {comparisonData ? (
            <>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-5">
                <div className="flex items-center gap-2 mb-2 text-sm">
                  <strong className="text-gray-700">Chat 1:</strong>
                  <span>{comparisonData.session_1.title}</span>
                  <span className="text-gray-600 text-xs ml-auto">
                    ({comparisonData.session_1.message_count} messages)
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <strong className="text-gray-700">Chat 2:</strong>
                  <span>{comparisonData.session_2.title}</span>
                  <span className="text-gray-600 text-xs ml-auto">
                    ({comparisonData.session_2.message_count} messages)
                  </span>
                </div>
              </div>

              <div
                ref={contentRef}
                className="leading-relaxed text-gray-700 prose prose-sm max-w-none"
              />
            </>
          ) : (
            <div className="text-center p-10 text-gray-600 text-base">
              <div className="text-4xl mb-3 animate-spin-loader">⏳</div>
              Analyzing chats with Haiku model...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ComparisonModal;
