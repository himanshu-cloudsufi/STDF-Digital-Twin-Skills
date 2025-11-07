const SystemMessage = ({ content }) => {
  return (
    <div className="flex justify-center mb-3">
      <div className="max-w-[80%] px-3 py-2 rounded bg-yellow-100 text-yellow-800 border border-yellow-200 text-xs">
        {content}
      </div>
    </div>
  );
};

export default SystemMessage;
