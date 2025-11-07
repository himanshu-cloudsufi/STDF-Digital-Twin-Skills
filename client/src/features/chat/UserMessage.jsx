const UserMessage = ({ content }) => {
  return (
    <div className="flex justify-end mb-3">
      <div className="max-w-[70%] px-3.5 py-2.5 rounded bg-primary text-white text-sm leading-relaxed">
        {content}
      </div>
    </div>
  );
};

export default UserMessage;
