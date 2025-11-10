import ArtifactRenderer from './ArtifactRenderer';

const AssistantMessage = ({ content, messageIndex }) => {
  return (
    <div className="flex justify-start mb-3">
      <div className="max-w-[85%] px-3.5 py-2.5 rounded bg-white text-gray-900 text-sm leading-relaxed border border-gray-300">
        <ArtifactRenderer content={content} messageIndex={messageIndex} />
      </div>
    </div>
  );
};

export default AssistantMessage;
