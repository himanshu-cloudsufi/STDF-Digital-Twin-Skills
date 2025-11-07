import { formatTimeAgo, escapeHtml } from '../../utils/formatters';
import useStore from '../../store/useStore';

const SessionItem = ({ session, isActive, isCompareMode, isSelected }) => {
  const { socket, sessionId, isCompareMode: compareModeActive, toggleSessionSelection } = useStore();

  const handleClick = () => {
    if (compareModeActive) {
      toggleSessionSelection(session.session_id);
    } else if (session.session_id !== sessionId) {
      socket?.emit('resume_session', { session_id: session.session_id });
    }
  };

  const handleRename = (e) => {
    e.stopPropagation();
    const newTitle = prompt('Enter new title:', session.title);
    if (newTitle && newTitle.trim() !== '' && newTitle !== session.title) {
      socket?.emit('update_session_title', {
        session_id: session.session_id,
        title: newTitle.trim()
      });
    }
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    if (confirm('Delete this conversation? This action cannot be undone.')) {
      socket?.emit('delete_session', { session_id: session.session_id });
    }
  };

  return (
    <div
      className={`group bg-white border border-gray-300 rounded-md mb-2 cursor-pointer transition-all overflow-hidden ${
        isActive ? 'bg-blue-50 border-primary' : 'hover:bg-gray-50 hover:border-primary'
      }`}
      onClick={handleClick}
    >
      <div className="px-3 py-3">
        <div className="flex justify-between items-start gap-2 mb-1.5">
          {compareModeActive && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => toggleSessionSelection(session.session_id)}
              onClick={(e) => e.stopPropagation()}
              className="mt-1 w-[18px] h-[18px] cursor-pointer accent-primary"
            />
          )}
          <div className="flex-1 text-sm font-medium text-secondary overflow-hidden text-ellipsis whitespace-nowrap">
            {session.title}
          </div>
          {!compareModeActive && (
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleRename}
                className="p-1 bg-transparent border-none rounded cursor-pointer hover:bg-blue-50 hover:text-primary transition-all"
                title="Rename"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
              <button
                onClick={handleDelete}
                className="p-1 bg-transparent border-none rounded cursor-pointer hover:bg-red-50 hover:text-danger transition-all"
                title="Delete"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </div>
          )}
        </div>
        <div className="flex gap-2.5 text-xs text-gray-600">
          <span>{formatTimeAgo(session.last_activity)}</span>
          <span>{session.message_count} messages</span>
        </div>
      </div>
    </div>
  );
};

export default SessionItem;
