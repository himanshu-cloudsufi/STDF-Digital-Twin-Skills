import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import useStore from '../../store/useStore';

/**
 * Parse XML artifacts from text content
 * Returns array of {type, content, originalXml}
 */
const parseArtifacts = (text) => {
  const artifacts = [];

  // Define artifact types to extract
  const artifactTypes = [
    'action_plan',
    'knowledge_graph',
    'query_understanding',
    'forecast_data',
    'mathematical_analysis',
    'technological_convergence',
    'market_transformation',
    'strategic_implications',
    'news_articles',
    'references'
  ];

  artifactTypes.forEach(type => {
    const regex = new RegExp(`<${type}>(.*?)</${type}>`, 's');
    const match = text.match(regex);

    if (match) {
      artifacts.push({
        type,
        content: match[1].trim(),
        originalXml: match[0]
      });
    }
  });

  return artifacts;
};

/**
 * Remove XML artifacts from text, leaving only surrounding content
 */
const removeArtifacts = (text) => {
  const artifactTypes = [
    'action_plan',
    'knowledge_graph',
    'query_understanding',
    'forecast_data',
    'mathematical_analysis',
    'technological_convergence',
    'market_transformation',
    'strategic_implications',
    'news_articles',
    'references'
  ];

  let cleanText = text;
  artifactTypes.forEach(type => {
    const regex = new RegExp(`<${type}>.*?</${type}>`, 's');
    cleanText = cleanText.replace(regex, '');
  });

  return cleanText.trim();
};

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
 * Button component for opening an artifact in the side panel
 */
const ArtifactButton = ({ type, content, messageIndex, onClick }) => {
  const title = getArtifactTitle(type);

  const icon = type === 'action_plan' ? '📋' :
               type === 'knowledge_graph' ? '🕸️' :
               type === 'query_understanding' ? '🔍' :
               type === 'forecast_data' ? '📊' :
               type === 'mathematical_analysis' ? '🧮' :
               type === 'technological_convergence' ? '🔬' :
               type === 'market_transformation' ? '📈' :
               type === 'strategic_implications' ? '💡' :
               type === 'news_articles' ? '📰' :
               type === 'references' ? '📚' : '📄';

  return (
    <button
      onClick={() => onClick({ type, content }, messageIndex)}
      className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm hover:shadow-md"
    >
      <span className="text-lg">{icon}</span>
      <span className="font-medium text-sm text-gray-800">{title}</span>
      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
    </button>
  );
};

/**
 * Main component: renders artifacts with buttons
 */
const ArtifactRenderer = ({ content, messageIndex }) => {
  const { openArtifactPanel } = useStore();
  const artifacts = parseArtifacts(content);
  const cleanContent = removeArtifacts(content);

  const handleArtifactClick = (artifact, msgIndex) => {
    openArtifactPanel(artifact, msgIndex);
  };

  if (artifacts.length === 0) {
    // No artifacts, just render markdown
    return (
      <div className="prose prose-sm max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Render non-artifact content first */}
      {cleanContent && (
        <div className="prose prose-sm max-w-none mb-4">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {cleanContent}
          </ReactMarkdown>
        </div>
      )}

      {/* Render artifact buttons */}
      <div className="flex flex-wrap gap-2">
        {artifacts.map((artifact, idx) => (
          <ArtifactButton
            key={`${artifact.type}-${idx}`}
            type={artifact.type}
            content={artifact.content}
            messageIndex={messageIndex}
            onClick={handleArtifactClick}
          />
        ))}
      </div>
    </div>
  );
};

export default ArtifactRenderer;
