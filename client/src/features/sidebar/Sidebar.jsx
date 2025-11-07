import useStore from '../../store/useStore';
import SessionList from './SessionList';

const Sidebar = () => {
  const {
    isSidebarCollapsed,
    toggleSidebar,
    startNewChat,
    isCompareMode,
    toggleCompareMode,
    selectedSessions,
    socket
  } = useStore();

  const handleCompare = () => {
    if (selectedSessions.length === 2) {
      socket?.emit('compare_sessions', {
        session_id_1: selectedSessions[0],
        session_id_2: selectedSessions[1]
      });
    }
  };

  return (
    <aside
      className={`w-[280px] bg-gray-50 border-r border-gray-300 flex flex-col transition-all duration-300 ${
        isSidebarCollapsed ? '-ml-[280px]' : 'ml-0'
      } md:relative md:ml-0`}
    >
      <div className="flex justify-between items-center px-4 py-4 bg-secondary text-white border-b border-secondary-dark">
        <h3 className="text-base font-medium">Chat History</h3>
        <button
          onClick={toggleSidebar}
          className="bg-transparent border-none text-white cursor-pointer p-1.5 flex items-center justify-center rounded hover:bg-white/10"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
      </div>

      <button
        onClick={startNewChat}
        className="m-4 px-4 py-2.5 bg-primary text-white border-none rounded-md text-sm font-medium cursor-pointer flex items-center gap-2 justify-center transition-colors hover:bg-primary-dark"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 5v14M5 12h14" />
        </svg>
        New Chat
      </button>

      <button
        onClick={toggleCompareMode}
        className={`w-[calc(100%-32px)] px-4 py-3 mx-4 mb-4 border rounded-lg text-sm font-medium cursor-pointer transition-all flex items-center justify-center gap-2 ${
          isCompareMode
            ? 'bg-blue-100 border-blue-500 text-blue-800'
            : 'bg-gray-100 border-gray-300 text-gray-700 hover:bg-gray-200 hover:border-gray-400'
        }`}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 11l3 3L22 4" />
          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
        </svg>
        Compare Chats
      </button>

      {isCompareMode && (
        <div className="px-3 py-3 bg-blue-50 border border-blue-200 rounded-lg mx-4 mb-4">
          <p className="text-xs text-blue-800 text-center mb-3 font-medium">
            {selectedSessions.length === 0
              ? 'Select 2 chats to compare'
              : selectedSessions.length === 1
              ? 'Select 1 more chat'
              : 'Ready to compare!'}
          </p>
          <button
            onClick={handleCompare}
            disabled={selectedSessions.length !== 2}
            className="w-full px-4 py-2.5 bg-primary text-white border-none rounded-md text-sm font-semibold cursor-pointer transition-all mb-2 disabled:bg-gray-400 disabled:cursor-not-allowed hover:bg-primary-dark hover:-translate-y-0.5"
          >
            Compare Selected
          </button>
          <button
            onClick={toggleCompareMode}
            className="w-full px-4 py-2 bg-transparent text-gray-600 border border-gray-300 rounded-md text-xs cursor-pointer transition-all hover:bg-gray-100 hover:border-gray-400"
          >
            Cancel
          </button>
        </div>
      )}

      <SessionList />
    </aside>
  );
};

export default Sidebar;
