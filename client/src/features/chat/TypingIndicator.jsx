const TypingIndicator = () => {
  return (
    <div className="flex justify-start mb-3">
      <div className="flex gap-1 px-3.5 py-2.5 bg-white border border-gray-300 rounded w-fit">
        <div className="w-1.5 h-1.5 bg-gray-600 rounded-full typing-dot"></div>
        <div className="w-1.5 h-1.5 bg-gray-600 rounded-full typing-dot"></div>
        <div className="w-1.5 h-1.5 bg-gray-600 rounded-full typing-dot"></div>
      </div>
    </div>
  );
};

export default TypingIndicator;
