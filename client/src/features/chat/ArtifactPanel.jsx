import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import useStore from '../../store/useStore';

/**
 * Get user-friendly title for artifact type
 */
const getArtifactTitle = (type) => {
  const titles = {
    'action_plan': 'Action Plan',
    'knowledge_graph': 'Knowledge Graph',
    'query_understanding': 'Query Understanding',
    'forecast_data': 'Forecast Data',
    'mathematical_analysis': 'Mathematical Analysis',
    'technological_convergence': 'Technological Convergence',
    'market_transformation': 'Market Transformation',
    'strategic_implications': 'Strategic Implications',
    'news_articles': 'News Articles',
    'references': 'References'
  };

  return titles[type] || type;
};

/**
 * Get icon for artifact type
 */
const getArtifactIcon = (type) => {
  const icons = {
    'action_plan': '📋',
    'knowledge_graph': '🕸️',
    'query_understanding': '🔍',
    'forecast_data': '📊',
    'mathematical_analysis': '🧮',
    'technological_convergence': '🔬',
    'market_transformation': '📈',
    'strategic_implications': '💡',
    'news_articles': '📰',
    'references': '📚'
  };

  return icons[type] || '📄';
};

/**
 * Render artifact content based on type
 */
const renderArtifactContent = (type, content) => {
  if (type === 'action_plan') {
    // Extract steps from <step> tags
    const stepMatches = content.matchAll(/<step>(.*?)<\/step>/gs);
    const steps = Array.from(stepMatches, m => m[1].trim());

    if (steps.length > 0) {
      return (
        <ol className="list-decimal list-inside space-y-2 text-sm">
          {steps.map((step, idx) => (
            <li key={idx} className="text-gray-700">{step}</li>
          ))}
        </ol>
      );
    }
  }

  if (type === 'knowledge_graph') {
    // Parse nodes and relationships
    const nodesMatch = content.match(/<nodes>(.*?)<\/nodes>/s);
    const relationshipsMatch = content.match(/<relationships>(.*?)<\/relationships>/s);

    if (nodesMatch || relationshipsMatch) {
      return (
        <div className="space-y-4">
          {nodesMatch && (
            <div>
              <h4 className="font-semibold text-sm mb-2 text-gray-800">Nodes</h4>
              <div className="text-xs text-gray-600 font-mono bg-gray-50 p-3 rounded overflow-x-auto">
                {nodesMatch[1].trim()}
              </div>
            </div>
          )}

          {relationshipsMatch && (
            <div>
              <h4 className="font-semibold text-sm mb-2 text-gray-800">Relationships</h4>
              <div className="text-xs text-gray-600 font-mono bg-gray-50 p-3 rounded overflow-x-auto">
                {relationshipsMatch[1].trim()}
              </div>
            </div>
          )}
        </div>
      );
    }
  }

  if (type === 'query_understanding') {
    // Extract sections
    const detailedPlanMatch = content.match(/<detailed_plan>(.*?)<\/detailed_plan>/s);
    const confirmationMatch = content.match(/<confirmation_query>(.*?)<\/confirmation_query>/s);
    const datasetsMatch = content.match(/<datasets>(.*?)<\/datasets>/s);
    const missingMatch = content.match(/<missing_datasets>(.*?)<\/missing_datasets>/s);

    return (
      <div className="space-y-4">
        {detailedPlanMatch && (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {detailedPlanMatch[1].trim()}
            </ReactMarkdown>
          </div>
        )}

        {datasetsMatch && (
          <div>
            <h4 className="font-semibold text-sm mb-2 text-gray-800">Datasets</h4>
            <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
              {Array.from(datasetsMatch[1].matchAll(/<dataset>(.*?)<\/dataset>/gs), m =>
                <li key={m[1]}>{m[1].trim()}</li>
              )}
            </ul>
          </div>
        )}

        {missingMatch && (
          <div>
            <h4 className="font-semibold text-sm mb-2 text-gray-800">Missing Datasets</h4>
            <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
              {Array.from(missingMatch[1].matchAll(/<dataset>(.*?)<\/dataset>/gs), m =>
                <li key={m[1]}>{m[1].trim()}</li>
              )}
            </ul>
          </div>
        )}

        {confirmationMatch && (
          <div className="text-sm italic text-gray-700 border-l-4 border-blue-500 pl-3">
            {confirmationMatch[1].trim()}
          </div>
        )}
      </div>
    );
  }

  if (type === 'forecast_data') {
    // Parse datasets
    const datasetMatches = content.matchAll(/<dataset\s+(.*?)>(.*?)<\/dataset>/gs);
    const datasets = Array.from(datasetMatches, m => ({
      attrs: m[1],
      content: m[2].trim()
    }));

    if (datasets.length > 0) {
      return (
        <div className="space-y-4">
          {datasets.map((dataset, idx) => {
            // Parse attributes
            const nameMatch = dataset.attrs.match(/name="([^"]+)"/);
            const typeMatch = dataset.attrs.match(/type="([^"]+)"/);
            const unitsMatch = dataset.attrs.match(/units="([^"]+)"/);
            const regionMatch = dataset.attrs.match(/region="([^"]+)"/);

            // Parse content
            const descMatch = dataset.content.match(/<description>(.*?)<\/description>/s);
            const xMatch = dataset.content.match(/<x>(.*?)<\/x>/s);
            const yMatch = dataset.content.match(/<y>(.*?)<\/y>/s);

            return (
              <div key={idx} className="border border-gray-200 rounded p-3 bg-gray-50">
                <h5 className="font-semibold text-sm mb-2 text-gray-800">
                  {nameMatch ? nameMatch[1] : `Dataset ${idx + 1}`}
                </h5>

                {descMatch && (
                  <p className="text-xs text-gray-600 mb-2">{descMatch[1].trim()}</p>
                )}

                <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                  {typeMatch && (
                    <div><span className="font-medium">Type:</span> {typeMatch[1]}</div>
                  )}
                  {unitsMatch && (
                    <div><span className="font-medium">Units:</span> {unitsMatch[1]}</div>
                  )}
                  {regionMatch && (
                    <div><span className="font-medium">Region:</span> {regionMatch[1]}</div>
                  )}
                </div>

                {xMatch && yMatch && (
                  <div className="text-xs font-mono bg-white p-2 rounded overflow-x-auto">
                    <div className="mb-1"><span className="font-semibold">X:</span> {xMatch[1].trim()}</div>
                    <div><span className="font-semibold">Y:</span> {yMatch[1].trim()}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      );
    }
  }

  // Default: render as markdown
  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
};

/**
 * Resizable artifact panel that slides in from the right
 */
const ArtifactPanel = () => {
  const {
    sessionId,
    artifactPanelState,
    closeArtifactPanel,
    setArtifactPanelWidth
  } = useStore();

  const currentSessionId = sessionId || 'temp';
  const panelState = artifactPanelState[currentSessionId] || {
    isOpen: false,
    currentArtifact: null,
    panelWidth: 450
  };

  const { isOpen, currentArtifact, panelWidth } = panelState;

  const [isDragging, setIsDragging] = useState(false);
  const panelRef = useRef(null);
  const dragStartX = useRef(0);
  const dragStartWidth = useRef(0);

  // Handle resize drag
  const handleMouseDown = (e) => {
    setIsDragging(true);
    dragStartX.current = e.clientX;
    dragStartWidth.current = panelWidth;
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging) return;

      const deltaX = dragStartX.current - e.clientX; // Inverted because drag left = wider
      const newWidth = Math.max(300, Math.min(800, dragStartWidth.current + deltaX));
      setArtifactPanelWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, setArtifactPanelWidth]);

  if (!isOpen || !currentArtifact) {
    return null;
  }

  const { type, content } = currentArtifact;
  const title = getArtifactTitle(type);
  const icon = getArtifactIcon(type);

  return (
    <div
      ref={panelRef}
      className="h-full bg-white border-l border-gray-300 shadow-lg flex flex-col transition-all duration-300"
      style={{
        width: `${panelWidth}px`,
        minWidth: '300px',
        maxWidth: '800px'
      }}
    >
      {/* Resize Handle */}
      <div
        className={`absolute top-0 left-0 w-1.5 h-full cursor-col-resize hover:bg-blue-500 transition-colors ${isDragging ? 'bg-blue-600' : 'bg-gray-300'}`}
        onMouseDown={handleMouseDown}
        title="Drag to resize"
      />

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
        </div>
        <button
          onClick={closeArtifactPanel}
          className="p-2 rounded-lg hover:bg-gray-200 transition-colors text-gray-600 hover:text-gray-800"
          title="Close panel"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {renderArtifactContent(type, content)}
      </div>

      {/* Footer with resize hint */}
      <div className="px-6 py-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-500 text-center">
        Drag the left edge to resize
      </div>
    </div>
  );
};

export default ArtifactPanel;
